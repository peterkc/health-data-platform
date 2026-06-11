# Requirements

## Functional

- FR-001: WHEN the trim lands, the uv workspace SHALL resolve exactly 8 members:
  `hdp-core`, `hdp-api`, `hdp-agent`, `hdp-observability`, `hdp-hitl` (packages);
  `hh-scribe`, `hh-emr-sync` (verticals/home-health); `home-health-scribe` (apps).
- FR-002: `hdp-core` SHALL expose every absorbed primitive as a submodule —
  `hdp_core.canonical`, `hdp_core.audit`, `hdp_core.identity`, `hdp_core.consent`,
  `hdp_core.provenance`, `hdp_core.outbox` — so no primitive concept is dropped.
- FR-003: WHEN the structural phase executes, `verticals/home-health/hh-hitl/` SHALL
  move to `packages/hdp-hitl/` (importable as `hdp_hitl`), satisfying
  hdp-schema-seed FR-102 so the make-it-run epic (#12) resumes without spec edits.
- FR-004: `hh-scribe` SHALL absorb `hh-oasis`, `hh-skills`, and `hh-mcp` as
  submodules `hh_scribe.oasis`, `hh_scribe.skills`, `hh_scribe.mcp`.
- FR-005: `hdp-api` SHALL absorb `hdp-ingest` as submodule `hdp_api.ingest`.
- FR-006: `hh-emr-sync` SHALL expose an `EmrSyncTransport` Protocol
  (`hh_emr_sync.transport`) whose signatures reference no transport-specific types
  (no `httpx` imports in the protocol module), keeping the seam transport-agnostic
  for #14/#18.
- FR-007: WHEN members change, `.commitlintrc.yaml` `scope-enum` SHALL exactly equal
  the static scopes (workspace, packages, verticals, apps, docs, ci, deps, infra,
  vault, adr, spec, research) plus the 8 post-trim member names, and every
  `x-scope-patterns` glob SHALL resolve to an existing path.
- FR-008: `README.md` and `CLAUDE.md` architecture text SHALL describe the 8-member
  map and SHALL preserve the settled positioning language (AI-native workflow +
  governance layer; Medplum named complementary).
- FR-009: every remaining member README SHALL carry a Depth marker truthful to its
  contents (SKEL for interface-only shells; `hdp-observability` keeps its earned
  depth).

## Non-functional

- NFR-001: all moves SHALL use `git mv` so `git log --follow` reaches pre-move
  history (validated pattern: hdp-schema-seed tracer retro).
- NFR-002: the trim SHALL introduce zero new runtime dependencies; each merged
  package's dependencies are exactly the union of its absorbed members'
  dependencies (deduplicated).
- NFR-003: layering SHALL hold — no `packages/*` member depends on a vertical or
  app; no vertical depends on an app (pyproject dependency scan).
- NFR-004: merged `tests/` trees SHALL keep unique test-file basenames so pytest
  `--import-mode=importlib` collection stays collision-free.

(The template's negative-space trust-boundary NFR is deleted: this spec is a
structural refactor introducing no input-accepting surface; malformed workspace
states fail fast inside `uv` itself. Rationale in design.md § Decisions.)

## Acceptance criteria

- AC-001: `uv sync` exits 0 AND
  `ls -d packages/*/ verticals/home-health/*/ apps/*/ | wc -l` prints 8.
- AC-002: `just verify` (ruff + pytest, CI mirror) exits 0.
- AC-003: `reference/check_layering.py` exits 0 — zero layering violations across
  all member pyprojects.
- AC-004: `uv run python -c "import hdp_hitl"` exits 0 AND
  `git log --follow --oneline -- packages/hdp-hitl/src/hdp_hitl/__init__.py`
  lists the pre-move (hh-hitl) commits.
- AC-005: `uv run python -c "from hh_emr_sync.transport import EmrSyncTransport"`
  exits 0 AND the protocol module contains no `httpx` import.
- AC-006: `reference/check_commitlint.py` exits 0 — scope-enum equals the expected
  set and every x-scope-patterns glob resolves.
- AC-007: README.md and CLAUDE.md mention `hdp-core` and contain no removed member
  names in architecture text; README retains the positioning sentence.
- AC-008: `reference/check_depth_markers.py` exits 0 — every member README has a
  Depth line and no interface-only member claims MIN/DEEP/COMPOSED.
- AC-009: `uv run python -c "import hdp_core.canonical, hdp_core.audit,
  hdp_core.identity, hdp_core.consent, hdp_core.provenance, hdp_core.outbox,
  hdp_api.ingest, hh_scribe.oasis, hh_scribe.skills, hh_scribe.mcp"` exits 0
  (concept survival).
- AC-010: `uv run pytest -q --co` exits 0 (no duplicate-basename collisions).
- AC-011: `reference/check_dep_union.py` exits 0 — each post-trim member's
  pyproject dependencies equal the union recorded in `reference/target-map.json`
  (zero new runtime dependencies; verifies NFR-002).
