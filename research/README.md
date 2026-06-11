# MVP Schema Research Hub

Health OS started with 19 tables and a single `health_records` table holding six record types. That table worked for the POC. It breaks down when you need drug class lookups, immunization tracking, family history with relationships, or consent that varies by source, category, and jurisdiction. This hub documents where the single-table model fails, what replaces it, and why each choice was made. 27 locked decisions, 22 resolved open questions, 55+ target tables, 22 hub files. Every design choice traces back to five guiding principles in [ADR-0001](../../../adr/0001-guiding-principles.md): Privacy, Judgment, Trust, Ownership, Focus.

## State

| Layer          | Status                                     | Summary                                                                                                       |
| -------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| Schema design  | **27 decisions locked** (D1-D27)           | Identity model, consent, FHIR-aligned table split, authorization (OpenFGA), data-plane architecture           |
| Data plane     | **All 7 sections locked**                  | Repository read/write signatures, query composition, pagination, ingest, outbox, agent parity                 |
| Open questions | **All 22 resolved** (OQ-1 through OQ-22)   | Zero unresolved design items                                                                                  |
| Implementation | **Scoping locked** (2026-04-16)            | M3 = 38 tables + 12 columns + 11 patterns; M4 = 8 tables + 4 interop surfaces; Series A + scale events mapped |
| DDL            | **12 tables sketched** in table-designs.md | Remaining M3 tables pending DDL; M4 / Series A tables scoped                                                  |

## Reading paths

**Where does the single table break down?**
[decisions.md](decisions.md) D7 explains the split. [data-type-catalog.md](data-type-catalog.md) compares 15 public schemas (FHIR, OMOP, openEHR, Fasten, i2b2) to show why every production system separates conditions from observations. [table-designs.md](table-designs.md) has the DDL.

**How does authorization work?**
[decisions.md](decisions.md) D9 (XACML triad), D21 (audience-split errors), D22 (OpenFGA as PDP), D23 (outage behavior), D24 (LRU cache). [consent-model.md](consent-model.md) covers grants, purposes, 42 CFR Part 2 sensitive categories, and break-glass. [data-plane.md](data-plane.md) has the Repository signatures that enforce it.

**How does data flow in and out?**
[data-plane.md](data-plane.md) covers the full stack: Repository.read() and .write() signatures (section 1), query composition and timeline (section 2), pagination (section 4), ingest pipeline with FHIR Subscription (section 5), transactional outbox (section 6).

**What's the schema architecture?**
[diagrams.md](diagrams.md) has three zoom levels (tier, domain, ERD). [identity-model.md](identity-model.md) covers the persons hub + role satellites. [design-patterns.md](design-patterns.md) catalogs which patterns Health OS uses, which it should adopt, and which it avoids.

**How do third parties integrate with Health OS?**
[interoperability-surface.md](interoperability-surface.md) covers the four integration layers: data exchange, authorization (SMART on FHIR), discovery, and intelligence (CDS Hooks). [fhir-surface.md](fhir-surface.md) captures the build-vs-embed decision (build, own the moat), the multi-standard advantage, and the phased build plan post-seed.

**Can the platform serve other verticals?**
[platform-malleability.md](platform-malleability.md) has the 60/40 platform-vs-vertical thesis and pivot catalog. [vertical-billing.md](vertical-billing.md) is a worked example: medical billing as a patient-facing vertical, scoring 85% primitive reuse. The evaluation template at the end is reusable for any vertical.

**How were these decisions made?**
[decision-log.md](decision-log.md) shows the collaborative process: human intent → Claude reasoning → corrections → outcome. Evidence for [AI-WORKFLOW.md](../AI-WORKFLOW.md)'s methodology claims.

**Which existing ADRs need updating?**
[adr-alignment.md](adr-alignment.md) audits 5 target ADRs (1001, 1005, 2001, 2006, 3005) against the hub. ADR-1001 (Dolt single-table) and ADR-2006 (two-layer auth) need supersedes; ADR-1005 (Qdrant) and ADR-2001 (FHIR canonical) need refines; ADR-3005 (mini-project scope) stays as historical record. Also flags 6 other ADRs likely to need refinement and 4 new Health OS ADRs worth drafting.

**What ships when?**
[scoping.md](scoping.md) — locked. M3 MVP foundation (38 tables), M4 platform inflection (SMART on FHIR + outbound API), Series A scale, and triggered scale events. Uses a 3-axis framework: cost to add now / cost to defer / promotion trigger.

## Files

### Decisions

- [decisions.md](decisions.md) — 27 locked decisions (D1-D27) with pattern citations
- [open-questions.md](open-questions.md) — 22 resolved questions (historical record)
- [design-queue.md](design-queue.md) — 47 CSA proposals, all in Designed status
- [scoping.md](scoping.md) — phased rollout: M3 / M4 / Series A / scale events

### Design

- [data-plane.md](data-plane.md) — Repository, Data API, storage plane (7 sections, all locked)
- [table-designs.md](table-designs.md) — DDL for 12 new tables
- [identity-model.md](identity-model.md) — persons / org_roles / practitioners / patients
- [consent-model.md](consent-model.md) — access_grants, purposes, sensitive categories
- [diagrams.md](diagrams.md) — ASCII diagrams at 3 zoom levels
- [database-substrate.md](database-substrate.md) — Dolt vs Postgres evaluation for M3 foundation
- [semantic-search.md](semantic-search.md) — Embedding strategy, hybrid search, agent RAG pipeline
- [interoperability-surface.md](interoperability-surface.md) — External integration points, SMART on FHIR, outbound API
- [fhir-surface.md](fhir-surface.md) — Build strategy for FHIR compliance surface (own the moat, multi-standard, Python-first)
- [vertical-billing.md](vertical-billing.md) — Medical billing vertical evaluation (example + template)

### Process

- [decision-log.md](decision-log.md) — Human-AI collaborative reasoning provenance
- [adr-alignment.md](adr-alignment.md) — Audit of existing ADRs against hub; supersede/refine/align verdicts per ADR

### Context

- [endpoint-inventory.md](endpoint-inventory.md) — 25 API endpoints mapped to tables
- [scenarios.md](scenarios.md) — 7 end-to-end walkthroughs
- [data-type-catalog.md](data-type-catalog.md) — coverage matrix against 15 public schemas
- [references.md](references.md) — external schema and regulatory references
- [design-patterns.md](design-patterns.md) — pattern catalog with CSA mapping
- [design-lessons.md](design-lessons.md) — cross-schema patterns and anti-patterns
- [platform-malleability.md](platform-malleability.md) — "can the platform serve more than health?"
