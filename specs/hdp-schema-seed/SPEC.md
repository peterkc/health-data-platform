---
title: 'hdp-schema-seed'
spec_type: 'implementation'
schema: spx/v3
beads:
  epic:
---

# hdp-schema-seed

> Seed the runnable HDP foundation: Postgres 18 with pgvector + initial DDL (canonical + home-health OASIS + HITL tables) applied via Alembic + idempotent reference seed + one test patient. Primary source of truth for schema lands in `packages/hdp-canonical/sql/`. Exact table count is resolved in Phase 0 and recorded in `vault/research/hdp-initial-tables.md`.

## Success Criteria

| ID     | Criterion                                                                                       | Validation                                                                                                     |
| ------ | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| SC-001 | `just up` boots Postgres 18 (with pgvector) + Mongo 7 + adminer; all services healthy          | `docker compose ps` shows all Up within 30s                                                                    |
| SC-002 | `GET /health` on the composed app returns 200 with enriched JSON — `status`, `postgres`, `uuidv7`, `tables_count`, `alembic_version`, `hom_nodes_seeded` (progressive phase indicator) | `curl -sf localhost:8000/health \| jq .` returns all fields; values reflect current phase (pre-DDL / post-DDL / post-seed) |
| SC-003 | All four required extensions load cleanly                                                       | `psql -c "SELECT extname FROM pg_extension"` includes `uuid-ossp`, `vector`, `pg_trgm`, `btree_gin`            |
| SC-004 | HDP-initial tables created in FK dependency order; no resolution errors                         | `psql -c "\dt"` row count matches `vault/research/hdp-initial-tables.md` (Phase 0 output); `just db-ddl` exits 0 |
| SC-005 | `touch_updated_at()` function + per-table `updated_at` triggers attached                        | `SELECT COUNT(*) FROM pg_trigger WHERE tgname LIKE 'trg_%_updated_at'` matches DDL trigger count                |
| SC-006 | Audit triggers attached; seed-time writes produce audit rows with NULL batch_id                 | `SELECT COUNT(*) FROM audit_changes WHERE batch_id IS NULL` > 0 after `just seed`                              |
| SC-007 | Reference tables seeded at minimum cardinalities                                                | `ref_hom_nodes` >= 10, `ref_source_adapters` >= 4, `policy_rules` >= 1, `loinc_crosswalk` >= 5, `ref_organizations` >= 1 |
| SC-008 | One test patient inserted with consistent FKs                                                   | `SELECT * FROM patients p JOIN persons pe ON p.person_id = pe.id LIMIT 1` returns one row                      |
| SC-009 | `just seed` is idempotent — second run produces zero new rows, zero errors                      | Run twice; diff row counts must match                                                                          |
| SC-010 | `just db-ddl` is idempotent via Alembic — second run is a no-op                                 | Run `just db-ddl` twice; `alembic_version.version_num` stable at `001_initial_hdp_ddl`; both runs exit 0       |
| SC-011 | `alembic_version` table records the applied baseline revision                                   | `SELECT version_num FROM alembic_version` returns `001_initial_hdp_ddl`                                        |
| SC-012 | HITL state machine tables (`chart_items`, `chart_state_transitions`) exist and enforce Convention-#9 transitions | `\d chart_items` shows `state` column with CHECK constraint; finalize-gate trigger raises on any `suggested` row |

## Scope

### Precursors (Phase 0 of tasks.yaml)

Four dependencies must resolve before Phase 1 runs:

1. **mvp-schema research migration** — port 19 near-raw + 5 sanitized files from prior internal schema research to `vault/research/`; rename legacy `audit_batch_id` namespace to `hdp`; strip non-technical framing from the 5 sanitization targets
2. **`hh-hitl` → `hdp-hitl` promotion** — rename the package directory, update `pyproject.toml` `tool.uv.sources`, update imports across the workspace. Tracked as the first mechanical Fri task in the sprint plan
3. **HDP-initial table subset decision** — author `vault/research/hdp-initial-tables.md` listing exact table names + source + FK dependency order. Recommended default: ~25 tables (canonical core + identity + operational + HITL + OASIS). Sets the concrete number for SC-004 / AC-004.
4. **DB test-fixture choice** — record decision in `vault/research/test-fixture-decision.md`. Recommended default: shared docker stack matching the compose-defined postgres service (simplest, fewest moving parts for a sprint demo).

### Implementation target

Schema lives in `packages/hdp-canonical/sql/` (canonical tables) + `packages/hdp-hitl/sql/` (HITL state machine tables) + `verticals/home-health/hh-oasis/sql/` (OASIS-E2 item tables). Alembic migrations compose all three via `op.execute()` on sorted SQL files.

**Source of truth**: `vault/research/table-designs.md` (migrated from mvp-schema) — CREATE TABLE statements for canonical, reference, operational, and audit tables. HDP-specific additions (HITL + OASIS) authored fresh in this spec.

**New files**:

- `packages/hdp-canonical/sql/00-extensions.sql` — `CREATE EXTENSION` × 4
- `packages/hdp-canonical/sql/01-functions.sql` — `touch_updated_at()` + audit trigger function
- `packages/hdp-canonical/sql/10-reference.sql` — reference tables (no FK to user data)
- `packages/hdp-canonical/sql/20-identity.sql` — `persons`, `patients`, `person_identifiers`, `patient_org_access`
- `packages/hdp-canonical/sql/30-silver.sql` — D7 FHIR-aligned silver tables + procedures + orders
- `packages/hdp-canonical/sql/40-operational.sql` — `provenance`, `raw_payloads`, `documents`, `audit_batches`, `audit_changes`, `policy_rules`, `access_grants`, `access_log`, `source_connections`
- `packages/hdp-hitl/sql/50-hitl.sql` — `chart_items`, `chart_state_transitions`, finalize-gate trigger (Convention #9)
- `verticals/home-health/hh-oasis/sql/60-oasis.sql` — OASIS-E2 item catalog tables
- `packages/hdp-canonical/sql/99-triggers.sql` — `CREATE TRIGGER` per table (updated_at + audit where scoped)
- `migrations/alembic.ini` — Alembic config (DB URL via env override)
- `migrations/env.py` — Alembic env (offline/online; `target_metadata = None` until SQLAlchemy models arrive)
- `migrations/script.py.mako` — Alembic revision template
- `migrations/versions/001_initial_hdp_ddl.py` — initial migration: `op.execute()` each discovered `sql/*.sql` in sorted order across all three source trees
- `scripts/seed.py` — idempotent reference + test-patient seed (raw psycopg)

**Modified files**:

- `docker-compose.yml` — swap `postgres:18-alpine` → `pgvector/pgvector:pg18` (all four extensions bundled; credentials/port/volume unchanged)
- `justfile` — real `db-ddl`, `db-migration-status`, `db-reset`, `db-verify` recipes; extend existing `seed` stub
- `pyproject.toml` — add `alembic>=1.13` and `sqlalchemy>=2.0` to root dev group (or to `hdp-canonical` package deps); add `psycopg[binary]` where not already listed
- `apps/home-health-scribe/src/home_health_scribe/main.py` — `/health` endpoint gains progressive-phase fields (`tables_count`, `alembic_version`, `hom_nodes_seeded`, `uuidv7`)

**Out of scope** (tracked as follow-up issues):

- Real LLM extraction in `hh-scribe` (this spec lands schema only; Stage-2 extraction is a separate sprint item)
- `Repository.read()` / `.write()` layer (SQLAlchemy models arrive once `hdp-canonical` Python models land)
- OpenFGA PDP wiring + `access_log` writes
- API endpoints beyond `/health` (handled by `home-health-scribe` spec)
- Integration test suite end-to-end (composition spec covers this)
- **pgvector embedding tables**: the `vector` extension loads here, but no `embeddings` table is authored. Embedding-bearing tables land with the retrieval/RAG spec that introduces the LLM+RAG flow, not this one.
- **MongoDB schema validators**: docker-compose already ships Mongo 7 for transcripts + LLM artifacts (polyglot persistence ADR). Collections are created lazily by `hh-scribe` at runtime. A dedicated Mongo schema-validator spec lands separately once the collection shapes are stable.
- 42 CFR Part 2 strict-fail-closed enforcement (table ships; logic later)
- S3 document reference-counting cascade

## Risks

| ID    | Risk                                                                                             | Likelihood | Impact | Mitigation                                                                                                           |
| ----- | ------------------------------------------------------------------------------------------------ | ---------- | ------ | -------------------------------------------------------------------------------------------------------------------- |
| R-001 | Runtime regex-parses a large markdown DDL artifact                                               | Medium     | High   | Static extraction to `sql/*.sql` during Phase 2 (Decision 1). Alembic initial migration wraps those files via `op.execute()`; Alembic owns version tracking and re-run safety (Decision 5). |
| R-002 | PG 18 primitives (`uuidv7()`, temporal PK, `RETURNING OLD/NEW`) silently unavailable on PG < 18.3 | Medium     | High   | Pin `pgvector/pgvector:pg18` image; `/health` asserts `SELECT uuidv7()` as smoke gate                                |
| R-003 | Default `postgres:18-alpine` image lacks pgvector extension                                      | High       | High   | Swap to `pgvector/pgvector:pg18` (bundles pgvector + uuid-ossp + pg_trgm + btree_gin)                                |
| R-004 | FK dependency ordering drift between source (mvp-schema) and extracted SQL files                 | Low        | Medium | Cross-ref extracted files against `vault/research/table-designs.md` dependency block; Phase 2 verify counts tables   |
| R-005 | Audit trigger scope ambiguity (batch context missing during seed writes)                         | Resolved   | —      | `audit_changes.batch_id` NULLable; seed writes produce NULL-batched audit rows ("system-bootstrap"); see Decision 3  |
| R-006 | HOM tree seed is hierarchical (self-FK parent→child ordering)                                    | Medium     | Medium | Insert top-down (body-systems first, then subsystems); source ordering from `vault/research/table-designs.md`        |
| R-007 | Convention-#9 finalize-gate trigger mis-scoped — blocks legitimate accepted/edited items         | Medium     | High   | Trigger checks `state = 'suggested'` only (accepted/edited/rejected are all passing states); unit test covers all 4 terminal states + one transitional (reviewed). See Decision 7. |
| R-008 | Alembic `autogenerate` at the post-spec SQLAlchemy step produces spurious diffs                 | Medium     | High   | When SQLAlchemy models arrive, author them to match `sql/` exactly; first `alembic revision --autogenerate` run is expected to produce a no-op diff confirming model↔DB parity. |
| R-009 | Concurrent `alembic upgrade head` invocations from parallel dev sessions                         | Low        | Low    | Alembic uses Postgres advisory locks (`pg_advisory_lock`) around migration runs — safe by design. Documented here for transparency; no custom locking needed. |
| R-010 | Hardcoded localhost connection strings in `alembic.ini` block cloud deployment                   | Medium     | Medium | `env.py` honors `DATABASE_URL` env override (preferred path); `alembic.ini` default URL is dev-convenience only; cloud deploy injects DB URL via env. |
| R-011 | SQL file lexicographic sort drifts from FK dependency order if new files added out-of-band       | Low        | Medium | Filename prefix convention (00-, 01-, 10-, 20-, 30-, 40-, 50-, 60-, 99-) documented in design.md §Component Design; `db-verify` counts tables to catch silent drops; contributors add new files only during careful extraction, not ad-hoc |
