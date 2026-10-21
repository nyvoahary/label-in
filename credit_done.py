"""Credit finished segments that have no transcriber yet (finished before `done_by` existed).

Usage:
    python credit_done.py <username> [--dry-run]

Sets done_by=<username> on every done/excluded segment without a done_by, in every project
under DATASETS (default: ./datasets). Run it while nobody is annotating.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

DATA_ROOT = Path(os.environ.get("DATASETS", Path(__file__).parent / "datasets"))


def main(argv: list[str]) -> int:
    args = [a for a in argv if a != "--dry-run"]
    if len(args) != 1:
        print(__doc__)
        return 2
    user, dry = args[0], "--dry-run" in argv
    total = 0
    for path in sorted(DATA_ROOT.glob("*/annotations.json")):
        if path.parent.name.startswith("."):
            continue
        annos = json.loads(path.read_text("utf-8"))
        n = 0
        for a in annos.values():
            if isinstance(a, dict) and a.get("status") in ("done", "excluded") and not a.get("done_by"):
                a["done_by"] = user
                n += 1
        print(f"{path.parent.name}: {n}")
        total += n
        if n and not dry:
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(annos, ensure_ascii=False, indent=2), "utf-8")
            tmp.replace(path)
    print(f"total: {total}" + (" (dry run, nothing written)" if dry else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
