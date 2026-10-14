"""Login accounts shared by app.py and manage_users.py.

AUTH_FILE (default: datasets/users.json) maps username -> account:
    {"tolotra": {"hash": "<werkzeug hash>", "role": "admin", "created_at": "...", "last_login": "..."}}
Older files stored only the hash ({"tolotra": "<hash>"}); those accounts load as admins.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

USERNAME_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
ROLES = ("admin", "annotator")
MIN_PASSWORD = 8


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text("utf-8"))
    return {name: ({"hash": acc, "role": "admin"} if isinstance(acc, str) else acc) for name, acc in raw.items()}


def save(path: Path, users: dict[str, dict]) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(users, indent=2), "utf-8")
    tmp.replace(path)


def fingerprint(acc: dict) -> str:
    """Changes whenever the password changes, which signs out that user's sessions."""
    return hashlib.sha256(acc["hash"].encode()).hexdigest()[:16]


def admins(users: dict[str, dict]) -> list[str]:
    return [n for n, a in users.items() if a.get("role") == "admin"]


def password_problem(password: str) -> str | None:
    if len(password) < MIN_PASSWORD:
        return f"Password must be at least {MIN_PASSWORD} characters."
    return None
