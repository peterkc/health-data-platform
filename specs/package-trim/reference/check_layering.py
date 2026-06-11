"""AC-003 / NFR-003 gate: layering invariant across member pyprojects.

packages/* may depend only on packages/*; verticals may depend on packages +
sibling verticals; apps may depend on anything. Exit 0 = clean.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

# Run contract: invoke with the workspace root as cwd (main checkout or a
# feature worktree). __file__-based walk-up was amended at run time: the script
# lives in vault/, so it always resolved the MAIN checkout.
ROOT = Path.cwd()
if not (ROOT / "pyproject.toml").exists():
    print("run from the workspace root (pyproject.toml not in cwd)", file=sys.stderr)
    sys.exit(2)

VERTICAL_PREFIXES = ("hh-",)
APP_NAMES = {"home-health-scribe"}


def base_name(dep: str) -> str:
    for sep in (">", "<", "=", "[", " ", "!"):
        dep = dep.split(sep)[0]
    return dep.strip()


def main() -> int:
    violations: list[str] = []
    for layer_glob, layer in (("packages/*", "package"), ("verticals/home-health/*", "vertical")):
        for member in sorted(ROOT.glob(layer_glob)):
            pp = member / "pyproject.toml"
            if not pp.exists():
                continue
            deps = tomllib.loads(pp.read_text())["project"].get("dependencies", [])
            for dep in map(base_name, deps):
                if dep in APP_NAMES:
                    violations.append(f"{member.name} ({layer}) -> app {dep}")
                elif layer == "package" and dep.startswith(VERTICAL_PREFIXES):
                    violations.append(f"{member.name} (package) -> vertical {dep}")
    for v in violations:
        print(f"LAYERING VIOLATION: {v}", file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
