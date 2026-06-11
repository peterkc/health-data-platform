# Design Patterns — Architectural Vocabulary

**Status**: Living — first capture 2026-04-14
**Purpose**: Name the patterns Health OS uses, should adopt, and avoids -- so future engineers inherit trade-off knowledge instead of re-deriving it
**Audience**: Engineers joining the project; architecture review; readers learning the system vocabulary
**Companion to**: [decisions.md](decisions.md), [design-queue.md](design-queue.md), [design-lessons.md](design-lessons.md)

## How to read this file

- **Section 1** (patterns Health OS already uses): scan "Status" column to find implicit patterns that need naming
- **Section 2** (patterns to adopt): scan "Connects to" column to find the CSA or decision each pattern enables
- **Section 3** (anti-patterns): what Health OS explicitly avoids, with rationale
- Each pattern name links to external literature -- the name IS the documentation

## Why this catalog exists

Patterns are the inherited language of a system. A pattern name carries the literature behind it -- trade-offs, failure modes, integration cost, and the context where it works. When Health OS's hub says "we use Data Vault 2.0 satellites", a future engineer reads Linstedt and inherits decades of practice. When the hub says "we have these tables", they re-derive.

Three reasons this matters now:

1. **Exit asset** -- an acquirer reading a vocabulary inherits a system; reading a code base inherits a code base.
1. **Pivot enabler** -- Hexagonal architecture maps to "easy to add new sources"; Strangler Fig maps to "easy to evolve schema."
1. **Anti-regression** -- naming what we *don't* do prevents future "should we just..." regression.

## 1. Patterns Health OS already uses (often unnamed)

Each row: pattern name + Health OS manifestation + status (named in hub or implicit).

| Pattern                                                           | Health OS manifestation                                                                                                                                                                                                                                                      | Status                                                                  |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **Medallion architecture** (bronze/silver/gold)                   | `raw_payloads` (bronze) → 6 silver tables (D7) → `daily_summaries` (gold)                                                                                                                                                                                                    | Implicit — should be named in L0 diagram                                |
| **Hexagonal / Ports & Adapters**                                  | `ref_source_adapters` registry + `adapter_class` Python FQN; per-source adapter implementations                                                                                                                                                                              | Implicit                                                                |
| **Idempotent consumer**                                           | `raw_payloads.payload_hash` UNIQUE — repeated ingest of identical payload deduplicates                                                                                                                                                                                       | Used; not labeled                                                       |
| **Polymorphic association with discriminator**                    | Post-D7: `ref_hom_mapping.target_table` + `target_id`; `provenance` + `health_record_embeddings` follow same pattern                                                                                                                                                         | Introduced in D7; should be named                                       |
| **Class Table Inheritance** (Fowler PoEAA)                        | D7 split: each FHIR resource type gets its own table sharing `patient_id` + `raw_payload_id` semantics                                                                                                                                                                       | D7 implements; not framed as CTI                                        |
| **Data Vault 2.0 hub + satellite**                                | `persons` (hub) + `patients` / `practitioners` / `org_roles` (satellites); D1 implements                                                                                                                                                                                     | Implicit — D1 names "satellite" without crediting Data Vault            |
| **Soft delete + reference counting**                              | `documents.deleted_at` + content-addressed S3 dedup; purge S3 only when no live row references hash                                                                                                                                                                          | Used; HIPAA right-to-delete pattern                                     |
| **Capability-based security**                                     | `access_grants` rows are unforgeable capabilities (categories + sources + hom_nodes + scope + grantee)                                                                                                                                                                       | Used; not framed as capabilities                                        |
| **Trust grading**                                                 | `trust_level` 1-6 on every silver row (ADR-2007); per-source `trust_level_default` in `ref_source_adapters`                                                                                                                                                                  | Used; explicit                                                          |
| **Adapter registry as extensibility contract**                    | `ref_source_adapters` + `source_connections` (CSA-12) — registry IS the source extensibility story                                                                                                                                                                           | Used; D6 names "registry"                                               |
| **Repository pattern** (DDD)                                      | API layer reads from silver tables; PDP/PEP separation proposed (CSA-10)                                                                                                                                                                                                     | Implicit; CSA-10 makes explicit                                         |
| **Adjacency list for hierarchies**                                | `ref_hom_nodes` parent_id structure (HOM tree)                                                                                                                                                                                                                               | Used; alternatives noted (materialized path / closure table not chosen) |
| **Content-addressed storage**                                     | `documents.storage_path` = `docs/{hash[0:2]}/{hash[2:4]}/{hash}.{ext}` + SHA-256 dedup (D3)                                                                                                                                                                                  | Named in D3                                                             |
| **Transitive consent on derived data**                            | Derived rows (embeddings per D5, daily_summaries, alerts per CSA-28, impressions per D13) carry `source_table` + `source_id`; PDP (D9) dereferences to source on every read; cascade-delete on source FK ensures structural purge for HIPAA right-to-delete + GDPR Art. 17   | Named in D20 (resolves FQ-5) — pattern-not-table                        |
| **Relationship tuples + computed usersets** (Zanzibar / OpenFGA)  | D22: PDP substrate — `access_grants` (D10) encoded as OpenFGA tuples; `policy_rules` (D9 PAP) as OpenFGA type definitions; D20 transitive consent as computed usersets chaining through `source_table` + `source_id`. Apache 2 / CNCF sandbox; portable to SpiceDB / Permify | Named in D22                                                            |
| **Audience-scoped error collapsing** (OWASP info-leak prevention) | D21: non-patient reads return `NotFound` (collapsed); patient-facing reads return `PermissionDenied` with grant context (GDPR Art 15 + HIPAA §164.524 transparency). Precedent: FHIR empty Bundle, GitHub private-repo 404, AWS S3 post-fix, Stripe                          | Named in D21                                                            |
| **Graceful degradation with signaling** (Google SRE / IEEE)       | D23: during OpenFGA outage, Tier 1 LRU cache continues to serve; response `metadata.access_decision.degraded_mode = true` + `decision_source = 'cache' \| 'rls'` for caller calibration; every mode writes `access_log`                                                      | Named in D23                                                            |
| **Stale-bounded read** (Zanzibar zookie)                          | D23: Tier 1 LRU TTL (60s default) bounds stale-permit window; grant revocation forces cache invalidation on OpenFGA recovery; during outage, stale-permit is bounded by TTL not by outage duration                                                                           | Named in D23                                                            |
| **Circuit Breaker** (Hystrix / Resilience4j)                      | D23 wraps OpenFGA calls — open after N consecutive failures, half-open probe for recovery; CSA-12 (source_connections) wraps OAuth refresh + per-source retry                                                                                                                | Named in D23; CSA-12 instantiates for source adapters                   |

## 2. Patterns Health OS should adopt explicitly

Each row: pattern + why + what changes + connecting CSA.

| Pattern                                     | Why Health OS should adopt                                                                                                                                                                                   | What changes                                                                                                                                             | Connects to               |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| **Data Vault 2.0**                          | Future role satellites (CSA-19 care_team, future caregiver / coach / nutritionist) become trivial when the hub-satellite pattern is canonical. Persons IS Data Vault — name it.                              | Annotate D1 with "Data Vault 2.0 hub-and-satellite" credit                                                                                               | D1, CSA-19                |
| **Bitemporal modeling**                     | CSA-5 (recorded_at + asserted_at) heads toward bitemporal but does not name it. Bitemporal is "what did we know, when, and what was true" — both required for HIPAA + clinical reasoning.                    | Frame CSA-5 as bitemporal adoption; add `tx_time_start` / `tx_time_end` columns where audit needs are strict                                             | CSA-5                     |
| **Event sourcing for consent**              | CSA-3 (grant_history) IS event sourcing for `access_grants`. Naming clarifies append-only semantics; current state derives from event log.                                                                   | Frame CSA-3 as event sourcing; replay → current `access_grants` rows                                                                                     | CSA-3                     |
| **CQRS**                                    | Write model = 6 silver tables. Read model = `patient_timeline_view` materialized. Hinted in endpoint-inventory.md but never named.                                                                           | Materialize `patient_timeline_view` for `/timeline` and `/records` reads                                                                                 | endpoint-inventory.md     |
| **Outbox pattern**                          | Transactional ingest events (raw → silver) — guarantees event publishing even on failure. Currently implicit via `provenance` but not durable as outbox.                                                     | New table: `ingest_outbox` (event id, target table, payload, status); ingest writes silver row + outbox row in one transaction; downstream worker drains | CSA-45 (new)              |
| **PDP / PEP / PAP** (XACML / OPA / Cedar)   | CSA-10 names PDP/PEP separation but stops short of PAP (admin). Full triad clarifies who can grant, who blocks reads, who interprets policy.                                                                 | Extend CSA-10 to add PAP responsibilities                                                                                                                | CSA-10                    |
| **Strangler Fig** (Fowler)                  | D7 *is* a strangler migration — replacing one table at a time, not big-bang. Naming gives future migrations a precedent.                                                                                     | Annotate D7 with "Strangler Fig migration"                                                                                                               | D7                        |
| **Compositional clinical models** (openEHR) | `ref_record_type_schemas` partially adopts archetype + template. Full adoption gives Health OS a path to ISO 13606 / openEHR ingest.                                                                         | Formalize archetype contracts; CSA-41 ingest path                                                                                                        | CSA-41                    |
| **W3C PROV-O**                              | `provenance` table semantics could align to PROV-O entities (Activity, Agent, Entity). Validates against an international standard.                                                                          | Add `prov_activity_id` / `prov_agent_id` / `prov_entity_id` columns; cite PROV-O                                                                         | CSA-46 (new)              |
| **Backend-for-Frontend (BFF)**              | Patient-facing API and provider-facing API will diverge; current single-API assumption is a pivot blocker (charting pivot needs different shapes).                                                           | Plan BFF split when first non-patient-first pivot activates                                                                                              | (no CSA; design note)     |
| **Bulkhead**                                | Source adapter failures should not cascade. Per-adapter isolation (process / thread pool / queue).                                                                                                           | Document adapter isolation contract in `ref_source_adapters` design                                                                                      | D6                        |
| **Change Data Capture (CDC)**               | Postgres audit triggers capture every change as old/new JSONB in audit_changes. Transactional outbox (§6) delivers events to downstream consumers (AI agent notifications, embedding worker, analytics ETL). | Outbox pattern replaces Dolt-native diffs; trigger-based capture is stronger (fires on all callers)                                                      | §6, database-substrate.md |
| **Saga pattern**                            | Multi-step ingest workflows (raw → extracted → reviewed → promoted) need failure-aware orchestration.                                                                                                        | Apply to clinical_entities promotion pipeline                                                                                                            | clinical_entities         |

## 3. Anti-patterns Health OS avoids — name these too

Naming what we *don't* do prevents regression.

| Anti-pattern                                      | Why Health OS avoids                                                       | How avoided                                                                                              |
| ------------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Pure EAV** (Entity-Attribute-Value)             | Loses query performance, schema discoverability, type safety               | `extensions JSON` is a *controlled* EAV — limited to per-source quirks, never canonical fields           |
| **Generic foreign keys without discriminator**    | Untraceable references, no FK constraint enforcement, no JOIN planner help | Polymorphic refs (post-D7) always carry the `target_table` discriminator                                 |
| **Pure single-table inheritance** (i2b2 style)    | Loses domain structure, semantic richness, state machines                  | D7 just rejected this — chose Class Table Inheritance instead                                            |
| **Hard delete**                                   | Breaks audit trail, breaks reference counting, breaks regulatory holds     | Soft-delete via `deleted_at` (D3 documents pattern)                                                      |
| **Big-bang migration**                            | Too risky for production data; impossible to roll back                     | Strangler Fig (D7 demonstrates the pattern)                                                              |
| **String-typed enums in code without ref tables** | Schema drift, no central registry                                          | All enums become reference tables (`ref_record_type_schemas`, future `ref_observation_types` per CSA-13) |
| **Shared mutable reference data**                 | Hidden coupling, breaking changes propagate silently                       | Each `ref_*` table is owned + versioned                                                                  |
| **Direct app access to raw payloads**             | Loses canonical guarantees, bypasses trust grading                         | Bronze (raw) → Silver (canonical); apps read silver only                                                 |
| **Over-fetching for "give me everything"**        | API performance collapse                                                   | Cursor pagination + per-table specialized endpoints + materialized timeline view                         |
| **Schema-less storage at silver/gold layer**      | Loses queryability, observability, correctness                             | Silver = strict schema; bronze (`raw_payloads.payload_ref`) is the only schema-less zone                 |
| **Cross-table FKs without discriminator**         | Same as generic FK; extra confusing in polymorphic contexts                | Always pair `target_id` with `target_table`                                                              |
| **Implicit security through obscurity**           | Storage paths, IDs, or guessable URLs being the access boundary            | All access goes through `access_grants` + PDP layer; `documents.storage_path` is not access control      |

## 4. Pattern → CSA + decision mapping

Many CSAs become legible as concrete pattern adoptions:

| Pattern                        | Manifestation                                           | CSA / Decision        |
| ------------------------------ | ------------------------------------------------------- | --------------------- |
| Class Table Inheritance        | D7 split into 6 FHIR-aligned tables                     | D7                    |
| Polymorphic association        | `target_table` discriminator on cross-table refs        | D7 + CSA-13           |
| Strangler Fig                  | D7 split execution                                      | D7                    |
| Data Vault 2.0 hub + satellite | persons + patients / practitioners / org_roles          | D1 (annotate)         |
| Hexagonal / Adapter            | `ref_source_adapters` registry                          | D6                    |
| Content-addressed storage      | `documents.storage_path` SHA-256 layout                 | D3                    |
| Soft delete + ref counting     | `documents.deleted_at` + reference counting             | D3 (additive)         |
| Bitemporal modeling            | `recorded_at` + `asserted_at` + `effective_date` triple | CSA-5                 |
| Event sourcing                 | `grant_history` append-only                             | CSA-3                 |
| Audit log (HIPAA)              | `access_log` separate from ETL `provenance`             | CSA-1                 |
| Capability-based security      | `access_grants` are unforgeable capabilities            | D-additive (consent)  |
| PDP / PEP separation           | Repository auth split                                   | CSA-10                |
| CQRS                           | Materialized `patient_timeline_view`                    | endpoint-inventory.md |
| Outbox                         | Transactional ingest events                             | **CSA-45 (new)**      |
| W3C PROV-O alignment           | `provenance` table → PROV-O entities                    | **CSA-46 (new)**      |
| Compositional clinical models  | `ref_record_type_schemas` archetype contracts           | CSA-7 + CSA-41        |
| Idempotent consumer            | `raw_payloads.payload_hash` UNIQUE                      | (in current schema)   |
| Adjacency list                 | `ref_hom_nodes` parent_id                               | (in current schema)   |
| Trust grading                  | `trust_level` per row                                   | ADR-2007              |

## 5. External references — where the patterns come from

| Source                                            | Author / Body                  | What it teaches                                             |
| ------------------------------------------------- | ------------------------------ | ----------------------------------------------------------- |
| *Patterns of Enterprise Application Architecture* | Martin Fowler                  | CTI / STI / Concrete Table Inheritance, Repository, etc.    |
| *Building the Data Vault 2.0*                     | Dan Linstedt + Mike Olschimke  | Hub + Link + Satellite                                      |
| *Domain-Driven Design*                            | Eric Evans                     | Bounded contexts, aggregates, repositories                  |
| *Refactoring Databases*                           | Scott Ambler + Pramod Sadalage | Strangler Fig migration, schema evolution                   |
| *Building Microservices*                          | Sam Newman                     | Hexagonal, BFF, bulkhead                                    |
| *Designing Data-Intensive Applications*           | Martin Kleppmann               | Bitemporal, CDC, event sourcing, CQRS, idempotent consumers |
| *Cloud Native Patterns*                           | Cornelia Davis                 | Outbox, saga, circuit breaker                               |
| *Patterns of Distributed Systems*                 | Unmesh Joshi                   | Outbox, sequencer, gossip, leader election                  |
| Databricks Medallion architecture                 | Databricks blog                | Bronze / silver / gold tier semantics                       |
| Microsoft Azure Architecture Center               | Microsoft                      | Catalog of cloud-native patterns                            |
| AWS Well-Architected                              | AWS                            | Reliability, security, operational excellence pillars       |
| W3C PROV-O specification                          | W3C                            | Provenance ontology (Activity, Agent, Entity)               |
| openEHR Architecture Overview                     | openEHR International          | Two-level modeling: reference model + archetype + template  |
| HL7 FHIR Implementation Guide                     | HL7 International              | Resource model, extensions, profiles, must-support flags    |

## How this catalog is maintained

- Add a row when Health OS adopts a new pattern — explicit or implicit
- Move "should adopt" rows to "uses" rows when the pattern lands in DDL or code
- Move anti-patterns rows to "uses" rows only when a deliberate exception is documented (with rationale)
- Cite literature for every "should adopt" — patterns without citation are folklore

## Iteration log

| Date       | Change                                                     | Rationale                                                                                                                                                                                                                                                                                                                                                     |
| ---------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-04-15 | Added 5 patterns from D21 + D22 + D23 data-plane decisions | D22 (OpenFGA PDP) names Relationship tuples + computed usersets (Zanzibar); D21 (NotFound vs PermissionDenied audience-split) names Audience-scoped error collapsing (OWASP); D23 (outage behavior) names Graceful degradation with signaling (Google SRE), Stale-bounded read (Zanzibar zookie), and promotes Circuit Breaker from "should adopt" to "uses". |
| 2026-04-15 | Added "Transitive consent on derived data" pattern         | D20 resolves FQ-5 as a pattern-not-table. Every derived row (embedding, summary, alert, impression) carries source_table + source_id; PDP evaluates transitively; cascade-delete purges structurally. Pattern generalizes across all current and future derivations.                                                                                          |
| 2026-04-14 | Initial capture                                            | User asked "have we considered design patterns?" — surfaced 13 used + 14 should-adopt + 12 anti-patterns; CSA-45 (outbox) and CSA-46 (PROV-O) added to backlog.                                                                                                                                                                                               |

Append new entries above this line.
