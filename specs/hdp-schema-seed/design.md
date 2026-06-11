# Design: hdp-schema-seed

## Architecture Overview

### Before (Current State)

HDP ships Day-1 scaffolding (peterkc/health-data-platform, `main`, commit `0791618` after cleanup):

- `docker-compose.yml` — Postgres 18 (base `postgres:18-alpine`, no pgvector) + Mongo 7 + adminer
- `packages/hdp-*` and `verticals/home-health/hh-*` — skeletons with pyproject.toml + `__init__.py` + README + smoke tests; no DDL, no migrations
- `apps/home-health-scribe/` — package skeleton (pyproject.toml lists fastapi + uvicorn deps; `src/home_health_scribe/__init__.py` exists; **no `main.py` and no `/health` route yet** — Phase 2 creates both)
- `justfile` — `up`, `down`, `logs`, `dev`, `test`, `verify`; `db-migrate` and `seed` stubs that echo TODO

No runnable schema exists. pgvector is not loaded. Alembic is not wired up.

### After (Proposed State)

Schema + migrations + seed land in place within the existing repo layout. No new subtree is introduced — the prior mini-project's `m3/` parallel tree is not needed here because there is no legacy stack to coexist with.

```
health-data-platform/
|-- docker-compose.yml                       # edit: pgvector/pgvector:pg18
|-- justfile                                 # edit: real db-ddl / db-migration-status / db-reset / db-verify / seed
|-- pyproject.toml                           # edit: add alembic, sqlalchemy, psycopg[binary]
|-- migrations/                              # NEW: Alembic at repo root
|   |-- alembic.ini
|   |-- env.py                               # M_DATABASE_URL-aware; target_metadata=None initially
|   |-- script.py.mako
|   `-- versions/
|       `-- 001_initial_hdp_ddl.py           # Discovers and executes sql/*.sql across source trees
|-- scripts/
|   `-- seed.py                              # Idempotent seed (raw psycopg)
|-- packages/
|   |-- hdp-canonical/
|   |   `-- sql/                             # NEW: canonical DDL
|   |       |-- 00-extensions.sql            # 4 x CREATE EXTENSION
|   |       |-- 01-functions.sql             # touch_updated_at() + audit trigger fn
|   |       |-- 10-reference.sql             # reference tables
|   |       |-- 20-identity.sql              # persons, patients, person_identifiers, patient_org_access
|   |       |-- 30-silver.sql                # FHIR-aligned silver tables
|   |       |-- 40-operational.sql           # provenance, audit_batches, audit_changes, policy_rules, access_*
|   |       `-- 99-triggers.sql              # CREATE TRIGGER (updated_at + audit where scoped)
|   `-- hdp-hitl/
|       `-- sql/
|           `-- 50-hitl.sql                  # chart_items + chart_state_transitions + finalize-gate trigger
|-- verticals/home-health/
|   `-- hh-oasis/
|       `-- sql/
|           `-- 60-oasis.sql                 # OASIS-E2 item catalog
`-- apps/home-health-scribe/src/home_health_scribe/main.py   # edit: progressive /health
```

The Alembic migration discovers SQL files across all three source trees (`packages/hdp-canonical/sql/`, `packages/hdp-hitl/sql/`, `verticals/home-health/hh-oasis/sql/`) and executes them in filename-sorted order — the numeric prefix convention (00-, 01-, 10-, 20-, 30-, 40-, 50-, 60-, 99-) carries dependency order across trees.

## Key Decisions

### Decision 1: Static SQL extraction over runtime markdown parsing

**Context**: `vault/research/table-designs.md` (migrated from mvp-schema) holds the authoritative CREATE TABLE statements. Runtime regex parsing would be R-001.

**Options Considered**:

1. Regex-parse the markdown on every `db-ddl` invocation
2. Use `mistune` or `markdown-it` for structured parse at runtime
3. Statically extract the HDP-initial SQL into per-package `sql/*.sql` files during Phase 2; Alembic executes them

**Decision**: Option 3 — static extraction.

**Rationale**: Parsing theater. The research artifact is committed on the `vault` orphan branch; extraction is a one-time operation producing versionable derivatives in the main-branch tree. Runtime stays simple: `for f in sorted(glob): cur.execute(f.read_text())`. Test coverage becomes file-grep based. If the research artifact changes, re-extract.

### Decision 2: `pgvector/pgvector:pg18` image over base `postgres:18-alpine`

**Context**: pgvector is not bundled in the default Postgres image. Without it, `CREATE EXTENSION vector` fails at schema load (R-003).

**Options Considered**:

1. `postgres:18-alpine` + Dockerfile layer adding pgvector (custom build)
2. `pgvector/pgvector:pg18` (official pgvector image, Postgres 18.x)
3. Custom image layering multiple extensions

**Decision**: Option 2.

**Rationale**: `pgvector/pgvector:pg18` bundles all four required extensions on Postgres 18. Zero custom build; fastest path to green `docker compose up`.

### Decision 3: Audit triggers ship in this spec with NULL batch_id tolerance

**Context**: Audit triggers are mandated by `hdp-audit`. Seed-time writes have no application-provided batch context.

**Options Considered**:

1. Defer all audit triggers to a later spec
2. Ship audit triggers; create a "bootstrap" audit_batches row in seed; SET LOCAL around all seed INSERTs
3. Ship audit triggers; make `audit_changes.batch_id` NULLable; bootstrap writes produce NULL-batched audit rows

**Decision**: Option 3.

**Rationale**: Validates audit plumbing end-to-end during scaffold — catches trigger syntax bugs, `RETURNING OLD/NEW` behavior on PG 18, audit column mismatches early. NULL-batched rows are meaningful forensic signal ("system-bootstrap, not user-driven"). Later specs add `SET LOCAL hdp.audit_batch_id = X` for proper batching without rewriting triggers.

**Audit scope in this spec**: The source artifact attaches audit triggers to 8 specific tables, NOT all silver tables. Of the 8, `access_grants` and `policy_rules` are in HDP-initial scope. This spec scopes audit attachment to `policy_rules` alone — it's seeded so the trigger fires during seed, validating the plumbing. `access_grants` audit is deferred to consent-layer work where grant data arrives. D7 silver tables (`observations`, `conditions`, etc.) rely on `provenance` for ingestion traceability; their audit triggers are not in this spec's scope. HITL tables have their own transition log (FR-012), covered separately.

### Decision 4: Repo-root `migrations/` over per-package migrations

**Context**: SQL lives in three source trees (`packages/hdp-canonical/sql/`, `packages/hdp-hitl/sql/`, `verticals/home-health/hh-oasis/sql/`). Alembic can run one migration chain or multiple.

**Options Considered**:

1. One `migrations/` chain at repo root, discovering SQL across all source trees
2. Per-package migrations (each package owns its own `alembic.ini` + versions)
3. A registry package (`hdp-migrations`) that imports SQL from siblings

**Decision**: Option 1 — single repo-root `migrations/`.

**Rationale**: There is one database. Multiple migration chains against one database require custom coordination (see Alembic's multi-database example) for minor gain. Per-package SQL lives with its package for ownership signal, but the migration chain is one — consistent with how most Postgres apps are managed. If HDP later shards into multiple databases per vertical, revisit.

### Decision 5: Alembic as the migration framework from day one

**Context**: The research artifact uses bare `CREATE TABLE` statements with no `IF NOT EXISTS` clauses. Re-running a naive DDL script raises on a populated DB. SQLAlchemy will enter later (Repository layer for `hdp-canonical`), making Alembic the natural migration tool. The question is whether to plant the flag now or defer.

**Options Considered**:

1. Dynamic `IF NOT EXISTS` rewrite in a custom `ddl.py` helper — ad-hoc idempotency, no version tracking
2. Custom `schema_migrations` tracking table — reinventing what Alembic does
3. Rely on volume resets (`just db-reset`) before re-runs — no idempotency at all
4. **Alembic from day one** — initial migration executes `sql/*.sql` via `op.execute()`; Alembic's `alembic_version` table owns idempotency

**Decision**: Option 4 — Alembic is the migration framework starting in this spec.

**Rationale**: Alembic is best-in-class for SQLAlchemy/Postgres projects and SQLAlchemy models arrive at the Repository layer anyway. Planting Alembic now means:

- **No churn** — no custom idempotency helper that gets ripped out later
- **Proper version tracking** — `alembic_version` table records applied revisions; `alembic upgrade head` is a no-op if already at head
- **Up/down semantics** — real rollback hooks when we need them (scaffold's `downgrade()` raises `NotImplementedError`; later migrations can implement reversal)
- **`alembic revision --autogenerate` lights up later** — when SQLAlchemy models enter, future schema changes are auto-diffed from model state
- **Standard tooling** — reviewers expect Alembic for Python/SQLAlchemy; custom runners raise eyebrows

The initial migration (`migrations/versions/001_initial_hdp_ddl.py`) is a thin shim: for each source tree, it finds `sql/*.sql` and calls `op.execute()` on the sorted set. Static SQL files remain the diff-verifiable extraction; Alembic wraps them in proper migration semantics.

### Decision 6: `/health` endpoint lives in `home-health-scribe`, not a dedicated app

**Context**: The prior mini-project's m3 spec introduced a tiny FastAPI app solely for the `/m3/health` smoke endpoint. HDP has `apps/home-health-scribe/` scaffolded with fastapi + uvicorn deps and an empty `src/home_health_scribe/` package — no `main.py` and no routes yet.

**Options Considered**:

1. Ship a dedicated `apps/schema-probe/` with only `/health`
2. Author `main.py` + `/health` directly inside `home-health-scribe`'s already-scaffolded package
3. Put `/health` under `hdp-api` as platform-level infrastructure

**Decision**: Option 2.

**Rationale**: There is one runnable app in this sprint. Adding a second FastAPI app for one endpoint is ceremony. `home-health-scribe` already declares fastapi + uvicorn deps; authoring `main.py` there is the smallest legitimate addition. The progressive-phase logic (pre-DDL / post-DDL / post-seed) belongs wherever the runnable surface lives. Post-sprint, if `hdp-api` grows into a platform-level admin/probe layer, the `/health` implementation can lift up to there and `home-health-scribe` can re-expose it.

### Decision 7: Convention-#9 finalize-gate enforced at the database layer

**Context**: CMS OASIS-E2 Convention #9 says software may not answer or generate the final OASIS response for the assessing clinician. AI suggests; the clinician reviews; only after review can an item be considered finalized. The gate can be enforced in application code, in the database, or both.

**Options Considered**:

1. Application-layer only (FastAPI route handler rejects finalize requests that include `suggested` items)
2. Database-layer only (trigger raises on `UPDATE chart_items SET state='finalized' WHERE visit_id IN (...)` when any row in scope is `suggested`)
3. Both (defense in depth)

**Decision**: Option 2 for this spec, with the intent that Option 3 emerges as the application layer matures.

**Rationale**: The schema owns the invariant. Application code can be bypassed (admin scripts, direct psql access, future services). The database trigger is the last line of defense and the single place the invariant is physically enforced. Application-layer validation is useful for UX (reject faster, nicer error messages) but is not the authoritative gate. Shipping Option 2 alone in this spec means the invariant is correct from day one; application code wrapping it for UX is an enhancement.

**Trigger sketch** (authored in `packages/hdp-hitl/sql/50-hitl.sql`):

```sql
CREATE FUNCTION hdp_hitl.enforce_finalize_gate() RETURNS trigger AS $$
BEGIN
  -- Convention #9: only items the clinician positively endorsed may be finalized.
  -- Passing prior states: reviewed (clinician read AI suggestion as-is), accepted
  -- (explicitly approved the AI value), edited (modified the AI value). Both
  -- suggested (no clinician touch) and rejected (clinician refused) fail the gate
  -- because neither represents a positive clinical decision to include the item.
  -- Application code is expected to exclude rejected items from the finalize UPDATE
  -- scope (e.g. WHERE visit_id=... AND state <> 'rejected') so the gate only sees
  -- the three passing states. The trigger is the authoritative invariant; the
  -- WHERE-clause filter is a UX layer that avoids surfacing a raise for intended
  -- exclusions.
  IF NEW.state = 'finalized' AND OLD.state NOT IN ('reviewed', 'accepted', 'edited') THEN
    RAISE EXCEPTION 'Convention #9: chart_item % cannot move from state % to finalized; clinician must review, accept, or edit first', NEW.id, OLD.state;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_chart_items_finalize_gate
  BEFORE UPDATE ON chart_items
  FOR EACH ROW EXECUTE FUNCTION hdp_hitl.enforce_finalize_gate();
```

### Decision 8: Callers set `hdp.audit_batch_id` session variable for attribution

**Context**: `audit_changes.batch_id` and `chart_state_transitions.batch_id` are NULLable. Bootstrap writes (seed, ad-hoc admin) produce NULL-batched rows. Application-layer writes want attribution to a batch (request, scribe-extraction run, clinician-review session).

**Options Considered**:

1. Pass `batch_id` as a column value on every INSERT/UPDATE (application-level threading)
2. Use a Postgres session variable (`SET LOCAL hdp.audit_batch_id = <uuid>`) and have the trigger read it via `current_setting('hdp.audit_batch_id', true)`
3. Use a separate `audit_context` table with a `SELECT pg_backend_pid()` key (session-lifetime binding)

**Decision**: Option 2.

**Rationale**: `SET LOCAL` scopes the variable to the current transaction, matching the natural unit of work. The trigger already needs to peek at session state to distinguish bootstrap (NULL) from attributed (non-NULL) writes. `current_setting(..., true)` returns NULL silently when unset, giving the NULL-batched bootstrap pattern for free. Application code wraps write transactions:

```python
# In application code (hdp-audit or calling package):
async with db.transaction():
    await db.execute("SET LOCAL hdp.audit_batch_id = :b", {"b": str(batch_uuid)})
    await do_the_writes(db)
```

The trigger's INSERT into `chart_state_transitions` does:

```sql
INSERT INTO chart_state_transitions (chart_item_id, from_state, to_state, actor, reason, batch_id, created_at)
VALUES (NEW.id, OLD.state, NEW.state, ..., NULLIF(current_setting('hdp.audit_batch_id', true), '')::uuid, now());
```

`NULLIF(..., '')` covers the unset case (returns empty string); bootstrap rows store NULL cleanly.

## Worker Execution Notes

**Worktree topology (load-bearing for Phase 1 writes)**: HDP's repo layout uses git orphan-branch worktrees. The main branch is checked out at ``; the `vault` orphan branch is mounted at `vault/` and is **gitignored** on main. spx workers create a feature worktree at `.worktrees/<phase>/` (per ADR-4012). That feature worktree contains a checkout of the main branch — it does **not** include the `vault/` mount.

Phase 1 tasks `migrate-mvp-schema`, `pick-table-subset`, and `choose-db-test-fixture` write to `vault/research/*.md`. Those writes must use the absolute path `vault/research/<file>.md` so they land on the vault orphan branch via the main repo's worktree mount. Writing the same relative path from inside `.worktrees/<phase>/` creates a stranded file under the feature worktree with no link to the vault branch — the file would be invisible to subsequent verification (`test -f vault/research/...`) and lost when the worktree is removed.

Commits to vault content land on the `vault` orphan branch via `git -C vault commit`. The feature worktree's branch stays untouched — Phase 1 lands two independent commit chains (one on the feature branch for `swap-postgres-image` + the hh-hitl rename + pyproject edits; one on the `vault` branch for the research migrations).

**Test commands using absolute paths**: Phase 1's `validation.command` already uses `vault/research/...` absolute paths for the precursor file checks — the same convention applies to write-side file operations the worker performs.

## Component Design

### `packages/hdp-canonical/sql/` — Canonical DDL (Phase 2 output)

Each file contains exactly one logical group, extracted verbatim from `vault/research/table-designs.md`:

| File                    | Contents                                                                                              |
| ----------------------- | ----------------------------------------------------------------------------------------------------- |
| `00-extensions.sql`     | `CREATE EXTENSION uuid-ossp`, `vector`, `pg_trgm`, `btree_gin`                                        |
| `01-functions.sql`      | `touch_updated_at()` + audit trigger function                                                         |
| `10-reference.sql`      | `ref_hom_nodes`, `ref_source_adapters`, `ref_organizations`, `ref_analyte_conversions`, `ref_record_type_schemas`, `ref_drug_classes`, `loinc_crosswalk` |
| `20-identity.sql`       | `persons`, `patients`, `person_identifiers`, `patient_org_access`                                     |
| `30-silver.sql`         | `observations`, `conditions`, `medications`, `allergies`, `immunizations`, `family_history`, `procedures`, `orders` |
| `40-operational.sql`    | `provenance`, `raw_payloads`, `documents`, `audit_batches`, `audit_changes`, `policy_rules`, `access_grants`, `access_log`, `source_connections` |
| `99-triggers.sql`       | `CREATE TRIGGER trg_*_updated_at` per applicable table + audit trigger on `policy_rules`             |

### `packages/hdp-hitl/sql/50-hitl.sql` — HITL state machine (NEW — not in mvp-schema)

Tables and triggers authored fresh for this spec. Authoritative content:

- `chart_items` — id, visit_id (FK to hh-oasis.visits), oasis_item_id (FK to ref), source (referral|visit|dictation|clinician), confidence, citation, state (CHECK: suggested|reviewed|accepted|edited|rejected|finalized), extracted_value, reviewed_value, reviewed_by, reviewed_at, created_at, updated_at
- `chart_state_transitions` — id, chart_item_id (FK to chart_items), from_state, to_state, actor, reason, batch_id (nullable), created_at
- Trigger: `trg_chart_items_transition_log` — AFTER UPDATE, writes to `chart_state_transitions` when `NEW.state != OLD.state`
- Trigger: `trg_chart_items_finalize_gate` — BEFORE UPDATE, raises per Decision 7

### `verticals/home-health/hh-oasis/sql/60-oasis.sql` — OASIS-E2 item catalog (NEW — home-health-specific)

Tables authored fresh for this spec:

- `oasis_items` — canonical OASIS-E2 item catalog (M1800, M2020, etc.), name, question_text, response_type, options
- `episodes` — id, patient_id, start_date, end_date (60-day payment period per PDGM), hipps_code
- `visits` — id, episode_id, visit_type (SOC|ROC|Recert|DC|Routine), visit_date, clinician_id

### `migrations/alembic.ini` — Alembic configuration

See [`stubs/alembic.ini`](stubs/alembic.ini) for the full sketch. Key elements:

- `script_location = migrations` (relative to repo root)
- `sqlalchemy.url` default points at `localhost:5437/hdp` for dev; `env.py` overrides via `DATABASE_URL` env var when set
- Standard Alembic logger configuration (root + sqlalchemy + alembic at WARN/WARN/INFO)

### `migrations/env.py` — Alembic runtime

See [`stubs/env.py`](stubs/env.py) for the full sketch. Key elements:

- Standard Alembic `offline`/`online` runner pair
- `DATABASE_URL` env var overrides the ini's `sqlalchemy.url` at runtime
- `target_metadata = None` initially (no SQLAlchemy models yet); flips to `Base.metadata` when the Repository layer introduces models
- **Embedded warning comment** about `target_metadata=None` + `alembic revision --autogenerate` producing silent empty migrations — prevents a subtle footgun when SQLAlchemy models arrive

The DATABASE_URL override is the pattern operators touch most often; the snippet below shows the exact shape the stub implements:

```python
# migrations/env.py (excerpt)
config = context.config

# Override sqlalchemy.url from env var if present.
if db_url := os.environ.get("DATABASE_URL"):
    config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata stays None until SQLAlchemy models arrive (Repository-layer spec).
# WARNING: autogenerate produces a silent EMPTY migration when this is None.
target_metadata = None
```

### `migrations/versions/001_initial_hdp_ddl.py` — Initial migration

See [`stubs/001_initial_hdp_ddl.py`](stubs/001_initial_hdp_ddl.py) for the full sketch. Key elements:

- Revision id `001_initial_hdp_ddl`; `down_revision = None` (baseline)
- `upgrade()` walks the three source trees, collects `sql/*.sql`, sorts the full set by basename, and calls `op.execute()` on each — the SQL files are the single source of table text
- `downgrade()` raises `NotImplementedError` — clean-slate reset is via `just db-reset` (volume drop), not Alembic
- Modern type annotations using `collections.abc.Sequence`

The discovery-and-execute loop is the load-bearing part of the migration — it's the single place that ties SQL authorship (in three package trees) to the one Alembic chain. Snippet:

```python
# migrations/versions/001_initial_hdp_ddl.py (excerpt)
REPO_ROOT = Path(__file__).parent.parent.parent.parent
SQL_DIRS = [
    REPO_ROOT / "packages" / "hdp-canonical" / "sql",
    REPO_ROOT / "packages" / "hdp-hitl" / "sql",
    REPO_ROOT / "verticals" / "home-health" / "hh-oasis" / "sql",
]

def upgrade() -> None:
    all_sql_files: list[Path] = []
    for sql_dir in SQL_DIRS:
        if sql_dir.exists():
            all_sql_files.extend(sql_dir.glob("*.sql"))
    # Sort by basename so NN- prefix ordering spans all three trees.
    for sql_file in sorted(all_sql_files, key=lambda p: p.name):
        op.execute(sql_file.read_text())
```

**Discovery safety**: the three source directories are hardcoded in the migration. If a package is renamed or moved (e.g., `hh-oasis` → `home-health-oasis`), the glob returns empty and the migration silently creates zero tables. `packages/hdp-canonical/tests/test_sql_discovery.py` (added in Phase 2) asserts that each expected directory exists, contains at least one `.sql` file, and that filenames follow the `NN-name.sql` prefix convention. This test runs in pytest pre-commit and CI; a rename breaks the test before it breaks the migration.

### Test fixture strategy

Per Phase 0 Decision P-004, the default is a **shared docker stack** — integration tests connect to the compose-defined `postgres` service on `localhost:5437` with credentials `hdp/hdp/hdp`. Fixtures use `psycopg` directly against that DB, wrapped in transactions that roll back at teardown. This matches the development workflow (one docker stack, used for both interactive and test) and avoids the complexity of per-test container lifecycle (Testcontainers) or in-process stubs (pytest-postgresql) that may drift from production behavior.

If the implementation session discovers concurrency issues or needs faster iteration, the decision can flip to Testcontainers without a spec rewrite — fixtures are the only affected surface. Record the flip in `vault/research/test-fixture-decision.md`.

### `scripts/seed.py` — Idempotent seed (Phase 3)

See [`stubs/seed.py`](stubs/seed.py) for the full sketch. Key elements:

- `seed_all(conn_str)` orchestrator calls 9 helpers (8 reference tables + 1 test patient) inside one transaction
- Each `_seed_*` helper issues `ON CONFLICT DO NOTHING` INSERTs and returns `cur.rowcount`
- Helper bodies stubbed with `raise NotImplementedError` — filled during Phase 3 execution against the canonical table shapes in `sql/` files
- Post-seed invariants (AC-007, AC-008): `ref_hom_nodes >= 10`, `ref_source_adapters >= 4`, `policy_rules >= 1`, `loinc_crosswalk >= 5`, 1 patient row FK-consistent across `persons` + `patients` + `person_identifiers`

The idempotency contract hinges on `ON CONFLICT DO NOTHING`. The snippet below shows the representative pattern for `_seed_hom_nodes` that every other `_seed_*` helper mirrors:

```python
# scripts/seed.py (excerpt — representative helper)
def _seed_hom_nodes(cur: psycopg.Cursor) -> int:
    """Body-systems hierarchy, top-down. >= 10 rows."""
    rows = [
        ("cardiovascular", None, "Cardiovascular system"),
        ("metabolic",      None, "Metabolic system"),
        # ...8+ more top-level + child nodes
    ]
    cur.executemany(
        """
        INSERT INTO ref_hom_nodes (code, parent_code, label)
        VALUES (%s, %s, %s)
        ON CONFLICT (code) DO NOTHING
        """,
        rows,
    )
    return cur.rowcount  # zero on second run — AC-009 idempotency
```

Every other `_seed_*` helper follows the same shape: enumerate canonical rows, `executemany(... ON CONFLICT DO NOTHING)`, return `cur.rowcount`. The orchestrator aggregates per-table counts into a `dict[str, int]` for operator-visible output.

### `apps/home-health-scribe/src/home_health_scribe/main.py` — Progressive `/health` (NEW file)

Creates the FastAPI app and the `/health` endpoint with the progressive-phase fields. The package directory currently contains only `__init__.py` and `py.typed`; this file is authored fresh in Phase 2. See [`stubs/main.py`](stubs/main.py) for the full sketch. Key elements:

- `/health` always queries `SELECT version(), uuidv7() IS NOT NULL` (core liveness + PG 18 primitive smoke test)
- `/health` progressively queries: `information_schema.tables` count → `alembic_version.version_num` → `ref_hom_nodes` COUNT
- Missing-table queries catch `psycopg.errors.UndefinedTable`, roll back the cursor, return `null` for the affected field — endpoint stays 200 across all phases (pre-DDL, post-DDL pre-seed, post-seed)
- Hard failure only when the DB is unreachable → HTTP 503
- Response fields: `status`, `postgres`, `uuidv7`, `tables_count`, `alembic_version`, `hom_nodes_seeded`

### `docker-compose.yml` — Image swap

The only change is the `postgres` service image:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg18   # was: postgres:18-alpine
    # credentials, port (5437:5432), volume (postgres-data) unchanged
```

The `pgvector/pgvector:pg18` image ships Postgres 18.x with pgvector, uuid-ossp, pg_trgm, btree_gin preinstalled.

### `justfile` recipe additions

See [`stubs/justfile-additions`](stubs/justfile-additions) for the full recipe block. Recipes replaced/added:

- `db-ddl` — `alembic upgrade head` (applies the initial migration; idempotent)
- `db-migration-status` — `alembic current` + `alembic history`
- `db-reset` — `just down` → `docker volume rm postgres-data` → `just up`
- `seed` — run `scripts/seed.py` against the target DB (replaces current echo stub)
- `db-verify` — curl `/health`, `\dt` dump, `alembic current` summary

Top-level `up`, `down`, `logs`, `dev`, `test`, `verify` recipes remain as-is.

## Error Handling

| Error Condition                                                       | Handling Strategy                                                                                                         |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `CREATE EXTENSION vector` fails at DDL load                           | Fail fast — wrong image. Error propagates through Alembic → nonzero exit. Operator sees logs and switches image.          |
| `SELECT uuidv7()` returns error in `/health`                          | `/health` returns HTTP 500 with detail; signals wrong Postgres version. Pin image per NFR-001 prevents this.              |
| FK resolution fails mid-migration                                     | Alembic migration transaction rolls back; exit nonzero. Operator fixes sort order or file contents and re-runs.           |
| Seed detects existing rows                                            | `ON CONFLICT DO NOTHING` → zero new rows inserted; exit 0. Idempotency validated by AC-009.                              |
| Audit trigger fires during seed, no batch context                     | Trigger writes `audit_changes` row with `batch_id = NULL`. Tolerated by schema (Decision 3). AC-006 verifies.            |
| HOM tree seed: child INSERT references missing parent                 | Seed inserts top-down (body-systems first). If parent missing → FK violation → seed exits 1. Bug indicates source-order error. |
| Docker volume `postgres-data` has stale data from prior run           | Documented reset: `just db-reset` (drops volume then brings stack back up).                                               |
| `/health` unreachable (container slow to start)                       | Healthcheck retries 10x at 5s intervals. Operator waits >= 30s before declaring AC-001 failure.                          |
| `/health` query to `ref_hom_nodes` or `alembic_version` hits `UndefinedTable` pre-DDL | Endpoint catches `psycopg.errors.UndefinedTable`, rolls back cursor, returns `null` for the affected field. Endpoint stays responsive (200) throughout all lifecycle phases. |
| Convention-#9 finalize-gate raises                                    | Trigger raises SQLSTATE `P0001` with a descriptive message naming the offending `chart_items.id`. Caller catches and surfaces a user-facing message via the review UI (out of this spec's scope). |

## Validation Commands per Phase

**Phase 1 (tracer — pre-DDL state)**:

```bash
just up
sleep 20
# Liveness: service reachable (home-health-scribe with extended /health)
curl -sf localhost:8000/health | jq -e '.status=="ok"'
# Primitive: uuidv7() available (proves PG >= 18)
curl -sf localhost:8000/health | jq -e '.uuidv7==true'
# Phase check: DDL not yet applied
curl -sf localhost:8000/health | jq -e '.tables_count==0 and .alembic_version==null and .hom_nodes_seeded==null'
docker compose ps | grep -cE "(healthy|Up)"  # expect 3 (postgres, mongo, adminer)
```

**Phase 2 (mvs — post-DDL, pre-seed state)**:

```bash
just db-ddl                                                                          # alembic upgrade head
psql postgresql://hdp:hdp@localhost:5437/hdp -c "\dt" | tail -n +4 | wc -l          # expect N (derived)
psql postgresql://hdp:hdp@localhost:5437/hdp -c "SELECT COUNT(*) FROM pg_trigger WHERE tgname LIKE 'trg_%_updated_at'"
psql postgresql://hdp:hdp@localhost:5437/hdp -c "SELECT version_num FROM alembic_version"  # expect 001_initial_hdp_ddl
# HTTP health check reflects post-DDL state (tables exist, seed has not run)
curl -sf localhost:8000/health | jq -e '.tables_count>=N and .alembic_version=="001_initial_hdp_ddl" and .hom_nodes_seeded==0'
grep -rc "CREATE TABLE" migrations/ scripts/ 2>/dev/null | grep -v ":0$" && exit 1 || true  # expect 0 (NFR-002)
just db-ddl                                                                          # second run: alembic no-op
```

**Phase 3 (verify — post-seed state)**:

```bash
just seed
psql ... -c "SELECT COUNT(*) FROM ref_hom_nodes"           # expect >= 10
psql ... -c "SELECT COUNT(*) FROM ref_source_adapters"     # expect >= 4
psql ... -c "SELECT COUNT(*) FROM audit_changes WHERE batch_id IS NULL AND table_name = 'policy_rules'"  # expect >= 1
psql ... -c "SELECT p.* FROM patients p JOIN persons pe ON p.person_id = pe.id LIMIT 1"  # expect 1 row
# HTTP health check reflects post-seed state
curl -sf localhost:8000/health | jq -e '.hom_nodes_seeded>=10 and .alembic_version=="001_initial_hdp_ddl"'
just seed  # idempotency: expect 0 new rows

# HITL state machine checks
psql ... -c "\d+ chart_items" | grep -q "state text NOT NULL"       # CHECK constraint
# Convention-#9 finalize-gate negative test (AC-019 — manual during verify; full test in pytest)
```
