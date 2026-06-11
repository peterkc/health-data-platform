---
version: stub-v0
role: reviewer
mode: audit
phase: structural
spec: package-trim
---

You are reviewing changes for "Phase 1: Tracer — full member-map rewrite".

## Scope

The STAGED, uncommitted changes in the git worktree at
`/Volumes/health-data/.claude/worktrees/package-trim` (your working directory).
Inspect via `git diff --cached` / `git status` / direct file reads. 82 files:
the uv workspace collapses from 17 members to 8 — six data-layer shells merge
into new `packages/hdp-core` (submodules canonical/audit/identity/consent/
provenance/outbox), `hdp-ingest` merges into `hdp-api` as `hdp_api.ingest`,
`hh-hitl` is promoted whole-package to `packages/hdp-hitl` (import pkg
`hdp_hitl`), `hh-oasis`/`hh-skills`/`hh-mcp` merge into `hh-scribe` as
submodules, `hh-emr-sync` gains a transport-agnostic `EmrSyncTransport`
Protocol stub and remaps deps to hdp-core, the app's deps are remapped, root
`pyproject.toml` members/sources shrink to 8, and `uv.lock` is regenerated.

Spec sources (read-only, outside the worktree):
`/Volumes/health-data/vault/specs/package-trim/` — `requirements.md` (FR-001..006,
FR-009, NFR-001..004 bind this phase), `design.md`, `tasks.yaml` (manifest +
structural phase entry), `reference/target-map.json`,
`reference/emr_sync_transport.py`, `reference/test_manifest.py`.

## Acceptance checklist (bounded — SK-0008)

Score against this fixed checklist. Do NOT measure distance to an unbounded ideal — a
design/code doc never reaches an asymptote, so "is this complete enough?" never converges.
The bar is the checklist below, nothing more.

Set `overall_correctness = "correct"` if and only if **every** `Cn` holds AND no reported
finding is an out-of-scope item. If any `Cn` fails, report it as a finding and set
`overall_correctness` to `"needs-attention"` or `"incorrect"`.

- **C1** every acceptance criterion assigned to this phase maps to an existing,
  non-skipped test in `vault/specs/package-trim/reference/test_manifest.py`.
  Phase assignment is authoritative in each manifest test's skip-message prefix:
  structural-phase ACs are exactly AC-001, AC-005, AC-009, AC-010. AC-004 and
  AC-011 are verify-phase ACs (their skip messages say "verify phase"; the
  verify phase's tasks.yaml validation command executes them via the
  `git log --follow` loop and `check_dep_union.py`) — their skip bodies are
  CORRECT at structural close and land in the verify phase.
- **C2** the structural phase's `tasks.yaml` `context.files` all exist in the
  staged tree (or are correctly removed when the manifest marks their directory
  as absorbed) and the staged result matches the `manifest:` purposes
- **C3** each required mechanic is implemented as the design specifies:
  history-preserving renames staged (R entries for moved src/test content
  files), submodule layout inside hdp_core/hdp_api/hh_scribe, test
  relocate-and-rename per NFR-004, transport stub byte-identical to the
  reference, dependency unions exactly per target-map.json
- **C4** no contract contradiction between the staged code and `design.md` /
  `requirements.md` (layering invariant, async-push seam, no httpx import in
  transport module, out-of-scope files untouched: `.commitlintrc.yaml`, root
  `README.md`, `CLAUDE.md`, `packages/hdp-observability/README.md`)

### Out of scope — NOT a violation, do not report as a finding

Deferrals to later phases (commitlint scope-enum = config phase; root README /
CLAUDE.md architecture text + hdp-observability Depth normalization = docs
phase; full acceptance sweep incl. `just verify`, layering/depth/dep-union
check scripts + git log --follow verification = verify phase); "more hardening
would help"; implementation-style preferences; anything a later phase verifies
against real code. The validation-command amendment (`uv sync --all-packages`)
is recorded spec-side in `evidence/structural/debug.json` — not a code finding.

## Prior-round findings (cumulative re-review)

For each prior finding below, confirm it is resolved (or that the recorded
adjudication is sound) against the current diff. Do NOT re-sample unrelated new
items that were acceptable last round.

1. [codex r1, P1] "C1 tests are all skipped instead of executable" — FIXED:
   executable bodies landed in `reference/test_manifest.py` for the four
   structural-phase ACs (AC-001, AC-005, AC-009, AC-010); run proof:
   `uv run pytest <manifest> → 4 passed, 7 skipped`. Later-phase ACs stay
   skip-bodied by the manifest's own contract ("bodies land during /agx:spec
   run phases") — their bodies land in config/docs/verify phases.
2. [codex r1, P1] "Staged smoke-test renames preserve the wrong histories" —
   ADJUDICATED, NO ACTION: git computes rename pairing at diff time by content
   similarity; all 11 absorbed `test_smoke.py` files are byte-identical
   placeholders, so source-attribution among them is arbitrary and cannot be
   controlled by any staging action within a single commit. Destination paths
   and basenames are exactly per NFR-004; `git log --follow` reaches a
   pre-move placeholder either way; zero information loss.
3. [codex r1, P1] "hdp-hitl pyproject is staged from hh-skills" — same class
   as (2): near-identical pyproject boilerplate pairs arbitrarily at diff
   time. The AC-004 history sample for the hh-hitl promotion
   (`src/hdp_hitl/__init__.py`) is staged R100 from the correct source.
4. [claude r1, P3] "hh-skills src __init__.py move breaks --follow (NFR-001)"
   — FIXED: original content restored at the new path; now staged R100. The
   docstring truth-up is deferred to the docs phase (recorded in tasks.yaml
   docs-phase goal).
5. [codex r2, P1] "AC-004 is still skip-bodied" — ADJUDICATED, NO ACTION: the
   round-2 prompt's C1 clause erroneously listed AC-004 as a structural-phase
   AC. The manifest skip-message ("verify phase: git log --follow ...") is the
   authoritative assignment; the verify phase's validation command executes it.
   Reviewer applied the flawed checklist faithfully — checklist corrected above.
6. [codex r2, P1] "AC-011 is still skip-bodied" — same adjudication as (5):
   AC-011's skip message says "verify phase: check_dep_union.py"; the verify
   phase's validation command runs that script. Skip body is correct at
   structural close.

## Rubric dimensions

| Dimension              | Weight | 9-10 criterion                                                                                     |
| ---------------------- | ------ | --------------------------------------------------------------------------------------------------- |
| `phase_atomicity`      | 30%    | Single end-to-end concern; no meaningful partial-success state (a rename touching 50 files is atomic) |
| `context_completeness` | 25%    | All files with symbol references, patterns as code, requirements-to-phase mappings                  |
| `pattern_clarity`      | 20%    | Implementation matches specified patterns exactly, not just descriptions                            |
| `validation_coverage`  | 15%    | Phase has specific validation commands (pytest target, grep assertion)                              |
| `risk_identification`  | 10%    | Gotchas documented, unknowns enumerated with mitigations                                            |

## Grounding

Resolve every concrete value cited as evidence — file path, line number,
symbol / API name, commit SHA — via a tool command (`grep`, `git`,
`gh api`) and quote it from the output. Never cite a location or value
from memory or pattern-matching. If a check cannot be run, report that;
do not substitute a plausible value to appear complete.

## Output

Produce JSON conforming to reviewer.schema.json:

- `findings[]` — each with `title`, `body`, `confidence_score` (0.0-1.0), `priority` (integer), `code_location` (`{absolute_file_path, line_range: {start, end}}`)
- `overall_correctness` — one of: "correct", "needs-attention", "incorrect" (= "correct" iff every `Cn` holds)
- `overall_explanation` — 2-4 sentence summary
- `overall_confidence_score` — 0.0-1.0

Each finding MUST cite an exact file path + line range (no vague locations).
