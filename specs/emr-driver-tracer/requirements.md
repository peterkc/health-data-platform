# Requirements

Paths are relative to the `emr-sync-driver` repository root unless prefixed
`vault/` (HDP repository, hub feedback). Foundations and security posture
are user-ratified in `vault/research/computer-use-emr-sync/` and are
constraints here, not open questions.

## Functional

- FR-001: WHEN the bootstrap phase executes, the system SHALL exist as a
  public GitHub repository `peterkc/emr-sync-driver` (MIT license, uv
  project, Python >=3.13, CI running lint + type check + tests) — creation
  itself gated on main-session user sign-off (irreversible op).
- FR-002: WHEN `docker compose up` runs on the development machine (arm64),
  the sandbox SHALL provide a version-pinned OpenEMR instance and a
  Postgres instance (DBOS system database), seeded with synthetic patients
  only.
- FR-003: WHEN a demo sync job runs against the sandbox, the driver SHALL
  log in programmatically (credentials sourced from environment/secret
  store, never present in any LLM-visible surface), navigate to a target
  synthetic patient, read a named field, write a named field, and verify
  the write by re-reading the field.
- FR-004: every job step SHALL execute as a DBOS step with its completion
  checkpointed in Postgres; WHEN the driver process dies mid-job (including
  SIGKILL), a resume SHALL complete the job from the last completed step
  WITHOUT re-applying completed writes (idempotency keys on write steps).
- FR-005: every browser action SHALL append a structured audit event
  (timestamp, job id, step id, action, locator, outcome, failure class if
  any) to an append-only store; the CLI SHALL replay a job's audit log
  action-by-action in order.
- FR-006: the driver SHALL expose the same job operations through both
  surfaces: a typed CLI (run / resume / status / audit replay) and a thin
  FastAPI service (submit job, get status, resume) publishing an OpenAPI
  schema — the HTTP shape the future `hh-emr-sync` adapter integrates
  against.
- FR-007: WHEN a step fails, the driver SHALL classify the failure as one
  of `dead-session | latency | selector-drift | unknown` BEFORE any retry
  decision, and the classification SHALL land in the audit event.
- FR-008: the browser context SHALL enforce a default-deny egress allowlist
  (sandbox hosts only) via request routing as defense-in-depth, with
  blocked requests logged; authoritative network-layer enforcement is
  documented for production topologies (not implemented in the tracer).
- FR-009: session artifacts (Playwright storage_state) SHALL be treated as
  bearer credentials: stored outside the repository tree with file mode
  0600, and absent from audit events, checkpoints, logs, and traces.
- FR-010: WHEN the deterministic thread is proven end-to-end (FR-003/004
  acceptance passed), a gated fallback phase SHALL evaluate Stagehand BYOB
  as the selector-drift recovery layer behind a driver-owned seam
  interface; the deterministic path SHALL make zero LLM calls, and
  evaluation findings (including the open agent-cache replay question)
  SHALL be recorded to the research hub.

## Non-functional

- NFR-001: tracer-bullet quality (kept code): every code phase lands with
  `ruff check` clean, `mypy src/` clean, and `pytest` green in CI — no
  placeholder bodies on the executed path, no skipped quality gates.
- NFR-002 (negative-space): WHEN given invalid input at a trust boundary
  (CLI args, env/config, API request bodies, selector-map files), the
  system SHALL fail fast with a typed error — never crash, corrupt job
  state, or write to the EMR on bad input.
- NFR-003: synthetic-data-only scope: the egress allowlist and target
  configuration SHALL admit only the local sandbox; no PHI exists anywhere
  in the system, its logs, or its repository.
- NFR-004: public-reader hygiene: repository and hub content SHALL carry
  zero application-context leaks — verified before merge.

## Acceptance criteria

- AC-001: `gh repo view peterkc/emr-sync-driver --json visibility,licenseInfo`
  reports PUBLIC + MIT; a fresh clone runs `uv run pytest` green; CI is
  green on default branch. (FR-001)
- AC-002: `docker compose up -d` then an HTTP probe returns the OpenEMR
  login page; the compose file pins an explicit OpenEMR version tag; a
  seeded synthetic patient is retrievable. (FR-002)
- AC-003: `uv run emr-sync run field-roundtrip --patient <synthetic-id>`
  exits 0; the job's final audit event records read-after-write
  verification success. (FR-003)
- AC-004: an integration test SIGKILLs the driver mid-job, then
  `uv run emr-sync resume <job-id>` completes the job; the target field
  holds the expected value exactly once and the audit log shows no
  duplicate write application. (FR-004)
- AC-005: `uv run emr-sync audit replay <job-id>` prints every action of
  the job in order; the replayed action count equals the recorded step
  actions. (FR-005)
- AC-006: `POST /jobs` accepts a job, `GET /jobs/{id}` reports status
  transitions, `POST /jobs/{id}/resume` resumes; `/openapi.json` serves the
  schema. (FR-006)
- AC-007: an induced selector miss is classified `selector-drift` and an
  induced logout is classified `dead-session`, asserted on audit events.
  (FR-007)
- AC-008: a test request to a non-allowlisted host is blocked and a blocked
  event is logged. (FR-008)
- AC-009: a test asserts the storage_state file lives outside the repo tree
  with mode 0600, and greps audit/checkpoint payloads for its content
  finding nothing. (FR-009)
- AC-010: the hub taxonomy table
  (`vault/research/computer-use-emr-sync/README.md`) gains >=3 observed
  rows, each carrying a hardening recommendation. (#18 exit condition)
- AC-011: with fallback disabled, a full job's audit log contains zero LLM
  calls; with fallback enabled, an induced drift either recovers via the
  seam or halts cleanly with classification — and the hub records the
  Stagehand evaluation findings. (FR-010)
- AC-012 (negative-space): for each trust boundary (CLI args, env/config,
  API bodies, selector-map files), a test feeds malformed input and asserts
  a typed error / non-zero exit, not a crash or an EMR write. (NFR-002)
- AC-013: before merge, a hygiene grep over the full driver repository
  content and the hub-feedback diff returns zero application-context hits
  (term list carried in bead hdp-8qn, never in public artifacts); the merge
  phase records the clean grep as gate evidence. (NFR-004)
