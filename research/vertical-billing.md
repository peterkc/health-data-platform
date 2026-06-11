# Vertical — Medical Billing (Patient-Facing)

**Status**: Exploration — example vertical evaluation, not committed for implementation
**Purpose**: Demonstrate how Health OS's platform primitives apply to a non-clinical vertical. Medical billing is the example; this document doubles as a template for evaluating future verticals.
**Audience**: Architecture review; team for vertical evaluation methodology.
**Companion to**: [platform-malleability.md](platform-malleability.md) (malleability thesis + pivot catalog), [interoperability-surface.md](interoperability-surface.md) (integration points that billing would use), [consent-model.md](consent-model.md) (consent model that billing extends)

## How to read this file

- "Why billing" explains the market gap and why this vertical tests the platform thesis
- "Primitive mapping" shows which Health OS components transfer unchanged vs. need adaptation
- "Reference data swap" specifies the billing-specific vocabulary layer
- "New tables" sketches what billing adds to the schema
- "Legal landscape" covers HIPAA, No Surprises Act, and the HR/PBM firewall
- "Template" at the end is reusable for evaluating any vertical

## 1. Why billing as the example vertical

Medical billing is interesting for three reasons:

**Market gap**: Provider-side billing tools (Waystar, Cedar, Athena) are mature. Patient-side billing tools barely exist. Patients receive EOBs they can't read, charges they can't verify, and collection notices for bills they thought insurance covered. The information asymmetry is structural: providers and payers have real-time claims data; patients get paper 30 days later.

**Platform test**: Billing uses the same multi-source, multi-actor, consent-governed data patterns as clinical data — but with a different vocabulary. If Health OS's primitives handle billing without architectural changes, the malleability thesis in platform-malleability.md is real, not theoretical.

**Adjacent to clinical**: A patient's clinical record and billing record describe the same events from different angles. An observation (LOINC-coded lab result) maps to a claim line (CPT-coded procedure). Health OS already stores the clinical side. Adding billing creates a unified patient financial + clinical view that no consumer product offers today.

## 2. Primitive mapping

Health OS's platform primitives (from platform-malleability.md) and their billing applicability:

| Primitive                                | Clinical use                                       | Billing use                                                                 | Changes needed                                                                   |
| ---------------------------------------- | -------------------------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| **Identity (persons + role satellites)** | patients, practitioners                            | patients, payer_contacts, billing_advocates                                 | New satellite: `payer_contacts` (insurance rep identity)                         |
| **Source adapter registry** (D6)         | EHRs, labs, devices                                | Insurance portals, provider billing systems, PBMs, banks                    | New adapter entries — same table, new source_system values                       |
| **Multi-dimensional consent**            | Clinical data access by category, source, HOM node | Financial data access by payer, provider, claim type                        | Same access_grants shape; new purpose values (billing_review, dispute, advocacy) |
| **Content-addressed storage** (D3)       | Clinical documents (PDFs, scans)                   | EOBs, itemized bills, insurance cards, collection letters                   | Same documents table — billing docs are documents                                |
| **Canonical + raw separation**           | raw_payloads → silver tables                       | raw_billing_payloads → billing silver tables                                | New raw + silver tables; same pattern                                            |
| **Trust grading** (ADR-2007)             | Source reliability (clinical lab > self-reported)  | Source reliability (payer adjudicated > provider billed > patient estimate) | Same trust_level column; new trust hierarchy                                     |
| **AI agent with consent parity** (D18)   | Clinical reasoning, RAG                            | Bill review, charge verification, dispute drafting                          | Same agent identity; new capabilities                                            |
| **Provenance**                           | ETL lineage for clinical data                      | Claim lifecycle lineage (submitted → adjudicated → paid → appealed)         | Same provenance table; billing-specific event types                              |
| **Transactional outbox** (§6)            | Clinical event notifications                       | Billing event notifications (new EOB, claim status change, payment posted)  | Same outbox; new event types                                                     |
| **Semantic search**                      | Clinical text, uncoded symptoms                    | Bill descriptions, denial reason narratives, appeal letters                 | Same embedding pipeline; billing-specific text                                   |

**Score: 9 of 10 primitives transfer unchanged.** The only structural addition is new silver tables for billing-specific entities. Everything else is configuration: new source_system values, new purpose enums, new trust hierarchies.

## 3. Reference data swap

Clinical data uses medical vocabularies. Billing data uses financial/administrative vocabularies. The swap:

| Clinical vocabulary               | Billing equivalent                          | Purpose                                |
| --------------------------------- | ------------------------------------------- | -------------------------------------- |
| LOINC (lab codes)                 | CPT / HCPCS (procedure codes)               | What was done                          |
| SNOMED CT (clinical terms)        | ICD-10-CM/PCS (diagnosis + procedure codes) | Why it was done (shared with clinical) |
| RxNorm (drug codes)               | NDC (National Drug Codes)                   | Which drug (RxNorm maps to NDC)        |
| CVX (vaccine codes)               | CPT vaccine admin codes                     | Immunization billing                   |
| —                                 | DRG (Diagnosis Related Groups)              | Inpatient payment grouping             |
| —                                 | Revenue codes                               | Facility charge categories             |
| —                                 | NUBC (payer codes)                          | Insurance identification               |
| ref_hom_nodes (clinical ontology) | Billing category ontology                   | Hierarchical grouping                  |

Health OS's `loinc_crosswalk` pattern generalizes: a `billing_code_crosswalk` maps CPT → plain-language descriptions, typical cost ranges, and common denial reasons. Same table shape, different domain.

ICD-10 codes appear in both clinical and billing contexts — they're the bridge. A condition coded ICD-10-CM in the clinical record is the same code on the claim. This overlap is what makes Health OS's unified view possible.

## 4. New tables

Billing adds a domain-specific silver layer. The primitives (persons, access_grants, documents, provenance, outbox) don't change.

### Core billing tables

| Table               | Purpose                                                   | Key fields                                                                                                                                                                      |
| ------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `insurance_plans`   | Patient's insurance coverage                              | plan_id, patient_id, payer_name, member_id, group_number, plan_type, coverage_start, coverage_end, deductible, oop_max                                                          |
| `claims`            | Individual claim from provider to payer                   | claim_id, patient_id, provider_name, payer_id (FK insurance_plans), service_date, claim_status, total_billed, total_allowed, patient_responsibility, source_system, external_id |
| `claim_lines`       | Line items within a claim                                 | line_id, claim_id, cpt_code, icd_codes[], description, units, billed_amount, allowed_amount, paid_amount, adjustment_reason_code                                                |
| `eobs`              | Explanation of Benefits from payer                        | eob_id, claim_id, patient_id, payer_id, document_id (FK documents), received_date, payment_date                                                                                 |
| `payments`          | Patient payments made                                     | payment_id, patient_id, claim_id (nullable), amount, payment_date, payment_method, confirmation_number                                                                          |
| `disputes`          | Patient-initiated bill disputes                           | dispute_id, patient_id, claim_id, reason, status, opened_date, resolved_date, outcome, agent_session_id (D18 — AI helped draft?)                                                |
| `ref_billing_codes` | CPT/HCPCS code reference with plain-language descriptions | code, code_system, display, typical_cost_range, common_denial_reasons                                                                                                           |

### Trust hierarchy for billing

| Trust level | Source                            | Example                                                   |
| ----------- | --------------------------------- | --------------------------------------------------------- |
| 1           | Payer adjudicated (final EOB)     | Insurance company's determination of allowed/paid amounts |
| 2           | Provider billed (claim submitted) | Provider's charge master price                            |
| 3           | Third-party estimate              | GoodRx price, fair price estimate                         |
| 4           | Patient-entered                   | Manually entered bill amount, payment receipt             |

Same `trust_level` column as clinical data. Same conflict resolution pattern (D19): silver keeps all rows, gold reconciles per rules.

## 5. Use cases

### Patient bill tracking

```
Patient uploads EOB photo
  → OCR + AI extraction → raw_billing_payloads
  → Normalize → claims + claim_lines (with CPT, ICD-10)
  → Trust level 1 (payer-sourced)
  → Cross-reference: does claim_line.icd_code match any conditions in clinical record?
  → Display: "Lab work on 3/15 — Quest Diagnostics billed $450, insurance allowed $180, you owe $35"
```

### AI-assisted dispute

```
Patient: "This ER bill seems too high"
  → Agent (D18) retrieves: claim, claim_lines, insurance_plan, relevant clinical records
  → PDP (D22): agent has access via same GrantContext as clinical reads
  → Agent checks: duplicate charges? unbundled codes? balance billing violations?
  → Agent drafts dispute letter → disputes table (status: draft)
  → Patient reviews and submits
```

### Deductible tracking

```
Aggregate across all claims for current plan year:
  SELECT SUM(patient_responsibility) FROM claim_lines
    JOIN claims ON claims.id = claim_lines.claim_id
    WHERE claims.patient_id = ? AND claims.service_date >= plan_year_start

Compare against insurance_plans.deductible → "You've met $1,200 of your $3,000 deductible"
```

### Cross-domain insight (clinical + billing)

```
"Show me all my cardiovascular-related costs this year"
  → HOM query: ref_hom_mapping WHERE hom_node = 'hom-heart'
  → Clinical: observations, conditions, medications in cardiovascular HOM
  → Billing: claims WHERE claim_lines.icd_code IN (cardiovascular ICD-10 codes)
  → Unified view: "3 cardiology visits ($840), 2 labs ($210), Lisinopril 12 months ($360)"
```

The HOM ontology (ref_hom_nodes) bridges clinical and billing via shared ICD-10 codes.

## 6. Legal landscape

### What applies

| Law                                    | Relevance to billing vertical                                                                                                                                    |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **HIPAA**                              | Claims data is PHI. Same consent/audit requirements as clinical data. Health OS's existing model covers this.                                                    |
| **No Surprises Act (2022)**            | Patients have a right to good-faith cost estimates before service, and protection from surprise out-of-network billing. Health OS could surface these estimates. |
| **Fair Debt Collection Practices Act** | If Health OS stores collection notices, display/handling rules apply                                                                                             |
| **State balance billing laws**         | Vary by state; affect what charges are valid to display                                                                                                          |
| **HIPAA right of access**              | Patients can request their claims/billing data from payers. Health OS as aggregator facilitates this.                                                            |

### The HR / PBM firewall

Employer-sponsored health plans create a legal boundary between employer (as employer) and employer (as plan sponsor):

| Actor                             | Can see individual claims?       | Legal basis                                |
| --------------------------------- | -------------------------------- | ------------------------------------------ |
| HR department                     | **No**                           | HIPAA firewall (45 CFR 164.504(f))         |
| Benefits team (plan fiduciary)    | Aggregate only                   | Summary health information exemption       |
| TPA / PBM                         | Yes — processes claims           | BAA with plan sponsor                      |
| Employer (self-insured, \<500 EE) | Gray area — firewalls often weak | Compliance risk, not a product opportunity |
| **Employee themselves**           | **Yes — their own data**         | HIPAA right of access                      |

The valid product in this space is **employee self-service**: employees tracking their own pharmacy costs, understanding formulary options, comparing PBM pricing. Health OS's consent model enforces the firewall architecturally — the employee's access_grant covers their own data only. No grant exists for HR to query individual records.

If an employer wants aggregate analytics (plan cost trends, utilization by category), that's a separate product surface with de-identified data — CSA-9's analytics tier, not the patient-facing billing vertical.

## 7. Integration points

Billing connects to the interoperability surface (interoperability-surface.md) at specific points:

| Integration            | Standard                             | Direction | Notes                                                  |
| ---------------------- | ------------------------------------ | --------- | ------------------------------------------------------ |
| Payer EOB ingest       | FHIR ExplanationOfBenefit (R4)       | Inbound   | CARIN Blue Button IG — payer-to-patient claims data    |
| Provider charge ingest | HL7 v2 DFT (financial transaction)   | Inbound   | Legacy but common in hospital billing                  |
| Patient upload (OCR)   | Custom (image → extraction pipeline) | Inbound   | AI extraction → raw_billing_payloads                   |
| Cost estimator APIs    | Custom / Turquoise Health            | Inbound   | Fair price reference data                              |
| SMART on FHIR          | SMART v2.1                           | Outbound  | Third-party financial apps access patient billing data |
| Webhooks               | Custom                               | Outbound  | Notify when new EOB arrives, claim status changes      |

**CARIN Blue Button** is the key standard: it defines FHIR profiles for ExplanationOfBenefit, Coverage, and Patient resources specifically for payer-to-patient data exchange. Major US payers (UnitedHealth, Anthem, Aetna, Cigna) are required to support it under CMS Interoperability Rule.

## 8. Vertical evaluation template

This section is reusable for evaluating any vertical against Health OS's platform.

### Checklist

| Dimension                 | Question                                                     | Billing answer                                                                        |
| ------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| **Primitive reuse**       | How many of Health OS's 10 primitives transfer?              | 9/10 (all except new silver tables)                                                   |
| **Reference data**        | What domain vocabulary replaces the clinical one?            | CPT/HCPCS/NDC/DRG replace LOINC/SNOMED/RxNorm/CVX                                     |
| **New tables**            | What domain-specific silver tables are needed?               | 7 (insurance_plans, claims, claim_lines, eobs, payments, disputes, ref_billing_codes) |
| **Consent model**         | Does access_grants shape cover the vertical's consent needs? | Yes — add billing-specific purposes                                                   |
| **Trust model**           | Does the trust hierarchy apply?                              | Yes — payer adjudicated > provider billed > estimate > patient-entered                |
| **AI agent role**         | What does the agent do in this vertical?                     | Bill review, dispute drafting, cost optimization                                      |
| **Legal constraints**     | What regulations govern this data?                           | HIPAA (shared), No Surprises Act, FDCPA, state balance billing                        |
| **Integration standards** | What standards exist for data exchange?                      | CARIN Blue Button (FHIR), HL7 v2 DFT, payer APIs                                      |
| **Cross-domain value**    | Does combining with clinical data create new value?          | Yes — HOM bridges clinical + billing via shared ICD-10 codes                          |
| **Market gap**            | Is the consumer/patient side underserved?                    | Yes — provider-side mature, patient-side fragmented                                   |

### Scoring

- **90%+ primitive reuse**: Strong fit — vertical is a configuration change, not an architecture change
- **70-90%**: Good fit — needs a few new primitives or significant reference data work
- **50-70%**: Moderate — vertical is possible but strains the platform abstraction
- **\<50%**: Weak — Health OS is not the right foundation for this vertical

Medical billing scores ~85%: high primitive reuse, significant reference data swap, moderate new table count, strong cross-domain value.

## Related

- [platform-malleability.md](platform-malleability.md) — Platform thesis and pivot catalog
- [interoperability-surface.md](interoperability-surface.md) — Integration points billing would use
- [consent-model.md](consent-model.md) — access_grants shape (reused for billing consent)
- [data-plane.md](data-plane.md) — Repository patterns that billing inherits
- [semantic-search.md](semantic-search.md) — Embedding pipeline for billing text (denial reasons, appeal narratives)
