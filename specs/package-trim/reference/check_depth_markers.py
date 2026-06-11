"""AC-008 / FR-009 gate: every member README carries a Depth marker truthful to
its contents. Interface-only members (only __init__.py / py.typed in src) must
claim SKEL; members with real code may claim MIN/DEEP; apps may claim COMPOSED.
Exit 0 = clean.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve()
while not (ROOT / "pyproject.toml").exists() or ROOT == ROOT.parent:
    ROOT = ROOT.parent

MARKER_RE = re.compile(r"\*\*Depth\*\*:\s*(DEEP|MIN|SKEL|COMPOSED)")


def real_code_lines(member: Path) -> int:
    total = 0
    for py in (member / "src").rglob("*.py"):
        if py.name == "__init__.py":
            continue
        total += sum(1 for _ in py.open())
    return total


def main() -> int:
    errors = []
    for member in sorted(list(ROOT.glob("packages/*")) +
                         list(ROOT.glob("verticals/home-health/*")) +
                         list(ROOT.glob("apps/*"))):
        if not (member / "pyproject.toml").exists():
            continue
        readme = member / "README.md"
        if not readme.exists():
            errors.append(f"{member.name}: no README.md")
            continue
        m = MARKER_RE.search(readme.read_text())
        if not m:
            errors.append(f"{member.name}: no Depth marker")
            continue
        depth, loc = m.group(1), real_code_lines(member)
        if loc == 0 and depth in ("DEEP", "MIN") and "apps/" not in str(member):
            errors.append(f"{member.name}: claims {depth} with zero non-__init__ code")
    for e in errors:
        print(f"DEPTH MARKER: {e}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
