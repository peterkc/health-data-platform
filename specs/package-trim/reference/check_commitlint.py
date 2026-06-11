"""AC-006 / FR-007 gate: commitlint scope-enum matches post-trim members and
every x-scope-patterns glob resolves to an existing path. Exit 0 = clean.

Stdlib-only YAML extraction (the config is data-only; no yaml dep in workspace).
"""

from __future__ import annotations

import re
import sys
from glob import glob
from pathlib import Path

ROOT = Path(__file__).resolve()
while not (ROOT / ".commitlintrc.yaml").exists() or ROOT == ROOT.parent:
    ROOT = ROOT.parent

STATIC = {"workspace", "packages", "verticals", "apps", "docs", "ci", "deps",
          "infra", "vault", "adr", "spec", "research"}
MEMBERS = {"hdp-core", "hdp-api", "hdp-agent", "hdp-observability", "hdp-hitl",
           "hh-scribe", "hh-emr-sync", "home-health-scribe"}


def main() -> int:
    text = (ROOT / ".commitlintrc.yaml").read_text()
    enum_block = re.search(r"scope-enum:.*?\[(.*?)\]", text, re.S)
    if not enum_block:
        print("scope-enum block not found", file=sys.stderr)
        return 1
    scopes = {s.strip().rstrip(",") for s in enum_block.group(1).split(",") if s.strip()}
    expected = STATIC | MEMBERS
    errors = []
    if scopes != expected:
        extra, missing = scopes - expected, expected - scopes
        if extra:
            errors.append(f"unexpected scopes: {sorted(extra)}")
        if missing:
            errors.append(f"missing scopes: {sorted(missing)}")
    for m in re.finditer(r'^\s+(?:- )?"?([\w./*-]+/\*\*)"?\s*$', text, re.M):
        pattern = m.group(1)
        if not glob(str(ROOT / pattern.replace("/**", ""))):
            errors.append(f"x-scope-patterns glob resolves to nothing: {pattern}")
    for e in errors:
        print(f"COMMITLINT MISMATCH: {e}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
