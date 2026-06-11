You are validating an interview transcript for `/agx:spec` quality.

## Transcript

# package-trim — interview transcript

Provenance: answers derived from the orchestrating session's decisions (GH issue #11,
user-approved trim verdict of 2026-06-10, hdp-schema-seed spec FR-102 constraint) and
fresh tool evidence gathered 2026-06-11. No live user interview — the fork executing
this spec inherited the deciding conversation; deferred judgment calls are marked
`NEEDS CLARIFICATION`.

## Dim 1 — Users & their workflows

**Who triggers this, what do they currently do?**

Two users. (a) Contributors (including agent sessions) navigating the workspace: today
they face 17 uv workspace members for 452 total src LOC — 16 members contain only a
3-line `__init__.py` (evidence: per-member `wc -l` sweep 2026-06-11; only
`packages/hdp-observability` has real code, 178 LOC). Empty-shell navigation cost and
untruthful Depth markers (`packages/hdp-canonical/README.md:5` claims `DEEP` over 3
LOC) mislead both humans and agents. (b) The make-it-run epic (#12), which resumes the
`hdp-schema-seed` spec: its FR-102 task renames `verticals/home-health/hh-hitl/` →
`packages/hdp-hitl/` (`vault/specs/hdp-schema-seed/tasks.yaml:34`) and must find a
workspace shaped to receive that.

**Follow-up — what breaks if we do nothing?** #12 lands schema + app code into a
17-member layout the team has already judged ahead of its code volume (GH #11
Overview); every later consolidation pays migration cost on real code instead of
empty shells. Merging now is mechanical: zero cross-package imports exist outside
`__init__`/tests (grep sweep 2026-06-11, zero hits).

## Dim 2 — Scope & functional requirements

**What does success look like? Non-goals?**

Target map (8 workspace members, from 17):

| Member | Absorbs | Rationale |
| --- | --- | --- |
| `packages/hdp-core` | hdp-canonical, hdp-audit, hdp-identity, hdp-consent, hdp-provenance, hdp-outbox | Data-layer primitives; all sqlmodel/pydantic shells |
| `packages/hdp-api` | hdp-ingest | Both are I/O boundary (FastAPI serving + intake) |
| `packages/hdp-agent` | — | Unchanged |
| `packages/hdp-observability` | — | Unchanged (only real code, 178 LOC) |
| `packages/hdp-hitl` | hh-hitl (promoted) | FR-102 alignment so #12 resumes cleanly |
| `verticals/home-health/hh-scribe` | hh-oasis, hh-skills, hh-mcp | Domain pipeline + models + agent-facing surfaces |
| `verticals/home-health/hh-emr-sync` | — | Stands alone: transport seam needs its own dependency boundary (#14/#18) |
| `apps/home-health-scribe` | — | Deps updated to post-trim members |

Non-goals: no new feature code (that is #12/#13); no layering change (3-layer
packages → verticals → apps principle is unchanged per GH #11); no dropping of any
primitive concept — merged packages survive as modules inside `hdp-core`.

**Follow-up — why does hh-emr-sync stay standalone instead of merging?** Its
adapter seam is the integration point for the computer-use transport (#14/#18); a
separate member keeps its dependency surface auditable (today exactly
`httpx>=0.28, hdp-outbox` per `verticals/home-health/hh-emr-sync/pyproject.toml`,
becoming `httpx, hdp-core` post-merge).

## Dim 3 — Integration & data flow

**What does this consume / produce / depend on?**

Consumes: current dependency edges (tool-resolved 2026-06-11): hh-hitl →
{fastapi, hdp-audit, hdp-canonical}; hh-mcp → {mcp, hdp-api}; hh-oasis →
{pydantic, hdp-canonical}; hh-scribe → {anthropic, hdp-canonical, hdp-agent};
hh-emr-sync → {httpx, hdp-outbox}; app → {fastapi, uvicorn, hh-scribe, hh-oasis,
hh-hitl, hh-emr-sync}. Produces: rewritten root `pyproject.toml`
(`tool.uv.sources` shrinks to 8 entries), per-member pyprojects with remapped
deps (audit/canonical → hdp-core etc.), regenerated `uv.lock`, updated
`.commitlintrc.yaml` scope-enum + `x-scope-patterns`, updated README/CLAUDE.md
architecture text. Depends on: `git mv` history preservation (validated on the
prior tracer: "git mv preserves file history across the hh-hitl -> hdp-hitl
rename", `vault/specs/hdp-schema-seed/evidence/tracer-scaffold/retro.json:18`).

**Follow-up — downstream consumers?** #12 (resumes hdp-schema-seed against the
new map), CI (`just verify`), commitlint hook (scope-enum must match or every
commit fails), CodeRabbit path filters (unaffected — no excluded path moves).

## Dim 4 — Quality criteria

**Measurable acceptance criteria; how do we verify?**

- Workspace member count == 8 and `uv sync` exits 0
- `just verify` (ruff + pytest, CI mirror) exits 0
- Layering holds: no package depends on a vertical/app; no vertical depends on an
  app (pyproject dependency scan + import grep)
- `packages/hdp-hitl` exists, importable as `hdp_hitl`, moved via `git mv`
  (history-preserving), and `vault/specs/hdp-schema-seed/tasks.yaml` FR-102 task
  is satisfiable or marked done against the new layout
- `hh-emr-sync` exposes a transport-agnostic `EmrSyncTransport` Protocol stub;
  the seam contract has no httpx types in its signatures
- `.commitlintrc.yaml` scope-enum exactly matches the post-trim member set (plus
  the static scopes); every `x-scope-patterns` glob resolves to an existing path
- Every remaining member README carries a truthful Depth marker (SKEL for empty
  shells; hdp-observability keeps its real depth)
- README + CLAUDE.md architecture text reflects the 8-member map and preserves
  the settled positioning language (workflow + governance layer)

## Dim 5 — Risks & unknowns

**What could go wrong? What don't we know yet?**

- Merged-module collision: each merged package keeps a distinct module name
  (`hdp_core.audit`, `hdp_core.canonical`, …) — flattening into one namespace
  could collide later; mitigated by submodule layout inside `hdp_core`.
- Commitlint deadlock: trim commits reference scopes being removed — sequence the
  scope-enum change so commits validate at each step (config phase ordering).
- `pytest --import-mode=importlib` duplicate-basename discipline (root
  `pyproject.toml`) — merged `tests/` dirs must not collide on basenames.
- hdp-hitl as a platform package carrying `fastapi`: acceptable now (HITL review
  API is platform-level per hdp-schema-seed design); revisit if api surface
  consolidates. NEEDS CLARIFICATION: none blocking — placement is fixed by FR-102.
- Unknown: whether `uv` tolerates removing workspace members referenced in stale
  `uv.lock` without a clean `uv lock` regen — verify phase regenerates the lock.


## Required dimensions

1. Users & their workflows — who triggers this, what do they currently do?
2. Scope & functional requirements — what does success look like? non-goals?
3. Integration & data flow — what does this consume / produce / depend on?
4. Quality criteria — measurable acceptance criteria; how do we verify?
5. Risks & unknowns — what could go wrong? what don't we know yet?

## Ambiguity threshold

Report a gap ONLY when one of these bounded checks fails:
- C1: each of the 5 interview dimensions has a concrete answer
- C2: every measurable claim cites a transcript-resolvable evidence line (file path, command sweep, or spec line reference)
- C3: no contradiction across answers

OUT OF SCOPE (NOT a gap): "the user could elaborate more", choices deferred to design, anything `/agx:spec run` phases verify against real code.

## Grounding

Resolve every concrete value cited as evidence — file path, line number, symbol / API name — via a tool command (`grep`, `git`, `cat`) against the worktree at /Volumes/health-data and quote it from the output. Never cite a location or value from memory or pattern-matching. If a check cannot be run, report that; do not substitute a plausible value to appear complete.

## Output

Produce JSON conforming to the provided schema:
- `dim_coverage_gaps[]` — dimensions the transcript fails to address (empty objects; describe in suggested_probes)
- `ambiguities[]` — statements requiring clarification before /agx:spec can proceed
- `missing_evidence[]` — claims unsupported by transcript citations
- `suggested_probes[]` — follow-up questions (strings) to close the gaps

Be exhaustive on C1-C3 failures only; the goal is to prevent under-scoped specs from proceeding without flagging deferred-to-design choices.