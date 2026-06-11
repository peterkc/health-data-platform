# Schema Diagrams — 3 Zoom Levels

**Status**: Current (2026-04-15) — reflects D1-D20 full design pass
**Purpose**: Visual navigation from tier overview down to per-table FK relationships
**Audience**: Engineers exploring the schema; architecture walkthroughs
**Companion to**: [table-designs.md](table-designs.md), [decisions.md](decisions.md), [design-patterns.md](design-patterns.md)

## How to read this file

- Start at L0 for the 30-second mental model, then drill into the cluster you care about
- L2 cluster ERDs (2.1-2.10) show FK relationships per subsystem; L2 cross-cutting flows (2.11-2.15) show table interactions in workflows
- For column-level detail, jump to [table-designs.md](table-designs.md) (L3)
- Convention: plain ASCII only — renders everywhere, no tooling dependency, diffs cleanly

## Zoom levels

| Level  | Scope               | Use when                                              |
| ------ | ------------------- | ----------------------------------------------------- |
| **L0** | Tier overview       | You want the 30-second mental model                   |
| **L1** | Domain clusters     | You want to see which tables belong to what subsystem |
| **L2** | Per-cluster ERD     | You need FK relationships for a specific subsystem    |
| **L2** | Cross-cutting flows | You need to see how tables interact in a workflow     |
| **L3** | DDL (SQL)           | You need column-level detail → see `table-designs.md` |

## Table of contents

**Per-cluster ERDs**

- [L0 — Tier overview](#l0--tier-overview)
- [L1 — Domain clusters](#l1--domain-clusters)
- [L2.1 — Identity + Actors](#l21--identity--actors)
- [L2.2 — Authorization + Policy](#l22--authorization--policy)
- [L2.3 — Clinical data: core (D7)](#l23--clinical-data-core-d7)
- [L2.4 — Clinical data: adjunct](#l24--clinical-data-adjunct)
- [L2.5 — Documents + Compositions](#l25--documents--compositions)
- [L2.6 — Encounters](#l26--encounters)
- [L2.7 — Care plans + Goals](#l27--care-plans--goals)
- [L2.8 — Workflow (Appointments + Tasks)](#l28--workflow-appointments--tasks)
- [L2.9 — Journal + Notes](#l29--journal--notes)
- [L2.10 — Reference + Raw](#l210--reference--raw)

**Cross-cutting flows**

- [L2.11 — Ingest flow](#l211--ingest-flow)
- [L2.12 — HOM query flow](#l212--hom-query-flow)
- [L2.13 — AI agent flow](#l213--ai-agent-flow)
- [L2.14 — Authorization decision flow (PDP/PEP)](#l214--authorization-decision-flow-pdppep)
- [L2.15 — Agent-authored output flow](#l215--agent-authored-output-flow)
- [Diagram conventions](#diagram-conventions)

## L0 — Tier overview

```
+-------------------------+       +-------------------------+       +---------------+
| REFERENCE (9)           |       | IDENTITY + ACTORS (12)  |       | GOLD (1)      |
|                         |       |                         |       |               |
| ref_hom_nodes           |       | persons (hub)           |       | daily_summary |
| ref_hom_mapping         |       |  +- patients            |       +---------------+
| loinc_crosswalk         |       |  +- practitioners       |
| ref_source_adapters     |       |  +- agents          [D18]       +---------------+
| ref_drug_classes        |       |  +- org_roles           |       | OPS (1)       |
| ref_record_type_schemas |       | ref_organizations       |       |               |
| ref_analyte_conversions |       | person_identifiers  [D16]       | data_quality  |
| ref_reconciliation  [D19]       | person_preferences  [D16]       +---------------+
|                         |       | patient_org_access      |
+-----------+-------------+       | patient_relationships   |
            | lookup             | source_connections       |
            v                     | agent_sessions       [D18]
+-------------------------+       +---+---------------------+
| BRONZE (1)              |           |
|                         |           | grants + policies gate all reads
| raw_payloads (hash UK)  |           v
+-----------+-------------+       +-------------------------+
            | ingested into       | AUTHORIZATION + POLICY (7)
            v                     |                         |
+-------------------------+       | access_grants           |
| SILVER — CORE (6, D7)   |       |  +- access_grant_sources   [D10]
|                         |       |  +- access_grant_categories[D10]
| observations            |       |  +- access_grant_hom_nodes [D10]
| conditions              |<--PDP-+ policy_rules         [D9]
| medications             | reads | [CSA-1 access_log]      |
| allergies               |       | [CSA-3 grant_history]   |
| immunizations           |       +-------------------------+
| family_history          |
+-----------+-------------+       +-------------------------+
            | used by             | SILVER — CLINICAL ADJUNCT (8)
            v                     |                         |
+-------------------------+       | observation_components  |
| SILVER — DOCUMENTS (5)  |       | clinical_entities       |
|                         |       | reports                 |
| documents               |       | provenance              |
| compositions       [D15]|       | health_record_embeddings|
| composition_authors[D15]|       | clinical_impressions [D13]
| composition_sections[D15]       | clinical_impression_findings [D13]
| composition_section_entries[D15]| clinical_impression_problems [D13]
+-------------------------+       +-------------------------+

+-------------------------+       +-------------------------+       +-----------+
| SILVER — ENCOUNTERS +   |       | SILVER — WORKFLOW (2)   |       | SILVER —  |
|          CARE (5)       |       |                         |       | JOURNAL(2)|
|                         |       | appointments       [D11]|       |           |
| encounters              |       | tasks              [D12]|       | journal_  |
| care_plans              |       +-------------------------+       |   entries |
| goals                   |                                          | notes     |
+-------------------------+                                          +-----------+

Total: 55 tables across 10 clusters + 1 gold + 1 ops.
[D8] OMOP tier lives in a separate schema (omop_cdm), not shown — fed by nightly ETL from silver.
Bracketed decisions [D8..D20] / [CSA-N] = landed in decisions.md or designed in queue.
```

## L1 — Domain clusters

```
+===============================+         +===============================+
|    IDENTITY + ACTORS (L2.1)   |<--grantee    | AUTHORIZATION + POLICY (L2.2)|
|                               |    ----> |                               |
|  persons (hub)                |         |  access_grants                |
|   +-> patients / practitioners|         |   +-> _sources / _categories  |
|   +-> agents               [D18]        |   +-> _hom_nodes           [D10]
|   +-> org_roles               |         |  policy_rules           [D9]  |
|  ref_organizations            |         |  [CSA-1 access_log]           |
|  person_identifiers   [D16]   |         |  [CSA-3 grant_history]        |
|  person_preferences   [D16]   |         |                               |
|  patient_org_access           |         |  PDP evaluates EVERY read     |
|  patient_relationships        |         |  PEP enforces on every route  |
|  source_connections           |         |  Agent same engine as human   |
|  agent_sessions       [D18]   |         +==============+================+
+===============+===============+                        |
                |                                         | gates reads
       owns / subject of                                  |
                |                                         v
+===============+============================+=============+===============+
|         CLINICAL DATA (L2.3 core + L2.4 adjunct)                          |
|                                                                           |
|  CORE (D7):                           ADJUNCT:                            |
|    observations                         observation_components            |
|    conditions                           clinical_entities (staging)       |
|    medications                          reports (grouped envelope)        |
|    allergies                            provenance (ETL lineage)          |
|    immunizations                        health_record_embeddings          |
|    family_history                       clinical_impressions       [D13]  |
|                                         clinical_impression_findings  [D13]
|                                         clinical_impression_problems [D13]
+=============+==========================+==========+============+=========+
              |                          |          |            |
              v                          v          v            v
+=============+==========+   +===========+======+ +=+==========+ +=+========+
| DOCUMENTS + COMPOSIT.  |   | ENCOUNTERS (L2.6)| | CARE PLANS | | WORKFLOW |
| (L2.5)                 |   |                  | | (L2.7)     | | (L2.8)   |
|                        |   | encounters       | |            | |          |
| documents              |   | inline location  | | care_plans | | appts[D11]
| compositions      [D15]|   | practitioner_id  | | goals      | | tasks[D12]
| composition_authors    |   +==================+ +============+ +==========+
| composition_sections   |
| composition_section_   |   +======================+    +=======================+
|     entries            |   | JOURNAL + NOTES (L2.9)|    | REFERENCE + RAW (L2.10)
+========================+   |                      |    |                       |
                             | journal_entries      |    | raw_payloads          |
                             | notes                |    | ref_* (9 tables)      |
                             +======================+    | ref_reconciliation[D19]
                                                         +=======================+
```

## L2 — Per-cluster ERDs

ERD format: box per table, `(PK)` = primary key, `(FK)` = foreign key, `(UK)` = unique key.
Arrows point from the FK side to the referenced table.

### L2.1 — Identity + Actors

```
                          +--------------------------+
                          | persons (hub, D1)        |
                          +--------------------------+
                          | id (PK)                  |
                          | given_name               |
                          | family_name              |
                          | date_of_birth            |
                          | email                    |
                          | auth_provider_id (UK)    |
                          +-------------+------------+
                                        |
           +---------+---------+--------+--------+---------+---------+
           |         |         |                 |         |         |
           | FK      | FK      | FK              | FK      | FK      | FK
           |         |         |                 |         |         |
           v         v         v                 v         v         v
+----------+---+ +---+------+ +--+-----------+ +-+------+ +---------+-------+ +-+------+
| patients     | | practit. | | org_roles    | | agents | | person_identif. | | person_
|              | |          | |              | |   [D18]| | [D16 rename]    | | prefs
+--------------+ +----------+ +--------------+ +--------+ +-----------------+ | [D16]  |
| id (PK)      | | id (PK)  | | id (PK)      | | person_| | id (PK)         | +--------+
| person_id UK | | person_id| | person_id(FK)| |  id PK | | person_id (FK)  | | id (PK)|
| sex_at_birth | | npi      | | org_id (FK)  | | agent_ | | use             | | person_|
| gender_id    | | specialty| | role         | |  type  | | system          | |  id FK |
| medical_rec_n| | creds    | | permissions  | | model_ | | value           | | unit_  |
| primary_pract| | org_id FK| | granted_at   | |  vers  | | verified_at     | | system |
+----+---------+ +---+------+ +--------------+ | capab. | +-----------------+ | lang   |
     |              |                           | tenant_|                      | timez. |
     |              |                           |  id FK |                      +--------+
     |              |                           | active.|
     |              |                           +--+-----+
     | FK           | FK                           |
     |              |                              | FK
     v              v                              v
+----+-----+  +-----+----+                    +----+---------+
| patient_ |  | patient_ |                    | agent_       |
| org_acc. |  | relation.|                    | sessions[D18]|
+----------+  +----------+                    +--------------+
| id (PK)  |  | id (PK)  |                    | id (PK)      |
| patient_ |  | patient_ |                    | agent_id (FK)|
|  id FK   |  |  id FK   |                    | patient_id FK|
| org_id FK|  | related_ |                    | started_at   |
| access_lv|  |  pid FK  |                    | ended_at     |
| granted_a|  | relation |                    | context JSON |
+----------+  | start_dt |                    | summary      |
              | end_dt   |                    +--------------+
              +----------+

+------------------+
| source_connections|   (CSA-12 — per-patient OAuth state per source)
+------------------+
| id (PK)          |
| patient_id (FK)  |
| adapter_id (FK) ------> ref_source_adapters (L2.10)
| refresh_token    |
| access_token     |
| expires_at       |
| scopes JSON      |
| last_sync_at     |
| sync_status      |
+------------------+

+----------------------+
| ref_organizations    |   (owners for org_roles, practitioners, etc.)
+----------------------+
| id (PK)              |
| name                 |
| slug (UK)            |
| org_type             |
| default_hom_node_id  |   (FK to ref_hom_nodes; single-PK per D17)
| jurisdiction         |
| timezone             |
+----------------------+

Unique keys:
  - persons.auth_provider_id (UK)
  - patients.person_id (UK) — one patient row per person
  - org_roles (person_id, org_id, role) (UK)
  - practitioners (person_id, org_id) (UK)
  - person_preferences (person_id, org_id) (UK)
  - source_connections (patient_id, adapter_id) (UK)
  - agents.person_id (PK — satellite shape)

Data Vault 2.0 pattern (D1): persons is the hub; patients / practitioners / agents /
org_roles are satellites sharing the persons.id foreign key. A single human OR AI agent
always has exactly one persons row; role contexts attach as satellites.
```

### L2.2 — Authorization + Policy

```
+--------------------------+          +-----------------------+
| patients                 |          | persons               |
+--------------------------+          +-----------------------+
| id (PK)                  |          | id (PK) (grantee when |
+-----------+--------------+          |  grantee_type =       |
            |                         |  'practitioner' |     |
            | FK                      |  'agent')             |
            v                         +----------+------------+
+-----------+-------------------------+          |
| access_grants                       |          |
+-------------------------------------+          |
| id (PK)                             |<---------+
| patient_id (FK)                     |  grantee_id
| grantee_id (see note)               |
| grantee_type (practitioner|app|agent)|
| scope (SMART on FHIR string)        |
| categories JSON (NULL = all)        |<---+
| sources JSON (NULL = all)           |<---+-- source-of-truth
| hom_nodes JSON (NULL = all)         |<---+   (PDP queries
| legal_basis (CSA-40)                |    |   child tables)
| jurisdiction (CSA-40)               |    |
| granted_at / expires_at / revoked_at|    |
| granted_by (FK persons)             |    |
| org_id (FK)                         |    |
+------+---------+---------+----------+    |
       |         |         |               |
       | FK      | FK      | FK            | maintained by
       v         v         v               | repository writes
+------+--+ +----+------+ +---+---------+   |
|access_  | |access_    | |access_      |   |
|grant_   | |grant_     | |grant_       |   |
|sources  | |categories | |hom_nodes    |   |
|   [D10] | |      [D10]| |        [D10]|   |
+---------+ +-----------+ +-------------+   |
|grant_id | |grant_id   | |grant_id     |   |
|source_s.| |category   | |hom_node_id  |   |
|(PK pair)| |(PK pair)  | |(PK pair)    |   |
+---------+ +-----------+ +-------------+   |
      ^          ^              ^           |
      |          |              |           |
      +----------+---< PDP reads child tables for index-hit filtering
                                |
                                v
+---------------------+         |
| ref_hom_nodes (L2.10)          |
+---------------------+         |
                                |
                                |
+------------------------------+--+
| policy_rules [D9] (PAP storage) |
+---------------------------------+
| id (PK)                         |   PDP consults policy_rules first,
| name                            |   then access_grants + children.
| effect (permit|deny)            |   Jurisdiction + legal_basis enable
| priority                        |   GDPR / HIPAA / etc. policy routing.
| predicate JSON                  |
| obligations JSON                |
| jurisdiction (ISO country)      |
| legal_basis                     |   ---->  every PDP decision logged
| applies_from / applies_until    |   ---->  in access_log (CSA-1, proposed)
| owner_org_id (FK)               |
+---------------------------------+

[CSA-1 proposed: access_log]  — HIPAA 164.312(b) audit of every read; references
[CSA-3 proposed: grant_history] — append-only lifecycle of access_grants (event sourcing)

Note: grantee_id is FK to persons when grantee_type in ('practitioner', 'agent')
      (D18 makes agent a persons satellite). For app grantee_type, grantee_id
      holds the external client_id with no FK constraint.
```

### L2.3 — Clinical data: core (D7)

D7 (2026-04-14) split the former single `health_records` into 6 FHIR-aligned tables.
Each table has a FK to `patients` + `raw_payload_id`; diagram shows those once for
clarity, then focuses on each table's distinguishing fields.

```
                      +---------------------+         +---------------------+
                      | raw_payloads        |         | patients            |
                      +---------------------+         +---------------------+
                      | id (PK)             |         | id (PK)             |
                      | payload_hash (UK)   |         | ... (see L2.1)      |
                      | payload_ref (S3)    |         +----------+----------+
                      +----------+----------+                    |
                                 |                               |
                    FK raw_payload_id  (all 6 below)   FK patient_id  (all 6 below)
                                 |                               |
    +----------+----------+------+-------+----------+------------+-----------+
    |                |           |              |                |           |
    v                v           v              v                v           v
+---+-----+  +-------+-----+ +---+-----+ +-----+----+ +----------+-+ +------+---------+
|observ.  |  | conditions  | |medicat. | |allergies | |immunizations| | family_history |
+---------+  +-------------+ +---------+ +----------+ +-------------+ +----------------+
|id (PK)  |  |id (PK)      | |id (PK)  | |id (PK)   | |id (PK)      | |id (PK)         |
|patient  |  |patient      | |patient  | |patient   | |patient      | |patient         |
|obs_type |  |clinical_stat| |status   | |clinical_s| |status       | |relationship    |
|code+sys |  |verification | |intent   | |verify_st | |dose_number  | |condition_code  |
|code_disp|  |category     | |code+sys | |type      | |series_count | |condition_sys   |
|code_text|  |severity     | |code_disp| |category  | |lot_number   | |age_at_onset    |
| [D14]   |  |onset_date   | |code_text| |critical. | |manufacturer | |deceased        |
|value_*  |  |abatement_dt | | [D14]   | |reactions | |route        | |age_at_death    |
|unit     |  |recorded_at  | |dose_val | | JSON     | |site         | |recorded_at     |
|effective|  |recorder_id  | |dose_unit| |code_text | |administered | |narrative       |
|recorded |  |code_text    | |route    | | [D14]    | |next_due_at  | |trust_level     |
|asserted |  | [D14]       | |freq     | |onset_date| |performer    | |extensions JSON |
|narrative|  |narrative    | |prn      | |recorded  | |code_text    | +----------------+
|trust_lvl|  |trust_level  | |prescrib | |narrative | | [D14]       |
|ext JSON |  |extensions   | |period_* | |trust_lvl | |trust_level  |
+----+----+  +------+------+ |narrative| |ext JSON  | |extensions   |
     |              |        |trust_lvl| +----+-----+ +------+------+
     |              |        |ext JSON |      |              |
     |              |        +----+----+      |              |
     |              |             |           |              |
     | lookup (code + code_system + target_table)            |
     v              v             v           v              v
+----+--------------+-------------+-----------+--------------+----+
| ref_hom_mapping (target_table routes to right silver table)     |
+-----------------------------------------------------------------+
| code, code_system                                               |
| target_table (observations|conditions|medications|allergies|    |
|               immunizations|family_history)                     |
| hom_node_id (FK, single-PK per D17)                             |
+---------------------+-------------------------------------------+
                      |
                      v
             +--------+-------------+
             | ref_hom_nodes (D17)  |
             +----------------------+
             | id (PK, single PK)   |
             | tree_id              |
             | tree_version         |
             | node_code            |
             | parent_id (FK)       |
             | retired_at           |
             | successor_node_id FK |
             +----------------------+

[D14] code_text column added to every silver table (FHIR CodeableConcept.text
      free-text fallback alongside code_display label).
```

### L2.4 — Clinical data: adjunct

Tables that support, derive from, or stage into the D7 core. Each links to one or more
core tables via polymorphic or direct FK.

```
Supporting (multi-component + derived vectors):

+---------------------+       +---------------------+       +---------------------+
| observation_comp.   |       | provenance          |       | health_record_emb   |
+---------------------+       +---------------------+       +---------------------+
| id (PK)             |       | id (PK)             |       | id (PK)             |
| observation_id (FK) |       | target_table        |       | target_table        |
| code + display      |       | target_id           |       | target_id           |
| value_*             |       | raw_payload_id (FK) |       | patient_id (FK)     |
+---------------------+       | extraction_method   |       | model + version     |
                              | confidence          |       | vector JSON         |
(component sub-measurements   | [CSA-46 PROV-O]     |       | [D20: inherits      |
 on observations, e.g., BP    +---------------------+       |   source consent]   |
 with systolic + diastolic)   (ETL lineage;                 +---------------------+
                               polymorphic target_table)    (polymorphic to D7
                                                             silver; PDP eval
                                                             transitively per D20)

Grouping + staging:

+---------------------+          +---------------------+
| reports             |          | clinical_entities   |
+---------------------+          +---------------------+
| id (PK)             |          | id (PK)             |
| patient_id (FK)     |          | raw_payload_id (FK) |
| report_type         |          | patient_id (FK)     |
| code + code_system  |          | entity_type         |
| effective_date      |          | extracted_code      |
| status              |          | extracted_value     |
| narrative           |          | confidence          |
| document_ref ------>+--> docs  | source_span         |
| raw_payload_id ---->+--> raw   | promoted_to         |
+---------------------+          |  (target_table +    |
                                 |   target_id)        |
                                 | review_status       |
                                 +----------+----------+
                                            |
                                 promotion  |
                                            v
                                   +--------+---------+
                                   | one of the 6     |
                                   | D7 silver tables |
                                   +------------------+

Agent / clinician reasoning (D13):

+---------------------------+                      +---------------------------+
| clinical_impressions [D13]|                      | persons                   |
+---------------------------+                      +---------------------------+
| id (PK)                   |                      | id (PK) (performer_id     |
| patient_id (FK)           |                      |         polymorphic)      |
| encounter_id (FK, nullable)|                     +-------------+-------------+
| performer_id              |---- performer_table='practitioners'|'agents'|'patients'
| performer_table           |<-------------------+
| status (in-progress|completed|entered-in-error)
| code + code_system + display + text [D14]
| summary TEXT              |
| prognosis_code / display / text [D14]
| prognosis_reference_table + id
| effective_period_start / _end
| date                      |
| previous_impression_id (FK self) ---> longitudinal chain
| raw_payload_id (FK)       |
| narrative / extensions / trust_level
+-------+-------------------+
        |
        | FK (impression_id) ON DELETE CASCADE
        |
+-------+-----------------------------------+   +------------------------+
| clinical_impression_findings      [D13]   |   | clinical_impression_   |
+-------------------------------------------+   | problems         [D13] |
| id (PK)                                   |   +------------------------+
| impression_id (FK)                        |   | impression_id (FK PK)  |
| rank (1 = primary)                        |   | condition_id (FK PK)   |
| item_code + item_system + item_display    |   +------------------------+
| item_text [D14]                           |
| item_reference_table + item_reference_id  |
|   (polymorphic link to supporting evidence)|
| basis TEXT                                |
| basis_references JSON [{table, id}, ...]  |
+-------------------------------------------+

Agent-authored pattern: performer_table='agents', performer_id=persons.id of the agent.
Every finding can reference supporting observations / conditions / labs via item_reference.
previous_impression_id enables "agent's opinion evolved from X to Y" queries.
```

### L2.5 — Documents + Compositions

Documents = blob-of-truth (D3, content-addressed). Compositions = structured parse (D15,
FHIR Composition). Hybrid: a composition may optionally reference a source document;
born-structured compositions (agent-authored) have no document link.

```
+---------------------+              +---------------------+
| patients            |              | raw_payloads        |
+---------------------+              +---------------------+
| id (PK)             |              | id (PK)             |
+--------+------------+              | payload_hash (UK)   |
         |                           | payload_ref (S3 key)|
         | FK (patient_id)           +----------+----------+
         |                                      |
         v                                      | FK (raw_payload_id)
+--------+-----------------+                    |
| documents (D3)           |<-------------------+
+--------------------------+
| id (PK)                  |
| patient_id (FK)          |
| title / document_type    |
| mime_type / size_bytes   |
| storage_path (S3:        |
|    docs/{hash[0:2]}/...) |
| payload_hash (UK, SHA-256)
| source_system / source_standard
| trust_level              |
| raw_payload_id (FK)      |
| org_id (provenance only  |
|     — NOT access control)|
| deleted_at (soft-delete) |
+---+----------------------+
    |
    | FK document_id (nullable — compositions may be born structured)
    v
+---+------------------------+           +--------------------------+
| compositions (D15)         |           | persons (author target)  |
+----------------------------+           +--------------------------+
| id (PK)                    |           | id (PK)                  |
| patient_id (FK)            |           +-----------+--------------+
| document_id (FK, nullable) |                       |
| encounter_id (FK, nullable)|                       |
| status                     |                       |
| type_code + system + disp  |                       |
| type_text [D14]            |                       |
| title / date               |                       |
| custodian_org_id (FK)      |                       |
| raw_payload_id (FK)        |                       |
+------+---------------------+                       |
       |                                             |
       | FK composition_id ON DELETE CASCADE         |
       |                                             |
       +-----+---------------------+                 |
             |                     |                 |
             v                     v                 |
+------------+------+        +-----+-------------+   | FK author_id
| composition_      |        | composition_      |   | (polymorphic
|   sections (D15)  |        |   authors (D15)   |---+  via author_table)
+-------------------+        +-------------------+
| id (PK)           |        | composition_id PK |
| composition_id FK |        | author_table PK   |
| parent_section_id |        | author_id PK      |
|   (FK self)       |        +-------------------+
| sort_order        |
| title             |
| section_code + sys|
| section_display   |
| section_text [D14]|        Composition authors are polymorphic:
| text TEXT         |        author_table in ('practitioners', 'agents', 'patients').
|   (FHIR sect.text)|
+-----+-------------+
      |
      | FK section_id ON DELETE CASCADE
      v
+-----+--------------+
| composition_       |
|   section_entries  |
|              (D15) |
+--------------------+
| id (PK)            |
| section_id (FK)    |
| entry_table        |------> silver-table reference (conditions,
| entry_id           |        observations, medications, clinical_
| sort_order         |        impressions, etc.) — polymorphic
+--------------------+

Read pattern: "show every Assessment section in 2026 that referenced hypertension" =
  compositions JOIN composition_sections ON section_code = 'LOINC-51848-0'
  JOIN composition_section_entries ON entry_table = 'conditions'
  JOIN conditions ON entry_id = conditions.id AND conditions.code = 'I10'
```

### L2.6 — Encounters

```
+---------------------+          +---------------------+
| patients            |          | practitioners       |
+---------------------+          +---------------------+
| id (PK)             |          | id (PK)             |
+--------+------------+          | person_id (FK)      |
         |                       | npi                 |
         | FK (patient_id)       | specialty           |
         |                       | org_id (FK)         |
         v                       +----------+----------+
+--------+----------------------------------+----------+
| encounters                                           |
+------------------------------------------------------+
| id (PK)                                              |
| patient_id (FK)                                      |
| encounter_type (office_visit, telehealth, lab_draw,  |
|   imaging, executive_physical)                       |
| status (finished, in-progress, planned, cancelled)   |
| period_start, period_end                             |
| practitioner_id (FK, nullable)                       |
| location_name (D2: inline)                           |
| location_type                                        |
| reason_code, reason_display, reason_text [D14]       |
| org_id                                               |
| raw_payload_id (FK, nullable)                        |
+------------------+-----------------------------------+
                   |
                   | optionally referenced by
                   | (encounter_id column on D7 tables,
                   |  compositions, clinical_impressions,
                   |  appointments, tasks, journal_entries)
                   v
              (many tables link back to encounters)
```

### L2.7 — Care plans + Goals

```
+---------------------+         +---------------------+
| patients            |         | ref_hom_nodes (D17) |
+---------------------+         +---------------------+
| id (PK)             |         | id (PK)             |
+-------+-------------+         | tree_id             |
        |                       | node_code           |
        | FK (patient_id)       +----------+----------+
        |                                  |
        v                                  |
+-------+------------------+                |
| care_plans               |                |
+--------------------------+                |
| id (PK)                  |                |
| patient_id (FK)          |                |
| title / description      |                |
| status (active|completed |                |
|   |cancelled|draft)      |                |
| category                 |                |
| period_start / end       |                |
| author_id (FK persons)   |                |
| org_id                   |                |
+------+-------------------+                |
       |                                    |
       | FK (care_plan_id)                  |
       v                                    |
+------+-----------------------+            |
| goals                        |            |
+------------------------------+            |
| id (PK)                      |            |
| care_plan_id (FK)            |            |
| patient_id (FK)              |            |
| description                  |            |
| target_code + target_system  |            |
| target_value + target_unit   |            |
| target_operator              |            |
| current_value (denormalized) |            |
| due_date / status            |            |
| hom_node_id (FK) ------------+------------+
+------------------------------+

Goals reference HOM nodes for dashboard rendering.
current_value denormalized from latest observation query.
```

### L2.8 — Workflow (Appointments + Tasks)

Co-exist pattern (D12): per-table status on canonical resources + standalone tasks for
action items and workflow overlays. Appointments (D11) own their own status; tasks
overlay on top via polymorphic focus.

```
+---------------------+          +---------------------+
| patients            |          | practitioners       |
+---------------------+          +---------------------+
| id (PK)             |          | id (PK)             |
+--------+------------+          +----------+----------+
         |                                  |
         | FK (patient_id)                  | FK (practitioner_id)
         |                                  |
         v                                  v
+--------+--------------------------------------------+
| appointments [D11] (FHIR Appointment shape)         |
+-----------------------------------------------------+
| id (PK)                                             |
| patient_id (FK) / practitioner_id (FK, nullable)    |
| encounter_id (FK, populated post-arrival)           |
| org_id (FK)                                         |
| status (FHIR AppointmentStatus:                     |
|   proposed|pending|booked|arrived|fulfilled|        |
|   cancelled|noshow)                                 |
| service_category / service_type / specialty         |
| start_at / end_at / minutes_duration                |
| reason_code + system + display + text [D14]         |
| reason_reference_table + id (polymorphic:           |
|   conditions / observations / referrals)            |
| priority                                            |
| location_name + location_type (D2 inline)           |
| telehealth_join_url                                 |
| source_system + external_id (UK round-trip sync)    |
| raw_payload_id (FK, nullable)                       |
+-----------------------------------------------------+

+------------------------------------------------------+
| tasks [D12] (FHIR Task shape — action items +       |
|              workflow overlay on canonical resources)|
+------------------------------------------------------+
| id (PK)                                              |
| patient_id (FK)                                      |
| requester_id (persons — person / agent)              |
| owner_id (persons — person / agent / org-role)       |
| code + system + display + text [D14]                 |
| description TEXT                                     |
| status (FHIR TaskStatus)                             |
| intent (FHIR TaskIntent)                             |
| priority                                             |
| focus_table + focus_id (polymorphic target:          |
|   the resource this task concerns — appointment,     |
|   observation, report, composition, ...)             |
| for_table + for_id (usually 'patients')              |
| execution_period_start / _end                        |
| input JSON  / output JSON                            |
| source_system + external_id (UK)                     |
+------+-----------------------------------------------+
       |
       | focus_table + focus_id polymorphic FK
       v
+------+--------------+
| any canonical       |  e.g., focus_table='appointments',
| resource            |       focus_id=... -> "call patient to
+---------------------+       confirm 5/3 appointment"

Tasks do NOT own canonical-resource lifecycle; each resource keeps its own status.
Tasks are action items that reference resources through focus_table / focus_id.
```

### L2.9 — Journal + Notes

```
+---------------------+    +---------------------+    +---------------------+
| patients            |    | (any silver record) |    | encounters          |
+---------------------+    +---------------------+    +---------------------+
| id (PK)             |    | id                  |    | id (PK)             |
+----+----------------+    +---------+-----------+    +---------+-----------+
     |                               |                          |
     | FK (patient_id)               | FK (health_record_id —   | FK (encounter_id)
     |                               |  polymorphic by record_  |
     v                               |  table post-D7)          v
+----+----------------------+--------+------------------+-------+
| journal_entries                                              |
+--------------------------------------------------------------+
| id (PK)                                                      |
| patient_id (FK)                                              |
| entry_type (clinical_note | patient_note | ai_summary |      |
|   life_event)                                                |
| title / content (TEXT)                                       |
| health_record_id (FK, nullable) — annotation on a record     |
| health_record_table (polymorphic discriminator post-D7)      |
| encounter_id (FK, nullable) — annotation on an encounter     |
| author_id (FK persons — person / agent)                      |
| org_id                                                       |
| effective_date / created_at                                  |
+---+----------------------------------------------------------+
    |
    | FK (journal_entry_id) ON DELETE CASCADE
    v
+---+----------------+
| notes              |
+--------------------+
| id (PK)            |
| journal_entry_id   |
|   (FK)             |
| author_id (FK      |
|   persons)         |
| content (TEXT)     |
| created_at         |
+--------------------+

Notes = replies on a journal entry (patient <-> clinician / agent threads).
Free-text for narrative; structured reasoning lives in clinical_impressions (L2.4).
```

### L2.10 — Reference + Raw

```
+---------------------------+        +---------------------+
| ref_source_adapters (D6)  |        | raw_payloads        |
+---------------------------+        +---------------------+
| id (PK)                   |        | id (PK)             |
| source_system (UK)        |<------.| source_system       |
| display_name              | named  | payload_hash (UK)   |
| adapter_class (Python FQN)| lookup | payload_ref (S3 key)|
| source_standard           |        | source_standard     |
| auth_type                 |        | captured_at         |
| config JSON               |        | processed_at        |
| trust_level_default       |        | org_id              |
| active (bool)             |        +----+----------------+
+---------------------------+             |
                                          | referenced by FK
                                          | (raw_payload_id)
                                          v
                                 +--------+--------------+
                                 | 6 D7 silver tables    |
                                 | documents             |
                                 | encounters            |
                                 | provenance            |
                                 | appointments / tasks  |
                                 | compositions          |
                                 | clinical_impressions  |
                                 +-----------------------+

HOM ontology (D17 refactored):

+-----------------------+          +----------------------+
| ref_hom_nodes (D17)   |<---------| ref_hom_mapping      |
+-----------------------+  joined  +----------------------+
| id (PK, single)       |          | code                 |
| tree_id               |          | code_system          |
| tree_version          |          | target_table         |
| node_code             |          |   (post-D7; routes   |
| parent_id (FK self)   |          |   to right silver)   |
| display               |          | hom_node_id (FK)     |
| retired_at            |          +----------+-----------+
| successor_node_id FK  |                     |
+-----------------------+                     | joined with
                                              | D7 silver tables
                                              | on (code, code_system,
                                              |     target_table)
                                              v
                                 +-------------------------+
                                 | one of 6 D7 silver tbls |
                                 +-------------------------+

Code evolution + contracts:

+---------------------+      evolves LOINC codes; not FK'd,
| loinc_crosswalk     |      referenced by convention in
+---------------------+      observations.code_system
| loinc_code          |
| new_code            |      +--------------------------+
| display             |      | ref_record_type_schemas  |  extension
| effective_period    |      +--------------------------+  contracts
+---------------------+      | record_type              |  per record
                             | extension_key            |  type (soft
+---------------------+      | required (bool)          |  contract,
| ref_drug_classes    |      | data_type                |  not FK'd)
+---------------------+      | description              |
| rxnorm_code         |      +--------------------------+
| drug_class          |
| display             |      +--------------------------+
+---------------------+      | ref_analyte_conversions  |
                             +--------------------------+
+---------------------+      | source_unit              |
| ref_reconciliation_ |      | canonical_unit           |
|   rules (D19)       |      | conversion_factor        |
+---------------------+      +--------------------------+
| id (PK)             |
| metric_code         |      Reconciliation per metric: ordered source
| metric_system       |      priority + fallback strategy. Gold-tier
| priority_chain JSON |      daily_summaries consults this when two
| fallback_strategy   |      sources at same trust level disagree (D19).
| strategy_params JSON|
| applies_org_id (FK) |
+---------------------+
```

## L2 — Cross-cutting flows

### L2.11 — Ingest flow

```
Source adapter (Oura / Quest / Fitbit / Epic / manual upload)
      |
      | HTTP + OAuth (using source_connections.refresh_token)
      v
+---------------------+
| Ingest service      |
| (adapter-per-source)|
+----------+----------+
           |
           | 1. Persist raw (idempotent via SHA-256)
           v
+----------+----------+         +--------------------+
| raw_payloads        |-------->| provenance         |
| (hash UK dedup)     |  ETL    | [CSA-46: PROV-O    |
+----------+----------+ lineage |  prov_activity_id, |
           |                    |  prov_agent_id,    |
           | 2. Extract entities|  prov_entity_id]   |
           |    (ADR-2002)      +--------------------+
           v
+----------+----------+
| clinical_entities   |
| (staged, confidence)|
+----------+----------+
           |
           | 3. Human or auto-promote (review_status='approved')
           v
+----------+----------+         +--------------------+
| one of 6 D7 silver  |-------->| health_record_emb  |
| (canonical, trusted)|  async  | (embeddings; D20:  |
+----------+----------+         |  inherits consent) |
           |                    +--------------------+
           |
           | 4. Group (if source is a bundle like lab panel)
           v
+----------+----------+
| reports             |
| (grouped envelope)  |
+---------------------+

Trust levels (ADR-2007) set at adapter registration:
  ref_source_adapters.trust_level_default -> raw_payloads.trust_level
  -> propagates to silver table trust_level

[CSA-45 proposed: ingest_outbox] — transactional ingest event publishing.
```

### L2.12 — HOM query flow

```
Client request: "Give me all cardiovascular records for patient X"
      |
      v
+---------------------+
| API endpoint        |
| GET /patients/X/hom |
|     /cardiovascular |
+----------+----------+
           |
           | 1. Resolve HOM node (D17 single-PK)
           v
+----------+----------+
| ref_hom_nodes       |  lookup by tree + node_code -> id
| id = <uuid>         |
+----------+----------+
           |
           | 2. Find canonical codes in this group (post-D7)
           v
+----------+----------+
| ref_hom_mapping     |  WHERE hom_node_id = <uuid>
| (code, code_system, |  returns: (I21.9, icd-10, 'conditions'),
|  target_table)      |           (50560-2, loinc, 'observations'), ...
+----------+----------+
           |
           | 3. UNION ALL across the 6 D7 silver tables
           |    (each JOIN filtered by target_table)
           v
+----------+----------+          +---------------------+
| observations +      |<---------| PDP (D9) applies    |
| conditions +        |  consent | access_grants +     |
| medications +       |  filter  |   children (D10) +  |
| allergies +         |          |   policy_rules (D9) |
| immunizations +     |          +---------------------+
| family_history      |
+----------+----------+
           |
           | 4. Return with consent-filtered rows
           v
+---------------------+
| Response            |
| {records: [...]}    |
+---------------------+

Key insight: HOM query is a 3-table JOIN pattern (ref_hom_nodes -> ref_hom_mapping
-> one of 6 D7 silver tables) UNIONed across target_table, with PDP consent eval
applied at the repository layer (D9 full XACML triad).
```

### L2.13 — AI agent flow

```
Patient prompts agent: "What were my lab trends last quarter?"
      |
      v
+------------------------+
| Agent (persons row +   |        [D18] Agent is a persons hub row with
| agents satellite [D18])|        agents satellite. Authored impressions /
+----+-----+-------------+        tasks / compositions reference persons.id.
     |     |
     |     +--- agent_sessions row opened (session_id, agent_id, patient_id)
     |
     | 1. PDP (D9) evaluates agent request through same engine as humans
     v
+----+----------------+          +---------------------+
| access_grants       |--- joined-->| access_grant_*   |
| grantee_id = agent  | for index   | (3 child tables, |
|   persons.id        |    hits     |  D10)            |
+----+----------------+          +---------------------+
     |                                      ^
     |                                      |
     |                                      +---- policy_rules (D9 PAP)
     |                                           evaluated first by PDP
     | 2. Build filtered query scope
     v
+----+----------------+   filter by categories (e.g., 'laboratory')
| 6 D7 silver tables  |   filter by sources (e.g., ['quest', 'labcorp'])
| + observation_comp  |   filter by hom_nodes (e.g., 'lipid_panel')
| + reports           |   filter by time range (last quarter)
+----+----------------+
     |
     | 3. Vector retrieval (semantic)
     v
+----+----------------+
| health_record_emb   |   similarity search on question embedding
| (cosine vs query)   |   + transitive consent via D20 — PDP
+----+----------------+     re-evaluates source consent per row
     |
     | 4. Compose response with citations
     v
+----+-----------------+         +---------------------+
| LLM response         |-------->| access_log (CSA-1)  |  records which
| {answer, citations,  |  audit  | records agent read; |  rules matched +
|  records_accessed}   |         | rule_id from PDP    |  which rows
+----+-----------------+         +---------------------+
     |
     | 5. Optional: agent authors clinical reasoning
     v
+----+----------------+          +---------------------+
| clinical_impressions|          | tasks (owner_id =   |
|   [D13] (agent-     |          |   agent persons.id  |
|   authored)         |          |   — follow-ups)     |
+---------------------+          +---------------------+

Agent-authored outputs follow same PDP eval as any other grantee.
Revoking the agent's grant invalidates reading AND writing.
```

### L2.14 — Authorization decision flow (PDP/PEP)

```
Request arrives at any authorized API endpoint
      |
      v
+--------------------------+
| PEP: FastAPI dependency  |   (D9) Policy Enforcement Point
| extracts (grantee,       |       intercepts every route;
| action, resource,        |       no route bypasses PEP.
| context)                 |
+-----------+--------------+
            |
            | delegates decision
            v
+-----------+--------------------+
| PDP: AuthorizationService      |   (D9) Policy Decision Point
|   .evaluate(grantee, action,   |       Pure function: same inputs
|             resource, context) |       always yield same decision.
+-----------+--------------------+
            |
            | 1. Load applicable policy rules
            v
+-----------+----------+       WHERE (jurisdiction IS NULL OR
| policy_rules (D9 PAP)|         jurisdiction = context.jurisdiction)
+----------------------+       AND (applies_from IS NULL OR
| effect / priority    |            applies_from <= NOW())
| predicate JSON       |       AND (applies_until IS NULL OR
| obligations JSON     |            applies_until >  NOW())
| jurisdiction         |       ORDER BY priority ASC
| legal_basis          |
+----------------------+
            |
            | 2. Evaluate predicate against context
            | 3. If rule permits, gather PIP attributes
            v
+-----------+----------+       PIP (Policy Information Point)
| access_grants +      |       = attributes for eval. Child
|   child tables (D10) |       tables (D10) hit by B-tree
|   (index-hit filter) |       index on category / source /
+-----------+----------+       hom_node_id.
            |
            | 4. Apply obligations (redact / log / notify)
            v
+-----------+----------+
| Decision:            |       permit | deny | redact <fields>
| (effect, obligations,|
|  matched_rule_id)    |
+-----------+----------+
            |
            +----> PEP proceeds with data read (if permit)
            |
            +----> access_log (CSA-1) records decision
            |       (grantee, resource, rule_id, effect, timestamp)
            |
            +----> for derived data (D20), PDP re-evaluates
                    with source_table / source_id — transitive
                    consent enforced on embeddings, summaries,
                    impressions, alerts.
```

### L2.15 — Agent-authored output flow

```
Agent decides to author clinical reasoning (e.g., weekly summary)
      |
      v
+---------------------+
| agent_sessions [D18]|   Current conversation / batch session,
| (session_id active) |   linked to agent persons.id.
+----------+----------+
           |
           | 1. Agent creates a task for itself (D12 self-assignment)
           v
+----------+----------+
| tasks               |   owner_id = agent persons.id
| (intent='plan',     |   code = SNOMED authoring task code
|  status='in-progress')  focus_table may reference encounter
+----------+----------+   description = "weekly summary for patient X"
           |
           | 2. Gather evidence (PDP-filtered reads via L2.14)
           v
+----------+----------+
| observations +      |   reads with PDP consent eval
| conditions +        |   + transitive consent (D20)
| medications +       |   on embeddings / derived data
| clinical_entities + |
| previous impressions|
+----------+----------+
           |
           | 3. Author clinical_impressions (D13)
           v
+----------+----------+
| clinical_impressions|   performer_id = agent persons.id
|   [D13]             |   performer_table = 'agents'
| + _findings (ranked)|   previous_impression_id links to last
| + _problems (M:N    |    agent impression for longitudinal view
|   with conditions)  |
+----------+----------+
           |
           | 4. Optional: assemble structured document
           v
+----------+----------+
| compositions [D15]  |   author (via composition_authors)
|   + _sections       |   author_table='agents'
|   + _section_entries|   sections link to evidence silver rows
|   (polymorphic to   |   through composition_section_entries
|     silver rows)    |
+----------+----------+
           |
           | 5. Close out task
           v
+----------+----------+
| tasks (status       |   output JSON = {impression_id, composition_id}
|   = 'completed')    |   execution_period_end = NOW()
+---------------------+

The agent operates at the workflow layer via tasks (D12), reasons via impressions
(D13), and publishes structured artifacts via compositions (D15). Every step is
PDP-gated (D9 + D14) and cascade-audited (CSA-1). Revoking the agent's grant
halts all of these steps at the PDP layer.
```

## Diagram conventions

- ASCII box characters: `+` corners, `-` horizontal, `|` vertical, `=` emphasis
- `(PK)` primary key, `(FK)` foreign key, `(UK)` unique key
- Arrows: `-->` solid (ownership / FK), `..>` dotted (lookup / reference data)
- `[D-N]` = decision from `decisions.md` (e.g., `[D18]` = D18 agent identity model)
- `[CSA-N: ...]` = proposed addition from `design-queue.md`
- Avoid Unicode box-drawing (`─│┌┐└┘`) — renders inconsistently; stick to ASCII
