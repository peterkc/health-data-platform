# Scoping Pass

**Status**: Locked 2026-04-16 (revisable as partners land and telemetry arrives)
**Purpose**: Assign each locked decision and CSA proposal to a phase (M3 MVP / M4 next milestone / Series A / scale events) with cost-to-defer analysis and promotion triggers
**Audience**: Prioritization decisions; engineers for "is this in scope for M3?"
**Companion to**: [design-queue.md](design-queue.md) (47 CSA proposals), [decisions.md](decisions.md) (D1-D28 locked), [open-questions.md](open-questions.md) (OQ-1-OQ-22 resolved), [database-substrate.md](database-substrate.md) (Postgres 18 foundation)

## How to read this file

- **Phase 0 (M3 MVP)** lists every item that ships in the first build. Default rule: items where cost-to-defer compounds (audit, timestamps, provenance, coded-value semantics) ship now.
- **Phase 1 (M4 Platform Inflection)** lists items activated by SMART on FHIR and outbound API. Default rule: items where third-party integration makes them load-bearing.
- **Phase 2 (Series A)** lists items gated on funded engineering capacity and broader vertical pivots. Default rule: items with bounded defer cost and clear triggers.
- **Phase 3+ (Scale events)** lists items triggered by specific observable events (volume, partner requirement, measurement cliff). Default rule: measure-first.
- **Pending team alignment** lists items awaiting team sign-off before phase lock.

## Inputs to the scoping pass

- **Locked design decisions**: D1-D28 (see [decisions.md](decisions.md))
- **Design proposals**: CSA-1 through CSA-47 (see [design-queue.md](design-queue.md))
- **Resolved open questions**: OQ-1 through OQ-22 (see [open-questions.md](open-questions.md))
- **Frontier questions resolved**: FQ-2 (D18), FQ-3 (D19), FQ-4 (D17), FQ-5 (D20)
- **External constraints**: M3 = lossless foundation, M4 = platform inflection (SMART on FHIR + outbound API), Series A = scale & compliance, Scale = partner-driven
- **Platform context**: [platform-malleability.md](platform-malleability.md) pivot catalog, [vertical-billing.md](vertical-billing.md) as reusable template

## Scoping framework

Each design item answered along three axes:

| Axis                  | Question                                                                  |
| --------------------- | ------------------------------------------------------------------------- |
| Cost to add now       | DDL lines, migration effort, cross-table impact                           |
| Cost of deferring     | Compounding (lost data forever) vs bounded (can add later without regret) |
| Trigger for later add | Specific observable event that promotes "later" to "now"                  |

**Default rules**:

- Items where **cost-to-defer compounds** (audit, history, provenance, semantic fidelity) → ship M3
- Items with **bounded defer cost + clear trigger** (analytics tier, volume aggregation, optional sub-types) → defer with trigger documented
- Items that are **cheap column additions today but expensive migrations later** (CSA-2, CSA-5, CSA-6, CSA-46) → ship M3 even if utility is future

## Phase definitions

| Phase       | Name                | Gate                                                            |
| ----------- | ------------------- | --------------------------------------------------------------- |
| M3          | MVP foundation      | Current — design locked, substrate locked (D28), ready to build |
| M4          | Platform inflection | SMART on FHIR + outbound FHIR API + CDS Hooks ship              |
| Series A    | Scale & compliance  | Funded team, broader vertical pivots active                     |
| Scale event | Triggered           | Specific observable event (volume, partner, measurement cliff)  |

______________________________________________________________________

## Phase 0 (M3 MVP) — ships now

Foundation that any future pivot builds on. Split into **table DDL**, **pattern ships** (no DDL, but architectural shape), and **cheap additive columns** (adding later = migration pain).

### Identity foundation (7 tables)

| Item                 | Source   | Rationale                                                                    |
| -------------------- | -------- | ---------------------------------------------------------------------------- |
| `persons`            | D1, D16  | Root hub — every FK eventually traces here. Irreplaceable.                   |
| `org_roles`          | D1       | Role satellite — patient/practitioner/staff identities.                      |
| `patients`           | D1       | Role satellite — clinical context per org.                                   |
| `practitioners`      | D1       | Role satellite — licensed clinician identity.                                |
| `person_identifiers` | D16      | Source IDs (Oura UUID, Quest MRN, Epic FHIR ID) + use + verified_at (CSA-4). |
| `person_preferences` | D16      | Communication channel, language, timezone, units.                            |
| `ref_organizations`  | registry | Org registry — patient_id + org_id composites need this.                     |

### Clinical core — D7 silver split (6 tables)

| Item             | Source | Rationale                                                        |
| ---------------- | ------ | ---------------------------------------------------------------- |
| `observations`   | D7     | Renamed from `health_records`; houses vitals, labs, assessments. |
| `conditions`     | D7     | First-class table (SNOMED / ICD-10-CM); state machine.           |
| `medications`    | D7     | First-class table (RxNorm / NDC); status lifecycle.              |
| `allergies`      | D7     | First-class table; criticality + verification.                   |
| `immunizations`  | D7     | First-class table (CVX); status + occurrence.                    |
| `family_history` | D7     | First-class table; relationship-keyed.                           |

### Agent-first primary output (3 tables) — D13

| Item                           | Source | Rationale                                                           |
| ------------------------------ | ------ | ------------------------------------------------------------------- |
| `clinical_impressions`         | D13    | AI agent's primary clinical output shape (FHIR ClinicalImpression). |
| `clinical_impression_findings` | D13    | Ranked findings with `basis_references` pointing to sources.        |
| `clinical_impression_problems` | D13    | Associated condition/problem linkage.                               |

### Documents + care artifacts (5 tables)

| Item              | Source | Rationale                                                        |
| ----------------- | ------ | ---------------------------------------------------------------- |
| `documents`       | D3     | S3 reference + content-addressed hash + soft delete. Foundation. |
| `care_plans`      | D4     | Authored artifacts with rich relationships; not source-ingested. |
| `goals`           | D4     | Patient goal tracking.                                           |
| `journal_entries` | core   | Patient self-entered longitudinal journal.                       |
| `notes`           | core   | Practitioner / agent notes attached to resources.                |

### Consent + authorization (8 tables + 1 policy store)

| Item                      | Source | Rationale                                                               |
| ------------------------- | ------ | ----------------------------------------------------------------------- |
| `access_grants`           | D10    | Consent root; sources JSON NULL=all, array=filter.                      |
| `access_grant_sources`    | D10    | Child table — PDP query surface.                                        |
| `access_grant_categories` | D10    | Child table — PDP query surface.                                        |
| `access_grant_hom_nodes`  | D10    | Child table — PDP query surface.                                        |
| `policy_rules`            | D9     | XACML PAP — predicate + effect + obligations + jurisdiction.            |
| `sensitive_categories`    | D9 PIP | 42 CFR Part 2 + state-level sensitive classification.                   |
| `ref_hom_nodes`           | D17    | Surrogate PK + tree_version + retired_at + successor chain.             |
| `access_log`              | CSA-1  | HIPAA audit — every PDP decision logged. **Compounding cost-to-defer.** |
| OpenFGA PDP on Postgres   | D22    | Static policies → type definitions; dynamic grants → tuples.            |

### Agent identity (2 tables) — D18

| Item             | Source | Rationale                                                            |
| ---------------- | ------ | -------------------------------------------------------------------- |
| `agents`         | D18    | Satellite on persons; `agent_type`, `model_version`, `capabilities`. |
| `agent_sessions` | D18    | Per-conversation trace; referenced by `access_log`.                  |

### Embeddings (1 table) — D5

| Item                       | Source | Rationale                                                      |
| -------------------------- | ------ | -------------------------------------------------------------- |
| `health_record_embeddings` | D5     | Separate table for multi-model support; pgvector HNSW+IVFFlat. |

### Source adapter infrastructure (1 table) — D6

| Item                  | Source | Rationale                                                  |
| --------------------- | ------ | ---------------------------------------------------------- |
| `ref_source_adapters` | D6     | Full registry — every source Health OS ingests from. Core. |

### Encounters (1 table) — D2

| Item         | Source | Rationale                                                           |
| ------------ | ------ | ------------------------------------------------------------------- |
| `encounters` | D2     | Inline `location_name` + `location_type`; split trigger documented. |

### Compositions (4 tables) — D15

| Item                          | Source | Rationale                                         |
| ----------------------------- | ------ | ------------------------------------------------- |
| `compositions`                | D15    | Document structure wrapper (FHIR Composition).    |
| `composition_authors`         | D15    | Polymorphic M:N — practitioner / agent / patient. |
| `composition_sections`        | D15    | Recursive via `parent_section_id`.                |
| `composition_section_entries` | D15    | Polymorphic `entry_table` + `entry_id`.           |

**Note**: Table shape ships M3. Ingest adapter activation (C-CDA, Epic, openEHR) deferred to M4 per [fhir-surface.md](fhir-surface.md).

### Provenance + audit infrastructure

| Item               | Source          | Rationale                                                         |
| ------------------ | --------------- | ----------------------------------------------------------------- |
| `audit_batches`    | data-plane §6.4 | Postgres audit trigger — batch metadata.                          |
| `audit_changes`    | data-plane §6.4 | Postgres audit trigger — old/new JSONB. Replaces Dolt commit log. |
| `provenance` table | data-plane §6   | Core provenance. PROV-O alignment (CSA-46) additive.              |
| `raw_payloads`     | data-plane §5   | Bronze tier — canonical source payloads with hash.                |
| Outbox pattern     | CSA-45          | `ingest_outbox` table for transactional ingest guarantee.         |

### Cheap additive columns (add now, migration cost compounds)

| Item   | Source | Rationale                                                                       |
| ------ | ------ | ------------------------------------------------------------------------------- |
| CSA-2  | add    | `narrative TEXT NULL` on D7 silver tables. Cheap now, migration later.          |
| CSA-4  | add    | `patient_identifiers.use` + `verified_at`. Merged into person_identifiers.      |
| CSA-5  | add    | `recorded_at` + `asserted_at` on `observations`. **Timestamps never backfill.** |
| CSA-6  | D14    | `code_text` column on all coded silver tables. Migration script exists.         |
| CSA-13 | add    | `observation_type` VARCHAR + `ref_observation_types`. DDL-free sub-type.        |
| CSA-18 | add    | `persons.deceased_at` + `cause_of_death` + `disposition`.                       |
| CSA-46 | add    | `provenance.prov_activity_id` + `prov_agent_id` + `prov_entity_id`.             |

### Compliance-critical primitives (no new tables)

| Item   | Source  | Rationale                                                                                                                                                      |
| ------ | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CSA-47 | add     | Patient data export endpoint (GDPR Art. 20 / HIPAA §164.524). Endpoint-only; uses D7 silver tables + access_grants. **PHR positioning credibility primitive.** |
| D21    | add     | Audience-split errors — extends `access_grants.purpose` enum.                                                                                                  |
| D20    | pattern | Derived data consent through PDP transitive evaluation.                                                                                                        |

### Data plane + API surface (architectural, not DDL)

| Item                            | Source        | Rationale                                                          |
| ------------------------------- | ------------- | ------------------------------------------------------------------ |
| Repository.read() / .write()    | data-plane §1 | All 7 sections locked; production-ready contract.                  |
| Query composition               | data-plane §2 | Postgres UNION VIEW with temporal columns.                         |
| Pagination + cursor             | data-plane §4 | Token-based cursors.                                               |
| Ingest pipeline                 | data-plane §5 | FHIR Subscription + adapter pattern.                               |
| Transactional outbox            | data-plane §6 | At-least-once delivery with dedup.                                 |
| FHIR R4 format adapter          | D26           | STU 4.0.1 — 95%+ US EHR interop.                                   |
| Envelope versioning             | D27           | `metadata.envelope_version: 1` on every response.                  |
| International privacy framework | CSA-40        | `legal_basis` enum + `jurisdiction` — day-one scope per D9.        |
| LRU Tier 1 cache                | D24           | 10k entries / 60s TTL / action-aware key; hit-rate metrics.        |
| Graceful degradation            | D23           | Circuit breaker + TTL-bounded stale-permit; fails-closed on miss.  |
| Batch PDP aggregation           | D25           | Partial-permit on collections, binary on items + `filtered_count`. |

### Substrate (D28 — locked)

| Item                 | Source                | Rationale                                                       |
| -------------------- | --------------------- | --------------------------------------------------------------- |
| PostgreSQL 18 (18.3) | database-substrate.md | uuidv7() PKs, temporal PK/FK, RETURNING OLD/NEW, pgvector, AIO. |

**M3 totals**: ~38 tables, ~12 additive columns, ~10 patterns / API contracts. Data-plane §1-7 locked.

______________________________________________________________________

## Phase 1 (M4) — Platform Inflection

Activated when third-party read integration ships. M4 turns Health OS from aggregator-only into a platform other apps build against.

### Interoperability activation

| Item                                 | Source     | Rationale                                                  |
| ------------------------------------ | ---------- | ---------------------------------------------------------- |
| SMART on FHIR scopes layer           | interop §2 | `patient/*.read`, `user/*.read`, `launch/patient` context. |
| Outbound FHIR read API               | interop §1 | `GET /fhir/Patient/{id}`, `$everything`, Bundle responses. |
| External event subscription registry | interop §4 | Replace direct DB access with subscriptions.               |
| CDS Hooks (patient-view minimal)     | interop §5 | Clinical decision hooks at read path.                      |

### Workflow resources (2 tables) — D11 + D12

| Item           | Source      | Rationale                                                                        |
| -------------- | ----------- | -------------------------------------------------------------------------------- |
| `appointments` | D11, CSA-36 | Canonical scheduling table; ingest + AI-agent-write. Slot-grid + RRULE deferred. |
| `tasks`        | D12, CSA-37 | Workflow overlay; polymorphic `focus_table` + `focus_id`.                        |

### Care continuity (3 tables)

| Item         | Source | Rationale                                                           |
| ------------ | ------ | ------------------------------------------------------------------- |
| `procedures` | CSA-14 | First-class (CPT / ICD-10-PCS / SNOMED CT); post-D7 clean addition. |
| `orders`     | CSA-16 | Lab / imaging / procedure / medication requests. Owns status.       |
| `referrals`  | CSA-27 | Cross-org routing semantics; explicit status.                       |

### Source onboarding (1 table)

| Item                 | Source | Rationale                                                    |
| -------------------- | ------ | ------------------------------------------------------------ |
| `source_connections` | CSA-12 | Per-patient OAuth state per source. Gap G1 confirmed absent. |

### Consent versioning (1 table)

| Item            | Source | Rationale                                                                      |
| --------------- | ------ | ------------------------------------------------------------------------------ |
| `grant_history` | CSA-3  | Append-only grant evolution. Activate when consent changes are audit-relevant. |

### Specialized domains (activation-driven)

| Item                                  | Source | Rationale                                                               |
| ------------------------------------- | ------ | ----------------------------------------------------------------------- |
| `devices`                             | CSA-15 | Durable medical device + alerts. **Trigger: RPM pivot engagement.**     |
| `survey_responses` + `questionnaires` | CSA-17 | Structured PROs. **Trigger: mental health / pediatric / trials pivot.** |

### Composition adapter activation — D15

| Item                          | Source | Rationale                                                               |
| ----------------------------- | ------ | ----------------------------------------------------------------------- |
| C-CDA / Epic / openEHR ingest | D15    | Ingest adapters activate when first Composition-producing source lands. |

______________________________________________________________________

## Phase 2 (Series A) — Scale & Compliance

Scale-readiness + broader vertical pivots + international expansion. Assumes funded engineering team.

### Compliance primitives (3 tables)

| Item                       | Source | Rationale                                                |
| -------------------------- | ------ | -------------------------------------------------------- |
| `advance_directives`       | CSA-29 | DNR, living will, healthcare proxy. Compliance-critical. |
| `consent_documents`        | CSA-34 | Consent-to-treat forms (distinct from access_grants).    |
| `ref_reconciliation_rules` | D19    | Gold-tier conflict resolution per-metric.                |

### Rich data types (5 tables)

| Item                                 | Source | Rationale                                                    |
| ------------------------------------ | ------ | ------------------------------------------------------------ |
| `imaging_studies` + `imaging_series` | CSA-20 | DICOM metadata. S3 blob reference same pattern as documents. |
| `genomic_variants`                   | CSA-23 | VCF-aligned. **Gated on specimens.**                         |
| `specimens`                          | CSA-30 | Lab sample lifecycle; prerequisite for genomics + research.  |
| `waveforms`                          | CSA-21 | Sample rate, leads, channels, annotations, S3 blob ref.      |

### Care coordination (4 tables)

| Item                | Source | Rationale                                  |
| ------------------- | ------ | ------------------------------------------ |
| `care_team`         | CSA-19 | Multi-practitioner teams with HOM binding. |
| `care_team_members` | CSA-19 | Team membership with roles.                |
| `messaging_threads` | CSA-32 | Portal / SMS / voicemail threading.        |
| `messages`          | CSA-32 | Individual message records.                |

### Quality + risk (4 tables)

| Item                            | Source | Rationale                                                   |
| ------------------------------- | ------ | ----------------------------------------------------------- |
| `clinical_alerts` / `care_gaps` | CSA-28 | Derived state from observations + rules (CMS HEDIS / eCQM). |
| `risk_assessments`              | CSA-35 | Structured risk scores (suicide, fall, readmission).        |
| `growth_measurements`           | CSA-26 | Pediatric growth curves. **Trigger: pediatric pivot.**      |
| `developmental_milestones`      | CSA-26 | Pediatric developmental tracking.                           |

### Research (3 tables)

| Item                  | Source | Rationale                                                |
| --------------------- | ------ | -------------------------------------------------------- |
| `research_studies`    | CSA-33 | **Trigger: clinical trials / employer wellness pivot.**  |
| `study_subjects`      | CSA-33 | Study enrollment linkage.                                |
| `program_enrollments` | CSA-33 | Employer wellness program enrollment.                    |
| `adverse_events`      | CSA-25 | Pharmacovigilance. Depends on MedDRA crosswalk (CSA-43). |

### Reference data expansion

| Item   | Source | Rationale                                      |
| ------ | ------ | ---------------------------------------------- |
| CSA-31 | CSA-31 | SNOMED CT + ICD-10-CM + ICD-10-PCS crosswalks. |
| CSA-43 | CSA-43 | MedDRA crosswalk for adverse event coding.     |
| CSA-44 | CSA-44 | WHO ICF crosswalk for functional status.       |

### Analytics tier (separate schema) — D8

| Item                    | Source    | Rationale                                           |
| ----------------------- | --------- | --------------------------------------------------- |
| `omop_cdm` schema + ETL | D8, CSA-9 | OMOP CDM v5.4 analytics; nightly silver → OMOP ETL. |

### Advanced authorization

| Item                           | Source | Rationale                                                 |
| ------------------------------ | ------ | --------------------------------------------------------- |
| Postgres RLS coarse fallback   | D23    | Belt-and-suspenders for PDP outage.                       |
| Break-glass emergency override | D23    | Typed justification + 48hr review + patient notification. |
| Consistency tokens             | D24    | OpenFGA-native; write-path cache bypass.                  |

### International ingest patterns

| Item                          | Source | Rationale                                            |
| ----------------------------- | ------ | ---------------------------------------------------- |
| ISO 13606 / openEHR archetype | CSA-41 | **Trigger: first EU health partner.**                |
| IHE XDS / XCA / PIX / PDQ     | CSA-42 | **Trigger: EU national HIE integration.**            |
| International crosswalks      | CSA-39 | `ref_atc`, `ref_icpc2`, `ref_icd11`, `ref_dmd`.      |
| Push-ingest + `ingest_events` | CSA-22 | **Trigger: IoT / wearables high-frequency partner.** |

______________________________________________________________________

## Phase 3+ (Scale events) — Triggered

Items where the trigger is the scoping decision. Measure first, promote on observable signal.

| Trigger                                                              | Item                       | Source         |
| -------------------------------------------------------------------- | -------------------------- | -------------- |
| Extension JSON on `medications` exceeds utility (N fields / queries) | MedicationRequest split    | CSA-8, D7 note |
| HealthKit 1Hz or similar 86,400 rows/patient/day                     | `stream_windows`           | CSA-24         |
| In-process LRU hit rate < 70% OR p99 exceeds budget                  | Tier 2 Valkey shared cache | D22            |
| Static policies exceed ~20 types                                     | OPA sidecar                | D22            |
| Concrete partner requires R5 FHIR                                    | R5 format adapter          | D26            |
| PDP measurements stable post-MVP                                     | Consistency tokens         | D24            |

______________________________________________________________________

## Pending team alignment

Items requiring team sign-off before phase lock.

| Item                                              | Current phase | Blocker                                    |
| ------------------------------------------------- | ------------- | ------------------------------------------ |
| 42 CFR Part 2 sensitive-category strict-fail      | M3            | Compliance depth — legal review. |
| S3 reference-counting for right-to-delete cascade | M3            | Infra depth — confirm S3 client supports.  |

______________________________________________________________________

## Summary — all items by phase

**M3 MVP (38 tables + 12 column additions + 11 patterns)**:

persons, org_roles, patients, practitioners, person_identifiers, person_preferences, ref_organizations, observations, conditions, medications, allergies, immunizations, family_history, clinical_impressions, clinical_impression_findings, clinical_impression_problems, documents, care_plans, goals, journal_entries, notes, access_grants, access_grant_sources, access_grant_categories, access_grant_hom_nodes, policy_rules, sensitive_categories, ref_hom_nodes, access_log, agents, agent_sessions, health_record_embeddings, ref_source_adapters, encounters, compositions, composition_authors, composition_sections, composition_section_entries, audit_batches, audit_changes, provenance, raw_payloads, ingest_outbox

- CSA-2 narrative, CSA-4 use/verified_at, CSA-5 recorded_at/asserted_at, CSA-6 code_text, CSA-13 observation_type, CSA-18 deceased_at, CSA-46 PROV-O

- Repository contract, FHIR R4 adapter, envelope versioning, CSA-40 international privacy, CSA-1 access_log, CSA-45 outbox, CSA-47 data export endpoint, D20 derived-data pattern, D21 audience-split, D22 OpenFGA PDP, D23 graceful degradation, D24 LRU cache, D25 batch PDP

**M4 Platform Inflection (8 tables + 4 interop surfaces)**: SMART on FHIR, outbound FHIR API, subscription registry, CDS Hooks (patient-view), appointments, tasks, procedures, orders, referrals, source_connections, grant_history, devices (trigger), survey_responses + questionnaires (trigger), Composition ingest adapters

**Series A Scale & Compliance (18 tables)**: advance_directives, consent_documents, ref_reconciliation_rules, imaging_studies, imaging_series, genomic_variants, specimens, waveforms, care_team, care_team_members, messaging_threads, messages, clinical_alerts, risk_assessments, growth_measurements, developmental_milestones, research_studies, study_subjects, program_enrollments, adverse_events, SNOMED/ICD-10 crosswalks (CSA-31), MedDRA (CSA-43), WHO ICF (CSA-44), OMOP schema + ETL (D8), Postgres RLS (D23), break-glass (D23), consistency tokens (D24), ISO 13606/openEHR (CSA-41), IHE (CSA-42), international crosswalks (CSA-39), push-ingest (CSA-22)

**Scale events (6 triggered items)**: MedicationRequest split (CSA-8), stream_windows (CSA-24), Tier 2 cache (D22), OPA sidecar (D22), R5 adapter (D26), consistency tokens (D24)

## How phase assignment was resolved

Every item was evaluated against two questions:

1. **Does cost-to-defer compound?** If yes → M3. Audit log, timestamps, provenance columns, coded-value semantics (`code_text`), international privacy framework, authorization primitives, and identity foundation all fall here.
1. **Is cost-to-defer bounded with a clear trigger?** If yes → defer to M4 / Series A / scale event. OMOP analytics, medication split, stream windows, Valkey cache, R5 adapter, international ingest all fall here.

**M3 is not minimum — it is lossless foundation.** A schema that captures less than the foundation later pays it back in migration pain and data quality debt. Items such as CSA-5 (dual timestamps), CSA-6 (code_text), and CSA-46 (PROV-O alignment) are M3 even though their utility is future, because they are cheap now and impossible to backfill.

**M4 is inflection, not expansion.** Only items activated by third-party integration (SMART on FHIR, outbound API, CDS Hooks, source_connections) ship at M4. Workflow resources (appointments, tasks, procedures, orders, referrals) ride along because they are load-bearing for third-party read flows.

**Series A is scale, not polish.** Funded capacity + vertical activation signals (pediatric, mental health, research, international) drives table activation. OMOP analytics ships here because the ETL can backfill silver data any time.

**Scale events are measured, not guessed.** Each trigger names a concrete observable (hit rate, p99, row count, partner requirement). Items promote when the observable fires.
