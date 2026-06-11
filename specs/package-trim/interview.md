# package-trim — interview transcript

Provenance: answers derived from the orchestrating session's decisions (GH issue #11,
user-approved trim verdict of 2026-06-10, hdp-schema-seed spec FR-102 constraint) and
fresh tool evidence gathered 2026-06-11. No live user interview — the fork executing
this spec inherited the deciding conversation; deferred judgment calls are marked
`NEEDS CLARIFICATION`.

## Dim 1 — Users & their workflows

**Who triggers this, what do they currently do?**

Two users. (a) Contributors (including agent sessions) navigating the workspace: today
they face 17 uv workspace members for 226 total src LOC — 16 members contain only a
3-line `__init__.py` (evidence: per-member `wc -l` sweep over `*/src/**/*.py`,
2026-06-11: 16 × 3 + 178 = 226; only `packages/hdp-observability` has real code,
178 LOC). Empty-shell navigation cost and
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

GH #11 decision text (quoted for worktree-independence; epic approved by the user
2026-06-10): "The workspace declares 17 members for ~450 lines of source; 16
packages contain only a version string. […] Collapse to ~7–8 packages until
implementation volume earns the finer split; the layering principle is unchanged."
Decomposition items: hdp-core merge; vertical to two; hh-hitl placement
adjudication (hdp-schema-seed FR-102); transport-agnostic emr-sync seam; commitlint
/ workspace / docs updates. Success criteria: "Workspace member count ≤ 8 with CI
green"; layering respected; truthful Depth markers. (The epic's "~450 lines" figure
counted src + tests; the src-only sweep above is 226 — both describe the same
empty-shell state.) Related issues: #12 "epic: make it run — runnable app + real
schema" (resumes hdp-schema-seed), #13 "epic: domain depth", #14 "epic:
computer-use EMR workflow automation" with spike #18 (consumes the emr-sync seam).

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

Non-goals: no new feature code, meaning behavior/implementation (that is #12/#13)
— the one deliberate exception is the `EmrSyncTransport` Protocol stub in
`hh-emr-sync`, which is SKEL-depth interface contract (signatures +
`NotImplementedError`), the artifact that makes the seam-preservation requirement
verifiable rather than aspirational; no layering change (3-layer packages →
verticals → apps principle is unchanged per GH #11); no dropping of any primitive
concept — merged packages survive as modules inside `hdp-core`.

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
