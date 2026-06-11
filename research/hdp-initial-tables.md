# HDP-initial Tables

**Status**: Authored 2026-04-25 for spec `hdp-schema-seed` Phase 1 (FR-103)
**Purpose**: Concrete subset of tables landing in the initial HDP DDL — sets the SC-004 N for `\dt` count assertion
**Companion to**: [table-designs.md](table-designs.md), [database-substrate.md](database-substrate.md), [decisions.md](decisions.md)

## How to read this file

- The list below groups tables by destination SQL file (`packages/hdp-canonical/sql/`, `packages/hdp-hitl/sql/`, `verticals/home-health/hh-oasis/sql/`).
- Within each file, tables are listed in **FK dependency order**. Phase 2 SQL extraction must preserve this order so a single `for f in sorted(glob): cur.execute(...)` migration loop applies cleanly.
- "Source" cites the research artifact carrying the canonical CREATE TABLE shape (or the design decision that authorizes a fresh authoring of an HDP-specific table).
- "FKs" lists the tables this row depends on — within the same SQL file or upstream files. Tables with no FKs land first in their group.

**Total table count**: **30** (this is the SC-004 / AC-004 N).

Breakdown: 7 reference + 4 identity + 8 silver + 6 operational + 2 HITL (new) + 3 OASIS (new) = 30. Three operational tables (`access_grants`, `access_log`, `source_connections`) are explicitly deferred — their canonical CREATE TABLE shapes are not in the migrated research, and Decision 3 of `vault/specs/hdp-schema-seed/design.md` defers `access_grants` audit to consent-layer work. They will land in a follow-up DDL pass.

## Tables by destination

### `packages/hdp-canonical/sql/10-reference.sql` — 7 tables (no FKs to user data)

| # | Table | Source | FKs | Notes |
|---|-------|--------|-----|-------|
| 1 | `ref_hom_nodes` | `table-designs.md` §D17 | self (`successor_node_id`) | Hierarchical body-systems tree; D17 single-PK refactor; seed populates ≥10 rows top-down |
| 2 | `ref_source_adapters` | `table-designs.md` §D6 | none | D6 locked registry; seed ≥4 rows (fhir, csv, oura, biomarkers) |
| 3 | `ref_organizations` | `table-designs.md` §214 (DDL Insertion Order, NEW) | none | NEW per Phase 0 D-list; seed ≥1 row |
| 4 | `ref_analyte_conversions` | `table-designs.md` §214 | none | Unit conversion lookup; per ADR-2010 |
| 5 | `ref_record_type_schemas` | `table-designs.md` §D7 (extensibility contract) | none | D7.1 contract for canonical record types |
| 6 | `ref_drug_classes` | `table-designs.md` §214 | none | Drug class lookup |
| 7 | `loinc_crosswalk` | `table-designs.md` §214 | none | LOINC code mapping; seed ≥5 rows |

### `packages/hdp-canonical/sql/20-identity.sql` — 4 tables

| # | Table | Source | FKs | Notes |
|---|-------|--------|-----|-------|
| 8 | `persons` | `table-designs.md` §D16 (rename trail), §214 | none | NEW root identity table |
| 9 | `patients` | `table-designs.md` §214 | `persons` | Patient-as-person specialization |
| 10 | `person_identifiers` | `table-designs.md` §D16 (renamed from `patient_identifiers`) | `persons` | External identifier mapping |
| 11 | `patient_org_access` | `table-designs.md` §214 | `patients`, `ref_organizations` | Org-scoped access binding |

### `packages/hdp-canonical/sql/30-silver.sql` — 8 tables (FHIR-aligned silver)

All silver tables FK `patients` (subject) and `ref_record_type_schemas` (extensibility); medications additionally FK `ref_drug_classes`; observations additionally FK `loinc_crosswalk` and `ref_hom_nodes`.

| # | Table | Source | FKs | Notes |
|---|-------|--------|-----|-------|
| 12 | `observations` | `table-designs.md` §D7 / §348 | `patients`, `ref_record_type_schemas`, `loinc_crosswalk`, `ref_hom_nodes` | Replaces legacy `health_records` |
| 13 | `conditions` | `table-designs.md` §D7 / §384 | `patients`, `ref_record_type_schemas` | FHIR Condition |
| 14 | `medications` | `table-designs.md` §D7 / §416 | `patients`, `ref_drug_classes`, `ref_record_type_schemas` | FHIR Medication{Statement,Request} |
| 15 | `allergies` | `table-designs.md` §D7 / §450 | `patients`, `ref_record_type_schemas` | FHIR AllergyIntolerance |
| 16 | `immunizations` | `table-designs.md` §D7 / §478 | `patients`, `ref_record_type_schemas` | FHIR Immunization |
| 17 | `family_history` | `table-designs.md` §D7 / §508 | `patients`, `ref_record_type_schemas` | FHIR FamilyMemberHistory |
| 18 | `procedures` | `table-designs.md` §D14 (CSA-14), `decisions.md` §D14 | `patients`, `ref_record_type_schemas` | FHIR Procedure |
| 19 | `orders` | `table-designs.md` §D14 (CSA-16), `decisions.md` §D14 | `patients`, `ref_record_type_schemas` | FHIR ServiceRequest / MedicationRequest umbrella |

### `packages/hdp-canonical/sql/40-operational.sql` — 6 tables

The operational set fans out below FK dependency: `raw_payloads` is root; `provenance` and `documents` reference upstream tables (provenance optionally points at raw_payloads; documents references raw_payloads); `audit_batches` is root; `audit_changes` references `audit_batches`. `policy_rules` is scoped per spec design `Decision 3` (audit attached only to `policy_rules` in this spec).

| # | Table | Source | FKs | Notes |
|---|-------|--------|-----|-------|
| 20 | `raw_payloads` | `table-designs.md` §214 (Bronze) | none (root) | Bronze layer holding raw ingest |
| 21 | `provenance` | `table-designs.md` §214 | `patients` (subject), `raw_payloads` (optional) | Ingestion-level traceability |
| 22 | `documents` | `table-designs.md` §214 | `raw_payloads`, `patients` (optional) | Pointer table for document objects (S3-style); FHIR DocumentReference analogue |
| 23 | `audit_batches` | `database-substrate.md` §83 | none (root) | Batch-level audit context |
| 24 | `audit_changes` | `database-substrate.md` §90 | `audit_batches` (NULLable per Decision 3) | Row-level OLD/NEW JSONB; NULLable batch_id |
| 25 | `policy_rules` | `table-designs.md` §D9 / §577, `decisions.md` §D9 | none (root) | XACML PAP storage; audit trigger attaches here per Decision 3 |

> Note: `access_grants`, `access_log`, `source_connections` referenced in spec design.md §40-operational.sql are **deferred** out of this initial subset — their canonical CREATE TABLE shapes are not yet authoritatively captured in the migrated research, and Decision 3 of the spec defers `access_grants` audit to consent-layer work where grant data arrives. They land in a follow-up DDL pass when the consent / source-connection components ship. This deferral is a SCHEMA-OMISSION decision (table not present at all), distinct from Decision 3's audit-attachment scope (which speaks to which tables get audit triggers among those that ARE present).

### `packages/hdp-hitl/sql/50-hitl.sql` — 2 tables (new — authored fresh per spec design.md §HITL state machine)

| # | Table | Source | FKs | Notes |
|---|-------|--------|-----|-------|
| 26 | `chart_items` | `design.md` §HITL state machine | `oasis_items` (FK to ref), `visits` (FK to hh-oasis below) | State machine per Convention #9 |
| 27 | `chart_state_transitions` | `design.md` §HITL state machine | `chart_items` | Transition log (FR-012) |

### `verticals/home-health/hh-oasis/sql/60-oasis.sql` — 3 tables (new — authored fresh per spec design.md §OASIS catalog)

| # | Table | Source | FKs | Notes |
|---|-------|--------|-----|-------|
| 28 | `oasis_items` | `design.md` §OASIS catalog | none (root) | Canonical OASIS-E2 catalog |
| 29 | `episodes` | `design.md` §OASIS catalog | `patients` | 60-day PDGM payment period |
| 30 | `visits` | `design.md` §OASIS catalog | `episodes` | Per-visit instance |

## Decisions and rationale

**SC-004 N = 30**. The Phase 2 verifier runs:

```
psql ... -c "\dt" | tail -n +4 | wc -l   # expects: 30
```

Numbering 1..30 above is dependency-order index. Every row is required by an explicit Phase 2 task: `extract-reference-tables` enumerates 7; `extract-identity-tables` enumerates 4; `extract-silver-tables` enumerates 8; `extract-operational-tables` enumerates 9 in design.md §40-operational.sql, of which 6 land here (deferral note above lists the 3 that don't); `author-hitl-sql` authors 2; `author-oasis-sql` authors 3. Total: 7 + 4 + 8 + 6 + 2 + 3 = 30.

The spec's design.md §40-operational.sql Component Design table lists 9 operational tables. This file's 40-operational.sql section ships 6; the remaining 3 are deferred above with rationale. That deferral is the only deviation from the design.md surface count.

**Why deferred tables matter**:

- `access_grants`, `access_log`, `source_connections` deferred per Decision 3 ("`access_grants` audit deferred to consent-layer work") and because their canonical CREATE TABLE shapes are not in the migrated research yet. Adding them here without authoritative shape would invite drift; they ship cleanly in the follow-up consent + source-connection spec.
- D7 silver is fully covered (8 tables) — the design's "8 silver tables" maps exactly to the rows above (observations, conditions, medications, allergies, immunizations, family_history, procedures, orders).
- HITL and OASIS tables are authored fresh in this spec — their FK pointers (chart_items → oasis_items / visits; visits → episodes → patients) span all three SQL trees and the migration's filename-sort order (00-, 01-, 10-, 20-, 30-, 40-, 50-, 60-, 99-) carries dependency correctness.

## FK dependency at a glance (compressed)

```
ref_*  (no FK)                                    [10-reference]
   ↑
persons -> patients -> patient_org_access         [20-identity]
                  ↘     person_identifiers
                   ↘
                    ↘ silver/* (D7 + procedures + orders)   [30-silver]
                       ↘
                        ↘ raw_payloads -> provenance, documents   [40-operational]
                           ↘ audit_batches -> audit_changes
                              policy_rules
                                 ↘ chart_items <- chart_state_transitions   [50-hitl]
                                                ↑
                                         oasis_items, episodes -> visits   [60-oasis]
```

Filename-sort order across all three trees:

```
00-extensions.sql
01-functions.sql
10-reference.sql
20-identity.sql
30-silver.sql
40-operational.sql
50-hitl.sql
60-oasis.sql
99-triggers.sql
```

Phase 2 verifier asserts the migration applies this set in this order and the resulting `\dt` count is 30.
