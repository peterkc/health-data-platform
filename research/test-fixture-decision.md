# DB Test Fixture Decision

**Status**: Decided 2026-04-25 for spec `hdp-schema-seed` Phase 1 (FR-104)
**Purpose**: Record the chosen approach for DB-integration tests so Phase 2/3 fixtures are unambiguous
**Companion to**: [database-substrate.md](database-substrate.md), [hdp-initial-tables.md](hdp-initial-tables.md)

## Decision

**Shared docker stack** — integration tests connect to the `postgres` service defined by the repo's `docker-compose.yml`, reachable on `localhost:5437` with credentials `hdp/hdp/hdp`. Fixtures use `psycopg` directly against that DB and wrap each test in a transaction that rolls back at teardown.

This is the option pre-anchored by spec `design.md` §Test fixture strategy. Phase 1 confirms it.

## Alternatives considered

| Option | What it is | Why rejected (for now) |
|--------|------------|------------------------|
| **`pytest-postgresql`** | Spawns an in-process Postgres per test session via `pg_ctl` against a temp datadir | Adds a second Postgres binary path + version assumption; pgvector + uuidv7 (PG ≥ 18.3) require pinning the binary tightly. Real friction for very little marginal value over the docker stack. |
| **Testcontainers (Python)** | Spawns ephemeral Docker containers per test session | Per-session container start/teardown is tens of seconds even with the image cached; hides the dev-equivalent stack behind a different lifecycle, so debugging "works in test, fails in dev" becomes harder. Harder to debug at the `psql` prompt because the container ID is ephemeral. |
| **Mocked psycopg** | Pure unit tests with mock cursors | Doesn't exercise real SQL; defeats the point of testing CREATE TABLE / TRIGGER / extension behavior. Unit tests where we mock the cursor are still useful at the application layer, but for schema-integration the real engine is the SUT. |

## Rationale

- **Matches dev workflow** — developers run `just up && just db-ddl && just seed` interactively; tests connect to the same stack. One fewer cognitive context.
- **Fewest moving parts** — no extra binary, no extra container, no extra version pin. The `pgvector/pgvector:pg18` image already covers PG 18.3 + all four required extensions.
- **Fast iteration** — once the stack is up, each test is a transaction-scoped rollback (sub-millisecond on local Docker). No container-start overhead per session.
- **Real engine, real failures** — `CREATE EXTENSION vector` failing surfaces immediately; trigger semantics and `RETURNING OLD/NEW` behavior on PG 18 are exercised on the real binary, not approximated.

## Trade-offs

- **Concurrency caveat** — multiple test workers sharing one DB risk row-level cross-talk. Mitigated by transaction-scoped rollback and per-test schemas/data namespacing where needed. Phase 3 fixtures default to single-worker pytest; concurrent xdist runs are deferred.
- **Stateful dev DB** — test runs that bypass rollback (e.g. early-exit fixtures) leave residue. `just db-reset` is the safety net.
- **CI shape** — CI must `just up && just db-ddl && just seed` before running pytest's integration markers. Acceptable as a one-time sprint cost; `pytest -m integration` selects the integration subset where needed.

## Migration trigger

Flip to **Testcontainers** (without spec rewrite) if any of:

1. Concurrency tests need parallel DB instances (xdist with isolated state)
1. CI runners cannot run Docker Compose reliably and per-container lifecycle is simpler
1. Integration tests start to depend on Postgres-version diffs we want to range-test (`pg18` AND `pg19-beta`)

Fixtures are the only affected surface for any of these flips. The DDL files, the seed script, and the `/health` endpoint do not change.

## Cross-references

- [database-substrate.md](database-substrate.md) — Postgres version pin and extension list
- [hdp-initial-tables.md](hdp-initial-tables.md) — table inventory the fixture suite must cover
- spec `design.md` §"Test fixture strategy" — anchored this default
