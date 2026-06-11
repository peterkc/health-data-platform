# Platform Malleability — What Health OS Can Be Used For

**Status**: Living — analysis captured 2026-04-14, updated with new CSAs
**Purpose**: Can the platform serve more than longevity/concierge health, and what is the malleability story?
**Audience**: Reviewers assessing architectural pivot feasibility
**Companion to**: [data-type-catalog.md](data-type-catalog.md), [design-patterns.md](design-patterns.md), [design-queue.md](design-queue.md)

## How to read this file

- **Thesis** section: the 60/40 platform-vs-vertical split argument
- **Positioning tiers** (PHR / Health CMS / Health OS): each tier compounds on the last
- **Pivot catalog**: scan the "Effort" column to find low-cost pivots vs. multi-quarter bets
- Source: cross-schema study + domain analysis based on the locked design (D1-D6, CSA proposals)

## Thesis

Health OS's architecture is ~60% platform primitives and ~40% vertical-specific reference data.
The primitives generalize to any multi-source, multi-actor, consent-governed data platform.
The health-specific bits are swappable reference data, not architectural assumptions.

**Malleability IS architecture quality.** If the platform generalizes, it means we avoided
over-fitting to health. That's a defensibility argument: Health OS is not a CRUD app painted
healthcare — it's a sound data platform that chose health as its first market.

## Positioning tiers — PHR -> Health CMS -> Health OS

Three nested framings, each a superset of the previous. Each tier compounds
defensibility of the last.

| Tier           | What it is                                                                                                          | Who pays                                      | Health OS status                                            | Public analogs                                                 |
| -------------- | ------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- | ----------------------------------------------------------- | -------------------------------------------------------------- |
| **PHR**        | Patient-owned, multi-source health record. Aggregation + export + portability.                                      | Consumer, employer, provider (patient-facing) | Foundational — already there by D1-D7                       | Fasten Health, CommonHealth, Apple Health, IPS spec            |
| **Health CMS** | Content + governance + workflow layer over clinical objects. Authoring, versioning, consent, extensibility.         | Provider orgs, ISVs, domain verticals         | ~70% — missing workflow trio (CSA-36/37/38) + CSA-41 ingest | Sanity / Contentful (content), WordPress (publishing), openEHR |
| **Health OS**  | PHR + Health CMS + AI agent as first-class grantee. Autonomous clinical reasoning across the patient's full record. | Consumer + provider + payer                   | Product vision — requires both tiers below locked           | No public analog (frontier positioning)                        |

**Why this tiering matters**:

- **PHR** is a credibility primitive — patients own their data; this is already table-stakes
  for EU (GDPR Article 20 portability) and increasingly for US (21st Century Cures info-blocking rule).
  Health OS does PHR well out of the box; this is the foundation, not the story.
- **Health CMS** is the industry trend line. Every healthcare ISV is rediscovering that clinical
  objects need authoring + governance + workflow — which is what content management systems
  do. openEHR templates, FHIR profiles, and EHR form designers are all converging on CMS semantics.
  Health OS's `ref_record_type_schemas` + D7 split + consent architecture IS a Health CMS. Naming
  it clarifies the architecture.
- **Health OS** is the differentiation story. PHR + CMS are the prerequisite; AI agent parity
  (agent as grantee in `access_grants`, same trust/consent model as a human) is the wedge.
  This is what Fasten / Apple Health / openEHR do not have.

### What each tier earns on the cap table

| Tier       | Defensibility argument                                                       | Revenue model activation                                |
| ---------- | ---------------------------------------------------------------------------- | ------------------------------------------------------- |
| PHR        | Patient ownership + portability = regulatory tailwind + user lock-in         | Consumer subscription, employer benefit                 |
| Health CMS | Extensibility contract = ISV / provider / vertical developer ecosystem       | Per-seat provider, per-template marketplace, API access |
| Health OS  | AI agent with consent parity = autonomous clinical reasoning no one else has | Per-patient-per-month, outcomes-linked, risk-sharing    |

### What's already there per tier

| Tier       | Delivered                                                                       | Remaining                                                |
| ---------- | ------------------------------------------------------------------------------- | -------------------------------------------------------- |
| PHR        | D1 persons, D7 6-table split, `access_grants`, `documents`, source adapters     | Export/portability endpoint (GDPR-grade) — new CSA below |
| Health CMS | `ref_record_type_schemas`, `provenance`, `clinical_entities`, multi-dim consent | CSA-36/37/38 workflow trio, CSA-41 openEHR/ISO 13606     |
| Health OS  | AI agent as grantee, trust grading, bitemporal (CSA-5)                          | Agent action audit (CSA-29-ish), policy engine (CSA-10)  |

Add CSA-47: **patient data export + portability endpoint**. GDPR Article 20 + HIPAA right-of-access compliant.
Returns full record as FHIR Bundle or IPS Composition. Blocks nothing, unlocks credible PHR positioning.

## Platform primitives (reusable across domains)

| Primitive                     | Schema expression                                                | Why it generalizes                                                                  |
| ----------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Identity with role satellites | `persons` + patients / practitioners / future satellites         | Any N-actor system has identities with multiple role contexts                       |
| Source adapter registry       | `ref_source_adapters`                                            | Any data platform ingests from sources; registry is the extensibility contract      |
| Multi-dimensional consent     | `access_grants` (categories + sources + hom_nodes + time-bounds) | Any compliance regime (HIPAA, GDPR, SOC 2, 42 CFR Part 2) needs this shape          |
| Content-addressed storage     | `documents` content-addressed S3 + SHA-256                       | Any digital asset system benefits from dedup + reference counting + right-to-delete |
| Canonical + raw separation    | `raw_payloads` + `health_records` with `extensions JSON`         | Any data normalization problem (source-specific → canonical)                        |
| Semantic grouping             | `ref_hom_nodes` + `ref_hom_mapping`                              | Any hierarchical categorization of codes (think HOM for finance, law, education)    |
| Trust grading                 | `trust_level` on every row (ADR-2007)                            | Any multi-source-truth problem where sources vary in reliability                    |
| AI agent with consent parity  | Agent as grantee in `access_grants`                              | Any system combining AI with PII / regulated data                                   |
| Provenance (ETL lineage)      | `provenance` table                                               | Any derived-data system needs this                                                  |

## Vertical-specific (swappable for new domains)

| Health-specific                          | What it would become for another vertical                                       |
| ---------------------------------------- | ------------------------------------------------------------------------------- |
| `loinc_crosswalk`                        | Domain vocabulary (e.g., `legal_citation_crosswalk`, `finance_cusip_crosswalk`) |
| FHIR-aligned `record_type` enum          | Domain-native record types                                                      |
| 42 CFR Part 2 sensitive categories       | Domain-specific sensitive category list                                         |
| `ref_hom_nodes` (HOM tree)               | Domain-specific ontology tree                                                   |
| `clinical_entities` staging              | Domain-specific extraction staging                                              |
| `patients` / `practitioners` role labels | Domain-specific roles (client / advisor; student / instructor)                  |

## Can Health OS build a medical charting solution?

**Yes. Three feature gaps, zero architectural gaps.**

| Charting requirement                      | Health OS status                                    | Gap type                                              |
| ----------------------------------------- | --------------------------------------------------- | ----------------------------------------------------- |
| Patient identity + demographics           | Covered (persons + patients satellite)              | None                                                  |
| Practitioner identity + credentialing     | Covered (practitioners)                             | None                                                  |
| Clinical documentation (notes, narrative) | Covered (journal_entries + notes + narrative CSA-2) | None                                                  |
| Encounter capture                         | Covered (encounters)                                | None                                                  |
| Observations / vitals                     | Covered (health_records)                            | None                                                  |
| Problems / conditions                     | Covered (health_records record_type='condition')    | None                                                  |
| Medications                               | Covered (health_records record_type='medication')   | FHIR split at scale (CSA-8)                           |
| Allergies                                 | Covered (health_records record_type='allergy')      | None                                                  |
| Care plans + goals                        | Covered (care_plans + goals)                        | None                                                  |
| Orders (CPOE)                             | Not covered                                         | **Feature**: orders table + workflow                  |
| Scheduling / appointments                 | Not covered                                         | **Feature**: appointments table                       |
| Billing / claims                          | Not covered                                         | **Feature**: billing tables (already deferred)        |
| Clinical decision support                 | Partial (AI agent)                                  | Depends on positioning                                |
| E-prescribing (SureScripts)               | Not covered                                         | **Feature**: prescription table + SureScripts adapter |
| Provider-facing workflow UI               | Not covered                                         | **Feature**: front-end, not schema                    |

The missing items are features, not primitives. Health OS's architecture supports provider-first
mode — you would flip the default `access_grants` semantic from "patient grants practitioner"
to "practitioner has org-scoped default grant." Same schema, different defaults.

## Other domains Health OS could serve

Ranked by architectural fit (how much of existing schema applies).

| Domain                                | Fit      | Reusable primitives                            | Additions needed                                          |
| ------------------------------------- | -------- | ---------------------------------------------- | --------------------------------------------------------- |
| Clinical trials platform              | 95%      | Everything                                     | Trial protocol + consent form templates                   |
| Mental health / therapy               | 95%      | Everything                                     | Session types (42 CFR Part 2 already covered)             |
| Remote patient monitoring             | 95%      | Everything                                     | Device management, alerting                               |
| **Health CMS for provider ISVs**      | **90%**  | **Everything + ref_record_type_schemas**       | **CSA-36/37/38 workflow trio, CSA-41 openEHR ingest**     |
| Employer wellness programs            | 85%      | Most                                           | Program + reward tables                                   |
| Health research / OMOP analytics tier | 85%      | Most + CSA-9                                   | De-ID pipeline                                            |
| Pediatric longitudinal tracking       | 85%      | Most                                           | Growth / milestone extensions                             |
| **Patient-first PHR (baseline)**      | **100%** | **Everything**                                 | **CSA-47 export/portability endpoint**                    |
| GDPR personal data vault (EU play)    | 75%      | Identity + consent + content-addressed + audit | Non-health reference tables                               |
| Veterinary                            | 70%      | Most                                           | Species reference + owner→patient pattern                 |
| Citizen data portability (generic)    | 60%      | Primitives                                     | Vertical-specific reference layer                         |
| Enterprise knowledge + AI agent       | 50%      | Content-addressed + consent + agent pattern    | Refactor "patient" → "subject"; different reference layer |

## Positioning framing (three layers, increasing depth)

### Layer 1 — Primary positioning (vertical focus)

> Health OS is a patient-owned data platform aggregating across every source,
> with consent and AI agent parity as core architecture.

Tight, easy to understand. The default outward-facing description.

### Layer 2 — Defensibility (when pressed on moat)

> The architecture generalizes. The primitives — persons + role satellites, source adapter
> registry, multi-dimensional consent, content-addressed storage, trust grading, AI agent
> parity — apply to clinical trials, mental health, employer wellness, and research. That
> is why we can sustain feature velocity: every new adapter, every new consent shape, every
> new role compounds across markets. We chose health first because it is the largest and
> most regulated. We did not over-index on it.

### Layer 3 — Discipline (when pressed on horizontal platform risk)

> We stay focused. Health through Series A. Adjacent verticals (clinical trials, mental
> health, employer wellness) enabled by the platform — activated only when customer
> commitment drives them. We do not chase verticals; we let them pull us.

## What the malleability argument does NOT mean

- **Not** that Health OS should build charting, trials, therapy, and wellness products in parallel
- **Not** that the current schema is complete for any of those domains
- **Not** a reason to defer health-specific features (FHIR ingest, HIPAA audit, LOINC)
- Malleability is a *defensibility story* — proof that the architecture is sound —
  not a product roadmap

## Data types per pivot — what each pivot actually needs

The pivot analysis above answered *whether* Health OS can pivot. The question below is *what
data types each pivot requires as first-class tables* (not `extensions JSON` escape-hatches).

This lens came from asking: "if we composed every public Health IT schema (FHIR,
USCDI, OMOP, HealthKit, CDISC, GA4GH, IEEE 11073), what fraction of data types does
Health OS's current design cover?" Answer: ~45%. See [data-type-catalog.md](data-type-catalog.md)
for the full matrix.

| Pivot                              | Critical data types (first-class requirement)                                       | Blocking CSAs from design-queue |
| ---------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------- |
| Longevity / concierge (primary)    | Observations, Conditions, Medications, Allergies, Family Hx, Encounters, Care Plans | None — already covered          |
| Medical charting                   | Orders, Procedures, Care Team, Referrals, Appointments                              | CSA-14, -16, -19, -27           |
| Clinical trials platform           | ResearchStudy / Subject, AdverseEvent, Questionnaires, CRFs, OMOP analytics         | CSA-9, -17, -25, -33            |
| Mental health / therapy            | Questionnaires (PROs), RiskAssessments, AdvanceDirectives, structured session notes | CSA-17, -29, -35                |
| Remote patient monitoring          | Devices, DeviceMetrics, push-ingest, Continuous streams, ClinicalAlerts             | CSA-15, -22, -24, -28           |
| Pediatric longitudinal             | GrowthMeasurements, Milestones, Questionnaires (screening)                          | CSA-17, -26                     |
| Employer wellness                  | ProgramEnrollment, Tasks, Rewards                                                   | CSA-33                          |
| GDPR personal data vault           | ConsentDocuments, AdvanceDirectives, AccessLog                                      | CSA-1, -29, -34                 |
| Citizen data portability (generic) | Configurable ref_record_types + full consent audit                                  | CSA-13, -1, -3                  |
| Enterprise knowledge + AI agent    | record_type rename → "subject_data_type"; vertical-specific ref layer               | CSA-13                          |

**The single architectural precondition for every pivot beyond longevity is CSA-13**
(`record_type` ENUM → VARCHAR + `ref_record_types` reference table). One DDL edit
unlocks the option value of every downstream pivot. All other CSAs are additive;
CSA-13 is foundational.

This reframes the malleability argument precisely: Health OS is not malleable by *default* —
Health OS becomes malleable by landing CSA-13. Without it, the pivot story is theoretical;
with it, the story is grounded in a single, small, reversible architectural change.

## How this framing affects current decisions

- **Scope lens stays POC → exit with minimal refactor** (from README.md) — unchanged
- **D1 persons satellite pattern** — reinforced: persons root is the platform primitive, not a health-specific choice
- **D6 full ref_source_adapters registry** — reinforced: source plurality is architectural
- **Consent architecture (access_grants)** — reinforced: multi-dimensional consent is a platform primitive
- **Deferred analytics tier (CSA-9)** — cost of deferring is higher than previously scored, since the analytics tier is the entry point to research/trials/employer markets
- **CSA-13 promoted to architectural precondition** — not a data-model tweak; a small foundational change that converts the malleability story from theoretical to demonstrable

## Related

- [design-lessons.md](design-lessons.md) — cross-schema patterns; "Health OS's frontier" section maps to the platform primitives
- [references.md](references.md) — public schemas that validate the primitives
- [scoping.md](scoping.md) — phasing decisions; the malleability argument affects which deferrals cost how much

## Iteration log

| Date       | Change                                                     | Rationale                                                                                                                                                                                                                                                                                                                                                     |
| ---------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-04-15 | Added "Positioning tiers — PHR -> Health CMS -> Health OS" | Industry converging on Health CMS framing (openEHR templates, FHIR profiles, EHR form designers all rediscovering CMS semantics). PHR is the credibility primitive; CMS is the ecosystem play; Health OS is the AI-agent differentiator. Provides a story arc for external positioning. Added CSA-47 (export/portability) for GDPR Article 20 + HIPAA right-of-access. |
| 2026-04-14 | Added "Data types per pivot" lens                          | User: "pivots shape our thinking." Composed 15 public schemas into coverage matrix (data-type-catalog.md); surfaced CSA-13 as single architectural precondition for every pivot beyond longevity.                                                                                                                                                             |
| 2026-04-14 | Initial capture                                            | User asked "can Health OS's platform be used to build medical charting? What else? If malleable, compelling positioning story." Captured analysis so it survives /compact.                                                                                                                                                                                       |

Append new entries above this line.
