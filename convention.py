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
import zlib
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

FORBIDDEN_CHARS = tuple(SCHEMA.get("forbidden_chars", ()))

FLAG_MULTI = "plusieurs locuteurs"
FLAG_UNCERTAIN = "transcription incertaine"
FLAG_PERSONAL = "données personnelles"
TAG_PERSONAL = "[personnel]"
DIALECT_MULTI = "plusieurs"
# Flags that keep a segment out of training (schema: export.exclude_from_train_if).
NO_TRAIN_FLAGS = tuple(c["indicateurs_contains"] for c in SCHEMA["export"]["exclude_from_train_if"]
                       if "indicateurs_contains" in c)
NO_PUBLISH_FLAGS = tuple(c["indicateurs_contains"]
                         for c in SCHEMA["export"].get("exclude_from_publication_until_audio_masked_if", [])
                         if "indicateurs_contains" in c)

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
    if TAG_PERSONAL in text and FLAG_PERSONAL in FLAGS and FLAG_PERSONAL not in flags:
        out.append(_issue(f"Le texte contient {TAG_PERSONAL} : cocher l'indicateur « {FLAG_PERSONAL} » (règle 6.1).",
                          {"type": "flag", "value": FLAG_PERSONAL, "label": f"Cocher « {FLAG_PERSONAL} »"}))
    for ch in FORBIDDEN_CHARS:
        if ch in text:
            out.append(_issue(f"Apostrophe typographique {ch} interdite : écrire l'apostrophe droite ' (règle 2).",
                              {"type": "replace", "from": ch, "to": "'", "label": f"Remplacer {ch} par '"}))
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
    for ch in FORBIDDEN_CHARS:  # already reported as errors
        plain = plain.replace(ch, "'")
    bad = sorted(set(ALLOWED_CHARS_RE.findall(plain)) - {"_"})
    if bad:
        out.append(_issue(f"Ponctuation non permise : {' '.join(bad)}. Seuls . , ? sont autorisés (règle 5)."))
    for acro in sorted(set(DOTTED_ACRONYM_RE.findall(text))):
        fixed = acro.replace(".", "").upper()
        out.append(_issue(f"Sigle « {acro} » : en capitales, sans points ({fixed}) (règle 5).",
                          {"type": "replace", "from": acro, "to": fixed, "label": f"Écrire {fixed}"}))
    for title in sorted(set(m.group(0) for m in TITLE_RE.finditer(text))):
        out.append(_issue(f"« {title} » : écrire le titre tel qu'il est prononcé, ex. dokotera Rabe ou docteur Rabe (règle 5)."))
    # Rule 5.1: the sentence decides, not the segment (a segment may start mid-sentence), so
    # only a lowercase letter right after . or ? inside the segment is suspicious.
    after_stop = sorted(set(m.group(1) for m in re.finditer(r"[.?]\s+(\w+)", plain) if m.group(1)[0].islower()))
    if after_stop:
        out.append(_issue(f"Après un point ou un ?, la phrase suivante prend une majuscule : {', '.join(after_stop[:5])} (règle 5.1)."))
    for word in sorted(set(m.group(0) for m in re.finditer(r"\b(\w+)-(\1)\b", plain, re.I))):
        joined = word.replace("-", "")
        out.append(_issue(f"Redoublement « {word} » : un seul mot, sans tiret ({joined}) (règle 2).",
                          {"type": "replace", "from": word, "to": joined, "label": f"Écrire {joined}"}))
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
    loop = loop_reasons(text, duration)
    if loop:
        out.append(_issue("Répétition suspecte dans la transcription (" + " ; ".join(loop) + "). Réécouter et ne "
                          "garder que ce qui est réellement dit : boucle Whisper ou vraie répétition (règle 7.4)."))
    norm = " ".join(text.split()).lower()
    if norm and any(norm == " ".join((d or "").split()).lower() for d in drafts):
        out.append(_issue("Texte identique au brouillon automatique : le relire mot à mot avant de valider (règle 7)."))
    return out


# --- Whisper loops (rule 7.4, technical annex) -------------------------------------------------
COMPRESSION_THRESHOLD = 2.4   # Whisper's own compression_ratio_threshold
MAX_WORDS_PER_SECOND = 6.0    # Malagasy speech rarely goes past 4 to 5 short words per second


def _words(text: str) -> list[str]:
    return [w for w in re.split(r"[^\w']+", TAG_RE.sub(" ", text).lower()) if w]


def loop_reasons(text: str, duration: float | None = None) -> list[str]:
    """Why a text looks like a Whisper loop (empty list = nothing suspicious)."""
    text = (text or "").strip()
    out = []
    raw = text.encode("utf-8")
    if len(raw) >= 40:
        ratio = len(raw) / len(zlib.compress(raw))
        if ratio > COMPRESSION_THRESHOLD:
            out.append(f"texte très répétitif (taux de compression {ratio:.1f} > {COMPRESSION_THRESHOLD})")
    words = _words(text)
    best = None  # (repetitions, n-gram)
    for n in range(1, 9):
        for i in range(len(words) - n):
            gram, reps = words[i:i + n], 1
            while words[i + reps * n:i + (reps + 1) * n] == gram:
                reps += 1
            if reps >= (4 if n == 1 else 3) and (best is None or reps * n > best[0] * len(best[1])):
                best = (reps, gram)
    if best:
        out.append(f"« {' '.join(best[1])} » répété {best[0]} fois de suite")
    sentences = [" ".join(_words(s)) for s in re.split(r"[.?!]+", text)]
    repeated = {s for s in sentences if len(s.split()) >= 4 and sentences.count(s) >= 2}
    if repeated and not best:
        s = next(iter(repeated))
        out.append(f"phrase répétée : « {s[:60]}{'…' if len(s) > 60 else ''} »")
    if duration and duration >= 1 and len(words) / duration > MAX_WORDS_PER_SECOND:
        out.append(f"{len(words)} mots pour {duration:.1f} s : trop de texte pour la durée")
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
    flags = meta.get("flags") or []
    out["train"] = not excluded and not any(f in flags for f in NO_TRAIN_FLAGS)
    # Not publishable until the audio is masked (schema: exclude_from_publication_until_audio_masked_if).
    out["publish"] = not any(f in flags for f in NO_PUBLISH_FLAGS)
    return out


def options() -> dict:
    return {"version": VERSION, "langs": LANGS, "registers": REGISTERS, "qualities": QUALITIES,
            "flags": FLAGS, "exclude_reasons": EXCLUDE_REASONS, "dialects": DIALECTS, "tags": TAGS,
            "speaker_pattern": SPEAKER_RE.pattern}
