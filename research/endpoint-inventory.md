# Endpoint Inventory — Table Requirements

**Status**: Living — updated as new endpoints are designed or tables change
**Purpose**: Map every API endpoint to the SQL tables it requires, exposing schema gaps before implementation.
**Audience**: Engineers planning repository methods; reviewers verifying table coverage against the API surface.
**Companion to**: [table-designs.md](table-designs.md) (DDL for the tables referenced here), [design-queue.md](design-queue.md) (proposals that add new tables), [data-plane.md](data-plane.md) (runtime architecture that serves these endpoints)
**Source**: Thread 04 (API design), SYSTEM.md 1.5-1.6, `docs/api-design.md`

## How to read this file

- Scan the **Gap?** column to find endpoints that need tables not yet designed
- Each section groups endpoints by domain (Readings, Documents, Consent, etc.)
- Query pattern blocks show the post-D7 SQL shape for complex joins (e.g., HOM grouped reads)

## Endpoint → Table Matrix

### Readings & HOM (SYSTEM.md 2.3, Thread 04)

| Endpoint                                                        | Method | Tables Required                                         | Gap? |
| --------------------------------------------------------------- | ------ | ------------------------------------------------------- | ---- |
| `/v1/orgs/{org}/patients/{pid}/readings`                        | GET    | observations                                            | No   |
| `/v1/orgs/{org}/patients/{pid}/readings?code=2093-3`            | GET    | observations                                            | No   |
| `/v1/orgs/{org}/patients/{pid}/hom/{hom}/nodes/{node}/readings` | GET    | observations + 5 others, ref_hom_mapping, ref_hom_nodes | No   |
| `/v1/orgs/{org}/patients/{pid}/hom/schemas`                     | GET    | ref_hom_nodes                                           | No   |
| `/v1/orgs/{org}/patients/{pid}/hom/schemas/{hom}/nodes`         | GET    | ref_hom_nodes, ref_hom_mapping                          | No   |

**D7 note**: `health_records` was split into 6 FHIR-aligned silver tables. `readings` now targets `observations` (the canonical home for measurements + findings + surveys). Grouped HOM query fans across all 6 via `ref_hom_mapping.target_table`.

**Query pattern post-D7** (HOM grouped, UNION ALL across 6 silver tables):

```sql
-- Resolve the hom node once
WITH matches AS (
  SELECT code, code_system, target_table
  FROM ref_hom_mapping m
  JOIN ref_hom_nodes n ON m.hom_id = n.hom_id AND m.hom_node_id = n.id
  WHERE n.hom_id = ? AND n.code = ?
)
SELECT 'observations' AS src, o.id, o.effective_date, o.code, o.code_display
FROM observations o
WHERE o.patient_id = ? AND o.canonical_id IS NULL
  AND EXISTS (SELECT 1 FROM matches WHERE target_table='observations'
              AND matches.code = o.code AND matches.code_system = o.code_system)
UNION ALL
SELECT 'conditions' AS src, c.id, c.onset_date AS effective_date, c.code, c.code_display
FROM conditions c
WHERE c.patient_id = ?
  AND EXISTS (SELECT 1 FROM matches WHERE target_table='conditions'
              AND matches.code = c.code AND matches.code_system = c.code_system)
UNION ALL
SELECT 'medications', ... FROM medications WHERE ...  -- etc.
ORDER BY effective_date DESC LIMIT 51
```

For production, consider a materialized `patient_timeline_view` (scoping decision — perf vs freshness trade-off; see scoping.md).

### Clinical Records (Thread 04 — `/records`)

| Endpoint                                                          | Method | Tables Required                                                                      | Gap? |
| ----------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------ | ---- |
| `/v1/orgs/{org}/patients/{pid}/records`                           | GET    | observations + conditions + medications + allergies + immunizations + family_history | No   |
| `/v1/orgs/{org}/patients/{pid}/records?type=condition,medication` | GET    | conditions + medications (table selection by type filter)                            | No   |
| `/v1/orgs/{org}/patients/{pid}/records?type=family_history`       | GET    | family_history (dedicated table, structured lineage fields)                          | No   |

**D7 note**: `/records` now selects tables by the `type` query parameter (1-to-1 mapping to the 6 silver tables). Absent filter → UNION ALL across all 6, grouped by source in response envelope. Each table has its own structured shape (conditions have clinical_status; medications have dose + route; allergies have reactions[]; immunizations have dose_number + series; family_history has relationship + age_at_onset).

**Response shape** (grouped by table source when no single type filter):

```
{ data: { observation: [...], condition: [...], medication: [...], allergy: [...],
          immunization: [...], family_history: [...] },
  meta: { counts: { observation: 42, condition: 6, medication: 8, ... } } }
```

### Timeline (Thread 04 — `/timeline`)

| Endpoint                                                                  | Method | Tables Required                                        | Gap?    |
| ------------------------------------------------------------------------- | ------ | ------------------------------------------------------ | ------- |
| `/v1/orgs/{org}/patients/{pid}/timeline`                                  | GET    | health_records, reports, **encounters**, **documents** | **YES** |
| `/v1/orgs/{org}/patients/{pid}/timeline?entry_type=lab_result,medication` | GET    | health_records                                         | No      |

**Gap**: Timeline mixes health_records with encounters and documents. Need `encounters`
and `documents` tables to populate the full chronological feed.

### Documents (Thread 04 — `/documents`)

| Endpoint                                                 | Method | Tables Required    | Gap?    |
| -------------------------------------------------------- | ------ | ------------------ | ------- |
| `/v1/orgs/{org}/patients/{pid}/documents`                | GET    | **documents**      | **YES** |
| `/v1/orgs/{org}/patients/{pid}/documents/{did}`          | GET    | **documents**      | **YES** |
| `/v1/orgs/{org}/patients/{pid}/documents/{did}/download` | GET    | **documents** + S3 | **YES** |

**Design**: `documents` table stores metadata + S3 path. Download endpoint generates
pre-signed URL from `storage_path`. Follows `raw_payloads.payload_ref` pattern.

### Ingest (Thread 04 — `/ingest`)

| Endpoint                | Method | Tables Required                                       | Gap?    |
| ----------------------- | ------ | ----------------------------------------------------- | ------- |
| `/v1/orgs/{org}/ingest` | POST   | raw_payloads, health_records, **ref_source_adapters** | Partial |

**Gap**: `ref_source_adapters` needed for adapter routing. Currently hardcoded in code.

### Identity & Auth (ADR-2005, ADR-2006)

| Endpoint                        | Method | Tables Required                                     | Gap?        |
| ------------------------------- | ------ | --------------------------------------------------- | ----------- |
| `/v1/orgs/{org}/members`        | GET    | **persons**, **org_roles**, **ref_organizations**   | **YES**     |
| `/v1/orgs/{org}/patients/{pid}` | GET    | patients, patient_org_access, **ref_organizations** | **Partial** |
| `/v1/orgs/{org}/practitioners`  | GET    | **practitioners**, **persons**                      | **YES**     |
| `/v1/patients/{pid}/grants`     | GET    | **access_grants**                                   | **YES**     |
| `/v1/patients/{pid}/grants`     | POST   | **access_grants**                                   | **YES**     |

### Journal & Notes (ADR-3005, Thread 03)

| Endpoint                                            | Method | Tables Required     | Gap?    |
| --------------------------------------------------- | ------ | ------------------- | ------- |
| `/v1/orgs/{org}/patients/{pid}/journal`             | GET    | **journal_entries** | **YES** |
| `/v1/orgs/{org}/patients/{pid}/journal/{eid}/notes` | POST   | **notes**           | **YES** |

### Care Plans (Brief — "action plans")

| Endpoint                                                | Method | Tables Required | Gap?    |
| ------------------------------------------------------- | ------ | --------------- | ------- |
| `/v1/orgs/{org}/patients/{pid}/care-plans`              | GET    | **care_plans**  | **YES** |
| `/v1/orgs/{org}/patients/{pid}/care-plans/{cpid}/goals` | GET    | **goals**       | **YES** |

### AI Agent (SYSTEM.md 1.6)

| Endpoint            | Method   | Tables Required                                                   | Gap?        |
| ------------------- | -------- | ----------------------------------------------------------------- | ----------- |
| `/v1/agent/ask`     | POST     | health_records, ref_hom_mapping, ref_hom_nodes, **access_grants** | **Partial** |
| `/v1/agent/tools/*` | Internal | Same tables as Developer API (same repository layer)              | Same gaps   |

**Agent tools** (from SYSTEM.md): `get_readings()`, `get_timeline()`, `get_hom_grouped()`, `search_records()` — all use the same tables as the Developer API.

### Admin / HOM Management

| Endpoint                               | Method   | Tables Required       | Gap?    |
| -------------------------------------- | -------- | --------------------- | ------- |
| `/v1/admin/hom/schemas`                | GET/POST | ref_hom_nodes         | No      |
| `/v1/admin/hom/schemas/{hom}/mappings` | GET/POST | ref_hom_mapping       | No      |
| `/v1/admin/orgs`                       | GET/POST | **ref_organizations** | **YES** |

## Gap Summary

| Table                       | Endpoints Blocked                    | Priority |
| --------------------------- | ------------------------------------ | -------- |
| `ref_organizations`         | members, admin/orgs, patient detail  | P1       |
| `persons` + `org_roles`     | members, practitioners, grants       | P1       |
| `documents`                 | 3 document endpoints + timeline      | P1       |
| `encounters`                | timeline (full feed)                 | P2       |
| `access_grants`             | consent CRUD, agent authorization    | P2       |
| `practitioners`             | practitioner list, encounter context | P2       |
| `care_plans` + `goals`      | care plan CRUD                       | P2       |
| `journal_entries` + `notes` | journal CRUD                         | P2       |
| `ref_source_adapters`       | ingest routing                       | P3       |

**Endpoint coverage**:

- Total endpoints: ~25
- Fully covered by existing tables: ~12
- Blocked or partially blocked: ~13
- Tables needed to close all gaps: 11
