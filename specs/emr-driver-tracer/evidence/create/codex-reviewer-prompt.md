You are reviewing changes for "Create-time spec review" of spec `emr-driver-tracer`.

## Scope

The 4-file spec artifact + reference stubs at
`vault/specs/emr-driver-tracer/` (worktree-relative): `SPEC.md`,
`requirements.md`, `design.md`, `tasks.yaml`, `interview.md`, and
`reference/` (`cli.py`, `models.py`, `audit-event.golden.json`,
`test_manifest.py`, `test_matrix.md`). Supporting ratified research:
`vault/research/computer-use-emr-sync/` (README.md, state.yaml). The spec
targets a NEW repository (`emr-sync-driver`) — manifest paths reference
future files there; do not report their absence on disk as a finding.

## Acceptance checklist (bounded — SK-0008)

Score against this fixed checklist. Do NOT measure distance to an unbounded
ideal. Set `overall_correctness = "correct"` iff EVERY Cn holds AND no
reported finding is an out-of-scope item.

- C1: every CLI command in `reference/cli.py` has a complete signature + I/O + exit contract, consistent with design.md
- C2: `reference/audit-event.golden.json` validates against the `AuditEvent` model stub in `reference/models.py` (field names, types, enum values)
- C3: every FR/NFR in requirements.md has >=1 AC; every AC maps to a `reference/test_manifest.py` test
- C4: no contradiction across SPEC.md / requirements.md / design.md / tasks.yaml / reference/ stubs (including against the ratified research decisions)
- C5: every required gate/constraint has a producer phase in tasks.yaml
- C6: every typed-key kind (FailureClass, JobStatus, ActionOutcome) is assigned consistently in prose + model stub
- C7: `python3 /Volumes/agx/plugins/agx/skills/spec/scripts/spec_coverage.py emr-driver-tracer` exits 0 (run it from the worktree root)
- C8: every AC has a row in `reference/test_matrix.md` with a backend home (or a static/build gate), and every matrix-referenced AC maps to >=1 `test_manifest.py` test

### Out of scope — NOT a violation, do not report as a finding

"An implementer must still decide X" / "more detail would help";
implementation choices deferred to `/agx:spec run` phases (exact DBOS step
granularity, OpenEMR selector specifics, compose port numbers); anything
the first build phase verifies against real code; the three known unknowns
already logged in SPEC.md § Risks & Unknowns.

## Prior-round findings (cumulative re-review)

For each prior finding below, confirm it is resolved by the current
artifact. Do NOT re-sample unrelated new items that were acceptable last
round.

1. "NFR-004 has no acceptance criterion" (requirements.md:65, both vendors,
   round 1): NFR-004 (public-reader hygiene) had no AC and no test-matrix
   row; only the merge-phase goal string referenced it. Claimed resolution:
   AC-013 added to requirements.md mapping NFR-004 to a merge-phase hygiene
   grep gate; matching row added to reference/test_matrix.md; matching
   skip-bodied test added to reference/test_manifest.py tagged AC-013.

## Rubric dimensions

Score each 1-10 with rationale (informative for findings; the verdict is
the Cn checklist): phase_atomicity (30%) — one concern per phase, no
keepable partial-success state; context_completeness (25%) — files,
symbols, requirement-to-phase mappings present; pattern_clarity (20%) —
contracts specified not just described; validation_coverage (15%) — every
phase has a specific validation command/AC; risk_identification (10%) —
gotchas enumerated with mitigations.

## Grounding

Resolve every concrete value cited as evidence — file path, line number,
symbol / API name — via a tool command (`grep`, `cat`, `python3`) and quote
it from the output. Never cite a location or value from memory. If a check
cannot be run, report that; do not substitute a plausible value.

## Output

Produce JSON conforming to the provided reviewer schema:

- `findings[]` — each with `title`, `body`, `confidence_score` (0.0-1.0), `priority` (integer), `code_location` (`{absolute_file_path, line_range: {start, end}}`)
- `overall_correctness` — "correct" | "needs-attention" | "incorrect" (= "correct" iff every Cn holds)
- `overall_explanation` — 2-4 sentence summary
- `overall_confidence_score` — 0.0-1.0

Each finding MUST cite an exact file path + line range.