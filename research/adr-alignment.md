# ADR Alignment Audit

**Status**: Audit complete 2026-04-16 — follow-on supersede/refine pass pending
**Purpose**: Audit existing ADRs for staleness against the locked mvp-schema hub. Produce a supersede / refine / align / no-change verdict per ADR, with specific deltas and proposed actions.
**Audience**: Engineers implementing M3; reviewers tracing decisions back to ADRs; future-me drafting supersede ADRs
**Companion to**: [scoping.md](scoping.md) (the driving research), [decisions.md](decisions.md) (hub decisions D1-D27), [database-substrate.md](database-substrate.md), [fhir-surface.md](fhir-surface.md)

## How to read this file

- **Verdict column** is one of four: SUPERSEDE (direction reversed), REFINE (scope extended), ALIGN (consistent but framing needs update), NO-CHANGE (still correct).
- **Delta column** names the specific items where the ADR disagrees with the hub.
- **Action column** is the proposed next step — either a new supersede ADR, an in-place refine edit, or a cross-reference addition.
- A SUPERSEDE verdict does NOT discard the historical record. The old ADR stays with a `superseded_by` header pointing to the new one.

## Audit summary

| ADR      | Area                          | Verdict   | Delta                                                                    | Action                                               |
| -------- | ----------------------------- | --------- | ------------------------------------------------------------------------ | ---------------------------------------------------- |
| **1001** | Dolt + single health_records  | SUPERSEDE | Substrate: Dolt→Postgres 18. Schema: single-table→D7 FHIR split.         | New ADR superseding 1001; fold in D28 substrate      |
| **1005** | Nomic + Qdrant                | REFINE    | Nomic stays (HIPAA local). Qdrant→pgvector (Postgres substrate).         | New ADR superseding vector-store half; keep Nomic    |
| **2001** | FHIR R4 canonical + medallion | REFINE    | Canonical is neutral, not FHIR. FHIR is one projection. Medallion stays. | New ADR reframing canonical; preserve medallion core |
| **2006** | Two-layer authorization       | SUPERSEDE | 2-layer RBAC+Consent → 4-layer XACML triad (PEP+PDP+PAP+PIP) per D9.     | New ADR for XACML triad + OpenFGA PDP                |
| **3005** | Mini-project scope matrix     | NO-CHANGE | Governs the prior mini-project trial, not Health OS product. Different scale & scope. | Add cross-reference pointing to hub scoping.md       |

## Detailed findings

### ADR-1001 — Dolt as Single Versioned Database with Record-Type Discriminator

**Status quo**: Dolt (MySQL wire protocol) + single `health_records` table + `record_type` discriminator. HIPAA audit via `dolt_log`. Time-travel via `AS OF`. TimescaleDB as scaling fallback.

**Hub reality**:

- [database-substrate.md](database-substrate.md) targets **PostgreSQL 18.3** — uuidv7() PKs, temporal PK/FK constraints, RETURNING OLD/NEW, pgvector, AIO, OAuth 2.0 auth.
- [decisions.md](decisions.md) D7 **splits `health_records` into six FHIR-aligned tables** (observations + conditions + medications + allergies + immunizations + family_history) and promotes record_type away from being a discriminator.
- HIPAA audit replaced by **Postgres audit triggers** writing to `audit_batches` + `audit_changes` (see [data-plane.md](data-plane.md) §6.4).
- Time-travel replaced by **temporal PK/FK** native in Postgres 18.
- [decision-log.md](decision-log.md) records the substrate pivot as collaborative reasoning.

**Delta**:

1. Substrate reversed (Dolt → Postgres 18).
1. Schema reversed (single-table → D7 split).
1. Audit mechanism changed (dolt_log → Postgres triggers).
1. Time-travel mechanism changed (AS OF → temporal constraints).
1. Scaling fallback changed (TimescaleDB → pgvector + AIO + B-tree skip scan).

**Verdict**: **SUPERSEDE** — both core decisions (substrate and schema) reversed.

**Proposed action**:

1. Draft **ADR-1006 (or renumber)**: "PostgreSQL 18 substrate with FHIR-aligned table split". Cites 1001 in `superseded_by` header. Fold in pending D28 team alignment.
1. Update 1001 frontmatter: `status: Superseded by ADR-XXXX, 2026-04-16`.
1. Keep 1001 intact for historical record.

______________________________________________________________________

### ADR-1005 — Nomic Embed + Qdrant for Semantic Search

**Status quo**: Nomic Embed v1.5 (local, HIPAA by architecture) + Qdrant (payload filtering). Option V2 (pgvector) rejected because "platform uses Dolt (MySQL-compatible), not PostgreSQL."

**Hub reality**:

- [decisions.md](decisions.md) D5 locks embeddings in a **separate `health_record_embeddings` table** — model-specific, multi-model support.
- [table-designs.md](table-designs.md) references **pgvector HNSW + IVFFlat** as the index strategy.
- With Postgres 18 as substrate (see 1001 supersede), the original pgvector rejection reasoning is **moot**.
- Nomic rationale (HIPAA by architecture, Matryoshka dimensions, local inference) is **still load-bearing** — the hub research did not revisit embedding model choice.

**Delta**:

1. Vector store reversed (Qdrant → pgvector).
1. Nomic embedding model retained.
1. Matryoshka dimension flexibility retained.
1. Service count impact changes: pgvector adds zero services (co-located with Postgres), vs. Qdrant as service 8 of 8.

**Verdict**: **REFINE** — vector store half superseded; embedding model half retained.

**Proposed action**:

1. Draft **ADR-1010 (or renumber)**: "pgvector for embedding storage and search". Cites 1005's vector-store half in `superseded_by`. Keeps Nomic embedding references.
1. Update 1005 frontmatter: `status: Partially superseded by ADR-XXXX (vector store), 2026-04-16`.
1. Embedding model decision remains load-bearing; no action needed on Nomic side.

______________________________________________________________________

### ADR-2001 — FHIR R4 Canonical Model with Three-Layer Medallion Schema

**Status quo**: FHIR R4 as canonical vocabulary + bronze (raw_payloads) / silver (health_records) / gold (daily_summaries) medallion.

**Hub reality**:

- [fhir-surface.md](fhir-surface.md) **reframes canonical**: the canonical layer is neutral (Health OS Model), and FHIR is one of several projections (IPS, openEHR, OMOP CDM, C-CDA, 11 country profiles).
- Multi-standard is a **competitive moat**, not an implementation detail. "Build the FHIR surface, own the moat" — no sidecar, no managed service, no embed.
- Medallion preserved: bronze (raw_payloads), silver (D7 split tables), gold (daily_summaries).
- D7 splits silver from a single table into six FHIR-aligned tables.
- D15 adds **compositions** tables (FHIR Composition) as a document-structure layer.
- D26 locks **FHIR R4 first, R5 additive later** — but now via a version-agnostic adapter interface.
- D14 / CSA-6 adds `code_text` alongside `code_display` (FHIR CodeableConcept) on every silver table.

**Delta**:

1. Canonical framing: FHIR-as-canonical → neutral-canonical with FHIR as a projection.
1. Silver: single `health_records` → D7 split.
1. Composition support added (D15 — not in 2001).
1. Multi-standard positioning (IPS, openEHR, OMOP, C-CDA, country profiles) not addressed in 2001.
1. Code_text column additions (D14 / CSA-6) not in 2001.
1. FHIR version adapter interface (D26) formalized.

**Verdict**: **REFINE** — medallion architecture preserved; canonical framing extended; D7/D14/D15/D26 are additive.

**Proposed action**:

1. Draft **ADR-2012 (or renumber)**: "Canonical Health OS Model with multi-standard projection". Cites 2001 in `refined_by` header (or `superseded_by` if full replacement is cleaner). Reframes canonical as neutral + captures multi-standard moat.
1. Update 2001 frontmatter: `status: Refined by ADR-XXXX, 2026-04-16` (stays Accepted for historical medallion reference).
1. Cross-link new ADR to fhir-surface.md, interoperability-surface.md, and decisions D7 / D14 / D15 / D26.

______________________________________________________________________

### ADR-2006 — Two-Layer Authorization (RBAC + Consent)

**Status quo**: Layer 1 RBAC (Auth0 JWT `permissions` or `org_roles.permissions`) + Layer 2 Consent (`access_grants`). AND gate. Sensitive categories opt-in. HOM-node scoping. Grant categories + HOM nodes as metadata.

**Hub reality**:

- [decisions.md](decisions.md) D9 introduces the **full XACML triad**: PEP (FastAPI dependency) + PDP (AuthorizationService.evaluate) + PAP (new `policy_rules` table) + PIP (`access_grants`, `ref_hom_nodes`, `sensitive_categories`, CSA-40 legal_basis).
- D10 normalizes `access_grants` multi-value fields into child tables (`access_grant_sources`, `access_grant_categories`, `access_grant_hom_nodes`).
- D18 adds **agent identity** as a first-class persons satellite; PDP evaluates agent requests via the same engine as humans.
- D20 adds **derived-data transitive consent** (pattern, not a table).
- D21 adds **audience-split errors** (NotFound for non-patient-facing, PermissionDenied for patient-facing).
- D22 selects **OpenFGA on Postgres** as the PDP implementation + Tier 1 LRU cache.
- D23 adds **graceful degradation** with circuit breaker + TTL-bounded stale permit.
- D24 sizes + keys + evicts the LRU cache.
- D25 aggregates **batch PDP** (partial-permit on collections, binary on items).
- CSA-40 adds **international privacy framework** — `legal_basis` enum + `jurisdiction` — as day-one scope.
- CSA-1 `access_log` captures every PDP decision with matched rule_id.
- [interoperability-surface.md](interoperability-surface.md) adds **SMART on FHIR scopes** as an additional layer at the API boundary.

**Delta**:

1. Architecture: 2 layers → 4 layers (XACML triad) → plus SMART on FHIR at API boundary.
1. Policy storage: implicit in role defaults → explicit `policy_rules` table (PAP).
1. PDP implementation: ad-hoc middleware → **OpenFGA** with relationship tuples.
1. Cache: none specified → Tier 1 LRU (10k / 60s TTL / action-aware key) with measure-first Tier 2.
1. Outage behavior: undefined → graceful degradation + circuit breaker + 42 CFR Part 2 strict-fail exception.
1. Derived data: not addressed → transitive consent via source dereference.
1. International jurisdictions: not addressed → CSA-40 `legal_basis` + `jurisdiction` day-one scope.
1. Batch semantics: not specified → partial-permit + `filtered_count` per D25.
1. Audience-split errors: not addressed → D21 hybrid classification.
1. Agent identity: "AI agents go through both layers" → D18 persistent `agents` satellite + `agent_sessions` log.

**Verdict**: **SUPERSEDE** — the architectural shape fundamentally changed from a two-check middleware pattern to a full XACML triad with OpenFGA PDP. The PoC two-layer model is inadequate for international scope (CSA-40) and for the Health OS agent-first design (D18).

**Proposed action**:

1. Draft **ADR-2013 (or renumber)**: "Authorization as XACML triad — PEP + PDP + PAP + PIP with OpenFGA". Cites 2006 in `superseded_by`.
1. Draft companion ADRs (optional, or sections within the main supersede):
   - D22 OpenFGA PDP selection (could stand alone as an ADR).
   - D23 Graceful degradation (could stand alone).
   - D24 LRU cache sizing (could be an appendix or internal doc).
1. Update 2006 frontmatter: `status: Superseded by ADR-XXXX, 2026-04-16`.
1. Keep 2006 intact — it is still the cleanest statement of the two-layer rationale and the RBAC/consent separation argument.

______________________________________________________________________

### ADR-3005 — Mini-Project Scope Matrix (Build / Stub / Skip)

**Status quo**: Consolidated build/stub/skip matrix for the prior mini-project trial across its component packages. Mapped to M1 (~3h), M2 (~10h), M3 (~25h) milestones. Explicitly for the trial repo.

**Hub reality**:

- [scoping.md](scoping.md) locks Health OS product phasing at M3 MVP foundation (38 tables + 12 columns + 11 patterns), M4 platform inflection, Series A, scale events.
- Different repo (Health OS product, not the mini-project trial).
- Different time scale (milestones in months, not hours).
- Different artifact scope (production platform, not founding-engineer trial).
- The `record_type` discriminator row in 3005's core section is stale (D7 split), but 3005 describes the trial deliverable as built, not the product roadmap.

**Delta**:

1. No conflict with Health OS product scoping — 3005 governs a different artifact at a different scale.
1. The specific items in 3005 (e.g., "record_type discriminator", "Dolt session factory", "SQL search sufficient at demo scale") describe **what was built for the trial** — accurate as historical record, stale as forward-looking guidance.

**Verdict**: **NO-CHANGE** on the decision; **cross-reference needed** to prevent future readers from treating 3005 as Health OS product scope.

**Proposed action**:

1. Add a **Related** block entry to 3005 pointing to `../research/mini-project/mvp-schema/scoping.md` (path relative to the `adr/` directory) with a note: "3005 governs the prior mini-project trial; Health OS product scoping lives in scoping.md".
1. Add a corresponding entry in scoping.md's "Companion to" header pointing back to 3005 for the trial-phase scope record.
1. No supersede needed. Both coexist.

______________________________________________________________________

## Broader ADR inventory — beyond the 5 audited

The audit focused on the 5 ADRs where hub research indicates likely staleness. Other ADRs may also need review:

| ADR       | Area                            | Likely status       | Rationale                                                           |
| --------- | ------------------------------- | ------------------- | ------------------------------------------------------------------- |
| 0001      | Guiding principles              | ALIGN (cite hub)    | P1-P5 propagated to hub; add "cited by mvp-schema hub" note.        |
| 1002      | Auth0 identity provider         | REFINE or SUPERSEDE | 2006 supersede changes JWT permissions flow; Auth0 may stay as IdP. |
| 1003      | Dagster ETL orchestration       | REFINE              | Ingest pipeline (data-plane.md §5) may shift DAG structure.         |
| 1004      | Pydantic AI agent framework     | REFINE              | D18 adds persistent agents satellite + sessions log.                |
| 1006      | NATS JetStream event bus        | ALIGN               | Outbox pattern (CSA-45) complements NATS; no conflict.              |
| 1007      | FastAPI + Pydantic              | ALIGN               | Data-plane §1 confirms FastAPI envelope versioning D27.             |
| 1008      | MinIO / S3 object storage       | ALIGN               | D3 documents pattern builds on 1008 content-addressed storage.      |
| 1009      | Redis caching                   | REFINE              | D24 Tier 1 in-process LRU; Tier 2 Valkey deferred — not Redis.      |
| 2002      | Document extraction pipeline    | ALIGN               | D3 documents + D15 compositions build on 2002.                      |
| 2003      | HOM as schema                   | REFINE              | D17 formalizes ref_hom_nodes PK + versioning + retirement chain.    |
| 2004      | Plugin architecture             | ALIGN               | D6 ref_source_adapters is the plugin registry; consistent.          |
| 2005      | Multi-tenant organization model | ALIGN               | D1 persons + org_roles extends 2005 without conflict.               |
| 2007      | Conflict resolution trust model | REFINE              | D19 adds `ref_reconciliation_rules` at gold tier; extends 2007.     |
| 2008      | Service decomposition           | ALIGN (re-read)     | Check against data-plane.md service boundaries.                     |
| 2009      | Compliance-first design policy  | ALIGN               | HIPAA / GDPR / 42 CFR Part 2 hub references trace back here.        |
| 2010      | Unit storage and conversion     | ALIGN               | Hub does not revisit unit conversion.                               |
| 2011      | HITRUST certification strategy  | ALIGN               | Hub aligns on HIPAA; HITRUST path unchanged.                        |
| 3001-3007 | Execution / CI / repo config    | ALIGN               | Tooling, not architecture; hub does not conflict.                   |
| 4001      | ADR standard                    | ALIGN               | Format standard; no content drift.                                  |

**Recommendation**: After the 5-ADR supersede/refine pass (task 174), do a second audit pass over 1002, 1003, 1004, 1009, 2003, 2007 — these have higher likelihood of needing refinement. Remaining ADRs are either tooling or consistent with the hub.

## New ADRs to draft (from hub decisions not yet in ADR form)

| Source                                                                                    | Proposed ADR                                                                      | Priority |
| ----------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | -------- |
| [platform-malleability.md](platform-malleability.md) + [fhir-surface.md](fhir-surface.md) | Health OS platform strategy (PHR → Health CMS → Health OS tier; FHIR as moat)     | **High** |
| [database-substrate.md](database-substrate.md)                                            | D28: PostgreSQL 18 substrate (pending team alignment)                             | **High** |
| [fhir-surface.md](fhir-surface.md)                                                        | FHIR surface: build, don't embed (no sidecar / managed / library)                 | **High** |
| [interoperability-surface.md](interoperability-surface.md)                                | Multi-standard canonical projection (IPS, openEHR, OMOP, C-CDA, country profiles) | **High** |
| D8 (analytics tier)                                                                       | OMOP CDM v5.4 analytics tier                                                      | Medium   |
| D9 (XACML triad)                                                                          | Already captured in 2006 supersede above                                          | Medium   |
| D17 (HOM versioning)                                                                      | ref_hom_nodes PK + tree_version + retirement                                      | Medium   |
| D18 (agent identity)                                                                      | Persistent agents satellite + agent_sessions                                      | Medium   |
| D22 (OpenFGA PDP)                                                                         | Already captured in 2006 supersede above                                          | Medium   |
| D23 (graceful degradation)                                                                | Already captured in 2006 supersede above, or standalone                           | Medium   |
| D21 (audience-split)                                                                      | Error model: NotFound vs PermissionDenied                                         | Medium   |

Priority reflects:

- **High**: Load-bearing for M3 build and for external storytelling and team alignment.
- **Medium**: Valuable for long-term traceability, but not blocking M3.

## Next steps

This audit completes task 173. The follow-on work splits into three tasks:

1. **Task 174** (supersede/refine pass) — draft the specific supersede / refine ADRs identified above. Use `Skill('adr')` for MADR format consistency.
1. **Task 175** (new Health OS ADRs) — draft Health OS platform strategy + D28 substrate + FHIR moat + multi-standard as standalone ADRs.
1. **Task 176** (D-series extraction) — draft the remaining D-series ADRs (D8, D17, D18, and any not folded into the supersedes).

Order recommendation: Task 174 first (supersedes touch more code than new ADRs), then task 175 (new direction ADRs), then task 176 (supplementary extractions). All three depend on this audit as input.
