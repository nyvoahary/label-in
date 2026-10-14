"""Manage label-in login accounts.

Usage:
    python manage_users.py add <username>      # prompts for the password
    python manage_users.py remove <username>
    python manage_users.py list

Accounts live in AUTH_FILE (default: datasets/users.json) as password hashes.
While the file has no accounts, the app does not ask for a login.
"""
from __future__ import annotations

import getpass
import json
import os
import re
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

AUTH_FILE = Path(os.environ.get("AUTH_FILE", Path(__file__).parent / "datasets" / "users.json"))
USERNAME_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


def load() -> dict[str, str]:
    return json.loads(AUTH_FILE.read_text("utf-8")) if AUTH_FILE.exists() else {}


def save(users: dict[str, str]) -> None:
    tmp = AUTH_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(users, indent=2), "utf-8")
    tmp.replace(AUTH_FILE)


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("add", "remove", "list") or (argv[0] != "list" and len(argv) != 2):
        print(__doc__)
        return 2
    users = load()
    cmd = argv[0]
    if cmd == "list":
        print("\n".join(sorted(users)) or "(no accounts: login is disabled)")
        return 0
    name = argv[1]
    if cmd == "remove":
        if users.pop(name, None) is None:
            print(f"No such account: {name}")
            return 1
        save(users)
        print(f"Removed {name}." + ("" if users else " No accounts left: login is now disabled."))
        return 0
    if not USERNAME_RE.match(name):
        print("Username may only contain letters, digits, _ and -")
        return 1
    password = getpass.getpass(f"Password for {name}: ")
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        return 1
    if getpass.getpass("Repeat password: ") != password:
        print("Passwords do not match.")
        return 1
    existed = name in users
    users[name] = generate_password_hash(password)
    save(users)
    print(f"{'Updated' if existed else 'Added'} {name}. Accounts: {', '.join(sorted(users))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
