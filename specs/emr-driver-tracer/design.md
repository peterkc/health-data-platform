# Design

## Architecture

The driver is the production skeleton of a browser-level EMR sync transport,
built as the thinnest end-to-end thread that exercises every load-bearing
joint: durable job orchestration, deterministic browser control, audit,
failure classification, and the two integration surfaces (CLI, thin API).
Extraction quality and OASIS modeling are explicitly not this system's
concern — the infrastructure is.

```
  CLI (typer)            thin API (FastAPI)
      |                        |
      +----------+------------+
                 v
        DBOS workflow (field-roundtrip job)
        each step checkpointed in Postgres
        write steps carry idempotency keys
                 |
                 v
        browser session (Playwright, Chromium)
        programmatic login -> storage_state custody
        egress: default-deny route() allowlist
                 |                          |
                 v                          v
        selector map (versioned)      audit store (append-only)
        miss -> failures.classify()   every action, replayable
        drift -> fallback seam
        (Stagehand BYOB, gated phase)
                 |
                 v
        OpenEMR sandbox (docker-compose, pinned, synthetic-only)
```

Job lifecycle: a job submitted via CLI or API becomes a DBOS workflow; each
browser interaction is a step whose completion is checkpointed. A killed
driver resumes from the last completed step — completed writes are not
re-applied because write steps consult their idempotency key before acting.
Every action (including blocked egress and failures) appends an audit
event; replay is a read of that stream in order. Failure classification
runs before any retry decision so the taxonomy data is captured even when
recovery succeeds.

The fallback seam is a driver-owned Protocol: the deterministic path never
imports or calls it (zero LLM calls, asserted by AC-011); the gated
fallback-eval phase provides a Stagehand BYOB implementation behind it and
measures recovery behavior plus the open agent-cache replay question.

## Execution note (cross-repo)

This spec lives in the HDP vault but its code phases execute in a clone of
`emr-sync-driver`. Evidence and phase state record here
(`vault/specs/emr-driver-tracer/`); the hub-feedback phase is the only one
that edits HDP files (the research hub, via the vault worktree). Repo
creation in the bootstrap phase is an irreversible op: main-session user
sign-off, never delegated.

## File manifest

Single SoT is `tasks.yaml` `manifest:` (file -> new|modified -> purpose).
Manifest paths are emr-sync-driver-relative except `vault/`-prefixed
entries (HDP). For interface contracts (CLI signatures, data models, golden
example, AC-mapped test manifest, behavior x backend matrix) see
`reference/`.

## Decisions

Foundational decisions are NOT re-made here — they are user-ratified in the
research hub's decision log (`vault/research/computer-use-emr-sync/state.yaml`,
6 entries): DOM-first/vision-assist control loop, self-hosted pinned OpenEMR
sandbox, structural security posture, taxonomy-from-spike-runs, Playwright +
DBOS foundations, deployment topology. Duplicating them as ADRs would create
mirror drift; this section records only spec-local decisions:

- **Standalone driver, converge later** (interview Dim 3): the tracer
  depends on no HDP package — HDP primitives are pre-trim shells and #11 is
  in flight. The thin API is the convergence seam: its job operations are
  the HTTP shape the `hh-emr-sync` adapter will consume, and the driver's
  audit/checkpoint interfaces inform HDP's primitives from real usage.
- **Fallback gated behind deterministic E2E** (interview Dim 2): the
  deterministic skeleton must pass AC-003/AC-004 before any LLM-assist code
  lands. Couples one unknown per phase; preserves the zero-LLM property of
  the primary path as a tested invariant rather than a hope.
- **Sessions are cattle** (from research, operationalized here):
  storage_state is a bearer credential — custody rules in FR-009; on
  session death the driver re-authenticates rather than persisting
  long-lived session stores.
- **Audit store is driver-local Postgres, not HDP's audit package**:
  consequence of standalone-first. The event shape (models.py AuditEvent)
  is written so a later HDP adapter can map it 1:1 into platform audit
  primitives.

## Risks

- DBOS + Playwright interaction is unproven in this combination (async
  Playwright inside DBOS steps; step granularity vs browser session
  affinity). The tracer phase exists to surface exactly this class of
  unknown early — if step-per-action is too chatty, the fallback design is
  step-per-page-interaction with action-level audit retained.
- OpenEMR compose specifics (ports, default creds, seeding) are known
  unknowns resolved at bootstrap (hub open questions); they affect setup
  cost, not architecture.
- `connect_over_cdp` reattach topology (browser survives driver death) is
  documented lower-fidelity; the tracer's SIGKILL test targets driver-process
  death with browser relaunch + storage_state re-injection, which is the
  supported path. Browser-process survival is an optimization, not a
  requirement.
