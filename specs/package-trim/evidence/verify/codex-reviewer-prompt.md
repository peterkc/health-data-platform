---
version: stub-v0
role: reviewer
mode: audit
phase: verify
spec: package-trim
---

You are reviewing changes for "Phase 4: Verify — full acceptance sweep".

## Scope

The FULL branch diff of `feat/package-trim` vs `origin/main` in the worktree
at `/Volumes/health-data/.claude/worktrees/package-trim` (your working
directory) — three commits: the structural member-map rewrite (17→8), the
commitlint scope realignment, and the docs 8-member-map update. Inspect via
`git diff origin/main...HEAD`, `git log origin/main..HEAD`, direct reads.
This is the last gated phase before merge: the question is whether the
ASSEMBLED tree satisfies the spec end-to-end.

Spec sources (read-only): `/Volumes/health-data/vault/specs/package-trim/`
(requirements.md FR-001..009 + NFR-001..004, design.md, tasks.yaml,
reference/target-map.json, reference/emr_sync_transport.py,
reference/test_manifest.py, reference/check_*.py).

## Acceptance checklist (bounded — SK-0008)

Score against this fixed checklist; the bar is the checklist, nothing more.
Set `overall_correctness = "correct"` iff EVERY Cn holds and no out-of-scope
item is reported.

- **C1** every acceptance criterion AC-001..AC-011 maps to an existing,
  NON-SKIPPED test in `reference/test_manifest.py` (all 11 bodies are now
  executable; zero pytest.skip bodies remain)
- **C2** every file/dir in tasks.yaml `manifest:` exists in the branch tree
  (or is correctly absent when marked absorbed/removed) and matches its
  stated purpose
- **C3** mechanics as designed across all three commits: history-preserving
  renames, submodule layout, NFR-004 test renames, transport stub
  byte-identical to reference, dep unions per target-map.json, commitlint
  scope-enum = 12 static + 8 members with resolving globs, docs reflect the
  8-member map with positioning intact
- **C4** no contract contradiction between the assembled tree and design.md /
  requirements.md (layering invariant, async push + sync health, no httpx
  import in transport module, Guiding Principles section in CLAUDE.md
  preserved from main)

### Out of scope — NOT a violation, do not report as a finding

"More hardening would help"; implementation-style preferences; future-phase
concerns (merge mechanics, PR shape); the documented spec-side amendments
(validation-command --all-packages fix, check-script cwd contract,
rebase-map.json) — all recorded in evidence with rationale; rename-attribution
scrambling among byte-identical placeholder files (adjudicated rounds 1-3 of
the structural phase: git pairs identical content arbitrarily at diff time;
the four AC-004 samples are R100 from correct sources).

## Prior-round findings (cumulative re-review)

For each, confirm resolved against the current branch (now 4 commits). Do NOT
re-sample unrelated items that were acceptable last round.

1. [codex verify r1, P2] "App README still documents removed member names"
   — FIXED in commit 6c0708b: `apps/home-health-scribe/README.md` TODO now
   composes `hh-scribe + hdp-hitl + hh-emr-sync`. A whole-tree sweep after
   the fix also caught `justfile` line 35's `hdp-canonical / hdp-audit`
   comment (same stale-name class) — truth-ed to hdp-core schemas in the
   same commit. The sweep
   (`grep -rnE 'hdp-(canonical|audit|...)|hh-(oasis|hitl|mcp|skills)'` over
   *.py/*.toml/*.md/justfile, excluding .venv/.agx/.tmp) now returns zero
   hits. Both files added to the tasks.yaml manifest.
2. Structural-phase rounds remain resolved: manifest bodies (zero skips),
   hh-skills __init__ R100, AC-004/AC-011 assignment (moot — all 11 ACs
   executable).

## Rubric dimensions

| Dimension              | Weight | 9-10 criterion                                                              |
| ---------------------- | ------ | ---------------------------------------------------------------------------- |
| `phase_atomicity`      | 30%    | The branch lands one end-to-end concern (the trim); no partial-success state |
| `context_completeness` | 25%    | Every manifest file covered; requirements-to-change mapping complete         |
| `pattern_clarity`      | 20%    | Implementation matches specified patterns exactly                            |
| `validation_coverage`  | 15%    | All 11 ACs executable and green; checks runnable against the tree            |
| `risk_identification`  | 10%    | Spec-named risks addressed; amendments documented in evidence                |

## Grounding

Resolve every concrete value cited as evidence — file path, line number,
symbol — via a tool command and quote it from the output. Never cite from
memory. If a check cannot be run (e.g., uv/just blocked in sandbox), say so
explicitly; static verification of those surfaces is acceptable.

## Output

Produce JSON conforming to reviewer.schema.json:

- `findings[]` — each with `title`, `body`, `confidence_score` (0.0-1.0), `priority` (integer), `code_location` (`{absolute_file_path, line_range: {start, end}}`)
- `overall_correctness` — "correct" | "needs-attention" | "incorrect"
- `overall_explanation` — 2-4 sentences
- `overall_confidence_score` — 0.0-1.0

Each finding MUST cite an exact file path + line range.
