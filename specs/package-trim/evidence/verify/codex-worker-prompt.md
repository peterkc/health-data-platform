---
version: stub-v0
role: worker
mode: implement
phase: verify
spec: package-trim
---

You are executing phase verify of spec "package-trim".

## Goal

Independent acceptance sweep against the assembled tree: layering invariant,
truthful Depth markers, dependency unions, commitlint scopes, history
preservation, and docs checks. This is a RUN-ONLY phase: you make ZERO edits
and create NO commits. Your deliverable is execution evidence.

## Context

Working directory (repo worktree): `/Volumes/health-data/.claude/worktrees/package-trim`
Spec sources: `/Volumes/health-data/vault/specs/package-trim/`

Your sandbox cannot run `uv`/`just` (cache + network restrictions, known from
the structural phase). The orchestrator runs those. You run the
stdlib-python3 + git subset below — they are the independent halves of
AC-003, AC-004, AC-006, AC-007, AC-008, AC-011.

## Grounding

Run every command yourself and quote exit codes/output from the actual runs.
If a command fails, report the exit code and stderr verbatim — do not
substitute, retry-and-hide, or improvise.

## Validation

Run each, from the worktree root, reporting exit code per line:

```bash
python3 /Volumes/health-data/vault/specs/package-trim/reference/check_layering.py
python3 /Volumes/health-data/vault/specs/package-trim/reference/check_depth_markers.py
python3 /Volumes/health-data/vault/specs/package-trim/reference/check_dep_union.py
python3 /Volumes/health-data/vault/specs/package-trim/reference/check_commitlint.py
for f in packages/hdp-hitl/src/hdp_hitl/__init__.py packages/hdp-core/src/hdp_core/audit/__init__.py packages/hdp-api/src/hdp_api/ingest/__init__.py verticals/home-health/hh-scribe/src/hh_scribe/oasis/__init__.py; do git log --follow --oneline -- "$f" | grep -c .; done
grep -c 'hdp-core' README.md CLAUDE.md
grep -cE 'hdp-canonical|hdp-provenance|hh-oasis' README.md CLAUDE.md; echo "expect 0 per file (grep -c exits 1 on zero matches — that exit 1 is the PASS signal here)"
```

## Output

Summarize:

- Each command + exit code + one-line output summary
- Overall verdict: every check green or list of failures
- Any deviations (commands you could not run + why)
