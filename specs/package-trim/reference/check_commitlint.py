"""AC-006 / FR-007 gate: commitlint scope-enum matches post-trim members and
every x-scope-patterns glob resolves to an existing path. Exit 0 = clean.

Glob extraction covers every x-scope-patterns shape — inline scalar values
(`key: "glob"`) and list-valued keys (`- "glob"`). Uses a real YAML parse when
a yaml lib is importable in the runtime; otherwise stdlib line parsing (the
config is data-only; no yaml dep in workspace).
"""

from __future__ import annotations

import re
import sys
from glob import glob
from pathlib import Path

# Run contract: invoke with the workspace root as cwd (main checkout or a
# feature worktree). __file__-based walk-up was amended at run time: the script
# lives in vault/, so walking up from __file__ always resolved the MAIN
# checkout and could never validate a feature worktree.
ROOT = Path.cwd()
if not (ROOT / ".commitlintrc.yaml").exists():
    print("run from the workspace root (.commitlintrc.yaml not in cwd)", file=sys.stderr)
    sys.exit(2)

STATIC = {"workspace", "packages", "verticals", "apps", "docs", "ci", "deps",
          "infra", "vault", "adr", "spec", "research"}
MEMBERS = {"hdp-core", "hdp-api", "hdp-agent", "hdp-observability", "hdp-hitl",
           "hh-scribe", "hh-emr-sync", "home-health-scribe"}

INLINE_RE = re.compile(r'^\s+[\w./*-]+:\s*(?:"([^"]+)"|([^\s#"][^\s#]*))\s*(?:#.*)?$')
ITEM_RE = re.compile(r'^\s+-\s*(?:"([^"]+)"|([^\s#"][^\s#]*))\s*(?:#.*)?$')


def globs_via_yaml(text: str) -> list[str] | None:
    """Real YAML parse when a yaml lib is importable; None otherwise."""
    try:
        import yaml
    except ImportError:
        return None
    patterns = (yaml.safe_load(text) or {}).get("x-scope-patterns") or {}
    out: list[str] = []
    for value in patterns.values():
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, list):
            out.extend(v for v in value if isinstance(v, str))
    return out


def globs_via_lines(text: str) -> list[str]:
    """Stdlib fallback: every inline scalar value and list item under
    x-scope-patterns, until the next top-level key."""
    out: list[str] = []
    in_block = False
    for line in text.splitlines():
        if line.startswith("x-scope-patterns:"):
            in_block = True
            continue
        if not in_block:
            continue
        if line.strip() and not line[0].isspace():
            break  # next top-level key ends the block
        m = INLINE_RE.match(line) or ITEM_RE.match(line)
        if m:
            out.append(m.group(1) or m.group(2))
    return out


def main() -> int:
    text = (ROOT / ".commitlintrc.yaml").read_text()
    errors = []
    enum_block = re.search(r"scope-enum:.*?\[(.*?)\]", text, re.S)
    if not enum_block:
        print("scope-enum block not found", file=sys.stderr)
        return 1
    scopes = {s.strip().rstrip(",") for s in enum_block.group(1).split(",") if s.strip()}
    expected = STATIC | MEMBERS
    if scopes != expected:
        extra, missing = scopes - expected, expected - scopes
        if extra:
            errors.append(f"unexpected scopes: {sorted(extra)}")
        if missing:
            errors.append(f"missing scopes: {sorted(missing)}")
    patterns = globs_via_yaml(text)
    if patterns is None:
        patterns = globs_via_lines(text)
    if len(patterns) < len(MEMBERS):
        errors.append(
            f"x-scope-patterns extraction returned only {len(patterns)} glob(s) — "
            f"expected at least one per member; extraction is broken, not the config"
        )
    for pattern in patterns:
        if not glob(str(ROOT / pattern), recursive=True):
            errors.append(f"x-scope-patterns glob resolves to nothing: {pattern}")
    for e in errors:
        print(f"COMMITLINT MISMATCH: {e}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
