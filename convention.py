"""PROVA-MG transcription convention (static/convention-transcription-prova-mg.md): allowed
values for the per-segment fields and the checks that block a segment from being marked done.

Annotations saved under the convention carry `convention` (the version) and `meta`:
    {"lang": "mg", "dialect": "betsileo", "register": "spontané", "quality": "propre",
     "speaker": "S1", "flags": ["chevauchement"], "exclude_reason": "chant / musique"}
Annotations without `convention` were made before it ("avant convention").
"""
from __future__ import annotations

import re

VERSION = "v1.2"

LANGS = ("mg", "fr", "mixte", "autre")
REGISTERS = ("lu", "semi-préparé", "spontané")
QUALITIES = ("propre", "bruit léger", "bruit fort", "musique de fond")
FLAGS = ("chevauchement", "incertain", "nom_propre", "emprunt_ambigu")
EXCLUDE_REASONS = ("inaudible", "chant / musique", "autre langue", "trop de chevauchement",
                   "acquiescement sans contenu")
# Suggested in the editor; any other variety can be typed.
DIALECTS = ("officiel (merina standard)", "betsimisaraka", "betsileo", "sakalava", "antandroy",
            "antaisaka", "antaimoro", "antanosy", "antakarana", "bara", "sihanaka", "tsimihety",
            "mahafaly", "vezo", "autre / incertain")
TAGS = ("[euh]", "[rire]", "[bruit]", "[inaudible]")

SPEAKER_RE = re.compile(r"^[A-Za-z0-9_\-]{1,20}$")
TAG_RE = re.compile(r"\[[^\[\]]*\]")


def clean_meta(raw) -> dict:
    """Keep only known fields with allowed values (dialect is free text)."""
    raw = raw if isinstance(raw, dict) else {}
    meta: dict = {}
    for key, allowed in (("lang", LANGS), ("register", REGISTERS), ("quality", QUALITIES),
                         ("exclude_reason", EXCLUDE_REASONS)):
        if raw.get(key) in allowed:
            meta[key] = raw[key]
    dialect = " ".join(str(raw.get("dialect") or "").split())[:60]
    if dialect:
        meta["dialect"] = dialect
    speaker = str(raw.get("speaker") or "").strip()
    if SPEAKER_RE.match(speaker):
        meta["speaker"] = speaker
    flags = raw.get("flags") if isinstance(raw.get("flags"), list) else []
    meta["flags"] = [f for f in FLAGS if f in flags]
    return meta


def unknown_tags(text: str) -> list[str]:
    return sorted({t for t in TAG_RE.findall(text) if t not in TAGS})


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
    labels = {"lang": "la langue", "dialect": "le dialecte", "register": "le registre", "quality": "la qualité audio"}
    missing = [label for key, label in labels.items() if not meta.get(key)]
    if missing:
        out.append("Renseigner " + ", ".join(missing) + ".")
    bad = unknown_tags(text)
    if bad:
        out.append(f"Balise inconnue : {' '.join(bad)}. Balises permises : {' '.join(TAGS)}.")
    return out


def options() -> dict:
    return {"version": VERSION, "langs": LANGS, "registers": REGISTERS, "qualities": QUALITIES,
            "flags": FLAGS, "exclude_reasons": EXCLUDE_REASONS, "dialects": DIALECTS, "tags": TAGS}
