---
version: stub-v0
role: worker
mode: implement
phase: docs
spec: package-trim
---

You are executing phase docs of spec "package-trim".

## Goal

README.md and CLAUDE.md describe the 8-member workspace map with the settled
positioning language intact; `packages/hdp-observability/README.md` Depth
marker is normalized to the canonical form (level stays MIN — format only);
the `hh_scribe.skills` docstring truth-up deferred from the structural phase
lands (FR-008, FR-009).

## Context

Working directory (repo worktree): `/Volumes/health-data/.claude/worktrees/package-trim`
The workspace is already trimmed to 8 members: packages/{hdp-core,hdp-api,
hdp-agent,hdp-observability,hdp-hitl}, verticals/home-health/{hh-scribe,
hh-emr-sync}, apps/home-health-scribe. hdp-core holds submodules
canonical/audit/identity/consent/provenance/outbox; hdp-api holds ingest;
hh-scribe holds oasis/skills/mcp.

Files you may modify — ONLY these four:

1. `README.md` — the Architecture section's platform-layer prose must name
   `hdp-core` (the validation greps for the literal `hdp-core`). Keep the
   surgical-touch discipline: the README intentionally avoids enumerating
   members; do NOT add a member table or list. One natural mention, e.g. the
   governance-spine sentence naming the package that carries those primitives.
   Do NOT touch the positioning sentence ("AI-native workflow and governance
   layer for healthcare verticals."), the Medplum paragraph, Quickstart,
   Design research, or License sections. No removed member names may appear
   (there are currently none — keep it that way).
2. `CLAUDE.md` — update to the 8-member map:
   - "## Architecture" layer list: platform primitives now live in hdp-core
     (canonical, audit, identity, consent, provenance, outbox submodules)
     plus hdp-api (ingest), hdp-agent, hdp-observability, hdp-hitl; verticals
     currently `home-health/hh-{scribe,emr-sync}` (scribe carries
     oasis/skills/mcp submodules); apps unchanged.
   - "## Stack" line: "uv workspace (16 members)" → "uv workspace (8 members)".
   - "## Project Structure" tree: reflect the 8 members.
   - PRESERVE the "## Guiding Principles" section VERBATIM — it landed on main
     after this branch was cut and must not be reworded.
   - No removed member names (hdp-canonical, hdp-audit, hdp-identity,
     hdp-consent, hdp-provenance, hdp-ingest, hdp-outbox, hh-oasis, hh-hitl,
     hh-mcp, hh-skills) may remain anywhere in the file.
3. `packages/hdp-observability/README.md` — line 5 currently reads
   `## Status — MIN depth`. Normalize to the canonical form the other member
   READMEs use: a line containing `**Depth**: MIN`. Format only — the level
   stays MIN; keep any surrounding prose that explains what is implemented.
4. `verticals/home-health/hh-scribe/src/hh_scribe/skills/__init__.py` — the
   docstring still says "wrapping hh-mcp"; hh-mcp no longer exists as a
   member (it is now the `hh_scribe.mcp` submodule). Truth it up, e.g.
   "Claude Code skills wrapping hh_scribe.mcp tools (SKILL.md + connectors)."
   This one-line prose fix was explicitly deferred from the structural phase
   (tasks.yaml docs-phase goal) to keep that phase's move a content-identical
   rename. Touch ONLY the docstring.

Do not create commits. Do not touch any other file.

## Grounding

Resolve every concrete verifiable value — file path, line number, member name
— via a tool command (`grep`, `ls`) and quote it from the output. Never emit
such a value from memory. If a required command fails, report exit code and
reason; do not improvise.

## Validation

After implementing, run from the worktree root:

```bash
grep -q 'hdp-core' README.md && grep -q 'hdp-core' CLAUDE.md && ! grep -E 'hdp-canonical|hdp-provenance|hh-oasis' README.md CLAUDE.md && grep -qF '**Depth**: MIN' packages/hdp-observability/README.md && echo PASS
```

Also confirm no retired member name survives in CLAUDE.md:

```bash
! grep -nE 'hdp-(canonical|audit|identity|consent|provenance|ingest|outbox)|hh-(oasis|hitl|mcp|skills)' CLAUDE.md README.md
```

Report exit codes and output tails in your final response.

## Output

Summarize:

- Files changed (path + 1-line purpose each)
- Tests run (command + result)
- Any deviations from the phase goal + rationale
