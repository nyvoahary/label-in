"""PROVA-MG transcription convention: field values and validation rules.

The values come from static/annotation-schema.json (the reference, versioned with
static/convention-transcription-prova-mg.md), so updating that file updates the editor.

Annotations saved under the convention carry `convention` (the version they were validated
under) and `meta`:
    {"lang": "mg", "dialect": "betsileo", "register": "spontané", "quality": "propre",
     "speaker": "S1", "flags": ["chevauchement de voix"], "exclude_reason": "chant / musique"}
Annotations without `convention` were made before it ("avant convention").
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SCHEMA = json.loads((Path(__file__).parent / "static" / "annotation-schema.json").read_text("utf-8"))
_FIELDS = {f["name"]: f for f in SCHEMA["fields"]}

VERSION = SCHEMA["convention_version"]
LANGS = tuple(_FIELDS["langue"]["values"])
DIALECTS = tuple(_FIELDS["dialecte"]["values"])
REGISTERS = tuple(_FIELDS["registre"]["values"])
QUALITIES = tuple(_FIELDS["qualite"]["values"])
FLAGS = tuple(_FIELDS["indicateurs"]["values"])
EXCLUDE_REASONS = tuple(_FIELDS["raison_exclusion"]["values"])
TAGS = tuple(SCHEMA["allowed_tags"])
SPEAKER_RE = re.compile(_FIELDS["locuteur"]["pattern"])

FLAG_MULTI = "plusieurs locuteurs"
FLAG_UNCERTAIN = "transcription incertaine"
DIALECT_MULTI = "plusieurs"

TAG_RE = re.compile(r"\[[^\[\]]*\]")
SPEAKER_TAG_RE = re.compile(r"\[(S\d+)\]")
# Flag names used by the first test version of the editor.
_OLD_FLAGS = {"chevauchement": "chevauchement de voix", "incertain": "transcription incertaine",
              "nom_propre": "nom propre à vérifier", "emprunt_ambigu": "emprunt ambigu"}
# Internal key -> schema field name (used for the export).
SCHEMA_NAMES = {"lang": "langue", "dialect": "dialecte", "register": "registre", "quality": "qualite",
                "speaker": "locuteur", "flags": "indicateurs", "exclude_reason": "raison_exclusion"}


def clean_meta(raw) -> dict:
    """Keep only known fields with allowed values."""
    raw = raw if isinstance(raw, dict) else {}
    meta: dict = {}
    for key, allowed in (("lang", LANGS), ("dialect", DIALECTS), ("register", REGISTERS),
                         ("quality", QUALITIES), ("exclude_reason", EXCLUDE_REASONS)):
        if raw.get(key) in allowed:
            meta[key] = raw[key]
    speaker = str(raw.get("speaker") or "").strip().upper().replace(" ", "")
    if SPEAKER_RE.match(speaker):
        meta["speaker"] = speaker
    flags = raw.get("flags") if isinstance(raw.get("flags"), list) else []
    flags = {_OLD_FLAGS.get(f, f) for f in flags}
    meta["flags"] = [f for f in FLAGS if f in flags]
    return meta


def unknown_tags(text: str) -> list[str]:
    return sorted({t for t in TAG_RE.findall(text) if t not in TAGS and not SPEAKER_TAG_RE.fullmatch(t)})


def unknown_tag_message(tag: str) -> str:
    word = tag[1:-1].strip()
    hint = (f" Si c'est une hésitation, écrire [euh]. Si « {word} » est vraiment prononcé (interjection), "
            f"l'écrire sans crochets : {word}." if word else "")
    return f"Balise inconnue : {tag}.{hint} Balises permises : {' '.join(TAGS)} (et [S1], [S2]… règle 8.5)."


def problems(status: str, text: str, meta: dict) -> list[str]:
    """Reasons a segment can't be saved with this status (empty list = OK)."""
    out = []
    if status == "excluded":
        if not meta.get("exclude_reason"):
            out.append("Choisir la raison de l'exclusion.")
        return out
    if status != "done":
        return out
    if not text:
        out.append("La transcription est vide (ou exclure le segment).")
    labels = {"lang": "la langue", "dialect": "le dialecte", "register": "le registre",
              "quality": "la qualité audio", "speaker": "le locuteur"}
    missing = [label for key, label in labels.items() if not meta.get(key)]
    if missing:
        out.append("Renseigner " + ", ".join(missing) + ".")
    flags = meta.get("flags") or []
    if re.search(r"\d", SPEAKER_TAG_RE.sub("", text)):
        out.append("Chiffres interdits : écrire les nombres en lettres, dans la langue parlée (règle 4).")
    if "((" in text and FLAG_UNCERTAIN not in flags:
        out.append("Le texte contient ((mot)) : cocher l'indicateur « transcription incertaine ».")
    out += [unknown_tag_message(t) for t in unknown_tags(text)]

    # Rule 8.5: a segment with several speakers is written [S1] … [S2] …, speaker "S1+S2".
    tagged = SPEAKER_TAG_RE.findall(text)
    speakers = (meta.get("speaker") or "").split("+")
    multi = bool(tagged) or len(speakers) > 1 or FLAG_MULTI in flags or meta.get("dialect") == DIALECT_MULTI
    if multi:
        if not tagged:
            out.append("Plusieurs locuteurs (règle 8.5) : écrire [S1], [S2]… avant chaque tour de parole.")
        elif not re.match(r"\s*\[S\d+\]", text):
            out.append("La première prise de parole doit aussi commencer par sa balise, ex. [S1] (règle 8.5).")
        if len(speakers) < 2:
            out.append("Plusieurs locuteurs : le champ Locuteur doit les lister, ex. S1+S2 (règle 8.5).")
        elif tagged and re.match(r"\s*\[S\d+\]", text) and set(tagged) != set(speakers):
            shown = " ".join(f"[{s}]" for s in sorted(set(tagged)))
            out.append(f"Les balises du texte ({shown}) ne correspondent pas au champ Locuteur ({meta.get('speaker')}).")
        if FLAG_MULTI not in flags:
            out.append("Cocher l'indicateur « plusieurs locuteurs » (règle 8.5).")
    return out


def export_fields(anno: dict) -> dict:
    """The annotation in the schema's terms, for the export."""
    meta = anno.get("meta") or {}
    excluded = anno.get("status") == "excluded"
    out = {"label": "Exclu" if excluded else "Parole", "status": anno.get("status"),
           "convention_version": anno.get("convention")}
    for key, name in SCHEMA_NAMES.items():
        if key in meta:
            out[name] = meta[key]
    out["train"] = not excluded and FLAG_MULTI not in (meta.get("flags") or [])
    return out


def options() -> dict:
    return {"version": VERSION, "langs": LANGS, "registers": REGISTERS, "qualities": QUALITIES,
            "flags": FLAGS, "exclude_reasons": EXCLUDE_REASONS, "dialects": DIALECTS, "tags": TAGS,
            "speaker_pattern": SPEAKER_RE.pattern}
