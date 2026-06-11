You are validating an interview transcript for `/agx:spec` quality.
The spec is `emr-driver-tracer` — a tracer-bullet spec for a browser-automation
EMR sync driver (new repository `emr-sync-driver`; Playwright + DBOS
foundations; self-hosted OpenEMR sandbox; synthetic data only). The
transcript is at `vault/specs/emr-driver-tracer/interview.md`; supporting
ratified research is at `vault/research/computer-use-emr-sync/` (README.md +
state.yaml).

## Transcript

(read `vault/specs/emr-driver-tracer/interview.md` — quoted here for
convenience; the file on disk is authoritative)

The transcript records a 5-dimension interview conducted via structured
question rounds, with research pre-fill from
`vault/research/computer-use-emr-sync/` (8 sources, 6 user-ratified
decisions). Key answers: Dim 1 user surface = "Both in tracer" (CLI + thin
API) with an orchestrator interpretation flagged for your review; Dim 2 repo
name `emr-sync-driver`, public from creation, Stagehand fallback gated
behind deterministic E2E; Dim 3 standalone driver, converge with HDP later
via adapter contract; Dim 4 four-point done-bar confirmed (E2E thread,
kill -9 resume without re-applied writes, ≥3 taxonomy rows with hardening
recs, action-by-action audit replay); Dim 5 local Mac arm64, no deadline,
three known unknowns carried from research.

## Required dimensions

1. Users & their workflows — who triggers this, what do they currently do?
2. Scope & functional requirements — what does success look like? non-goals?
3. Integration & data flow — what does this consume / produce / depend on?
4. Quality criteria — measurable acceptance criteria; how do we verify?
5. Risks & unknowns — what could go wrong? what don't we know yet?

## Ambiguity threshold (bounded acceptance bar — report a gap ONLY when a Cn fails)

- C1: each of the 5 dimensions has a concrete answer in the transcript
- C2: every measurable claim cites a transcript line or a named research artifact
- C3: no contradiction across answers (including against the cited research decisions)

OUT OF SCOPE — NOT a gap: "the user could elaborate more"; choices
explicitly deferred to design or to `/agx:spec run` phases; the three known
unknowns already logged in Dim 5 (they are tracked, not missing);
implementation details the first build phase verifies against real code.

## Grounding

Resolve every concrete value cited as evidence — file path, line number,
symbol / API name — via a tool command (`grep`, `cat`, `git`) and quote it
from the output. Read `vault/specs/emr-driver-tracer/interview.md` and
`vault/research/computer-use-emr-sync/state.yaml` before reporting. Never
cite a location or value from memory or pattern-matching. If a check cannot
be run, report that; do not substitute a plausible value to appear complete.

## Output

Produce JSON conforming to the provided schema:

- `dim_coverage_gaps[]` — leave empty unless a C1 failure exists (emit one empty object per failing dimension)
- `ambiguities[]` — leave empty unless a C3 failure exists (emit one empty object per contradiction)
- `missing_evidence[]` — leave empty unless a C2 failure exists (emit one empty object per unsupported claim)
- `suggested_probes[]` — one string per finding, formatted "Cn-FAIL <dimension>: <specific follow-up question>"; this array carries ALL finding detail (the object arrays are schema-constrained to empty shapes)

If every Cn holds, return all four arrays empty.