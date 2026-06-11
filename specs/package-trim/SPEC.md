---
schema: spec/v0
name: package-trim
type: implementation
beads: hdp-1yi
---

# package-trim

## Summary

Collapse the uv workspace from 17 members to 8 (GH #11): merge six empty
data-layer shells into `hdp-core`, fold `hdp-ingest` into `hdp-api`, promote
`hh-hitl` to `packages/hdp-hitl` (satisfying hdp-schema-seed FR-102 so #12
resumes unedited), consolidate the home-health vertical to `hh-scribe` (+oasis,
+skills, +mcp) and a standalone `hh-emr-sync` whose transport-agnostic
`EmrSyncTransport` Protocol is the seam #14/#18 plug into. All moves are
history-preserving `git mv`; layering (packages → verticals → apps) is unchanged;
commitlint scopes, README, and CLAUDE.md follow the new map. The workspace is 226
src LOC with zero cross-package imports, so the rewrite is mechanical — the value
is honest structure (truthful Depth markers, member count matching code volume)
before #12 lands real code.

## Risks & Unknowns

- Merged-module collisions avoided by submodule layout (`hdp_core.audit`, …) —
  flat namespace rejected.
- Commitlint deadlock avoided by phase ordering (scope change after structural;
  see design.md § Decisions).
- pytest `--import-mode=importlib` requires unique test basenames post-merge
  (NFR-004; AC-010 verifies).
- `uv.lock` staleness across member removal: verify phase regenerates the lock;
  unknown whether `uv lock` needs `--upgrade` after member deletion — resolved at
  structural-phase run.
- `hdp-hitl` carries `fastapi` as a platform package — accepted now (HITL review
  API is platform-level per hdp-schema-seed design); revisit if API surfaces
  consolidate.
