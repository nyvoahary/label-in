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
    return out + [e["msg"] for e in text_errors(text, meta)]


def _issue(msg: str, fix: dict | None = None) -> dict:
    return {"msg": msg, "fix": fix} if fix else {"msg": msg}


def text_errors(text: str, meta: dict) -> list[dict]:
    """Blocking rules that depend on the text, each with a one-click fix when there is one."""
    out = []
    flags = meta.get("flags") or []
    if re.search(r"\d", SPEAKER_TAG_RE.sub("", text)):
        out.append(_issue("Chiffres interdits : écrire les nombres en lettres, dans la langue parlée (règle 4)."))
    if "((" in text and FLAG_UNCERTAIN not in flags:
        out.append(_issue("Le texte contient ((mot)) : cocher l'indicateur « transcription incertaine ».",
                          {"type": "flag", "value": FLAG_UNCERTAIN, "label": "Cocher « transcription incertaine »"}))
    out += [_issue(unknown_tag_message(t)) for t in unknown_tags(text)]

    # Rule 8.5: a segment with several speakers is written [S1] … [S2] …, speaker "S1+S2".
    tagged = SPEAKER_TAG_RE.findall(text)
    speakers = (meta.get("speaker") or "").split("+")
    multi = bool(tagged) or len(speakers) > 1 or FLAG_MULTI in flags or meta.get("dialect") == DIALECT_MULTI
    if multi:
        ids = "+".join(sorted(set(tagged), key=lambda s: int(s[1:])))
        if not tagged:
            out.append(_issue("Plusieurs locuteurs (règle 8.5) : écrire [S1], [S2]… avant chaque tour de parole."))
        elif not re.match(r"\s*\[S\d+\]", text):
            out.append(_issue("La première prise de parole doit aussi commencer par sa balise, ex. [S1] (règle 8.5)."))
        if tagged and set(tagged) != set(speakers) and (len(speakers) < 2 or re.match(r"\s*\[S\d+\]", text)):
            out.append(_issue(f"Le champ Locuteur doit lister les locuteurs des balises : {ids} (règle 8.5).",
                              {"type": "speaker", "value": ids, "label": f"Locuteur = {ids}"}))
        elif not tagged and len(speakers) < 2:
            out.append(_issue("Plusieurs locuteurs : le champ Locuteur doit les lister, ex. S1+S2 (règle 8.5)."))
        if FLAG_MULTI not in flags:
            out.append(_issue("Cocher l'indicateur « plusieurs locuteurs » (règle 8.5).",
                              {"type": "flag", "value": FLAG_MULTI, "label": "Cocher « plusieurs locuteurs »"}))
    return out


ALLOWED_CHARS_RE = re.compile(r"[^\w\s.,?'\-]")
MG_FORBIDDEN_RE = re.compile(r"[cquwxàâäçéèêëîïôöùûü]", re.I)
DOTTED_ACRONYM_RE = re.compile(r"\b(?:[A-Za-z]\.){2,}")
TITLE_RE = re.compile(r"\b(Dr|Pr|Mme|Mlle|Mr)\b\.?")


def text_warnings(text: str, meta: dict, duration: float | None = None, drafts: tuple = ()) -> list[dict]:
    """Likely mistakes that don't block saving: the transcriber may be right."""
    out = []
    # Text without the markup the convention allows.
    plain = SPEAKER_TAG_RE.sub(" ", TAG_RE.sub(" ", text)).replace("((", " ").replace("))", " ")
    if "’" in text:
        out.append(_issue("Apostrophe typographique ’ : écrire l'apostrophe simple '.",
                          {"type": "replace", "from": "’", "to": "'", "label": "Remplacer ’ par '"}))
    bad = sorted(set(ALLOWED_CHARS_RE.findall(plain.replace("’", "'"))) - {"_"})
    if bad:
        out.append(_issue(f"Ponctuation non permise : {' '.join(bad)}. Seuls . , ? sont autorisés (règle 5)."))
    for acro in sorted(set(DOTTED_ACRONYM_RE.findall(text))):
        fixed = acro.replace(".", "").upper()
        out.append(_issue(f"Sigle « {acro} » : en capitales, sans points ({fixed}) (règle 5).",
                          {"type": "replace", "from": acro, "to": fixed, "label": f"Écrire {fixed}"}))
    for title in sorted(set(m.group(0) for m in TITLE_RE.finditer(text))):
        out.append(_issue(f"« {title} » : écrire le titre tel qu'il est prononcé, ex. dokotera Rabe ou docteur Rabe (règle 5)."))
    first = re.search(r"[^\W\d_]", plain)
    if first and first.group(0).islower():
        out.append(_issue("Majuscule en début de phrase (règle 5).",
                          {"type": "capitalize", "label": "Mettre la majuscule"}))
    if meta.get("lang") == "mg":
        words = {w for w in re.split(r"[\s.,?]+", plain) if w}
        foreign = sorted(w for w in words if MG_FORBIDDEN_RE.search(w))
        if foreign:
            out.append(_issue(f"Langue « mg » mais {', '.join(foreign[:5])} : c, q, u, w, x et les accents n'existent pas "
                              "en malgache. Faute d'orthographe (règle 2), ou mot prononcé à la française : "
                              "alors langue « mixte » (règle 3).",
                              {"type": "lang", "value": "mixte", "label": "Passer en « mixte »"}))
        parts = {p.lower() for w in words - set(foreign) for p in re.split(r"['\-]", w) if len(p) > 1}
        final_i = sorted(p for p in parts if p.endswith("i"))
        inner_y = sorted(p for p in parts if "y" in p[:-1])
        if final_i:
            out.append(_issue(f"{', '.join(final_i[:5])} : en malgache, -y en fin de mot (misy, pas misi) (règle 2)."))
        if inner_y:
            out.append(_issue(f"{', '.join(inner_y[:5])} : en malgache, -i à l'intérieur du mot (fitiavana, pas fytiavana) (règle 2)."))
    if duration is not None and 0 < duration < 2:
        out.append(_issue("Segment de moins de 2 s : à garder seulement si c'est une réponse courte avec contenu, "
                          "sinon exclure (règle 8.2)."))
    elif duration and duration > 30:
        out.append(_issue("Segment de plus de 30 s : au-delà de la fenêtre de Whisper (règle 8)."))
    norm = " ".join(text.split()).lower()
    if norm and any(norm == " ".join((d or "").split()).lower() for d in drafts):
        out.append(_issue("Texte identique au brouillon automatique : le relire mot à mot avant de valider (règle 7)."))
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
