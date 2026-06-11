# Interoperability Surface — Health OS Integration Points

**Status**: Design — defines external integration surface for Health OS as aggregator
**Purpose**: Catalog the integration points third parties need to connect with Health OS, map what exists vs. what's missing, and identify the standards that make Health OS a participant in the healthcare ecosystem rather than a closed data warehouse.
**Audience**: Architecture review; FHIR/SMART implementation planning; platform positioning ("others integrate with us").
**Companion to**: [data-plane.md](data-plane.md) (internal read/write architecture), [decisions.md](decisions.md) (D9 XACML triad, D22 OpenFGA, D26 FHIR R4), [consent-model.md](consent-model.md) (access_grants that SMART scopes map to), [semantic-search.md](semantic-search.md) (search API surface)

## How to read this file

- "Positioning" explains why interoperability is architectural, not a feature
- "Four layers" is the integration taxonomy — scan for your concern (data, auth, discovery, intelligence)
- "Gap analysis" maps what the hub already covers vs. what's new work
- "SMART on FHIR" gets its own section — it's the linchpin

## 1. Positioning

Health OS's data-plane.md designs data flow *into* the platform (§5 ingest pipeline, source adapters, FHIR Subscription). That's half the story. An aggregator that only ingests is a data warehouse. An aggregator that exposes standardized read APIs, app authorization, and event streams is a platform.

The distinction matters for three audiences:

- **Patients** want third-party apps (nutrition trackers, care coordinators, family health dashboards) to read their Health OS data without re-uploading it
- **Providers** want their EHR workflows to query Health OS as a FHIR data source, not as a portal they log into separately
- **Developers** want to build on Health OS the same way they build on Epic's FHIR API or Apple HealthKit — standards-based, documented, sandboxed

Each audience requires a different integration layer. All four layers below must exist for Health OS to function as an aggregator.

## 2. Four integration layers

### Layer 1 — Data Exchange (what flows in and out)

| Direction    | Standard                                | Description                                      | Hub status             | Reference                                                               |
| ------------ | --------------------------------------- | ------------------------------------------------ | ---------------------- | ----------------------------------------------------------------------- |
| **Inbound**  | FHIR R4 write                           | Create/update clinical resources via REST        | Designed               | data-plane.md §5, D26                                                   |
| Inbound      | FHIR Subscription (R4)                  | Real-time push notifications from EHRs           | Designed               | data-plane.md §5 (HAPI + Synthea)                                       |
| Inbound      | FHIR Bulk Data (\$import)               | Backend-to-backend batch ingest                  | Not designed           | Complement to §5 pull adapters                                          |
| Inbound      | HL7 v2 (ADT, ORU, ORM)                  | Legacy hospital interfaces                       | Not designed           | ~60% of hospital integrations still use v2                              |
| Inbound      | C-CDA / CDA documents                   | Structured clinical document ingest              | Partial                | Documents table (D3) stores blob; parsing to silver tables not designed |
| Inbound      | Device APIs                             | HealthKit, Health Connect, Oura, Garmin, CGM     | Adapter pattern exists | ref_source_adapters (D6) — each device is a source                      |
| **Outbound** | FHIR R4 read API                        | Third-party apps query Health OS's clinical data | **Not designed**       | Repository.read() exists internally; external FHIR contract is new      |
| Outbound     | FHIR Bulk Data (\$export)               | Payer/researcher batch data extraction           | **Not designed**       | Backend services use case (NDJSON format)                               |
| Outbound     | IPS (International Patient Summary)     | Portable patient summary for cross-border care   | Proposed (CSA-47)      | GDPR Article 20 + HIPAA right-of-access                                 |
| **Events**   | Webhooks / FHIR Subscription (outbound) | Notify integrators when patient data changes     | Partial                | Outbox (§6) is internal; external subscription registry is new          |

**Biggest gap**: outbound FHIR read API. The Repository.read() interface (§1.1) returns DomainRecords; a FHIR adapter (D26) translates to FHIR R4 format at the Data API edge. But the external API contract — supported resources, search parameters, FHIR operations, pagination — is not specified.

### Layer 2 — Authorization (who's allowed)

| Concern                      | Standard      | Description                                              | Hub status       | Reference                                                                          |
| ---------------------------- | ------------- | -------------------------------------------------------- | ---------------- | ---------------------------------------------------------------------------------- |
| **App authorization**        | SMART on FHIR | OAuth 2.0 with FHIR-specific scopes for third-party apps | **Not designed** | Section 3 below                                                                    |
| **Patient consent for apps** | Consent API   | Patient manages which apps can access their data         | Partial          | access_grants exist (consent-model.md); no external API for apps to request grants |
| **Internal PDP**             | OpenFGA       | Policy decision point for all read/write operations      | Designed         | D22, data-plane.md §1                                                              |
| **Scope-to-grant mapping**   | Custom        | SMART scopes → access_grants purposes + categories       | **Not designed** | Connects Layer 2 to consent model                                                  |

SMART on FHIR is the single largest interoperability gap. Without it, third-party apps have no standards-compliant way to request patient-authorized access to Health OS's data. See section 3 for details.

### Layer 3 — Discovery (how integrators find and test)

| Component                         | Standard          | Description                                                                              | Hub status                                                               |
| --------------------------------- | ----------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| FHIR CapabilityStatement          | FHIR R4           | Machine-readable manifest: which resources, search params, operations Health OS supports | Not designed                                                             |
| `.well-known/smart-configuration` | SMART on FHIR     | Endpoint discovery for OAuth + FHIR authorization                                        | Not designed (depends on SMART)                                          |
| Developer sandbox                 | Custom            | Test environment with synthetic data                                                     | Partial — HAPI + Synthea in §5 for ingest testing; no outbound sandbox   |
| API documentation                 | OpenAPI / FHIR IG | Machine + human-readable API reference                                                   | Not designed                                                             |
| Rate limiting / SLAs              | Custom            | External rate limits, uptime commitments                                                 | Partial — Gateway + PEP in §7 covers internal; external SLAs not defined |

The CapabilityStatement is small work but required for FHIR compliance. Any FHIR client's first call is `GET /metadata` — that returns the CapabilityStatement, telling the client what the server supports.

### Layer 4 — Intelligence (value-add integrations)

| Component           | Standard                   | Description                                               | Hub status                                                                  |
| ------------------- | -------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------- |
| CDS Hooks           | HL7 CDS Hooks 2.0          | Third-party clinical decision support at trigger points   | Not designed                                                                |
| Semantic search API | Custom                     | External access to Repository.search() hybrid results     | Partial — search designed (semantic-search.md) but no external contract     |
| Agent API           | Custom                     | External AI agents access Health OS data through same PDP | Partial — D18 agent identity exists; external agent onboarding not designed |
| Event streaming     | FHIR Subscription / custom | Real-time data feed for analytics partners                | Partial — outbox (§6) handles internal events                               |

CDS Hooks lets external services fire at clinical decision points. A drug interaction checker, a cost transparency tool, a clinical guidelines engine — each registers a hook endpoint. Health OS provides patient context at the trigger point; the service returns a recommendation card. This is how Health OS becomes an operating system: other services run on it.

## 3. SMART on FHIR — the linchpin

### What it is

SMART on FHIR (Substitutable Medical Applications, Reusable Technologies) is the standard authorization framework for healthcare apps accessing FHIR data. Built on OAuth 2.0 with FHIR-specific extensions: clinical scopes, launch context, and patient-facing authorization.

ONC's 21st Century Cures Act info-blocking rule effectively mandates SMART on FHIR for any US health data platform. The SMART App Gallery has hundreds of apps that can connect to any SMART-enabled server.

### How it maps to Health OS's existing design

| SMART concept                                     | Health OS equivalent                                       | Gap                        |
| ------------------------------------------------- | ---------------------------------------------------------- | -------------------------- |
| **Clinical scopes** (`patient/Observation.read`)  | access_grants purposes + categories                        | Mapping layer needed       |
| **Launch context** (patient ID, encounter ID)     | GrantContext (actor_id, actor_kind, purpose, on_behalf_of) | Shape is compatible        |
| **Token introspection**                           | OpenFGA (D22) evaluates scope against grants               | Integration needed         |
| **Patient approval screen**                       | access_grants with `grantee_type = 'app'`                  | Extends D18 agent pattern  |
| **Standalone launch** (patient picks app)         | New — app registers, patient authorizes                    | OAuth server needed        |
| **EHR launch** (provider launches app in context) | New — Health OS as EHR-context provider                    | Deferred (provider-facing) |

### Scope-to-grant mapping

SMART scopes follow the pattern `{context}/{resource}.{action}`:

```
patient/Observation.read    → GrantContext(purpose='app_read') + resource_type filter
patient/Condition.read      → same grant, different resource_type
patient/MedicationRequest.* → read + write grant for medications
user/Patient.read           → practitioner-context grant (provider-facing)
```

Health OS's access_grants already support per-resource-type, per-category, per-source filtering. The mapping is:

| SMART scope component      | access_grants field                                                        |
| -------------------------- | -------------------------------------------------------------------------- |
| `patient/` context         | patient_id (the patient who authorized)                                    |
| Resource type              | categories or resource_type filter on read                                 |
| `.read` / `.write`         | Grant purpose (care, research, billing, app_read, app_write)               |
| Restricted scopes (`*.rs`) | categories array (sensitive categories excluded unless explicitly granted) |

### What Health OS needs to build

| Component                      | Description                                                                       | Effort signal |
| ------------------------------ | --------------------------------------------------------------------------------- | ------------- |
| OAuth 2.0 authorization server | Token issuance, refresh, revocation. Can use existing library (authlib, oauthlib) | Medium        |
| SMART configuration endpoint   | `.well-known/smart-configuration` JSON                                            | Small         |
| App registration               | `registered_apps` table (client_id, redirect_uris, allowed_scopes, approved_by)   | Small         |
| Patient authorization UI       | Consent screen: "App X wants to read your medications" → creates access_grant     | Medium        |
| Scope-to-grant translator      | Maps SMART scopes to OpenFGA tuples for PDP evaluation                            | Small-medium  |
| Token introspection middleware | PEP extracts token → resolves scopes → passes to Repository as GrantContext       | Small         |

### Phasing

| Phase    | Capability                              | Unlocks                                                     |
| -------- | --------------------------------------- | ----------------------------------------------------------- |
| **M3**   | None — SMART is post-MVP                | —                                                           |
| **M4**   | Standalone patient launch + read scopes | Third-party apps can read patient data with patient consent |
| **M5**   | Write scopes + EHR launch context       | Apps can write back; provider-facing launch                 |
| **Post** | Bulk FHIR + backend services auth       | Payer/researcher integrations                               |

SMART at M4 is the inflection point — it converts Health OS from a closed system to a platform.

## 4. Outbound FHIR read API

The ingest pipeline (§5) handles inbound. The outbound read API is the mirror: third-party apps querying Health OS's clinical data via standard FHIR REST.

### Relationship to Repository.read()

```
Third-party app
  |
  | GET /fhir/Patient/{pid}/Observation?code=2093-3
  |
  v
Data API (FHIR REST facade)
  |
  | Parse FHIR search params → ReadFilters
  | Extract GrantContext from SMART token
  |
  v
Repository.read_many(patient_id, grant_context, filters)
  |
  | PDP (D22) → filter by grant
  | Query composition (§2)
  |
  v
DomainRecord[] → FHIR adapter (D26) → FHIR Bundle response
```

The internal architecture already supports this flow. What's missing is the FHIR REST facade:

| Component                | Description                                        | Status                                    |
| ------------------------ | -------------------------------------------------- | ----------------------------------------- |
| FHIR resource endpoints  | `/fhir/{resource}` for each D7 silver table        | Not designed                              |
| FHIR search parameters   | `?code=`, `?date=`, `?patient=`, `?_count=`, etc.  | Maps to ReadFilters — not specified       |
| FHIR operations          | `$everything`, `$export`, `$validate`              | Not designed                              |
| FHIR Bundle response     | Paginated search results in FHIR Bundle format     | HMAC cursor (§4) maps to Bundle.link.next |
| FHIR CapabilityStatement | `/metadata` declaring supported resources + params | Not designed                              |
| Content negotiation      | `Accept: application/fhir+json`                    | Standard                                  |

### Supported resources (from D7 silver tables)

| FHIR Resource       | Health OS table      | Search parameters (minimum)                 |
| ------------------- | -------------------- | ------------------------------------------- |
| Patient             | patients (+ persons) | \_id, identifier, name, birthdate           |
| Observation         | observations         | patient, code, date, category, \_count      |
| Condition           | conditions           | patient, code, clinical-status, onset-date  |
| MedicationStatement | medications          | patient, code, status, effective            |
| AllergyIntolerance  | allergies            | patient, code, clinical-status, criticality |
| Immunization        | immunizations        | patient, vaccine-code, date, status         |
| FamilyMemberHistory | family_history       | patient, relationship, condition-code       |
| Encounter           | encounters           | patient, date, type, status                 |
| DocumentReference   | documents            | patient, type, date, category               |
| CarePlan            | care_plans           | patient, status, category                   |
| Goal                | goals                | patient, lifecycle-status, target-date      |

### Conformance level

ONC certification requires specific USCDI data classes and FHIR US Core profiles. For MVP (M3), Health OS does not need ONC certification. But designing the outbound API to align with US Core means certification is a configuration step later, not an architecture change.

## 5. Event subscriptions (outbound)

The transactional outbox (§6) guarantees internal event delivery. External event subscriptions let third-party apps receive notifications when patient data changes.

### Two patterns

| Pattern                          | Standard             | Use case                                                | Complexity                        |
| -------------------------------- | -------------------- | ------------------------------------------------------- | --------------------------------- |
| **Webhooks**                     | Custom               | Simple integrators, non-FHIR systems, billing platforms | Low — HTTP POST to registered URL |
| **FHIR Subscription** (outbound) | FHIR R4 Subscription | FHIR-native integrators, EHR systems, care coordination | Medium — topic-based with filters |

### Architecture

```
Repository.write() → outbox event
  |
  v
Event dispatcher (reads outbox)
  |
  +→ Internal consumers (embedding worker, gold refresh, etc.)
  |
  +→ External subscription registry
       |
       +→ Webhook: POST {callback_url} with event payload
       +→ FHIR Subscription: POST {endpoint} with FHIR Bundle notification
```

The external subscription registry is a new table:

| Field          | Type        | Description                                             |
| -------------- | ----------- | ------------------------------------------------------- |
| id             | UUID        | Subscription ID                                         |
| app_id         | UUID FK     | registered_apps (SMART app that owns this subscription) |
| patient_id     | UUID FK     | Scoped to one patient (consent-bound)                   |
| resource_types | VARCHAR[]   | Which resource changes to notify about                  |
| callback_url   | TEXT        | Where to POST notifications                             |
| format         | ENUM        | 'webhook' or 'fhir_subscription'                        |
| status         | ENUM        | active / paused / error / expired                       |
| secret         | TEXT        | HMAC secret for webhook signature verification          |
| created_at     | TIMESTAMPTZ |                                                         |
| expires_at     | TIMESTAMPTZ | Subscriptions must expire (no perpetual callbacks)      |

Consent-bound: a subscription can only fire for data the app's access_grant covers. If the patient revokes the grant, the subscription pauses automatically.

## 6. CDS Hooks (clinical decision support)

CDS Hooks is a lightweight REST-based protocol. At specific trigger points (patient-open, order-select, medication-prescribe, appointment-book), the host system calls registered CDS services with patient context. The service returns "cards" — suggestions, warnings, links.

### Why it matters for Health OS

Health OS's AI agent (D18) handles internal clinical reasoning. CDS Hooks opens that surface to external intelligence: drug interaction databases, clinical practice guidelines, insurance formulary checks, cost transparency tools. The agent can invoke hooks too — it becomes both a CDS consumer and a host.

### Architecture sketch

```
Trigger point (patient chart opened, medication selected, etc.)
  |
  v
CDS Hook dispatcher
  |
  | For each registered service matching this hook:
  |   POST {service_url}/cds-services/{hook_id}
  |   Body: { patient_id, fhir_server_url, prefetch: { relevant_resources } }
  |
  v
External CDS service returns cards:
  [
    { summary: "Drug interaction warning", indicator: "warning",
      detail: "Lisinopril + potassium supplements...",
      suggestions: [{ label: "Remove potassium", actions: [...] }] }
  ]
```

### New tables

| Table                  | Purpose                                                            |
| ---------------------- | ------------------------------------------------------------------ |
| `cds_service_registry` | Registered CDS services (endpoint, hook types, prefetch templates) |
| `cds_hook_responses`   | Audit log of hook invocations and responses (P4 Ownership)         |

### Phasing

CDS Hooks is post-M4. It requires the outbound FHIR read API (services need `fhir_server_url` in the request) and SMART authorization (services need scoped access to patient data for prefetch).

## 7. Gap summary — what ships when

| Integration point               | Layer        | M3  | M4      | M5+ | Dependency                           |
| ------------------------------- | ------------ | --- | ------- | --- | ------------------------------------ |
| FHIR R4 ingest (write)          | Data         | Yes | —       | —   | Already designed (§5)                |
| FHIR Subscription (inbound)     | Data         | Yes | —       | —   | Already designed (§5)                |
| **SMART on FHIR**               | Auth         | —   | **Yes** | —   | OAuth server + app registration      |
| **Outbound FHIR read API**      | Data         | —   | **Yes** | —   | Repository + FHIR adapter (D26)      |
| **FHIR CapabilityStatement**    | Discovery    | —   | **Yes** | —   | Outbound API defines what to declare |
| **Patient consent UI for apps** | Auth         | —   | **Yes** | —   | SMART scope-to-grant mapping         |
| Webhooks (outbound)             | Events       | —   | **Yes** | —   | Outbox (§6) + subscription registry  |
| FHIR Subscription (outbound)    | Events       | —   | —       | Yes | Webhooks + FHIR formatting           |
| Bulk \$export                   | Data         | —   | —       | Yes | Outbound API + async job             |
| HL7 v2 adapter                  | Data         | —   | —       | Yes | Source adapter (D6)                  |
| C-CDA parser                    | Data         | —   | —       | Yes | Documents (D3) + silver mapping      |
| CDS Hooks                       | Intelligence | —   | —       | Yes | Outbound API + SMART                 |
| Developer portal / sandbox      | Discovery    | —   | Partial | Yes | Synthea data + docs                  |
| External agent API              | Intelligence | —   | —       | Yes | D18 + SMART                          |
| IPS export (CSA-47)             | Data         | —   | —       | Yes | Outbound API                         |

**M4 is the platform inflection**: SMART + outbound FHIR + CapabilityStatement + webhooks. That bundle converts Health OS from aggregator to platform.

## 8. Standards reference

| Standard               | Version   | Governing body          | Relevance                                     |
| ---------------------- | --------- | ----------------------- | --------------------------------------------- |
| FHIR R4                | STU 4.0.1 | HL7                     | Data exchange format (D26)                    |
| SMART on FHIR          | v2.1      | HL7 / Boston Children's | App authorization                             |
| FHIR Bulk Data         | v2.0      | HL7                     | Backend data export                           |
| CDS Hooks              | 2.0       | HL7                     | Clinical decision support                     |
| IPS                    | v1.1      | HL7                     | International patient summary                 |
| US Core                | 6.1.0     | HL7                     | US FHIR profile conformance                   |
| OAuth 2.0              | RFC 6749  | IETF                    | Authorization framework                       |
| PKCE                   | RFC 7636  | IETF                    | Public client security (SMART apps)           |
| 21st Century Cures Act | 2016      | ONC / CMS               | Info-blocking rule mandating patient access   |
| TEFCA                  | v2        | ONC / Sequoia           | National health information exchange (future) |

## Related

- [data-plane.md](data-plane.md) — Internal read/write architecture (§1-7)
- [decisions.md](decisions.md) — D9 (XACML triad), D22 (OpenFGA), D26 (FHIR R4)
- [consent-model.md](consent-model.md) — access_grants that SMART scopes map to
- [semantic-search.md](semantic-search.md) — Search API internals
- [platform-malleability.md](platform-malleability.md) — Vertical positioning that interop enables
- [endpoint-inventory.md](endpoint-inventory.md) — Internal API endpoints (precursor to FHIR facade)
