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
# Common French and English words (the editor's suggestion lists): tells a borrowed word (voyage,
# mixte) from a Malagasy misspelling (fytiavana) in the y-inside-a-word warning.
FOREIGN_WORDS = {w.lower() for lang in ("fr", "en")
                 for w in json.loads((Path(__file__).parent / "static" / f"{lang}_words.json").read_text("utf-8"))}
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
# Spellings fixed by the team (lexicon): {"anankiray": ["anaky iray", "anakiray"]}.
SPELLINGS = [(right, re.compile(r"\b(?:" + "|".join(re.escape(w).replace(r"\ ", r"\s+") for w in wrong) + r")\b", re.I))
             for right, wrong in SCHEMA.get("spellings", {}).items()]

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


def _issue(msg: str, fix: dict | None = None, words: list[str] | None = None) -> dict:
    """words: the words the issue is about, highlighted in the editor's text box."""
    out = {"msg": msg}
    if fix:
        out["fix"] = fix
    if words:
        out["words"] = words
    return out


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
# Rules 2 and 3: letters Malagasy never uses, and no Malagasy word ends with a consonant. Accents
# only count in the official dialect: regional dialects write some (ô…).
NOT_MG_LETTERS_RE = re.compile(r"[cquwx]", re.I)
FINAL_CONSONANT_RE = re.compile(r"[bdfghjklmnprstvz]$", re.I)
ACCENT_RE = re.compile(r"[àâäçéèêëîïôöùûü]", re.I)


def has_inner_y(word: str) -> bool:
    """y anywhere but at the end of a word (or of a part: izy-ireo, an'ny): not Malagasy (rule 2)."""
    return any("y" in p[:-1] for p in re.split(r"['\-]", word.lower()) if p)
DIALECT_OFFICIAL = "officiel (merina standard)"
DOUBLE_VOWEL_RE = re.compile(r"([aeiouy])\1+", re.I)
# "an" alone before , . ? ! or at the end, not after another "an" nor French "un" (the editor's
# fixParticleAn() rewrites what this finds).
PARTICLE_AN_RE = re.compile(r"(?<![\w'-])(?<!\ban )(?<!\bun )an(?=\s*[.,?!]|\s*$)", re.I)
# Wrong forms of the shared lexicon (zah, anah…) are Malagasy misspellings, reported on their own.
SPELLING_WRONG = {w.lower() for wrong in SCHEMA.get("spellings", {}).values() for w in wrong if " " not in w}


def not_malagasy(word: str, official: bool = True) -> bool:
    """A word that cannot be Malagasy (the editor's foreignWords() applies the same rule).
    Elided forms (tamin'), a-an (yes, rule 1.1) and lexicon misspellings are left out; a
    capitalised word (a name: Ra-Loob) may end with a consonant. y only ends a word (rule 2)."""
    w = word.strip("()")
    lw = w.lower()
    # "an" alone is the particle a misspelt (rule 1.1), reported on its own.
    if not lw or lw.endswith("'") or lw in ("a-an", "an") or lw in SPELLING_WRONG or re.search(r"\d", lw):
        return False
    return bool(NOT_MG_LETTERS_RE.search(lw) or (official and ACCENT_RE.search(lw)) or has_inner_y(lw)
                or (not w[0].isupper() and FINAL_CONSONANT_RE.search(lw)))


def mid_sentence_names(text: str) -> set[str]:
    """Capitalised words inside a sentence: names (Axel), not words of another language."""
    return {w for sentence in re.split(r"[.?!]+", text)
            for w in re.split(r"[\s,;:]+", sentence.strip())[1:] if w and w[0].isupper()}


DOTTED_ACRONYM_RE =re.compile(r"\b(?:[A-Za-z]\.){2,}")
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
        out.append(_issue(f"Après un point ou un ?, la phrase suivante prend une majuscule : {', '.join(after_stop[:5])} (règle 5.1).",
                          {"type": "sentence_caps", "label": "Mettre les majuscules"}))
    # Two letters or more: "a-a-a" (no) is a word of its own (rule 1.1), not a reduplication.
    for word in sorted(set(m.group(0) for m in re.finditer(r"\b(\w{2,})-(\1)\b", plain, re.I))):
        joined = word.replace("-", "")
        out.append(_issue(f"Redoublement « {word} » : un seul mot, sans tiret ({joined}) (règle 2).",
                          {"type": "replace", "from": word, "to": joined, "label": f"Écrire {joined}"}))
    for right, wrong_re in SPELLINGS:
        for found in sorted(set(m.group(0) for m in wrong_re.finditer(plain))):
            fixed = right[0].upper() + right[1:] if found[0].isupper() else right
            out.append(_issue(f"« {found} » : écrire {fixed} (graphie retenue, lexique partagé).",
                              {"type": "replace", "from": found, "to": fixed, "label": f"Écrire {fixed}"}))
    # Rule 1.1: the end-of-sentence particle is written a, not an (French "un an" left alone).
    if meta.get("lang") in ("mg", "mixte") and PARTICLE_AN_RE.search(plain):
        out.append(_issue("Particule « an » en fin de phrase : écrire a (règle 1.1). "
                          "« a an » (oui) s'écrit a-an.",
                          {"type": "particle_an", "label": "Écrire a"}))
    # Malagasy never doubles a vowel (koaa, izahoo): a drawn-out sound is written once (rule 1.2).
    # French and English words (zoo, coopérer) and names are left alone.
    if meta.get("lang") in ("mg", "mixte"):
        official = meta.get("dialect") == DIALECT_OFFICIAL
        # A hybrid (feeling-na, rule 3.5) is left alone when one of its parts is not Malagasy.
        doubled = sorted({w for w in re.split(r"[\s.,?]+", plain) if w and not w[0].isupper()
                          and DOUBLE_VOWEL_RE.search(w)
                          and not any(not_malagasy(p, official) for p in w.split("-") if p)})
        for word in doubled[:5]:
            # Exception: the prefix maha- before a word starting with a keeps both, with a hyphen
            # (mahaankizy -> maha-ankizy, rule 2).
            prefixed = re.match(r"(maha)(a.*)", word, re.I)
            if prefixed:
                hyphened = f"{prefixed.group(1)}-{prefixed.group(2)}"
                out.append(_issue(f"« {word} » : préfixe maha- devant un mot qui commence par a, écrire "
                                  f"{hyphened} avec un trait d'union (règle 2).",
                                  {"type": "replace", "from": word, "to": hyphened, "label": f"Écrire {hyphened}"},
                                  [word]))
                continue
            single = DOUBLE_VOWEL_RE.sub(r"\1", word)
            out.append(_issue(f"« {word} » : pas de voyelle doublée en malgache, écrire {single} "
                              "(son allongé écrit une fois, règle 1.2).",
                              {"type": "replace", "from": word, "to": single, "label": f"Écrire {single}"},
                              [word]))
    if meta.get("lang") in ("mg", "mixte"):
        words = {w for w in re.split(r"[\s.,?]+", plain) if w} - mid_sentence_names(plain)
        official = meta.get("dialect") == DIALECT_OFFICIAL
        foreign = sorted(w for w in words if not_malagasy(w, official))
        # A capitalised word still here starts a sentence (mid-sentence ones are names already):
        # maybe a name (Claude François), which does not make the segment "mixte" (rule 3).
        names = [w for w in foreign if w[0].isupper()]
        lower = [w for w in foreign if not w[0].isupper()]
        quoted = ", ".join(f"« {w} »" for w in names[:5])
        if meta.get("lang") == "mg" and names:
            out.append(_issue(f"{quoted} commence la phrase et ne peut pas être malgache : gardé comme nom propre "
                              "(langue « mg », règle 3). Si c'est un mot français ou anglais, langue « mixte ».",
                              {"type": "lang", "value": "mixte", "label": "Passer en « mixte »"}, names[:5]))
        elif meta.get("lang") == "mixte" and names and not lower:
            out.append(_issue(f"{quoted} commence la phrase : nom propre ? Un nom propre ne rend pas le segment "
                              "mixte : si le reste est en malgache, langue « mg » (règle 3).",
                              {"type": "lang", "value": "mg", "label": "Passer en « mg »"}, names[:5]))
        # y inside a word makes it not Malagasy (the segment turns "mixte"), but fytiavana is most
        # likely a Malagasy misspelling: when y is the only problem and the word is not a known
        # French or English one (voyage), say so with a one-click fix, in "mg" and "mixte" alike.
        for w in lower:
            # A French root with a Malagasy ending is French too: voyagen'i (voyage + -n'i).
            pieces = [p for p in re.split(r"['\-]", w.lower()) if p]
            known = any(p in FOREIGN_WORDS or (p.endswith("n") and p[:-1] in FOREIGN_WORDS) for p in [w.lower(), *pieces])
            if not has_inner_y(w) or known:
                continue
            fixed = "".join(p[:-1].replace("y", "i") + p[-1:] if p not in "'-" else p
                            for p in re.split(r"(['\-])", w))
            if not_malagasy(fixed, official):
                continue
            out.append(_issue(f"« {w} » : y à l'intérieur du mot n'existe pas en malgache (fitiavana, pas "
                              f"fytiavana) : faute probable, écrire {fixed} (règle 2). Si c'est un mot étranger, "
                              "langue « mixte » (règle 3).",
                              {"type": "replace", "from": w, "to": fixed, "label": f"Écrire {fixed}"}
                              if w in plain else None, [w]))
    if meta.get("lang") == "mg":
        foreign = lower
        if foreign:
            out.append(_issue(f"Langue « mg » mais {', '.join(foreign[:5])} : c, q, u, w, x n'existent pas en malgache "
                              "(ni les accents en dialecte officiel, ni y ailleurs qu'en fin de mot), et un mot "
                              "malgache ne finit jamais par une consonne. Faute d'orthographe (règle 2), "
                              "ou mot prononcé à la française : alors langue « mixte » (règle 3).",
                              {"type": "lang", "value": "mixte", "label": "Passer en « mixte »"}, foreign[:5]))
        foreign = foreign + names
        parts = {p.lower() for w in words - set(foreign) for p in re.split(r"['\-]", w) if len(p) > 1}
        final_i = sorted(p for p in parts if p.endswith("i"))
        if final_i:
            out.append(_issue(f"{', '.join(final_i[:5])} : en malgache, -y en fin de mot (misy, pas misi) (règle 2).",
                              words=final_i[:5]))
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
            "speaker_pattern": SPEAKER_RE.pattern, "dialect_official": DIALECT_OFFICIAL,
            "spelling_wrong": sorted(SPELLING_WRONG)}
