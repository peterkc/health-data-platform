---
schema: spec/v0
name: emr-driver-tracer
type: implementation
beads: hdp-c3v
---

# emr-driver-tracer

## Summary

Build the tracer bullet for the computer-use EMR sync transport (GH #18,
parent #14): a new public repository `emr-sync-driver` containing the
thinnest production-quality thread — programmatic login to a self-hosted
synthetic OpenEMR, read one field, write one field, verify by re-reading —
with every step DBOS-checkpointed, every action audited and replayable,
failures classified before retry, and the same job operations exposed via
CLI and a thin FastAPI surface. Deliberate failure injection (SIGKILL
mid-job, induced selector miss, killed session) seeds the research hub's
failure taxonomy with >=3 observed rows. A gated final code phase evaluates
Stagehand BYOB as the drift-recovery fallback; the deterministic path makes
zero LLM calls by tested invariant. Kept code, no shortcuts: foundations
are the user-ratified research decisions, and the custom surface (selector
maps, audit, classification, adapter-shaped API) is the part with research
value.

## Risks & Unknowns

- DBOS step granularity vs Playwright session affinity — unproven
  combination; surfaced deliberately by the tracer phase (design.md §
  Risks).
- OpenEMR compose ports/credentials/seeding — known unknowns resolved at
  bootstrap (carried from hub open questions).
- Stagehand Python agent-cache replay path — UNVERIFIED in research;
  answered empirically in the fallback-eval phase.
- Dim 1 "thin API" interpretation (job submit/status/resume, no UI) was
  orchestrator-inferred and challenger-validated; if the adapter contract
  needs a different surface, it shows up at #11 integration, not here.
