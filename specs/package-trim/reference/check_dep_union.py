"""AC-011 / NFR-002 gate: each post-trim member's pyproject dependencies equal
the union recorded in reference/target-map.json (zero new runtime deps).
Exit 0 = clean.
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE
while not (ROOT / "pyproject.toml").exists() or ROOT == ROOT.parent:
    ROOT = ROOT.parent

LAYER_DIR = {"packages": "packages", "verticals/home-health": "verticals/home-health", "apps": "apps"}


def main() -> int:
    target = json.loads((HERE / "target-map.json").read_text())
    errors = []
    for member in target["members"]:
        pp = ROOT / LAYER_DIR[member["layer"]] / member["name"] / "pyproject.toml"
        if not pp.exists():
            errors.append(f"{member['name']}: pyproject not found at {pp}")
            continue
        actual = set(tomllib.loads(pp.read_text())["project"].get("dependencies", []))
        expected = set(member["deps"])
        if actual != expected:
            extra, missing = actual - expected, expected - actual
            if extra:
                errors.append(f"{member['name']}: deps not in recorded union: {sorted(extra)}")
            if missing:
                errors.append(f"{member['name']}: union deps missing: {sorted(missing)}")
    for e in errors:
        print(f"DEP UNION: {e}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
