# Table Designs — MVP Schema Additions

**Status**: Locked (2026-04-14) — D1-D7 resolved; see README.md decision matrix
**Purpose**: DDL for every new table in the MVP schema, with split triggers and FK dependency order.
**Audience**: Engineers writing migrations or repository code; reviewers checking DDL against decisions.
**Companion to**: [identity-model.md](identity-model.md) (persons/org_roles/practitioners DDL), [consent-model.md](consent-model.md) (access_grants DDL), [decisions.md](decisions.md) (D1-D7 that drove these designs)

## How to read this file

- Tables already designed elsewhere are listed in the "Already Designed" table with links
- Each remaining section is one table with full `CREATE TABLE` DDL and inline commentary
- Split triggers (e.g., "extract location to its own table when N > threshold") are documented per table
- Convention section at top shows the DDL patterns inherited from `scripts/ddl.py`

## Existing Pattern (from ddl.py)

- `UUID` native type with `DEFAULT uuidv7()` for PKs (PG 18 — time-sortable, better B-tree locality)
- `TIMESTAMPTZ` for timestamps (timezone-aware, microsecond precision)
- `DEFAULT NOW()` for audit columns
- Temporal columns (`valid_from`, `valid_to`) use PG 18 temporal PK/FK constraints for non-overlap enforcement
- Note: existing ddl.py still uses VARCHAR(36)/DATETIME(3) for Dolt compatibility in M1/M2; M3 DDL targets PostgreSQL 18 natively
- `INSERT ... ON CONFLICT DO UPDATE` for idempotent seeding (replaces MySQL's `INSERT IGNORE`)
- FK dependency order in `DDL_STATEMENTS` list

## New Tables (11)

### Already Designed (see dedicated files)

| Table             | Design In         | FK Deps                    |
| ----------------- | ----------------- | -------------------------- |
| ref_organizations | identity-model.md | None                       |
| persons           | identity-model.md | None                       |
| org_roles         | identity-model.md | persons, ref_organizations |
| practitioners     | identity-model.md | persons, ref_organizations |
| access_grants     | consent-model.md  | patients                   |

### documents

```sql
CREATE TABLE IF NOT EXISTS documents (
    id              VARCHAR(36) NOT NULL PRIMARY KEY,
    patient_id      VARCHAR(36) NOT NULL,
    title           VARCHAR(255) NOT NULL,
    document_type   VARCHAR(30) NOT NULL,
    mime_type       VARCHAR(100) NOT NULL,
    size_bytes      INT UNSIGNED NOT NULL,
    storage_path    VARCHAR(512) NOT NULL,
    payload_hash    VARCHAR(64) NOT NULL,
    source_system   VARCHAR(50) NOT NULL,
    source_standard VARCHAR(30) NULL,
    trust_level     TINYINT UNSIGNED NOT NULL,
    raw_payload_id  VARCHAR(36) NULL,
    org_id          VARCHAR(36) NOT NULL,
    created_at      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    deleted_at      DATETIME(3) NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (raw_payload_id) REFERENCES raw_payloads(id),
    UNIQUE KEY uq_hash (payload_hash),
    KEY idx_patient_type (patient_id, document_type),
    KEY idx_org (org_id),
    KEY idx_deleted (deleted_at)
)
```

**Design notes**:

- `storage_path`: **content-addressed** S3 key derived from `payload_hash`.
  Format: `docs/{hash[0:2]}/{hash[2:4]}/{hash}.{ext}` (directory-sharded to avoid S3 hotspots).
  Example: `docs/ab/cd/abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890.pdf`.
  Rationale: patient ↔ org is many-to-many; path-embedded identity (`orgs/X/patients/Y/...`)
  fragments under multi-org patients + Health OS. Content addressing decouples storage from
  the identity model — identity lives in DB columns, not in S3 keys.
- `payload_hash`: SHA-256 for dedup. `UNIQUE KEY uq_hash` enforces one row per unique content
  (same pattern as `raw_payloads.payload_hash`).
- `org_id`: **provenance** (which org uploaded the document), NOT access control.
  Access is mediated by `access_grants` + `patient_id`, never by path or org membership.
- `document_type`: `lab_report`, `imaging`, `discharge_summary`, `immunization_card`, `other`.
- Download endpoint generates pre-signed S3 URL from `storage_path`.
- **HIPAA deletion**: soft-delete via `deleted_at`. Purge S3 only when zero active rows
  reference the hash (reference counting). Honors right-to-delete without breaking
  concurrent references from other grant scopes.

### encounters

```sql
CREATE TABLE IF NOT EXISTS encounters (
    id                  VARCHAR(36) NOT NULL PRIMARY KEY,
    patient_id          VARCHAR(36) NOT NULL,
    encounter_type      VARCHAR(30) NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'finished',
    period_start        DATETIME(3) NOT NULL,
    period_end          DATETIME(3) NULL,
    practitioner_id     VARCHAR(36) NULL,
    location_name       VARCHAR(255) NULL,
    location_type       VARCHAR(50) NULL,
    reason_code         VARCHAR(20) NULL,
    reason_display      VARCHAR(255) NULL,
    org_id              VARCHAR(36) NOT NULL,
    raw_payload_id      VARCHAR(36) NULL,
    created_at          DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (practitioner_id) REFERENCES practitioners(id),
    FOREIGN KEY (raw_payload_id) REFERENCES raw_payloads(id),
    KEY idx_patient_date (patient_id, period_start),
    KEY idx_org (org_id)
)
```

**Design notes**:

- `encounter_type`: `office_visit`, `telehealth`, `lab_draw`, `imaging`, `executive_physical`
- **D2 locked**: `location_name` + `location_type` inline, no separate ref_locations table
  for MVP. Split trigger: when Health OS needs geospatial queries, facility analytics, or
  multi-source location reconciliation (post-Series A).
- `health_records` can optionally FK to encounters via `report_id` or a new `encounter_id` column

### care_plans

```sql
CREATE TABLE IF NOT EXISTS care_plans (
    id              VARCHAR(36) NOT NULL PRIMARY KEY,
    patient_id      VARCHAR(36) NOT NULL,
    title           VARCHAR(255) NOT NULL,
    description     TEXT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'active',
    category        VARCHAR(50) NULL,
    period_start    DATE NULL,
    period_end      DATE NULL,
    author_id       VARCHAR(36) NULL,
    org_id          VARCHAR(36) NOT NULL,
    created_at      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    KEY idx_patient_status (patient_id, status),
    KEY idx_org (org_id)
)
```

### goals

```sql
CREATE TABLE IF NOT EXISTS goals (
    id              VARCHAR(36) NOT NULL PRIMARY KEY,
    care_plan_id    VARCHAR(36) NOT NULL,
    patient_id      VARCHAR(36) NOT NULL,
    description     VARCHAR(255) NOT NULL,
    target_code     VARCHAR(20) NULL,
    target_system   VARCHAR(100) NULL,
    target_value    DOUBLE NULL,
    target_unit     VARCHAR(30) NULL,
    target_operator VARCHAR(10) NULL,
    current_value   DOUBLE NULL,
    due_date        DATE NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    hom_node_id     VARCHAR(36) NULL,
    created_at      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (care_plan_id) REFERENCES care_plans(id),
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (hom_node_id) REFERENCES ref_hom_nodes(id),
    KEY idx_care_plan (care_plan_id),
    KEY idx_patient (patient_id)
)
```

**Design notes**:

- `target_code`: LOINC code for the biomarker being tracked (e.g., 2093-3 for cholesterol)
- `target_operator`: `lt`, `gt`, `lte`, `gte`, `eq` (e.g., LDL < 100)
- `hom_node_id`: links goal to HOM tree for dashboard grouping
- `current_value`: denormalized from latest health_records query (updated by pipeline or on-read)

### journal_entries

```sql
CREATE TABLE IF NOT EXISTS journal_entries (
    id              VARCHAR(36) NOT NULL PRIMARY KEY,
    patient_id      VARCHAR(36) NOT NULL,
    entry_type      VARCHAR(30) NOT NULL,
    title           VARCHAR(255) NULL,
    content         TEXT NULL,
    health_record_id VARCHAR(36) NULL,
    encounter_id    VARCHAR(36) NULL,
    author_id       VARCHAR(36) NULL,
    org_id          VARCHAR(36) NOT NULL,
    effective_date  DATETIME(3) NOT NULL,
    created_at      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (health_record_id) REFERENCES health_records(id),
    FOREIGN KEY (encounter_id) REFERENCES encounters(id),
    KEY idx_patient_date (patient_id, effective_date),
    KEY idx_org (org_id)
)
```

### notes

```sql
CREATE TABLE IF NOT EXISTS notes (
    id                  VARCHAR(36) NOT NULL PRIMARY KEY,
    journal_entry_id    VARCHAR(36) NOT NULL,
    author_id           VARCHAR(36) NOT NULL,
    content             TEXT NOT NULL,
    created_at          DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE,
    KEY idx_entry (journal_entry_id)
)
```

**Design notes**:

- `entry_type`: `clinical_note`, `patient_note`, `ai_summary`, `life_event`
- `health_record_id`: optional link to a specific record (annotation on a lab result)
- `notes` is a child table — clinician/patient replies on a journal entry

## DDL Insertion Order (Full 30-table sequence)

```
# Reference (no FKs)
loinc_crosswalk
ref_hom_nodes
ref_hom_mapping
ref_analyte_conversions
ref_drug_classes
ref_record_type_schemas
ref_organizations                    # NEW
ref_source_adapters                  # NEW (full registry — D6 locked)

# Bronze
raw_payloads

# Identity
persons                              # NEW
patients
org_roles                            # NEW (persons, ref_organizations)
patient_preferences
patient_org_access
patient_relationships
patient_identifiers
practitioners                        # NEW (persons, ref_organizations)

# Silver — clinical
clinical_entities
reports
health_records
observation_components
documents                            # NEW (patients, raw_payloads)
encounters                           # NEW (patients, practitioners)
care_plans                           # NEW (patients)
goals                                # NEW (care_plans, patients)
journal_entries                      # NEW (patients, health_records, encounters)
notes                                # NEW (journal_entries)
provenance
access_grants                        # NEW (patients)

# Gold
daily_summaries

# Ops
data_quality_issues
```

## D5 Locked — Embeddings in separate table

Rejected: column on health_records (bloats row size, forces full-table re-embed when model changes).
On Postgres: pgvector extension provides HNSW + IVFFlat indexes (see [database-substrate.md](database-substrate.md)).

Locked: separate `health_record_embeddings` table.

```sql
CREATE TABLE IF NOT EXISTS health_record_embeddings (
    id                  VARCHAR(36) NOT NULL PRIMARY KEY,
    health_record_id    VARCHAR(36) NOT NULL,
    model               VARCHAR(100) NOT NULL,  -- e.g., text-embedding-3-large
    model_version       VARCHAR(30) NOT NULL,
    dimension           INT UNSIGNED NOT NULL,
    vector              JSON NOT NULL,
    generated_at        DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (health_record_id) REFERENCES health_records(id) ON DELETE CASCADE,
    UNIQUE KEY uq_record_model (health_record_id, model, model_version),
    KEY idx_model (model, model_version)
)
```

Why: embeddings are ML-derived, model-specific, and regenerate when models change.
Keeping them out of `health_records` avoids coupling the clinical source-of-truth table
to ML infrastructure. Multiple models per record supported (e.g., one for semantic search,
one for clustering).

## D6 Locked — ref_source_adapters full registry

Rejected: hardcode 4 built adapters in code (POC scale only; breaks under source plurality).

Locked: full registry table. Every source Health OS ingests from has a row.

```sql
CREATE TABLE IF NOT EXISTS ref_source_adapters (
    id                  VARCHAR(36) NOT NULL PRIMARY KEY,
    source_system       VARCHAR(50) NOT NULL,  -- e.g., quest, oura, epic, manual
    display_name        VARCHAR(100) NOT NULL,
    adapter_class       VARCHAR(200) NOT NULL,  -- fully qualified Python class
    source_standard     VARCHAR(30) NULL,       -- FHIR-R4, HL7-v2, OuraAPI-v3, manual
    auth_type           VARCHAR(30) NOT NULL,   -- oauth2, api_key, none, manual
    config              JSON NULL,              -- endpoint URLs, rate limits, scopes
    trust_level_default TINYINT UNSIGNED NOT NULL,  -- baseline ADR-2007 level
    active              BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    UNIQUE KEY uq_source (source_system),
    KEY idx_active (active)
)
```

Ingest flow:

1. Request arrives with `source_system` header
1. Lookup `ref_source_adapters` by `source_system`
1. Instantiate `adapter_class`, apply `config`, route to adapter
1. Record `trust_level_default` on resulting health_records (unless overridden)

Adding a new source (e.g., Whoop):

1. Write `WhoopAdapter` class in code
1. INSERT INTO ref_source_adapters (source_system='whoop', adapter_class='adapters.whoop.WhoopAdapter', ...)
1. Deploy

Zero schema change per new source. This is the Health OS extensibility contract.

## D7 Locked — Split `health_records` into FHIR-aligned tables

**Superseded** (2026-04-14): single-table split-trigger plan.
**Replaced by D7 (2026-04-14)**: hybrid split into 6 FHIR-aligned tables.

The earlier "keep single-table, split on trigger" plan was correct under the pre-catalog scope
(6 observation-like record_types for longevity). The data-type catalog surfaces ~150 data
types across 9 domains; every pivot requires 4-10 structured entities that cannot fit
`extensions JSON` without semantic loss. FHIR, OMOP, openEHR, and Fasten all separate
condition-like entities from observations. Health OS aligns.

See [decisions.md#D7](decisions.md) for the decision rationale.

### Target core shape (6 tables)

1. **`observations`** — point-in-time measurements, findings, survey results, social history
1. **`conditions`** — diagnoses with state machine (clinical_status, verification_status, onset, resolution)
1. **`medications`** — active meds with dose, route, frequency, prescriber (FHIR MedicationStatement / MedicationRequest unified)
1. **`allergies`** — intolerances with reaction arrays, severity, criticality
1. **`immunizations`** — with dose_number, series, route, site, forecasting
1. **`family_history`** — structured lineage with relationship, condition, age_at_onset

### observations (replaces current `health_records`)

```sql
CREATE TABLE IF NOT EXISTS observations (
    id                    VARCHAR(36)  NOT NULL PRIMARY KEY,
    patient_id            VARCHAR(36)  NOT NULL,
    observation_type      VARCHAR(50)  NOT NULL,  -- CSA-13: vital-signs | laboratory | social-history
                                                   --                   | survey-result | imaging-finding
                                                   --                   | activity | sleep | nutrition | ...
    code                  VARCHAR(50)  NOT NULL,
    code_system           VARCHAR(50)  NOT NULL,
    code_display          VARCHAR(255) NULL,
    code_text             VARCHAR(500) NULL,        -- CSA-6: free-text fallback when no code
    value_numeric         DOUBLE       NULL,
    value_string          VARCHAR(500) NULL,
    value_json            JSON         NULL,
    unit                  VARCHAR(30)  NULL,
    effective_date        DATETIME(3)  NOT NULL,
    recorded_at           DATETIME(3)  NULL,        -- CSA-5
    asserted_at           DATETIME(3)  NULL,        -- CSA-5
    narrative             TEXT         NULL,        -- CSA-2
    source_system         VARCHAR(50)  NOT NULL,
    source_standard       VARCHAR(30)  NULL,
    trust_level           TINYINT UNSIGNED NOT NULL,
    canonical_id          VARCHAR(36)  NULL,        -- alias / duplicate chain self-FK
    extensions            JSON         NULL,        -- source-specific fields (not canonical)
    raw_payload_id        VARCHAR(36)  NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (raw_payload_id) REFERENCES raw_payloads(id),
    FOREIGN KEY (canonical_id) REFERENCES observations(id),
    KEY idx_patient_date (patient_id, effective_date),
    KEY idx_code (code, code_system),
    KEY idx_type (observation_type)
);
```

### conditions

```sql
CREATE TABLE IF NOT EXISTS conditions (
    id                    VARCHAR(36)  NOT NULL PRIMARY KEY,
    patient_id            VARCHAR(36)  NOT NULL,
    code                  VARCHAR(50)  NOT NULL,      -- ICD-10-CM / SNOMED CT
    code_system           VARCHAR(50)  NOT NULL,
    code_display          VARCHAR(255) NULL,
    clinical_status       VARCHAR(30)  NOT NULL,      -- FHIR: active | recurrence | relapse
                                                       --       | inactive | remission | resolved
    verification_status   VARCHAR(30)  NOT NULL,      -- FHIR: unconfirmed | provisional | differential
                                                       --       | confirmed | refuted | entered-in-error
    category              VARCHAR(50)  NULL,          -- problem-list-item | encounter-diagnosis
    severity              VARCHAR(30)  NULL,          -- mild | moderate | severe
    onset_date            DATETIME(3)  NULL,
    abatement_date        DATETIME(3)  NULL,
    recorded_at           DATETIME(3)  NOT NULL,
    narrative             TEXT         NULL,          -- CSA-2
    recorder_id           VARCHAR(36)  NULL,          -- FK persons
    source_system         VARCHAR(50)  NOT NULL,
    source_standard       VARCHAR(30)  NULL,
    trust_level           TINYINT UNSIGNED NOT NULL,
    extensions            JSON         NULL,
    raw_payload_id        VARCHAR(36)  NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (raw_payload_id) REFERENCES raw_payloads(id),
    KEY idx_patient_status (patient_id, clinical_status),
    KEY idx_code (code, code_system)
);
```

### medications

```sql
CREATE TABLE IF NOT EXISTS medications (
    id                    VARCHAR(36)  NOT NULL PRIMARY KEY,
    patient_id            VARCHAR(36)  NOT NULL,
    code                  VARCHAR(50)  NOT NULL,      -- RxNorm
    code_system           VARCHAR(50)  NOT NULL,
    code_display          VARCHAR(255) NOT NULL,
    status                VARCHAR(30)  NOT NULL,      -- FHIR: active | completed | entered-in-error
                                                       --       | intended | stopped | on-hold | not-taken
    intent                VARCHAR(30)  NULL,          -- order | plan | proposal (MedicationRequest)
    dose_value_numeric    DOUBLE       NULL,
    dose_unit             VARCHAR(30)  NULL,
    route                 VARCHAR(50)  NULL,          -- oral | IV | topical | ...
    frequency             VARCHAR(100) NULL,          -- BID | QID | PRN | structured
    prn                   BOOLEAN      NULL,          -- as-needed flag
    prescriber_id         VARCHAR(36)  NULL,          -- FK persons / practitioners
    effective_period_start DATETIME(3) NULL,
    effective_period_end  DATETIME(3)  NULL,
    recorded_at           DATETIME(3)  NOT NULL,
    narrative             TEXT         NULL,
    source_system         VARCHAR(50)  NOT NULL,
    source_standard       VARCHAR(30)  NULL,
    trust_level           TINYINT UNSIGNED NOT NULL,
    extensions            JSON         NULL,
    raw_payload_id        VARCHAR(36)  NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (raw_payload_id) REFERENCES raw_payloads(id),
    KEY idx_patient_status (patient_id, status),
    KEY idx_code (code)
);
```

### allergies

```sql
CREATE TABLE IF NOT EXISTS allergies (
    id                    VARCHAR(36)  NOT NULL PRIMARY KEY,
    patient_id            VARCHAR(36)  NOT NULL,
    code                  VARCHAR(50)  NOT NULL,      -- RxNorm | SNOMED | UNII
    code_system           VARCHAR(50)  NOT NULL,
    code_display          VARCHAR(255) NULL,
    clinical_status       VARCHAR(30)  NOT NULL,      -- active | inactive | resolved
    verification_status   VARCHAR(30)  NOT NULL,      -- unconfirmed | confirmed | refuted
    type                  VARCHAR(30)  NULL,          -- allergy | intolerance
    category              VARCHAR(30)  NULL,          -- food | medication | environment | biologic
    criticality           VARCHAR(30)  NULL,          -- low | high | unable-to-assess
    reactions             JSON         NULL,          -- array of {manifestation, severity, onset}
    onset_date            DATETIME(3)  NULL,
    recorded_at           DATETIME(3)  NOT NULL,
    narrative             TEXT         NULL,
    source_system         VARCHAR(50)  NOT NULL,
    trust_level           TINYINT UNSIGNED NOT NULL,
    extensions            JSON         NULL,
    raw_payload_id        VARCHAR(36)  NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (raw_payload_id) REFERENCES raw_payloads(id),
    KEY idx_patient_status (patient_id, clinical_status)
);
```

### immunizations

```sql
CREATE TABLE IF NOT EXISTS immunizations (
    id                    VARCHAR(36)  NOT NULL PRIMARY KEY,
    patient_id            VARCHAR(36)  NOT NULL,
    code                  VARCHAR(50)  NOT NULL,      -- CVX
    code_system           VARCHAR(50)  NOT NULL,
    code_display          VARCHAR(255) NULL,
    status                VARCHAR(30)  NOT NULL,      -- completed | not-done | entered-in-error
    lot_number            VARCHAR(50)  NULL,
    manufacturer          VARCHAR(100) NULL,
    dose_number           TINYINT UNSIGNED NULL,      -- 1, 2, 3 in series
    series_count          TINYINT UNSIGNED NULL,      -- total doses in series
    route                 VARCHAR(30)  NULL,
    site                  VARCHAR(30)  NULL,          -- left-deltoid | right-deltoid | ...
    administered_at       DATETIME(3)  NOT NULL,
    next_due_at           DATETIME(3)  NULL,          -- forecasting (AAP Bright Futures)
    performer_id          VARCHAR(36)  NULL,
    narrative             TEXT         NULL,
    source_system         VARCHAR(50)  NOT NULL,
    trust_level           TINYINT UNSIGNED NOT NULL,
    extensions            JSON         NULL,
    raw_payload_id        VARCHAR(36)  NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (raw_payload_id) REFERENCES raw_payloads(id),
    KEY idx_patient_date (patient_id, administered_at)
);
```

### family_history

```sql
CREATE TABLE IF NOT EXISTS family_history (
    id                    VARCHAR(36)  NOT NULL PRIMARY KEY,
    patient_id            VARCHAR(36)  NOT NULL,
    relationship          VARCHAR(50)  NOT NULL,      -- mother | father | sibling | grandparent | ...
    condition_code        VARCHAR(50)  NOT NULL,      -- ICD-10-CM / SNOMED CT
    condition_code_system VARCHAR(50)  NOT NULL,
    condition_display     VARCHAR(255) NULL,
    age_at_onset          SMALLINT UNSIGNED NULL,
    deceased              BOOLEAN      NULL,
    age_at_death          SMALLINT UNSIGNED NULL,
    recorded_at           DATETIME(3)  NOT NULL,
    narrative             TEXT         NULL,
    source_system         VARCHAR(50)  NOT NULL,
    trust_level           TINYINT UNSIGNED NOT NULL,
    extensions            JSON         NULL,
    raw_payload_id        VARCHAR(36)  NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (raw_payload_id) REFERENCES raw_payloads(id),
    KEY idx_patient (patient_id)
);
```

### Migration implications

The prior mini-project DDL currently has single `health_records`
with 6 record_types. Migration steps (not executed yet; M3 not shipped):

1. Create 6 new tables above
1. Data migration: split `health_records` rows by `record_type` into respective tables
1. Rename `health_records` → `observations`; drop `record_type` ENUM; add `observation_type` VARCHAR
1. Update `observation_components` to FK `observations.id`
1. Update `ref_hom_mapping` to add `target_table` column (`observations` | `conditions` | `medications` | `allergies` | `immunizations` | `family_history`)
1. Update `health_record_embeddings` to polymorphic (target_table + target_id) OR split per-table (defer decision)
1. Rewrite `/records` endpoint to UNION across 6 tables (or materialize a timeline view)

### Cross-table HOM lookup

`ref_hom_mapping` gains a `target_table` column so that one mapping can point to any of the
6 tables. Query becomes:

```sql
-- Join HOM mapping to the right silver table by target_table
SELECT * FROM observations
WHERE patient_id = ? AND (code, code_system) IN (
  SELECT code, code_system FROM ref_hom_mapping
  WHERE hom_node_id = ? AND target_table = 'observations'
)
UNION ALL
SELECT * FROM conditions
WHERE patient_id = ? AND (code, code_system) IN (
  SELECT code, code_system FROM ref_hom_mapping
  WHERE hom_node_id = ? AND target_table = 'conditions'
)
-- ... repeat for medications, allergies, immunizations, family_history
```

Materialized `patient_timeline_view` is a scoping decision (perf vs freshness trade-off).

## D8–D20 Locked — DDL Sketches (13 new tables + D14 column additions)

DDL sketches for all tables introduced across D8–D20. Each sketch shows shape + indexes +
FK intent. Migration scripts + refinement during implementation.

### D9 — `policy_rules` (XACML PAP storage)

```sql
CREATE TABLE policy_rules (
  id BINARY(16) PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  description TEXT NULL,

  effect VARCHAR(16) NOT NULL,              -- 'permit' / 'deny'
  priority INT NOT NULL DEFAULT 100,        -- lower = higher precedence

  predicate JSON NOT NULL,                  -- policy predicate tree (grantee, action, resource, context)
  obligations JSON NULL,                    -- post-decision actions (redact / log / notify)

  jurisdiction VARCHAR(16) NULL,            -- ISO 3166 country code or region; NULL = universal
  legal_basis VARCHAR(32) NULL,             -- CSA-40: consent / contract / legitimate_interest / vital_interest / public_task / legal_obligation
  applies_from DATETIME(6) NULL,
  applies_until DATETIME(6) NULL,

  owner_org_id BINARY(16) NULL REFERENCES ref_organizations(id),
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  deleted_at DATETIME(6) NULL,

  INDEX ix_policy_rules_priority (effect, priority, applies_from),
  INDEX ix_policy_rules_jurisdiction (jurisdiction, legal_basis)
);
```

### D10 — `access_grant_sources`, `access_grant_categories`, `access_grant_hom_nodes`

```sql
CREATE TABLE access_grant_sources (
  grant_id BINARY(16) NOT NULL REFERENCES access_grants(id) ON DELETE CASCADE,
  source_system VARCHAR(64) NOT NULL,
  PRIMARY KEY (grant_id, source_system),
  INDEX ix_grant_sources_lookup (source_system, grant_id)
);

CREATE TABLE access_grant_categories (
  grant_id BINARY(16) NOT NULL REFERENCES access_grants(id) ON DELETE CASCADE,
  category VARCHAR(64) NOT NULL,
  PRIMARY KEY (grant_id, category),
  INDEX ix_grant_categories_lookup (category, grant_id)
);

CREATE TABLE access_grant_hom_nodes (
  grant_id BINARY(16) NOT NULL REFERENCES access_grants(id) ON DELETE CASCADE,
  hom_node_id BINARY(16) NOT NULL REFERENCES ref_hom_nodes(id) ON DELETE CASCADE,
  PRIMARY KEY (grant_id, hom_node_id),
  INDEX ix_grant_hom_nodes_lookup (hom_node_id, grant_id)
);
```

Maintained by repository writes (no triggers). `access_grants` JSON columns remain source-of-truth for the grant document shape.

### D11 — `appointments`

```sql
CREATE TABLE appointments (
  id BINARY(16) PRIMARY KEY,
  patient_id BINARY(16) NOT NULL REFERENCES patients(id),
  practitioner_id BINARY(16) NULL REFERENCES practitioners(id),
  encounter_id BINARY(16) NULL REFERENCES encounters(id),
  org_id BINARY(16) NULL REFERENCES ref_organizations(id),

  status VARCHAR(32) NOT NULL,              -- FHIR AppointmentStatus
  service_category VARCHAR(64) NULL,
  service_type VARCHAR(64) NULL,
  specialty VARCHAR(64) NULL,
  description TEXT NULL,

  start_at DATETIME(6) NOT NULL,
  end_at DATETIME(6) NOT NULL,
  minutes_duration INT NULL,

  reason_code VARCHAR(64) NULL,
  reason_system VARCHAR(64) NULL,
  reason_display TEXT NULL,
  reason_text TEXT NULL,                    -- D14 pattern
  reason_reference_table VARCHAR(32) NULL,
  reason_reference_id BINARY(16) NULL,

  priority SMALLINT NULL,
  location_name VARCHAR(256) NULL,
  location_type VARCHAR(32) NULL,
  telehealth_join_url TEXT NULL,

  source_system VARCHAR(64) NULL,
  external_id VARCHAR(256) NULL,
  raw_payload_id BINARY(16) NULL REFERENCES raw_payloads(id),

  narrative TEXT NULL,
  extensions JSON NULL,
  trust_level TINYINT NOT NULL DEFAULT 3,

  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  deleted_at DATETIME(6) NULL,

  INDEX ix_appointments_patient_start (patient_id, start_at),
  INDEX ix_appointments_practitioner_start (practitioner_id, start_at),
  INDEX ix_appointments_status (status, start_at),
  INDEX ix_appointments_reason_ref (reason_reference_table, reason_reference_id),
  UNIQUE KEY uq_appointments_source_external (source_system, external_id)
);
```

### D12 — `tasks`

```sql
CREATE TABLE tasks (
  id BINARY(16) PRIMARY KEY,
  patient_id BINARY(16) NOT NULL REFERENCES patients(id),
  requester_id BINARY(16) NULL,             -- persons.id (person / agent)
  owner_id BINARY(16) NULL,                 -- persons.id (person / agent / org-role)

  code VARCHAR(64) NULL,
  code_system VARCHAR(64) NULL,
  code_display TEXT NULL,
  code_text TEXT NULL,                      -- D14 pattern
  description TEXT NOT NULL,

  status VARCHAR(32) NOT NULL,              -- FHIR TaskStatus
  intent VARCHAR(32) NOT NULL,              -- FHIR TaskIntent
  priority VARCHAR(16) NULL,                -- routine / urgent / asap / stat

  focus_table VARCHAR(32) NULL,
  focus_id BINARY(16) NULL,

  for_table VARCHAR(32) NULL,               -- usually 'patients'
  for_id BINARY(16) NULL,

  execution_period_start DATETIME(6) NULL,
  execution_period_end DATETIME(6) NULL,

  input JSON NULL,
  output JSON NULL,

  source_system VARCHAR(64) NULL,
  external_id VARCHAR(256) NULL,
  raw_payload_id BINARY(16) NULL REFERENCES raw_payloads(id),

  narrative TEXT NULL,
  extensions JSON NULL,
  trust_level TINYINT NOT NULL DEFAULT 3,

  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  deleted_at DATETIME(6) NULL,

  INDEX ix_tasks_patient_status (patient_id, status, execution_period_start),
  INDEX ix_tasks_owner_status (owner_id, status, execution_period_start),
  INDEX ix_tasks_focus (focus_table, focus_id),
  UNIQUE KEY uq_tasks_source_external (source_system, external_id)
);
```

### D13 — `clinical_impressions` + `clinical_impression_findings` + `clinical_impression_problems`

```sql
CREATE TABLE clinical_impressions (
  id BINARY(16) PRIMARY KEY,
  patient_id BINARY(16) NOT NULL REFERENCES patients(id),
  encounter_id BINARY(16) NULL REFERENCES encounters(id),
  performer_id BINARY(16) NULL,             -- persons.id (polymorphic via performer_table)
  performer_table VARCHAR(32) NULL,         -- 'practitioners' | 'agents' | 'patients'

  status VARCHAR(32) NOT NULL,              -- FHIR: in-progress / completed / entered-in-error
  code VARCHAR(64) NULL,
  code_system VARCHAR(64) NULL,
  code_display TEXT NULL,
  code_text TEXT NULL,                      -- D14 pattern

  effective_period_start DATETIME(6) NULL,
  effective_period_end DATETIME(6) NULL,
  date DATETIME(6) NOT NULL,

  previous_impression_id BINARY(16) NULL REFERENCES clinical_impressions(id),

  summary TEXT NULL,
  prognosis_code VARCHAR(64) NULL,
  prognosis_system VARCHAR(64) NULL,
  prognosis_display TEXT NULL,
  prognosis_text TEXT NULL,
  prognosis_reference_table VARCHAR(32) NULL,
  prognosis_reference_id BINARY(16) NULL,

  source_system VARCHAR(64) NULL,
  external_id VARCHAR(256) NULL,
  raw_payload_id BINARY(16) NULL REFERENCES raw_payloads(id),

  narrative TEXT NULL,
  extensions JSON NULL,
  trust_level TINYINT NOT NULL DEFAULT 3,

  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  deleted_at DATETIME(6) NULL,

  INDEX ix_impressions_patient_date (patient_id, date DESC),
  INDEX ix_impressions_encounter (encounter_id),
  INDEX ix_impressions_performer (performer_table, performer_id),
  INDEX ix_impressions_previous (previous_impression_id),
  UNIQUE KEY uq_impressions_source_external (source_system, external_id)
);

CREATE TABLE clinical_impression_findings (
  id BINARY(16) PRIMARY KEY,
  impression_id BINARY(16) NOT NULL REFERENCES clinical_impressions(id) ON DELETE CASCADE,

  rank SMALLINT NULL,                       -- 1 = primary
  item_code VARCHAR(64) NULL,
  item_system VARCHAR(64) NULL,
  item_display TEXT NULL,
  item_text TEXT NULL,                      -- D14 pattern
  item_reference_table VARCHAR(32) NULL,
  item_reference_id BINARY(16) NULL,

  basis TEXT NULL,
  basis_references JSON NULL,               -- [{table, id}, ...]

  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

  INDEX ix_findings_impression_rank (impression_id, rank),
  INDEX ix_findings_item_ref (item_reference_table, item_reference_id)
);

CREATE TABLE clinical_impression_problems (
  impression_id BINARY(16) NOT NULL REFERENCES clinical_impressions(id) ON DELETE CASCADE,
  condition_id BINARY(16) NOT NULL REFERENCES conditions(id) ON DELETE CASCADE,
  PRIMARY KEY (impression_id, condition_id),
  INDEX ix_impression_problems_condition (condition_id, impression_id)
);
```

### D14 — `code_text` column additions

Add `code_text TEXT NULL` to all silver tables with coded values:

- `observations.code_text`, `conditions.code_text`, `medications.code_text`, `allergies.code_text`, `immunizations.code_text`, `family_history.code_text`
- Future additions per CSA lands: `procedures.code_text`, `orders.code_text`, `referrals.code_text`
- D13 tables already include code_text / item_text / prognosis_text above
- D11 `appointments.reason_text` already in sketch above

Migration (per table):

```sql
ALTER TABLE observations ADD COLUMN code_text TEXT NULL AFTER code_display;
UPDATE observations SET code_text = code_display, code_display = NULL
  WHERE code IS NULL AND code_system IS NULL AND code_display IS NOT NULL;
-- Repeat for each silver table
```

### D15 — `compositions` + `composition_authors` + `composition_sections` + `composition_section_entries`

```sql
CREATE TABLE compositions (
  id BINARY(16) PRIMARY KEY,
  patient_id BINARY(16) NOT NULL REFERENCES patients(id),
  document_id BINARY(16) NULL REFERENCES documents(id),
  encounter_id BINARY(16) NULL REFERENCES encounters(id),

  status VARCHAR(32) NOT NULL,              -- FHIR: preliminary / final / amended / entered-in-error
  type_code VARCHAR(64) NOT NULL,
  type_system VARCHAR(64) NULL,             -- typically LOINC
  type_display TEXT NULL,
  type_text TEXT NULL,                      -- D14 pattern

  title VARCHAR(256) NOT NULL,
  confidentiality VARCHAR(32) NULL,
  date DATETIME(6) NOT NULL,
  custodian_org_id BINARY(16) NULL REFERENCES ref_organizations(id),

  source_system VARCHAR(64) NULL,
  external_id VARCHAR(256) NULL,
  raw_payload_id BINARY(16) NULL REFERENCES raw_payloads(id),

  narrative TEXT NULL,
  extensions JSON NULL,
  trust_level TINYINT NOT NULL DEFAULT 3,

  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  deleted_at DATETIME(6) NULL,

  INDEX ix_compositions_patient_date (patient_id, date DESC),
  INDEX ix_compositions_type_date (type_code, date DESC),
  INDEX ix_compositions_document (document_id),
  UNIQUE KEY uq_compositions_source_external (source_system, external_id)
);

CREATE TABLE composition_authors (
  composition_id BINARY(16) NOT NULL REFERENCES compositions(id) ON DELETE CASCADE,
  author_table VARCHAR(32) NOT NULL,
  author_id BINARY(16) NOT NULL,
  PRIMARY KEY (composition_id, author_table, author_id),
  INDEX ix_composition_authors_ref (author_table, author_id, composition_id)
);

CREATE TABLE composition_sections (
  id BINARY(16) PRIMARY KEY,
  composition_id BINARY(16) NOT NULL REFERENCES compositions(id) ON DELETE CASCADE,
  parent_section_id BINARY(16) NULL REFERENCES composition_sections(id) ON DELETE CASCADE,

  sort_order INT NOT NULL,
  title VARCHAR(256) NULL,
  section_code VARCHAR(64) NULL,
  section_system VARCHAR(64) NULL,
  section_display TEXT NULL,
  section_text TEXT NULL,                   -- D14 pattern

  text TEXT NULL,                           -- FHIR section.text

  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

  INDEX ix_sections_composition (composition_id, sort_order),
  INDEX ix_sections_parent (parent_section_id, sort_order),
  INDEX ix_sections_code (section_code)
);

CREATE TABLE composition_section_entries (
  id BINARY(16) PRIMARY KEY,
  section_id BINARY(16) NOT NULL REFERENCES composition_sections(id) ON DELETE CASCADE,

  entry_table VARCHAR(32) NOT NULL,
  entry_id BINARY(16) NOT NULL,
  sort_order INT NOT NULL,

  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

  INDEX ix_entries_section (section_id, sort_order),
  INDEX ix_entries_entry (entry_table, entry_id)
);
```

### D16 — Rename `patient_identifiers` -> `person_identifiers`; `patient_preferences` -> `person_preferences`

```sql
-- Rename + re-parent FK:
ALTER TABLE patient_identifiers RENAME TO person_identifiers;
ALTER TABLE person_identifiers
  DROP FOREIGN KEY fk_patient_identifiers_patient,
  CHANGE patient_id person_id BINARY(16) NOT NULL,
  ADD CONSTRAINT fk_person_identifiers_person FOREIGN KEY (person_id) REFERENCES persons(id);

ALTER TABLE patient_preferences RENAME TO person_preferences;
ALTER TABLE person_preferences
  DROP FOREIGN KEY fk_patient_preferences_patient,
  CHANGE patient_id person_id BINARY(16) NOT NULL,
  ADD CONSTRAINT fk_person_preferences_person FOREIGN KEY (person_id) REFERENCES persons(id);
```

Data migration: for every existing row, `person_id = patients.person_id WHERE patients.id = old patient_id`. D1 patients satellite already carries `person_id`.

### D17 — `ref_hom_nodes` single-PK refactor + versioning + retirement

```sql
-- New shape (replaces composite-key definition):
CREATE TABLE ref_hom_nodes (
  id BINARY(16) PRIMARY KEY,
  tree_id VARCHAR(32) NOT NULL,
  tree_version VARCHAR(16) NOT NULL,
  node_code VARCHAR(64) NOT NULL,
  parent_id BINARY(16) NULL REFERENCES ref_hom_nodes(id),
  display VARCHAR(256) NOT NULL,
  description TEXT NULL,

  retired_at DATETIME(6) NULL,
  successor_node_id BINARY(16) NULL REFERENCES ref_hom_nodes(id),

  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

  UNIQUE KEY uq_hom_nodes_tree_code_version (tree_id, tree_version, node_code),
  INDEX ix_hom_nodes_parent (parent_id),
  INDEX ix_hom_nodes_retirement (retired_at, successor_node_id)
);
```

Migration: existing rows get generated `id` BINARY(16); all FKs (`ref_hom_mapping`, `access_grant_hom_nodes` from D10, future CSA bindings) re-point to `id`. Queries that need "current or successor" use `COALESCE(ref_hom_nodes.id, ref_hom_nodes.successor_node_id)` chain.

### D18 — `agents` satellite + `agent_sessions`

```sql
-- persons satellite (Data Vault 2.0 pattern, same shape as patients / practitioners)
CREATE TABLE agents (
  person_id BINARY(16) PRIMARY KEY REFERENCES persons(id),
  agent_type VARCHAR(64) NOT NULL,          -- 'health-os-core' / 'task-runner' / ...
  model_version VARCHAR(64) NOT NULL,
  capabilities JSON NULL,                   -- declared capabilities for policy scoping
  tenant_id BINARY(16) NULL REFERENCES ref_organizations(id),

  activated_at DATETIME(6) NOT NULL,
  deactivated_at DATETIME(6) NULL,

  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

  INDEX ix_agents_type_active (agent_type, deactivated_at),
  INDEX ix_agents_tenant (tenant_id, deactivated_at)
);

CREATE TABLE agent_sessions (
  id BINARY(16) PRIMARY KEY,
  agent_id BINARY(16) NOT NULL REFERENCES agents(person_id),
  patient_id BINARY(16) NULL REFERENCES patients(id),

  started_at DATETIME(6) NOT NULL,
  ended_at DATETIME(6) NULL,

  context JSON NULL,                        -- initial context, tool list, etc.
  summary TEXT NULL,                        -- post-session summary (agent-authored)

  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

  INDEX ix_agent_sessions_agent (agent_id, started_at DESC),
  INDEX ix_agent_sessions_patient (patient_id, started_at DESC)
);
```

Agent-authored tasks (D12), impressions (D13), compositions (D15) reference `persons.id` with `author_table='agents'` / `performer_table='agents'`. PDP (D9) evaluates the agent through the same engine as any other grantee.

### D19 — `ref_reconciliation_rules`

```sql
CREATE TABLE ref_reconciliation_rules (
  id BINARY(16) PRIMARY KEY,
  metric_code VARCHAR(64) NOT NULL,
  metric_system VARCHAR(64) NOT NULL,

  priority_chain JSON NOT NULL,             -- ordered ["oura", "apple_health", "fitbit"]
  fallback_strategy VARCHAR(32) NOT NULL,   -- 'most_recent' / 'weighted_avg' / 'user_preference'
  strategy_params JSON NULL,                -- per-strategy config

  applies_org_id BINARY(16) NULL REFERENCES ref_organizations(id),  -- NULL = global default

  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

  UNIQUE KEY uq_reconciliation_metric_org (metric_code, metric_system, applies_org_id)
);
```

Patient-level override: `person_preferences` carries per-metric preferred source; gold-tier reconcile logic checks person preference first, then org rule, then global default.

### D20 — Pattern (no table)

Transitive consent on derived data. See [design-patterns.md](design-patterns.md) — every derivation carries `source_table` + `source_id`; PDP dereferences on read; cascade-delete purges structurally.

## Scoping pass pending

Phasing for all design additions (D1–D20, CSAs 1–47) is deliberately deferred to a single
scoping pass after design is complete. Design proposals live in [design-queue.md](design-queue.md);
phasing decisions will land in [scoping.md](scoping.md).
