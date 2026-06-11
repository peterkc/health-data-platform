# Interview — emr-driver-tracer

Conducted 2026-06-11 (main session, orchestrator). Research pre-fill:
`vault/research/computer-use-emr-sync/` (8 sources, 6 user-ratified
decisions) answers the approach/integration baseline; questions below cover
only the dimensions the research left open. Answers recorded verbatim from
AskUserQuestion selections.

## Dim 1 — Users & their workflows

**Q:** Who is the tracer-phase user, and through what surface?
**A (user):** "Both in tracer" — CLI + thin API.

Orchestrator interpretation (flagged for challenger review): CLI is the
primary developer/researcher surface (run job, resume job, inspect audit
log); the thin API is a FastAPI layer exposing the same job operations
(submit, status, resume) so the eventual `hh-emr-sync` adapter contract has
a real HTTP shape to integrate against. No UI. If "thin API" meant
something broader, this is a NEEDS CLARIFICATION.

## Dim 2 — Scope & functional requirements

**Q:** Driver repository name?
**A (user):** `emr-sync-driver` — standalone framing, no HDP coupling in
the name.

**Q:** Repository visibility from creation?
**A (user):** Public from creation. Synthetic-only, zero application
context; the tracer is the portfolio's runnable slice. Repo creation
itself remains a main-session user sign-off at execution time (irreversible
op per CLAUDE.md delegation rules).

**Q:** Is the LLM-fallback layer (Stagehand BYOB evaluation) part of the
tracer's first thread?
**A (user):** Gated phase after deterministic E2E — prove the deterministic
skeleton first; Stagehand evaluation becomes its own phase with its own
evidence. Matches ratified DOM-first-primary.

Non-goals (from research scope + dispatch context, unchallenged): no OASIS
data modeling in the tracer; no vision-primary implementation; no PHI ever
(synthetic only); driver implementation stays out of the HDP repo.

## Dim 3 — Integration & data flow

**Q:** Does the tracer consume HDP packages (hdp-audit, hdp-outbox —
currently empty shells), or stand alone?
**A (user):** Standalone, converge later — HDP packages are pre-trim empty
shells (#11 in flight); the adapter contract is the deliberate seam, and
the driver's audit/outbox interfaces inform HDP's primitives from real
usage.

Pre-filled from research (ratified): consumes self-hosted pinned OpenEMR
(docker-compose, synthetic patients); produces taxonomy rows + hardening
recommendations back to the hub (#18 exit conditions) and adapter-contract
implications to #11's emr-sync seam; foundations Playwright (deterministic
loop) + DBOS (Postgres-backed checkpoint/resume).

## Dim 4 — Quality criteria

**Q:** Done-bar for the deterministic tracer phase — confirm or adjust:
(1) E2E thread completes against self-hosted OpenEMR (login → navigate →
read field → write field → read-after-write verify); (2) kill -9 mid-job →
resume completes from last checkpoint without re-applying writes; (3) ≥3
taxonomy rows filled from observed failures, each with a hardening
recommendation; (4) audit log replays the full job action-by-action.
**A (user):** Confirm all four.

Quality bar (user-directed, this session): tracer-bullet quality — kept
code, production skeleton, NOT throwaway spike code. "No shortcuts.
Shortcuts lead to bad assumptions and refactors are costly downstream."

## Dim 5 — Risks & unknowns

**Q:** Constraints on where the tracer runs and how long it should take?
**A (user):** Local Mac (arm64), no deadline pressure — quality over speed.

Known unknowns carried from research (hub open questions):
- Stagehand Python agent-cache replay path (server-side or client-built) —
  measure during the gated fallback phase
- OpenEMR synthetic-patient seeding mechanism (built-in demo data vs
  Synthea import) — resolve at scaffold time
- OpenEMR production-compose default ports/credentials (Docker Hub page) —
  resolve at scaffold time
