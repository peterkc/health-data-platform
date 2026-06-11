# Database Substrate — Dolt vs Postgres for M3

**Status**: Evaluation — recommendation ready, pending team alignment
**Purpose**: Evaluate whether M3 should build on Dolt Server or PostgreSQL, given that no MVP schema code exists yet (greenfield).
**Audience**: Team — architecture decision before M3 implementation begins.
**Companion to**: [data-plane.md](data-plane.md) (Repository design built on this choice), [decisions.md](decisions.md) (D22 OpenFGA already on Postgres), [table-designs.md](table-designs.md) (DDL targets this substrate)

## How to read this file

- "Context" explains why this question surfaced now
- "Comparison" is the side-by-side evaluation
- "Audit replication" shows exactly how Postgres replaces Dolt's versioning
- "Recommendation" states the position and what it costs

## Target version

**PostgreSQL 18** (latest stable: 18.3, Feb 2026). Three PG 18 features directly simplify Health OS's design:

| PG 18 feature                        | What it replaces                                          | Impact                                                                                                                                               |
| ------------------------------------ | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `uuidv7()` native function           | `gen_random_uuid()`                                       | Time-sortable UUIDs — B-tree index locality for append-heavy silver tables. Order correlates with insertion time without a separate timestamp index. |
| Temporal PK/FK constraints           | Custom trigger enforcement of `valid_from`/`valid_to`     | Database enforces non-overlapping validity periods natively. Eliminates temporal_trigger_func() below — ~0.5 days of effort removed.                 |
| `RETURNING OLD/NEW` in UPDATE/DELETE | Extra SELECT in audit trigger to capture pre-change state | Audit trigger gets old+new row in one statement. Simpler trigger, fewer round-trips.                                                                 |

Additional PG 18 features Health OS benefits from:

| Feature                    | Benefit                                                                               |
| -------------------------- | ------------------------------------------------------------------------------------- |
| Async I/O (AIO) subsystem  | Up to 3x read throughput on bulk queries — FHIR ingest, timeline UNION VIEW           |
| OAuth 2.0 authentication   | Direct Auth0 federation — relevant for SMART on FHIR (interoperability-surface.md §3) |
| Virtual generated columns  | Computed-at-read fields (BMI, unit conversions) without storage cost (ADR-2010)       |
| `NOT ENFORCED` constraints | Staged raw→canonical loading without constraint violations during ETL                 |
| B-tree skip scan           | Faster multicolumn index queries on (org_id, timestamp) patterns                      |
| SIMD JSON processing       | Faster JSONB parsing for wearable payloads and FHIR bundles                           |
| Data checksums default-on  | Silent data corruption detection (P3 Trust)                                           |

## Context

Health OS's POC (M1+M2) runs on Dolt Server — a MySQL-compatible database with built-in data versioning (`DOLT_COMMIT`, `dolt log`, `dolt diff`, `AS OF` queries). This gives HIPAA-grade audit for free.

Two problems surfaced:

1. **Vector search**: Dolt's vector index is alpha. DoltHub's own assessment: "Right now, it's simply too slow for us to recommend using it in production." Euclidean distance only — no cosine or dot-product. No production timeline published. Flagged for semantic search on clinical data that lacks standard codes (free-text notes, patient-reported symptoms).

1. **Operational complexity**: D22 locked OpenFGA on Postgres as the authorization PDP. Running Dolt + Postgres means two database engines to operate, monitor, and back up.

Since no MVP schema code exists yet (DDL tasks #115-#125 are pending), this is a greenfield choice — not a migration.

## Comparison

| Dimension             | Dolt Server                                                | PostgreSQL                                                   |
| --------------------- | ---------------------------------------------------------- | ------------------------------------------------------------ |
| Audit / versioning    | Native — `DOLT_COMMIT()`, `dolt log`, `dolt diff`, `AS OF` | Build with triggers + audit tables (~2-4 days)               |
| Vector search         | Alpha, Euclidean only, slow queries                        | **pgvector** — GA, HNSW + IVFFlat, cosine + L2 + dot-product |
| Row-level security    | Unclear support                                            | **Native** — D23's phased RLS fallback becomes day-one       |
| OpenFGA (D22)         | Separate Postgres instance required                        | **Same engine** — one database for data + authorization      |
| Wire protocol         | MySQL-compatible                                           | Native Postgres                                              |
| Ecosystem             | Niche — limited tooling, libraries, hiring pool            | Decades of hardening, every ORM, every cloud                 |
| Branch/merge for data | Native — unique capability                                 | Not available (schema branching via git + migrations)        |
| Community             | Small, responsive team at DoltHub                          | Massive, production-proven across industries                 |

## Audit replication in Postgres

Dolt's audit value comes from three capabilities. All three can be replicated with database-level triggers — no application code for change tracking.

### Architecture

```
Application (Repository.write())
  |
  |  SET LOCAL hdp.audit_batch_id = '<uuid>'
  |  then normal INSERT / UPDATE / DELETE
  |
  v
PostgreSQL trigger layer (fires automatically)
  +- audit_trigger_func()    -> captures old/new JSONB into audit_changes
  +- temporal_trigger_func() -> manages valid_from / valid_to
```

### Schema

```sql
CREATE TABLE audit_batches (
    id UUID PRIMARY KEY DEFAULT uuidv7(),  -- PG 18: time-sortable, index-friendly
    author_id UUID,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE audit_changes (
    id BIGSERIAL PRIMARY KEY,
    batch_id UUID REFERENCES audit_batches(id),
    table_name TEXT NOT NULL,
    row_id UUID NOT NULL,
    operation TEXT NOT NULL,  -- INSERT | UPDATE | DELETE
    old_data JSONB,          -- PG 18: RETURNING OLD simplifies trigger capture
    new_data JSONB,
    changed_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Capability mapping

| Dolt capability      | Postgres equivalent                                      | How                                                                                    |
| -------------------- | -------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `DOLT_COMMIT('msg')` | `INSERT INTO audit_batches`                              | Repository sets `SET LOCAL hdp.audit_batch_id` once per transaction; trigger reads it |
| `dolt log`           | `SELECT * FROM audit_batches ORDER BY created_at DESC`   | Direct query                                                                           |
| `dolt diff <a> <b>`  | `SELECT * FROM audit_changes WHERE batch_id IN (...)`    | Row-level old/new JSONB                                                                |
| `AS OF 'timestamp'`  | `WHERE valid_from <= ? AND valid_to > ?`                 | Temporal columns on silver tables; PG 18 temporal PK/FK enforces non-overlap natively  |
| Rollback bad batch   | Re-insert old_data rows from audit_changes for the batch | Manual but auditable                                                                   |

### Trigger-level enforcement

Triggers fire on every INSERT/UPDATE/DELETE regardless of caller — raw SQL from an admin session, ORM, or manual fix all get captured. No code path can bypass audit without explicitly disabling triggers (which pgAudit logs). This is a stronger guarantee than Dolt, where `dolt sql` queries bypass `DOLT_COMMIT()` unless explicitly called.

## Vector search

D5 locked embeddings in a separate `health_record_embeddings` table. The table design is storage-agnostic.

On Postgres with pgvector:

```sql
CREATE EXTENSION vector;

ALTER TABLE health_record_embeddings
    ADD COLUMN embedding vector(768);

CREATE INDEX ON health_record_embeddings
    USING hnsw (embedding vector_cosine_ops);
```

Semantic search is one query:

```sql
SELECT record_id, 1 - (embedding <=> query_embedding) AS similarity
FROM health_record_embeddings
ORDER BY embedding <=> query_embedding
LIMIT 10;
```

Supports cosine, L2, dot-product. HNSW and IVFFlat indexes. Production-ready.

### Which data should be semantically searchable?

Code-based search (LOINC, SNOMED, ICD-10, RxNorm) covers structured clinical data. Semantic search covers what codes miss:

| Data type                                  | Search method                                                       | Why                                                             |
| ------------------------------------------ | ------------------------------------------------------------------- | --------------------------------------------------------------- |
| Observations with LOINC codes              | Code lookup                                                         | Exact — code is the canonical identifier                        |
| Conditions with ICD-10/SNOMED              | Code lookup                                                         | Exact                                                           |
| Medications with RxNorm                    | Code lookup                                                         | Exact                                                           |
| Free-text clinical notes (D14 `code_text`) | **Semantic**                                                        | No code assigned; NLP-extracted, patient-reported               |
| Unstructured document content              | **Semantic**                                                        | PDFs, scanned records, discharge summaries                      |
| Patient-reported symptoms                  | **Semantic**                                                        | Natural language, no standard coding                            |
| Drug class queries ("ACE inhibitors")      | **Hybrid** — code lookup via `ref_drug_classes` + semantic fallback | RxNorm class hierarchy covers most; semantic catches edge cases |

## Effort

| Component                               | Work                                                                                                                    | Estimate       |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | -------------- |
| Audit tables + generic trigger function | DDL + one PL/pgSQL function applied to all silver tables; `RETURNING OLD/NEW` (PG 18)                                   | ~0.5 days      |
| Temporal columns                        | `valid_from`/`valid_to` on silver tables; PG 18 temporal PK/FK enforces non-overlap natively — no custom trigger needed | ~0.5 days      |
| pgvector setup                          | Extension + vector column + HNSW index on embeddings table                                                              | ~0.5 days      |
| pgAudit extension                       | Statement-level audit logging for HIPAA                                                                                 | ~0.5 days      |
| Repository integration                  | `SET LOCAL hdp.audit_batch_id` per transaction; `uuidv7()` for all PKs                                                 | ~0.5 days      |
| Testing                                 | Trigger correctness, temporal queries, vector search, batch grouping                                                    | ~1-2 days      |
| **Total**                               |                                                                                                                         | **3-4.5 days** |

## What Postgres cannot replicate

**Data branch/merge** — Dolt can branch a database, test changes against real data, and merge or discard. No production database does this. For M3 and production, this capability is replaced by: migration tools (Alembic) for schema changes + test databases for data changes + git for version control of migration files.

## Recommendation

**Build M3 on PostgreSQL 18.**

- pgvector answers the semantic-search question on day one
- Postgres RLS makes D23's phased fallback a day-one capability
- One database engine (data + OpenFGA + vector) instead of two
- Audit infrastructure is 3-4.5 days of M3 work, not migration tax
- Trigger-level audit is a stronger guarantee than Dolt's opt-in `DOLT_COMMIT()`
- PG 18 `uuidv7()` gives time-sortable PKs — better index performance on append-heavy clinical tables
- PG 18 temporal constraints enforce `valid_from`/`valid_to` non-overlap natively — eliminates custom trigger
- PG 18 `RETURNING OLD/NEW` simplifies the audit trigger (old+new in one statement)
- PG 18 OAuth 2.0 auth aligns with SMART on FHIR (interoperability-surface.md §3)
- Every engineer Health OS hires will know Postgres

The only loss is data branch/merge — a development convenience Health OS doesn't need for M3 or production.

Pending: team alignment before locking as D28.

## Related

- [data-plane.md](data-plane.md) §1.2 — `dolt_commit` in WriteResult becomes `audit_batch_id`
- [data-plane.md](data-plane.md) §6.4 — Dolt commit log becomes audit table in three-layer observability
- [decisions.md](decisions.md) D5 — embeddings table (storage-agnostic)
- [decisions.md](decisions.md) D22 — OpenFGA already on Postgres
- [decisions.md](decisions.md) D23 — RLS fallback (native in Postgres)
- ADR-0001 P4 (Ownership) — audit is architecture, not a toggle
