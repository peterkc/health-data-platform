# FHIR Surface — Build Strategy for Health OS API

**Status**: Strategic intent — direction locked, implementation post-M3 (post-seed)
**Purpose**: Capture the decision to build (not embed or buy) the FHIR compliance surface, define the multi-standard moat, and verify M3 design doesn't block the path.
**Audience**: Architecture alignment; FHIR implementation planning; platform positioning.
**Companion to**: [interoperability-surface.md](interoperability-surface.md) (integration gap analysis), [data-plane.md](data-plane.md) (Repository that FHIR wraps), [database-substrate.md](database-substrate.md) (PostgreSQL 18 target), [platform-malleability.md](platform-malleability.md) (positioning tiers)

## How to read this file

- "Decision" states the locked direction and why
- "The moat" explains what makes Health OS's FHIR surface different from existing servers
- "Multi-standard" maps the international landscape and Health OS's canonical-layer advantage
- "Path from M3" verifies current design doesn't block future build
- "Scoped build plan" outlines what ships and in what order

## 1. Decision

**Build the FHIR compliance surface. Own it. No sidecar, no managed service, no embedded third-party server.**

Why:

- **Moat**: The consent-aware, trust-graded, multi-standard projection layer is the differentiator. Embedding HAPI or Medplum gives that surface to someone else's software.
- **P4 Ownership**: Cloud-agnostic. No vendor lock-in. No new BAA relationships for the API surface.
- **Control**: Profile validation rules, search parameter behavior, extension fields, and authorization flow are all product decisions. Owning the code means owning those decisions.

What we evaluated and rejected:

| Option                                      | Why rejected                                                                                                                                                                                    |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Embed HAPI FHIR (Java sidecar)              | Adds Java to the stack. HAPI's consent model is role-based, not grant-based — would need to bypass HAPI's auth and pipe through Health OS's PDP anyway. Operational complexity of two services. |
| Embed Medplum (TypeScript)                  | Postgres-native (good), but Medplum's storage schema is its own — Health OS would need to sync data between two Postgres schemas in the same database. Complexity without control.              |
| Azure Health Data Services / AWS HealthLake | New BAA. Vendor lock-in. Violates P4. Loses the moat.                                                                                                                                           |

## 2. The moat — consent-aware, trust-graded, multi-standard

Existing FHIR servers are format routers: FHIR in, FHIR out. Health OS is a normalization engine that projects FHIR (and other standards) as views over a canonical model.

| Capability                  | Existing FHIR servers         | Health OS                                                                                                                               |
| --------------------------- | ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| FHIR R4 CRUD                | Yes                           | Yes                                                                                                                                     |
| Consent-filtered responses  | No — role-based access only   | Every query filtered by access_grants. 42 CFR Part 2 categories excluded unless explicitly granted. Sensitive data never leaks via API. |
| Trust-annotated data        | No                            | FHIR extension fields carry trust_level, source_system, provenance. Consumers know data reliability.                                    |
| Multi-standard ingest       | No — FHIR only                | HL7 v2, C-CDA, FHIR R4, openEHR, device APIs. Translate once at ingest.                                                                 |
| Multi-standard output       | No — FHIR only                | FHIR R4 (US/EU/UK/AU Core profiles), IPS, OMOP CDM, openEHR, C-CDA. Serve any standard at the edge.                                     |
| Multi-profile validation    | Single profile per deployment | Same resource validated against multiple profiles (US Core + AU Core).                                                                  |
| AI as first-class consumer  | No                            | CDS Hooks, agent RAG pipeline, semantic search. Same PDP, same consent model.                                                           |
| Patient-controlled app auth | SMART (basic)                 | SMART scopes map to access_grants with category/source/HOM filtering. Granularity no SMART server offers.                               |

**The pitch**: Health OS isn't building a FHIR server. Health OS is building a consent-aware health data engine that speaks every standard. The FHIR surface is a distribution channel, not the product.

## 3. Multi-standard landscape

Every region is converging on FHIR R4 with local profiles. The profiles add constraints but share the same base.

| Region       | Standard | Profile             | Mandate                           |
| ------------ | -------- | ------------------- | --------------------------------- |
| US           | FHIR R4  | US Core 6.1.0       | ONC 21st Century Cures            |
| EU           | FHIR R4  | EU Core (IPS-based) | EU Health Data Space (EHDS)       |
| UK           | FHIR R4  | UK Core             | NHS Digital                       |
| Australia    | FHIR R4  | AU Core             | Australian Digital Health Agency  |
| Canada       | FHIR R4  | CA Core             | Provincial mandates (ON, BC)      |
| Brazil       | FHIR R4  | BR Core             | RNDS national health network      |
| India        | FHIR R4  | ABDM profiles       | Ayushman Bharat Digital Mission   |
| Japan        | FHIR R4  | JP Core             | Ministry of Health                |
| Cross-border | IPS      | HL7 IPS 1.1         | G7 adopted                        |
| Research     | openEHR  | Archetypes          | Norway, Slovenia, clinical trials |
| Analytics    | OMOP CDM | v5.4                | OHDSI network                     |

### Health OS's canonical-layer advantage

```
Ingest (any standard)          Canonical Layer           Serve (any standard)
┌──────────────────┐     ┌─────────────────────┐     ┌────────────────────┐
│ FHIR R4          │     │                     │     │ FHIR R4 + profiles │
│ HL7 v2           │     │  DomainRecords      │     │ IPS                │
│ C-CDA            │────►│  + trust_level      │────►│ OMOP CDM           │
│ openEHR          │     │  + access_grants    │     │ openEHR            │
│ Device APIs      │     │  + PDP enforcement  │     │ C-CDA              │
│ Regional FHIR    │     │                     │     │ Regional profiles  │
└──────────────────┘     └─────────────────────┘     └────────────────────┘
```

Adding a new country profile = new validation rules + output adapter. Not an architecture change. This is what D26 (version-agnostic adapter interface) was designed for.

## 4. Technology — Python-first

**All-Python for the FHIR surface. No polyglot, no Rust, no sidecar.**

| Concern                        | Why Python is sufficient                                                                                                      |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| FHIR resource models           | `fhir.resources` — Pydantic v2 models for all R4 resources. Already Rust-accelerated under the hood via `pydantic-core`.      |
| FHIR serialization performance | At pre-seed scale (thousands of patients), Python handles this. Bottleneck is PDP eval + database queries, not serialization. |
| OAuth / SMART on FHIR          | `authlib` — mature Python OAuth 2.0 library.                                                                                  |
| Search parameter engine        | Greenfield in any language. SQL query builder in Python (SQLAlchemy or raw) is well-understood.                               |
| AI/ML pipeline                 | Python's core strength. Same process, same data models, no serialization boundary.                                            |
| Hiring                         | Python + FastAPI is the most common backend stack for health-tech startups.                                                   |

If profiling shows serialization is a bottleneck at scale: Pydantic v2's Rust core (pydantic-core) already handles validation and serialization in compiled Rust. No rewrite needed — it's already there.

## 5. Path from M3

M3 ships the foundation. Nothing in the current design blocks the FHIR surface build.

| M3 design element                         | Why it enables the FHIR surface                                         | Reference                      |
| ----------------------------------------- | ----------------------------------------------------------------------- | ------------------------------ |
| DomainRecord (Health OS-native, not FHIR) | Canonical model that FHIR projects from. Clean separation.              | D26                            |
| Repository.read()/write()                 | Interface the FHIR REST layer wraps. No FHIR leakage into data layer.   | data-plane.md §1               |
| PostgreSQL 18                             | Search param engine builds SQL on PG. uuidv7() PKs are FHIR-native IDs. | database-substrate.md          |
| access_grants + OpenFGA                   | SMART scopes map to grants. Consent-filtered FHIR responses.            | interoperability-surface.md §3 |
| Transactional outbox (§6)                 | FHIR Subscription event source.                                         | data-plane.md §6               |
| ref_source_adapters (D6)                  | Multi-standard ingest adapters plug in.                                 | table-designs.md               |
| trust_level on silver tables              | FHIR extension fields carry trust metadata.                             | ADR-2007                       |
| uuidv7() PKs                              | Stable, externally-referenceable FHIR resource IDs.                     | database-substrate.md          |
| HMAC cursor pagination (§4)               | Maps to FHIR Bundle.link.next.                                          | data-plane.md §4               |
| D26 adapter interface                     | Version-agnostic format adapter. R4 first, R5 additive, profile-based.  | decisions.md                   |

**No blockers identified.** The DomainRecord ↔ FHIR adapter separation (D26) is the key architectural decision that keeps the path open.

## 6. Scoped build plan (post-M3)

Not a roadmap — a scope definition. Build order TBD during M4 planning.

### Phase 1: FHIR R4 read API (US Core)

| Component                      | Description                                                                            | Effort signal        |
| ------------------------------ | -------------------------------------------------------------------------------------- | -------------------- |
| FHIR REST endpoints            | `/fhir/{Resource}` for 11 D7 silver table types                                        | Medium               |
| DomainRecord → FHIR R4 adapter | D26 implementation. Health OS-native to FHIR JSON.                                     | Medium               |
| Search parameters (~80-100)    | Per-resource query builder. Maps FHIR search params to Repository.read_many() filters. | High — the hard part |
| CapabilityStatement            | `/metadata` declaring supported resources + params                                     | Low                  |
| US Core profile validation     | Validate responses against US Core 6.1.0 profiles                                      | Medium               |

### Phase 2: SMART on FHIR + app authorization

| Component                 | Description                                           | Effort signal |
| ------------------------- | ----------------------------------------------------- | ------------- |
| OAuth 2.0 server          | Token issuance, refresh, revocation (authlib)         | Medium        |
| SMART configuration       | `.well-known/smart-configuration`                     | Low           |
| App registration          | registered_apps table                                 | Low           |
| Patient consent UI        | "App X wants to read your medications" → access_grant | Medium        |
| Scope-to-grant translator | SMART scopes → OpenFGA tuples                         | Medium        |

### Phase 3: Multi-standard output + international profiles

| Component              | Description                                    | Effort signal      |
| ---------------------- | ---------------------------------------------- | ------------------ |
| IPS export adapter     | DomainRecord → IPS Composition                 | Medium             |
| EU/UK/AU Core profiles | Profile-specific validation rules + extensions | Medium per profile |
| C-CDA output adapter   | DomainRecord → C-CDA XML                       | Medium             |
| openEHR output adapter | DomainRecord → openEHR composition (CSA-41)    | High               |
| OMOP CDM export        | DomainRecord → OMOP tables (D8, CSA-9)         | Already scoped     |

### Phase 4: Advanced operations

| Component                    | Description                          | Effort signal                 |
| ---------------------------- | ------------------------------------ | ----------------------------- |
| \$export (Bulk Data)         | Async job → NDJSON                   | Medium                        |
| FHIR Subscription (outbound) | Topic-based notifications via outbox | Medium                        |
| CDS Hooks host               | Trigger points + service registry    | Medium                        |
| \$everything                 | Patient-complete bundle              | Low (composes from read_many) |

## 7. What this means for M3

**No changes to M3 scope.** M3 ships:

- Repository with DomainRecord (canonical model)
- PDP with access_grants (consent layer)
- Source adapters for ingest (D6)
- PostgreSQL 18 with audit triggers
- The data layer the FHIR surface will wrap

M3's job is to make the foundation solid. The FHIR surface is the first major post-seed build.

## Related

- [interoperability-surface.md](interoperability-surface.md) — Integration gap analysis (SMART, outbound API, CDS Hooks)
- [data-plane.md](data-plane.md) — Repository interface the FHIR surface wraps
- [database-substrate.md](database-substrate.md) — PostgreSQL 18 target
- [decisions.md](decisions.md) — D26 (FHIR R4 adapter), D22 (OpenFGA), D9 (XACML triad)
- [platform-malleability.md](platform-malleability.md) — PHR → Health CMS → Health OS positioning
- [semantic-search.md](semantic-search.md) — Search API that FHIR surface exposes
