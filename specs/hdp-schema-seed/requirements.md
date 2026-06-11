# Requirements: hdp-schema-seed

## Precursor Requirements

Four dependencies resolve at the start of Phase 1 (`tracer-scaffold`) before any implementation step downstream can proceed:

FR-101: WHEN the `migrate-mvp-schema` precursor task completes
THE SYSTEM SHALL expose `vault/research/table-designs.md` with content derived from prior internal schema research and sanitized per the 5-file checklist (legacy namespace renamed to hdp, non-technical framing removed).

FR-102: WHEN the `promote-hh-hitl-to-platform` precursor task completes
THE SYSTEM SHALL expose `packages/hdp-hitl/` as a real workspace package (own `pyproject.toml`, `sql/` subdir) registered in `[tool.uv.sources]`; `uv sync` and `uv run pytest -q --co` both succeed.

FR-103: WHEN the `pick-table-subset` precursor task completes
THE SYSTEM SHALL expose `vault/research/hdp-initial-tables.md` with a concrete list of table names, source file, and FK dependency order. This file authorizes the specific table count asserted by AC-004.

FR-104: WHEN the `choose-db-test-fixture` precursor task completes
THE SYSTEM SHALL expose `vault/research/test-fixture-decision.md` recording the chosen approach for DB-integration tests (shared docker stack / pytest-postgresql / Testcontainers) with a one-line rationale.

## Functional Requirements

FR-001: WHEN `just up` is invoked
THE SYSTEM SHALL start the Postgres 18 (with pgvector) + Mongo 7 + adminer containers, all reachable on localhost within 30 seconds, with Docker healthchecks reporting Up.

FR-002: WHEN the Postgres container initializes
THE SYSTEM SHALL create the extensions `uuid-ossp`, `vector`, `pg_trgm`, and `btree_gin`.

FR-003: WHEN `GET /health` is received by the composed `home-health-scribe` application
THE SYSTEM SHALL return HTTP 200 with JSON body:

```
{
  "status": "ok",
  "postgres": "<version>",
  "uuidv7": true,
  "tables_count": <int>,            // count of public base tables; 0 before DDL
  "alembic_version": "<rev>" | null,// current alembic_version row; null before DDL
  "hom_nodes_seeded": <int> | null  // COUNT(*) from ref_hom_nodes; null if table absent, 0 pre-seed, >=10 post-seed
}
```

The `uuidv7` field is confirmed by executing `SELECT uuidv7() IS NOT NULL`. Each state-dependent field (`alembic_version`, `hom_nodes_seeded`) is obtained via its own query wrapped in a try/except for `psycopg.errors.UndefinedTable` — when the table is absent, the field returns `null` and the connection is rolled back to preserve subsequent queries. This progressive response acts as a phase indicator (pre-DDL, post-DDL pre-seed, post-seed).

FR-004: WHEN `just db-ddl` is invoked
THE SYSTEM SHALL run `alembic upgrade head` which applies the initial migration (`001_initial_hdp_ddl`), executing the CREATE TABLE statements from the discovered `sql/*.sql` files across `packages/hdp-canonical/sql/`, `packages/hdp-hitl/sql/`, and `verticals/home-health/hh-oasis/sql/` in dependency order.

FR-005: WHEN a CREATE TABLE statement includes `updated_at TIMESTAMPTZ`
THE SYSTEM SHALL define `touch_updated_at()` once (in `packages/hdp-canonical/sql/01-functions.sql`) and attach `trg_<table>_updated_at BEFORE UPDATE` triggers to each such table (in `packages/hdp-canonical/sql/99-triggers.sql`).

FR-006: WHEN an INSERT, UPDATE, or DELETE fires on `policy_rules` (the audit-attached reference table seeded at bootstrap)
THE SYSTEM SHALL write exactly one row to `audit_changes` capturing the operation type, source table, primary key, and `batch_id` — which MAY be NULL when `current_setting('hdp.audit_batch_id', true)` is unset (indicating a system-bootstrap write).

**Note on audit scope**: The source artifact lists 8 tables that receive full change-history audit triggers (`access_grants`, `policy_rules`, `clinical_impressions`, `care_plans`, `advance_directives`, `consent_documents`, `research_studies`, `study_subjects`). Of these, `access_grants` and `policy_rules` are in HDP-initial scope. This spec attaches the audit trigger only to `policy_rules` (seeded in Phase 3, so the trigger fires during seed and produces a NULL-batched audit row). `access_grants` audit attachment is deferred to consent-layer work where grant data arrives. D7 silver tables (`observations`, `conditions`, `medications`, …) do NOT receive audit triggers in this spec; they rely on `provenance` for ingestion-level traceability. HITL tables (`chart_items`, `chart_state_transitions`) have dedicated audit via the state-machine transition log (see FR-012).

FR-007: WHEN `just seed` is invoked
THE SYSTEM SHALL insert rows into `ref_hom_nodes`, `ref_source_adapters`, `ref_organizations`, `ref_analyte_conversions`, `ref_record_type_schemas`, `ref_drug_classes`, `loinc_crosswalk`, and `policy_rules` using `ON CONFLICT DO NOTHING` on each INSERT.

FR-008: WHEN `just seed` is invoked
THE SYSTEM SHALL insert exactly one test patient via rows in `persons`, `patients`, and `person_identifiers` with FK-consistent values (patients.person_id ↔ persons.id; person_identifiers.person_id ↔ persons.id).

FR-009: WHEN `just seed` is invoked a second time against an already-seeded database
THE SYSTEM SHALL produce zero new rows in all target tables and exit with code 0.

FR-010: WHEN `just db-verify` is invoked
THE SYSTEM SHALL call `/health` and `\dt` to print a human-readable smoke summary (HTTP status, extension list, table count, alembic revision).

FR-011: WHEN `just db-ddl` is invoked a second time against a database already at the head revision
THE SYSTEM SHALL recognize the current `alembic_version` as head and exit with code 0 having applied zero new migrations (Alembic-native idempotency — see Decision 5).

FR-012: WHEN an UPDATE fires on `chart_items` with `NEW.state <> OLD.state`
THE SYSTEM SHALL write exactly one row to `chart_state_transitions` capturing the item id, from_state (OLD.state), to_state (NEW.state), actor, reason, batch_id (NULLable), and timestamp. Initial INSERTs do not emit transition rows — the row's initial state is recorded by `chart_items.created_at` and the first UPDATE transition captures the first clinician touch.

FR-013: WHEN a caller attempts `UPDATE chart_items SET state = 'finalized' WHERE ...`
THE SYSTEM SHALL raise if any target row has `state = 'suggested'` (the Convention-#9 finalize-gate: software may not mark an AI suggestion as final without clinician review).

## Non-Functional Requirements

NFR-001: THE SYSTEM SHALL pin the Postgres image to `pgvector/pgvector:pg18` (or a documented equivalent that bundles all four required extensions AND runs Postgres >= 18.3).

NFR-002: THE SYSTEM SHALL keep all CREATE TABLE / TRIGGER / FUNCTION text in `sql/*.sql` files under `packages/hdp-canonical/sql/`, `packages/hdp-hitl/sql/`, and `verticals/home-health/hh-oasis/sql/`; the Alembic migration and seed script SHALL NOT contain CREATE TABLE text.

NFR-003: THE SYSTEM SHALL namespace any PostgreSQL session-variable-based audit batching under the `hdp.*` prefix (e.g. `hdp.audit_batch_id`) to avoid collision with application-layer settings.

## Scenarios

Narrative journeys that exercise the design end-to-end. Each maps to one or more ACs below.

**S1 — Reviewer gold path**
A reviewer clones the repo fresh, runs `just up && just db-ddl && just seed && just db-verify`. All services come up healthy; the initial migration (`001_initial_hdp_ddl`) applies cleanly; seed populates reference tables + test patient; verify prints HTTP 200 + extension list + `\dt` + `alembic current`. Target: <120s for first-run cold-path (docker volume empty, pgvector init runs); <60s for warm-run (volume pre-populated). The Phase 2 verify-mvs task measures actual timings and updates these numbers if observed runs diverge.

**S2 — Developer iteration**
A developer re-runs `just db-ddl` after a code change that does not add migrations. Alembic reports "no new migrations to apply" and exits 0. `just seed` second run produces zero deltas (ON CONFLICT DO NOTHING). No state mutation; no error.

**S3 — Clean reset**
A developer runs `just db-reset`. The `postgres-data` Docker volume is removed; containers restart. `just db-ddl && just seed` rebuilds from scratch in <30s (no image pull).

**S4 — Wrong Postgres image (failure mode)**
A developer pins `image: postgres:18-alpine` (without pgvector) in `docker-compose.yml`. `just up` boots the container successfully. `just db-ddl` fails when the initial migration hits `CREATE EXTENSION vector` — Alembic propagates the error, the migration transaction rolls back, exit code is nonzero. The error message surfaces "extension" and "vector" in stderr so the operator can diagnose and switch the image.

**S5 — Downstream handoff (forward-compat with ingest + HITL review)**
After this spec ships, `hh-scribe` writes an observation row from a transcript extraction. The audit trigger on `policy_rules` continues to fire during seeds with `batch_id = NULL`. When `hdp-agent` writes chart items under `SET LOCAL hdp.audit_batch_id = <uuid>`, chart-state transitions log with non-null batch_ids. Both NULL (bootstrap) and non-null (runtime) rows coexist in `audit_changes` and `chart_state_transitions`, providing a forensic timeline. This spec's schema must support both modes without migration.

**S6 — Convention-#9 finalize-gate**
A caller attempts to move chart_items from their current state to `finalized`. The HITL finalize-gate trigger (Decision 7) raises if any row's prior state is not in {`reviewed`, `accepted`, `edited`} — the three states that encode an explicit clinician touch. `suggested` items (no clinician review) and `rejected` items (clinician explicitly refused) both fail the gate. The application layer is responsible for excluding `rejected` items from the finalize UPDATE scope (e.g. `WHERE visit_id=... AND state <> 'rejected'`), so finalized charts contain only items the clinician positively endorsed. This enforces CMS OASIS-E2 Convention #9: software may not generate the final OASIS response without clinician review.

## Acceptance Criteria

| ID     | Criterion                                                                                               | Verification                                                                  | Covers        |
| ------ | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------- |
| AC-001 | `just up` boots all containers healthy within 30s                                                       | `docker compose ps` inspection                                                | FR-001, NFR-001 |
| AC-002 | `/health` returns expected JSON with uuidv7 confirmation + progressive state fields                    | Pre-DDL: `.tables_count==0 and .alembic_version==null and .hom_nodes_seeded==null`. Post-DDL pre-seed: `.tables_count>=N and .alembic_version=="001_initial_hdp_ddl" and .hom_nodes_seeded==0`. Post-seed: `.hom_nodes_seeded>=10`. In every state: `.uuidv7==true and .status=="ok"`. | FR-003         |
| AC-003 | All four extensions present post-boot                                                                   | `psql -c "SELECT extname FROM pg_extension" \| grep -E 'uuid-ossp\|vector\|pg_trgm\|btree_gin' \| wc -l` >= 4 | FR-002, NFR-001 |
| AC-004 | HDP-initial tables created, no FK errors                                                                | `\dt` count matches the exact table list in `vault/research/hdp-initial-tables.md` (Phase 0 FR-103 output) | FR-004         |
| AC-005 | `touch_updated_at()` + per-table `updated_at` triggers attached to every scoped table that has an `updated_at` column | `SELECT COUNT(*) FROM pg_trigger WHERE tgname LIKE 'trg_%_updated_at'` equals the count of tables with `updated_at TIMESTAMPTZ` in the sql/ files | FR-005         |
| AC-006 | Audit trigger on `policy_rules` fires during seed; produces audit row with NULL batch_id                | After `just seed`: `SELECT COUNT(*) FROM audit_changes WHERE batch_id IS NULL AND table_name = 'policy_rules'` >= 1 | FR-006         |
| AC-007 | Reference tables seeded at minimum cardinalities                                                        | Per-table `SELECT COUNT(*)` meets SC-007 minimums                             | FR-007         |
| AC-008 | One test patient with FK-consistent rows in persons + patients + person_identifiers                    | Join query returns exactly one row                                            | FR-008         |
| AC-009 | `just seed` idempotent — second run zero deltas                                                         | Run twice; diff row counts must match                                         | FR-009         |
| AC-010 | `just db-verify` prints health + table count + alembic revision                                         | Output inspection                                                             | FR-010         |
| AC-011 | SQL text lives only in `sql/` directories — no CREATE TABLE in migration or script code                 | `grep -rc "CREATE TABLE" migrations/ scripts/` shows 0 hits                    | NFR-002        |
| AC-012 | `just db-ddl` idempotent via Alembic — second run is a no-op                                            | Run `just db-ddl` twice; `alembic_version.version_num` stable; both exit 0    | FR-011         |
| AC-013 | `alembic_version` table records the applied revision                                                    | `SELECT version_num FROM alembic_version` returns `001_initial_hdp_ddl` post-upgrade | FR-004  |
| AC-014 | S3 reset cycle completes end-to-end without errors                                                      | `just db-reset && just up && just db-ddl && just seed` — all exit 0 in <= 120s cold / 60s warm | S3             |
| AC-015 | S4 wrong-image failure surfaces a diagnosable error                                                     | Substitute `image: postgres:18-alpine` in compose; run `just db-ddl`; assert stderr contains both "extension" and "vector" | S4             |
| AC-016 | S5 forward-compat: `audit_changes` + `chart_state_transitions` support both NULL and non-null batch_id simultaneously | Execute an UPDATE on `chart_items` under `SET LOCAL hdp.audit_batch_id = gen_random_uuid()`; assert the resulting transition row has non-null batch_id; pre-existing NULL-batched bootstrap rows remain | S5             |
| AC-017 | HITL state machine tables exist; state column has CHECK constraint covering {suggested, reviewed, accepted, edited, rejected, finalized} | `\d+ chart_items` inspection; manual INSERT of invalid state raises | FR-012, SC-012 |
| AC-018 | Chart-state transitions log on every state change                                                       | UPDATE one `chart_items` row's state from `suggested` to `reviewed`; assert exactly one new row in `chart_state_transitions` with correct from/to/timestamp | FR-012         |
| AC-019 | Convention-#9 finalize-gate blocks premature finalization                                               | Create 3 `chart_items` rows in states `reviewed`, `accepted`, `suggested`; attempt `UPDATE ... SET state='finalized' WHERE visit_id=...`; assert the update raises (`suggested` blocks). Retry with `WHERE visit_id=... AND state IN ('reviewed','accepted','edited')`; assert the update succeeds and touches exactly 2 rows. Then attempt `UPDATE ... SET state='finalized' WHERE visit_id=... AND state = 'rejected'` (after first transitioning the `suggested` row to `rejected`); assert the update raises (`rejected` is NOT a passing prior state — app layer must filter it out) | FR-013, S6     |
