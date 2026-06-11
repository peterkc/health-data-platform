"""AC-011 / NFR-002 gate: each post-trim member's pyproject dependencies equal
the union recorded in reference/target-map.json (zero new runtime deps).
Exit 0 = clean.
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

# target-map.json rides next to this script — file-relative stays correct.
HERE = Path(__file__).resolve().parent
# Run contract: invoke with the workspace root as cwd (main checkout or a
# feature worktree). __file__-based walk-up was amended at run time: the script
# lives in vault/, so it always resolved the MAIN checkout.
ROOT = Path.cwd()
if not (ROOT / "pyproject.toml").exists():
    print("run from the workspace root (pyproject.toml not in cwd)", file=sys.stderr)
    sys.exit(2)

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
