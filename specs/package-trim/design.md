# Design

## Architecture

The 3-layer principle (packages → verticals → apps) is unchanged; only member
count changes. Every merge is a history-preserving `git mv` of a `src/` tree into
a submodule of the surviving member, plus a dependency-union rewrite of the
surviving member's pyproject. Zero cross-package imports exist today (grep sweep
2026-06-11), so no import-rewrite pass is needed beyond the moved packages' own
`__init__` files.

Test trees move with their packages. Every member carries
`tests/test_smoke.py` + `tests/__init__.py`; a merge therefore relocates the
merged member's test file into the survivor's `tests/` renamed
`test_<submodule>_smoke.py` (`git mv`, same history rule), and the merged
member's `tests/` dir — `__init__.py` included — is removed with the package.
`hdp-core` gets a fresh `tests/__init__.py`; `hdp-api` and `hh-scribe` already
have one. `hdp-hitl` is a whole-package move, not a merge, so its test rides
along under its original basename (per-member `tests/` packages keep duplicate
basenames importable under `--import-mode=importlib`, exactly as the 17-member
tree does today).

```
BEFORE (17)                          AFTER (8)
-----------                          ---------
packages/                            packages/
  hdp-canonical  --+                   hdp-core        <- canonical, audit,
  hdp-audit      --+                                      identity, consent,
  hdp-identity   --+--- merge ----->                      provenance, outbox
  hdp-consent    --+                                      (submodules)
  hdp-provenance --+                   hdp-api         <- + ingest (submodule)
  hdp-outbox     --+                   hdp-agent       (unchanged)
  hdp-ingest     ------ merge ----->   hdp-observability (unchanged, real code)
  hdp-api                              hdp-hitl        <- hh-hitl promoted
  hdp-agent                                               (schema-seed FR-102)
  hdp-observability                  verticals/home-health/
verticals/home-health/                 hh-scribe       <- + oasis, skills, mcp
  hh-oasis       --+                                      (submodules)
  hh-skills      --+--- merge ----->   hh-emr-sync     (standalone: seam boundary)
  hh-mcp         --+                 apps/
  hh-scribe                            home-health-scribe (deps remapped)
  hh-hitl        ------ promote -->
  hh-emr-sync
apps/
  home-health-scribe
```

Dependency edges after the trim (union rule, NFR-002):

- `hdp-core` ← pydantic, fhir.resources, sqlmodel
- `hdp-api` ← fastapi, uvicorn, pydantic
- `hdp-hitl` ← fastapi, hdp-core
- `hh-scribe` ← anthropic, pydantic, mcp, hdp-core, hdp-agent, hdp-api
- `hh-emr-sync` ← httpx, hdp-core
- `home-health-scribe` ← fastapi, uvicorn, hh-scribe, hdp-hitl, hh-emr-sync

## File manifest

Single SoT is `tasks.yaml` `manifest:` (file -> new|modified -> purpose). For the
seam contract, target-map model, golden example, and AC-mapped test manifest see
`reference/`.

## Decisions

- **`hh-emr-sync` stays a standalone member** — its adapter seam is the
  integration point for the computer-use transport (#14/#18); a separate member
  keeps the dependency surface auditable (today exactly httpx + one workspace
  dep). The `EmrSyncTransport` Protocol stub (`reference/emr_sync_transport.py`,
  landed as `hh_emr_sync.transport`) is the only interface code this spec adds —
  it makes seam preservation verifiable (AC-005) rather than aspirational. The
  stub is the seam anchor, not the final adapter contract (see the async-push
  decision below).
- **`push` made async at birth (2026-06-11)** — the computer-use research hub
  (vault/research/computer-use-emr-sync/) flags synchronous request/response as
  disqualifying for the automation transport: a browser-driven write-back cannot
  complete inside a blocking call. Zero implementations exist today, so the
  signature change is free now and breaking later; `health()` stays sync (cheap
  liveness probe). Idempotency is honored in the stub now
  (`SyncResult.idempotency_key`); checkpoint/resume and
  job-handle/async-completion semantics are deferred to epic #14's "define the
  adapter contract" item — they need driver-run experience to design well.
- **`hdp-outbox` merges into `hdp-core`, not `hh-emr-sync`** — the outbox is a
  data-layer persistence pattern (sqlmodel dep, same as audit/consent); the
  vertical consumes it, doesn't own it.
- **`hh-mcp` merges into `hh-scribe`, not `hdp-api`** — the MCP server exposes
  home-health workflow tools; it is vertical-specific serving surface, not a
  platform primitive.
- **`hdp-hitl` promotion honors hdp-schema-seed FR-102 verbatim** — the
  alternative (folding HITL into `hdp-core`) would force edits to an approved,
  partially-executed spec; placement cost is one extra member, well inside the
  ≤8 budget.
- **Trust-boundary NFR deleted** — the trim adds no input-accepting surface; the
  only "inputs" are workspace files whose malformed states `uv`/`pytest` already
  fail fast on. Keeping a vacuous NFR would force a vacuous AC.
- **Commitlint sequencing** — the scope-enum change lands in its own config phase
  *after* the structural phase; trim commits use surviving scopes (`packages`,
  `verticals`, `workspace`) so no commit references a scope being deleted by the
  same PR.
- **No ADR lift** — placement choices above are spec-scoped consequences of the
  existing 3-layer architecture; the layer principle itself (the ADR-worthy
  decision) is untouched.
