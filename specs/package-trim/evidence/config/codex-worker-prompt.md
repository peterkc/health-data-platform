---
version: stub-v0
role: worker
mode: implement
phase: config
spec: package-trim
---

You are executing phase config of spec "package-trim".

## Goal

`.commitlintrc.yaml` scope-enum exactly matches the post-trim member set plus
the static scopes; every `x-scope-patterns` glob resolves to an existing path
(FR-007).

## Context

Working directory (repo worktree): `/Volumes/health-data/.claude/worktrees/package-trim`
The ONLY file you may modify: `.commitlintrc.yaml` (repo root). Do not touch
source, tests, or any other file. Do not create commits.

The structural phase already landed: the workspace is now 8 members
(packages/{hdp-core,hdp-api,hdp-agent,hdp-observability,hdp-hitl},
verticals/home-health/{hh-scribe,hh-emr-sync}, apps/home-health-scribe).

Required end state:

1. `scope-enum` list = EXACTLY these 20 scopes (12 static + 8 members):
   workspace, packages, verticals, apps, docs, ci, deps, infra, vault, adr,
   spec, research, hdp-core, hdp-api, hdp-agent, hdp-observability, hdp-hitl,
   hh-scribe, hh-emr-sync, home-health-scribe.
   (Removes the 11 retired members: hdp-canonical, hdp-audit, hdp-identity,
   hdp-consent, hdp-provenance, hdp-ingest, hdp-outbox, hh-oasis, hh-hitl,
   hh-mcp, hh-skills. Adds: hdp-core, hdp-hitl.)
2. `x-scope-patterns`:
   - remove the 11 retired members' pattern entries
   - add `hdp-core: "packages/hdp-core/**"` and `hdp-hitl: "packages/hdp-hitl/**"`
   - keep the existing entries for surviving members and static scopes
   - DROP the two dead globs that resolve to nothing in this tree:
     `docs/**` (under the docs key — keep its other globs) and `Dockerfile*`
     (under infra — keep docker-compose.yml). Spec decision: dead globs are
     dropped, not satisfied (SPEC.md Risks; FR-007 requires every glob to
     resolve).
3. Preserve the file's existing style (extends block, comment above
   x-scope-patterns, quoting, two-space indent).

Spec sources (read-only, absolute paths):
- `/Volumes/health-data/vault/specs/package-trim/requirements.md` (FR-007)
- `/Volumes/health-data/vault/specs/package-trim/reference/check_commitlint.py`
  (the gate — its STATIC and MEMBERS sets are the authoritative expected sets)

## Grounding

Resolve every concrete verifiable value — file path, glob, scope name — via a
tool command (`grep`, `ls`, `glob`) and quote it from the output. Never emit
such a value from memory. If a required command fails (non-zero exit), report
it with the exit code and reason; do not improvise.

## Validation

After implementing, run from the worktree root (plain python3 — the script is
stdlib-only; its run contract is cwd = workspace root):

```bash
python3 /Volumes/health-data/vault/specs/package-trim/reference/check_commitlint.py
```

Report the exit code and any output in your final response.

## Output

Summarize:

- Files changed (path + 1-line purpose each)
- Tests run (command + result)
- Any deviations from the phase goal + rationale
