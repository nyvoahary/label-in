"""Manage label-in login accounts (the admin page in the app does the same).

Usage:
    python manage_users.py add <username> [admin|annotator]   # prompts for the password
    python manage_users.py role <username> admin|annotator
    python manage_users.py remove <username>
    python manage_users.py list

`add` on an existing account changes its password (and role, if given). A new
account is an admin when no admin exists yet, otherwise an annotator.
Accounts live in AUTH_FILE (default: datasets/users.json) as password hashes.
While the file has no accounts, the app does not ask for a login.
"""
from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

import accounts

AUTH_FILE = Path(os.environ.get("AUTH_FILE", Path(__file__).parent / "datasets" / "users.json"))


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else ""
    arity = {"list": (1,), "remove": (2,), "role": (3,), "add": (2, 3)}
    if cmd not in arity or len(argv) not in arity[cmd]:
        print(__doc__)
        return 2
    users = accounts.load(AUTH_FILE)
    if cmd == "list":
        for name in sorted(users):
            acc = users[name]
            print(f"{name:<24} {acc.get('role', ''):<10} last login: {acc.get('last_login') or 'never'}")
        if not users:
            print("(no accounts: login is disabled)")
        return 0

    name = argv[1]
    role = argv[2] if len(argv) == 3 else None
    if role is not None and role not in accounts.ROLES:
        print(f"Role must be one of: {', '.join(accounts.ROLES)}")
        return 1

    if cmd in ("remove", "role"):
        if name not in users:
            print(f"No such account: {name}")
            return 1
        leaving_admin = users[name].get("role") == "admin" and (cmd == "remove" or role != "admin")
        if leaving_admin and accounts.admins(users) == [name] and len(users) > 1:
            print(f"{name} is the last admin. Make another account admin first.")
            return 1
        if cmd == "remove":
            del users[name]
            accounts.save(AUTH_FILE, users)
            print(f"Removed {name}." + ("" if users else " No accounts left: login is now disabled."))
        else:
            users[name]["role"] = role
            accounts.save(AUTH_FILE, users)
            print(f"{name} is now {role}.")
        return 0

    if not accounts.USERNAME_RE.match(name):
        print("Username may only contain letters, digits, _ and -")
        return 1
    password = getpass.getpass(f"Password for {name}: ")
    problem = accounts.password_problem(password)
    if problem:
        print(problem)
        return 1
    if getpass.getpass("Repeat password: ") != password:
        print("Passwords do not match.")
        return 1
    existed = name in users
    acc = users.get(name) or {"role": "annotator" if accounts.admins(users) else "admin", "created_at": accounts.now()}
    if role:
        if existed and acc.get("role") == "admin" and role != "admin" and accounts.admins(users) == [name]:
            print(f"{name} is the last admin. Make another account admin first.")
            return 1
        acc["role"] = role
    acc["hash"] = generate_password_hash(password)
    users[name] = acc
    accounts.save(AUTH_FILE, users)
    print(f"{'Updated' if existed else 'Added'} {name} ({acc['role']}). Accounts: {', '.join(sorted(users))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
