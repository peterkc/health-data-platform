You are reviewing changes for "Create-time spec review".

## Scope

Create-time spec review of the package-trim spec artifact (uncommitted, on the vault worktree):
- vault/specs/package-trim/SPEC.md, requirements.md, design.md, tasks.yaml, interview.md
- vault/specs/package-trim/reference/{emr_sync_transport.py, workspace_map.py, target-map.json, check_layering.py, check_commitlint.py, check_depth_markers.py, test_manifest.py, test_matrix.md}
Spec context: GH #11 epic (17 uv workspace members -> 8). Workspace root: /Volumes/health-data.

## Acceptance checklist (bounded — SK-0008)

Score against this fixed checklist. Do NOT measure distance to an unbounded ideal — a design/code doc never reaches an asymptote, so "is this complete enough?" never converges. The bar is the checklist below, nothing more.

Set `overall_correctness = "correct"` if and only if **every** `Cn` holds AND no reported finding is an out-of-scope item. If any `Cn` fails, report it as a finding and set `overall_correctness` to `"needs-attention"` or `"incorrect"`.

- C1: every interface contract in `reference/` has a complete signature + I/O + exit contract consistent with design.md (EmrSyncTransport Protocol; check_* gate scripts; workspace_map model)
- C2: `reference/target-map.json` validates against `reference/workspace_map.py` (run: `python3 vault/specs/package-trim/reference/workspace_map.py vault/specs/package-trim/reference/target-map.json`)
- C3: every FR/NFR in requirements.md has >=1 AC; every AC maps to a `reference/test_manifest.py` test (AC-001..AC-010)
- C4: no contradiction across SPEC.md / requirements.md / design.md / tasks.yaml / reference/ stubs (e.g. member lists, dependency unions, phase ordering)
- C5: every required gate/constraint has a producer phase in tasks.yaml (structural/config/docs/verify/merge/close)
- C6: every typed-key kind (Layer, Depth) is assigned consistently in prose + model stub
- C7: `python3 /Volumes/agx/plugins/agx/skills/spec/scripts/spec_coverage.py /Volumes/health-data/vault/specs/package-trim` exits 0 (already PASS; re-run to confirm)
- C8: every AC has a row in `reference/test_matrix.md` with a backend home, and every matrix AC maps to >=1 test_manifest test

### Out of scope — NOT a violation, do not report as a finding

- "an implementer must still decide X" / "more detail would help"
- implementation choices deferred to /agx:spec run phases (exact pyproject text, README wording)
- anything the structural/verify phase validates against real code (uv sync outcomes, lock regen behavior)

## Prior-round findings (cumulative re-review)

Round-1 finding (confirm resolved, do NOT re-sample unrelated items that were acceptable last round):
- "NFR-002 has no acceptance criterion covering dependency-union or zero-new-runtime-dependency validation" — resolution claimed: AC-011 added to requirements.md; `reference/check_dep_union.py` (new) compares each post-trim member's pyproject deps to the union recorded in `reference/target-map.json`; test_manifest.py gained an AC-011 test; test_matrix.md gained an AC-011 row; tasks.yaml verify-phase validation now runs check_dep_union.py and lists NFR-002.

## Rubric dimensions

SK-0004 5-dim rubric: requirements-fidelity, internal-consistency, verifiability (ACs are commands), right-sizing (no gold-plating; matches GH #11 scope), risk-coverage (risks named with mitigations).

## Grounding

Resolve every concrete value cited as evidence — file path, line number, symbol / API name — via a tool command (`grep`, `git`, `cat`, `python3`) and quote it from the output. Never cite a location or value from memory or pattern-matching. If a check cannot be run, report that; do not substitute a plausible value to appear complete.

## Output

Produce JSON conforming to reviewer.schema.json:
- `findings[]` — each with `title`, `body`, `confidence_score` (0.0-1.0), `priority` (integer), `code_location` (`{absolute_file_path, line_range: {start, end}}`)
- `overall_correctness` — one of: "correct", "needs-attention", "incorrect" (= "correct" iff every `Cn` holds)
- `overall_explanation` — 2-4 sentence summary
- `overall_confidence_score` — 0.0-1.0

Each finding MUST cite an exact file path + line range (no vague locations).