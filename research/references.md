# References — External Schemas and Data Sources

**Status**: Living document — add entries as new sources influence schema decisions
**Purpose**: Catalog the public schemas, open source systems, and regulations that informed MVP schema design
**Audience**: Engineers evolving the schema or citing external precedent; reviewers validating design claims
**Companion to**: [design-lessons.md](design-lessons.md), [data-type-catalog.md](data-type-catalog.md), [design-patterns.md](design-patterns.md)

## How to read this file

- Scan the "#" column for entry numbers referenced from other hub files (e.g., design-lessons.md cites by source name)
- "Relevance to Health OS" column explains why the source matters, not just what it is
- Sections are grouped by type: standards, open source PHRs, device APIs, regulatory
- Citation discipline: verify canonical URLs and version numbers before external citation (standards versions evolve)

## Standards and Reference Models

| #   | Source                              | Organization                                        | Relevance to Health OS                                                                                                                                                                               | URL                                                                         |
| --- | ----------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| 1   | FHIR R4 / R5                        | HL7 International                                   | Resource model (Patient, Observation, Condition, MedicationRequest, Encounter, CarePlan, Goal); extension pattern; Provenance resource. Aligned via ADR-2002.                                        | https://hl7.org/fhir/R4/                                                    |
| 2   | USCDI v4                            | ONC (US Dept HHS)                                   | Minimum data classes required for US interoperability certification. Compliance checklist for MVP coverage.                                                                                          | https://www.healthit.gov/isa/united-states-core-data-interoperability-uscdi |
| 3   | OMOP CDM v5.4                       | OHDSI consortium                                    | Vocabulary-first design (`concept` table), standard vs source concept distinction, long-format fact tables, `care_site` + `provider` as first-class entities. Reference for deferred analytics tier. | https://ohdsi.github.io/CommonDataModel/cdm54.html                          |
| 4   | openEHR                             | openEHR International                               | Two-level modeling (reference model stable, archetypes evolve). Inspirational for `ref_record_type_schemas` pattern; do not adopt wholesale.                                                         | https://specifications.openehr.org/                                         |
| 5   | i2b2 star schema                    | i2b2/tranSMART Foundation                           | `observation_fact` + `concept_dimension` + `patient_dimension`. Validates our `health_records` + `ref_hom_mapping` + `patients` direction.                                                           | https://www.i2b2.org/                                                       |
| 6   | PCORnet CDM                         | PCORnet                                             | Patient-centered outcomes research schema; simpler than OMOP.                                                                                                                                        | https://pcornet.org/data/                                                   |
| 6a  | International Patient Summary (IPS) | HL7 International + CEN / ISO                       | Minimum useful summary data set (~32 elements) for cross-border care. Litmus test for "bare-minimum interop completeness."                                                                           | https://hl7.org/fhir/uv/ips/                                                |
| 6b  | SMART on FHIR                       | Boston Children's / HL7                             | Patient + provider app authorization framework. `access_grants.scope` format maps to SMART scope syntax (`patient/Observation.read`).                                                                | https://docs.smarthealthit.org/                                             |
| 6c  | CDISC ODM + SDTM + ADaM             | CDISC                                               | Clinical trial data model — operational data (ODM) → study data tabulation (SDTM) → analysis data (ADaM). Trials pivot reference.                                                                    | https://www.cdisc.org/standards                                             |
| 6d  | GA4GH Variant Representation Spec   | GA4GH                                               | Genomic variant canonical form. Grounds CSA-23 `genomic_variants` table design.                                                                                                                      | https://vrs.ga4gh.org/                                                      |
| 6e  | IEEE 11073 PHD                      | IEEE                                                | Personal Health Device data exchange standards. Grounds CSA-22 push-ingest for RPM / IoT medical devices.                                                                                            | https://standards.ieee.org/standard/11073-10101-2020.html                   |
| 6f  | DICOM                               | NEMA                                                | Medical imaging metadata standard. Grounds CSA-20 `imaging_studies` table (study UID, series UID, modality, body part).                                                                              | https://www.dicomstandard.org/current                                       |
| 6g  | HL7 v2 / v2.x                       | HL7 International                                   | Legacy messaging protocol. Still dominant in hospital labs + ADT. Referenced for ingest patterns, not storage.                                                                                       | https://www.hl7.org/implement/standards/product_brief.cfm?product_id=185    |
| 6h  | SNOMED CT                           | SNOMED International                                | Clinical terminology (clinical findings, procedures, situations). Grounds CSA-14 procedure coding and CSA-31 crosswalk table.                                                                        | https://www.snomed.org/                                                     |
| 6i  | ICD-10-CM + ICD-10-PCS              | WHO / CMS                                           | Diagnosis coding (CM) + inpatient procedure coding (PCS). Grounds CSA-14 procedures and CSA-31 crosswalk table.                                                                                      | https://www.cms.gov/Medicare/Coding/ICD10                                   |
| 6j  | AAP Bright Futures                  | American Academy of Pediatrics                      | Pediatric well-visit schedule + age-appropriate screening batteries. Grounds CSA-26 `developmental_milestones` and CSA-17 pediatric survey batteries.                                                | https://www.aap.org/en/practice-management/bright-futures/                  |
| 6k  | CDC Growth Charts                   | CDC                                                 | Growth percentiles for pediatric weight/height/BMI/head circumference. Grounds CSA-26 `growth_measurements`.                                                                                         | https://www.cdc.gov/growthcharts/                                           |
| 6l  | CMS RPM billing codes               | CMS                                                 | Reimbursable remote patient monitoring CPT codes (99453, 99454, 99457, 99458, 99091). Grounds CSA-15 device lifecycle events + CSA-22 push-ingest cadence.                                           | https://www.cms.gov/medicare/physician-fee-schedule/search                  |
| 6m  | HEDIS / eCQM                        | NCQA / CMS                                          | Quality measures expressed as derived state from observations. Grounds CSA-28 `care_gaps` / `clinical_alerts` table.                                                                                 | https://www.ncqa.org/hedis/                                                 |
| 6n  | CPIC guidelines                     | Clinical Pharmacogenetics Implementation Consortium | Pharmacogenomic drug-gene interaction recommendations. Grounds genomics → medication interaction decisions.                                                                                          | https://cpicpgx.org/                                                        |
| 6o  | VeNom Coding Group                  | VeNom                                               | Veterinary clinical terminology (species / breed / diagnosis / procedure). Grounds veterinary pivot (if pursued).                                                                                    | https://www.venomcoding.org/                                                |

## Open Source Personal Health Records

The closest public analogs to Health OS positioning. Study their schema decisions
before inventing from first principles.

| #   | System                 | Why relevant                                                                                                                                                     | URL                                                         |
| --- | ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| 7   | Fasten Health          | Self-hostable PHR, FHIR-aligned, multi-source ingest. **Closest public analog to Health OS.** Study source adapter pattern, provenance design, consent handling. | https://github.com/fastenhealth/fasten-onprem               |
| 8   | CommonHealth (Android) | PHR, FHIR-aligned, patient-owned. UX reference more than schema.                                                                                                 | https://github.com/the-commons-project/commonhealth-android |
| 9   | OpenEMR                | Traditional open source EHR (provider-centric). Useful for clinical workflow shapes; less applicable to patient-owned model.                                     | https://github.com/openemr/openemr                          |
| 10  | OpenMRS                | Open source medical records, used in global health. Long-lived schema worth studying.                                                                            | https://github.com/openmrs/openmrs-core                     |

## Device and Source APIs (inform ref_source_adapters configs)

Each represents one column of the Health OS source matrix. Adapter `config` JSON documents
schema version + auth + transform contract.

| #   | Source              | Data types                                            | URL                                                 |
| --- | ------------------- | ----------------------------------------------------- | --------------------------------------------------- |
| 11  | Apple HealthKit     | Wearable/phone health types, units, source provenance | https://developer.apple.com/documentation/healthkit |
| 12  | Oura API v2         | Sleep, readiness, activity, heart rate                | https://cloud.ouraring.com/v2/docs                  |
| 13  | Fitbit Web API      | Heart rate, steps, sleep, SpO2                        | https://dev.fitbit.com/build/reference/web-api/     |
| 14  | Dexcom API          | Continuous glucose monitoring                         | https://developer.dexcom.com/                       |
| 15  | Withings API        | Scale, blood pressure, sleep                          | https://developer.withings.com/api-reference        |
| 16  | Whoop Developer API | Strain, recovery, sleep                               | https://developer.whoop.com/                        |

## Regulations and Compliance Frameworks

| #   | Regulation                                       | Scope                                                                            | Current schema impact                                                                   |
| --- | ------------------------------------------------ | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| 17  | HIPAA Privacy & Security Rules (45 CFR 160, 164) | Access control, minimum necessary, audit, breach notification, de-identification | `access_grants` (layer 2 authorization); audit log deferred; Safe Harbor de-ID deferred |
| 18  | 42 CFR Part 2                                    | Substance use disorder records                                                   | `access_grants.categories` sensitive category handling (consent-model.md)               |
| 19  | GINA                                             | Genetic information non-discrimination                                           | Genetic category in sensitive-categories list (consent-model.md)                        |
| 20  | HITECH Act                                       | Breach notification, meaningful use amendments to HIPAA                          | Informs deferred audit log design                                                       |

## International standards (added 2026-04-14)

Health OS's references were US-anchored despite the "Health OS" framing. The catalog below
fills the international gap that surfaced in the data-type catalog audit. Each entry
unblocks a specific pivot or jurisdiction.

### International terminologies

| #   | Source                                                 | Origin                                   | Why Health OS should care                                                                                                | URL                                                                                                             |
| --- | ------------------------------------------------------ | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| 20a | ATC (Anatomical Therapeutic Chemical) classification   | WHO Collaborating Centre                 | Drug classification used everywhere except US (US uses RxNorm). EU / UK / AU / CA pharmacy data lands here. CSA-39.      | https://www.whocc.no/atc_ddd_index/                                                                             |
| 20b | ICPC-2 (International Classification of Primary Care)  | WONCA                                    | Primary care diagnosis classification. Dominant in EU primary care (UK, NL, BE, NO). ICD-10 is hospital-centric. CSA-39. | https://www.who.int/standards/classifications/other-classifications/icpc                                        |
| 20c | ICD-11                                                 | WHO (released 2022)                      | Successor to ICD-10. Many countries already migrating. We only cite ICD-10-CM (US clinical modification). CSA-39.        | https://icd.who.int/en                                                                                          |
| 20d | dm+d (Dictionary of Medicines and Devices)             | UK NHS BSA                               | UK equivalent of RxNorm. Required for any UK pharmacy data. CSA-39.                                                      | https://services.nhsbsa.nhs.uk/dmd-browser/                                                                     |
| 20e | MedDRA                                                 | ICH (international regulatory)           | Adverse event coding for trials + pharmacovigilance. CSA-25 + CSA-43.                                                    | https://www.meddra.org/                                                                                         |
| 20f | WHO ICF (International Classification of Functioning)  | WHO                                      | Functional status / disability standard. Universal coverage. CSA-44.                                                     | https://www.who.int/standards/classifications/international-classification-of-functioning-disability-and-health |
| 20g | SNOMED CT national editions (UK, AU, CA, NL, ES, etc.) | SNOMED International + members           | International edition is the base; national editions extend with country-specific concepts. CSA-39 acknowledges.         | https://www.snomed.org/snomed-ct/five-step-briefing                                                             |
| 20h | Australian Medicines Terminology (AMT)                 | NEHTA / Australian Digital Health Agency | Required for AU pharmacy data.                                                                                           | https://www.healthterminologies.gov.au/                                                                         |

### International standards bodies + frameworks

| #   | Standard                                     | Origin                                       | Why Health OS should care                                                                                               | URL                                                                                                    |
| --- | -------------------------------------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 20i | ISO 13606                                    | ISO                                          | EHR communication standard, related to openEHR but distinct. Required for some EU integrations. CSA-41.                 | https://www.iso.org/standard/67868.html                                                                |
| 20j | ISO 27799                                    | ISO                                          | Health informatics security management — ISO equivalent of HIPAA security rule.                                         | https://www.iso.org/standard/62777.html                                                                |
| 20k | ISO 21090                                    | ISO                                          | Harmonized data types for health.                                                                                       | https://www.iso.org/standard/35646.html                                                                |
| 20l | IHE profiles (XDS, XCA, PIX/PDQ, MHD)        | IHE International                            | Cross-enterprise document sharing + patient identifier cross-referencing. Dominant interop profiles in EU / AU. CSA-42. | https://www.ihe.net/resources/profiles/                                                                |
| 20m | PRSB (Professional Record Standards Body)    | UK                                           | Care record standards mandatory for NHS England integration.                                                            | https://theprsb.org/                                                                                   |
| 20n | NHS Data Dictionary                          | UK NHS                                       | UK clinical data structures including unique items (NHS ethnicity codes, NHS Number format, etc.).                      | https://www.datadictionary.nhs.uk/                                                                     |
| 20o | eHealth Network cross-border patient summary | EU eHN                                       | Cross-border health summary spec, builds on IPS.                                                                        | https://health.ec.europa.eu/ehealth-digital-health-and-care/electronic-cross-border-health-services_en |
| 20p | EU Health Data Space (EHDS) regulation       | EU (in force 2024)                           | EU regulation for primary + secondary use of health data; mandatory for any EU operations. CSA-40.                      | https://health.ec.europa.eu/ehealth-digital-health-and-care/european-health-data-space_en              |
| 20q | CEN TC 251                                   | CEN (European Committee for Standardization) | EU health informatics standards body; many EU EHR integrations route through CEN profiles.                              | https://www.cencenelec.eu/areas-of-work/cen-cenelec-topics/cen-cenelec-priorities/health/              |

### International privacy / regulatory

| #   | Regulation                        | Jurisdiction | Why Health OS should care                                                             |
| --- | --------------------------------- | ------------ | ------------------------------------------------------------------------------------- |
| 20r | GDPR (EU 2016/679)                | EU           | Mandatory for EU patient data. Heavier consent + right-to-erasure than HIPAA. CSA-40. |
| 20s | UK Data Protection Act 2018       | UK           | UK post-Brexit equivalent of GDPR.                                                    |
| 20t | DSGVO                             | Germany      | GDPR implementation; adds federal stipulations.                                       |
| 20u | PIPEDA                            | Canada       | Federal privacy law for personal information. CSA-40.                                 |
| 20v | Australia Privacy Act 1988 + APPs | Australia    | Australian Privacy Principles.                                                        |
| 20w | PDPA                              | Singapore    | Personal Data Protection Act.                                                         |
| 20x | LGPD                              | Brazil       | Lei Geral de Proteção de Dados.                                                       |
| 20y | HK PDPO                           | Hong Kong    | Personal Data (Privacy) Ordinance.                                                    |

GDPR alone is the most consequential miss — Health OS's "GDPR personal data vault" pivot
(75% fit per platform-malleability.md) cannot be claimed credibly without GDPR explicitly
cited and consent semantics audited against it. CSA-40 starts the audit.

## Authorization + policy systems (data-plane grounding)

Public authorization systems and regulatory sources that inform Health OS's PDP substrate (D22), error envelope (D21), and outage behavior (D23) decisions.

### Authorization technologies

| #   | System                              | License                   | Relevance                                                                                                            | URL                                                          |
| --- | ----------------------------------- | ------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| 21a | OpenFGA                             | Apache 2 (CNCF sandbox)   | **D22 PDP substrate** — Zanzibar-style tuple store on Postgres. Auth0 / Okta open source.                            | https://openfga.dev/                                         |
| 21b | SpiceDB (AuthZed)                   | Apache 2                  | **D22 alternate** — Zanzibar clone with FullyConsistent / AtLeastAsFresh / MinimizeLatency per-call consistency.     | https://authzed.com/spicedb                                  |
| 21c | Permify                             | Apache 2                  | D22 alternate — Zanzibar-spec on Postgres / MongoDB.                                                                 | https://github.com/Permify/permify                           |
| 21d | Google Zanzibar paper (Pang 2019)   | —                         | Foundational paper — tuple-based authorization, zookie freshness, new-enemy problem.                                 | https://research.google/pubs/pub48190/                       |
| 21e | AWS Cedar                           | Apache 2                  | Policy language for batch evaluation; µs in-process eval; alternative to OPA.                                        | https://www.cedarpolicy.com/                                 |
| 21f | Open Policy Agent (OPA)             | Apache 2 (CNCF graduated) | **D22 optional** — Rego policy compilation; decision log powers HITRUST audit evidence.                              | https://www.openpolicyagent.org/                             |
| 21g | Ory Keto                            | Apache 2                  | Alternative tuple-based permissions.                                                                                 | https://www.ory.sh/keto/                                     |
| 21h | Valkey                              | BSD (Linux Foundation)    | **D22 Tier 2 cache substrate (phased)** — Redis protocol compatible, BSD fork after Redis Inc SSPL relicense (2024). | https://valkey.io/                                           |
| 21i | KeyDB                               | BSD                       | Valkey alternate — multi-threaded Redis fork by Snap.                                                                | https://docs.keydb.dev/                                      |
| 21j | PostgreSQL Row-Level Security (RLS) | PostgreSQL                | **D23 post-MVP coarse fallback** — policies enforced by Postgres query planner; belt-and-suspenders to OpenFGA.      | https://www.postgresql.org/docs/current/ddl-rowsecurity.html |

### Delegation + on-behalf-of precedents (D21)

| #   | System                                | License     | Relevance                                                                                              | URL                                                                  |
| --- | ------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| 21k | RFC 8693 OAuth 2.0 Token Exchange     | IETF        | **D21 On-Behalf-Of flow spec** — basis for D18 agent acting for patient; standard delegation chain.    | https://datatracker.ietf.org/doc/html/rfc8693                        |
| 21l | Microsoft Graph delegated permissions | Proprietary | D21 precedent — delegated vs application permissions distinction; canonical OBO implementation.        | https://learn.microsoft.com/en-us/graph/auth/auth-concepts           |
| 21m | Microsoft Entra Conditional Access    | Proprietary | D21 + D23 — break-glass accounts excluded from policies; conditional access layered on top.            | https://learn.microsoft.com/en-us/entra/identity/conditional-access/ |
| 21n | Azure RBAC                            | Proprietary | D21 precedent — `(principal, role, scope)` triple; inheritance through resource hierarchy.             | https://learn.microsoft.com/en-us/azure/role-based-access-control/   |
| 21o | Google Cloud IAM                      | Proprietary | D21 precedent — `principal + role + resource + condition` quadruple.                                   | https://cloud.google.com/iam/docs                                    |
| 21p | Kubernetes RBAC                       | Apache 2    | D23 precedent — kubelet uses in-flight creds during API-server outage (Option B continuation pattern). | https://kubernetes.io/docs/reference/access-authn-authz/rbac/        |
| 21q | OWASP Information Exposure guide      | OWASP       | D21 precedent — collapse 403→404 to prevent existence-leak for non-audiences.                          | https://owasp.org/www-community/Improper_Error_Handling              |

### Resilience patterns (D23)

| #   | Source                              | License  | Relevance                                                               | URL                                            |
| --- | ----------------------------------- | -------- | ----------------------------------------------------------------------- | ---------------------------------------------- |
| 21r | Hystrix (retired) + Resilience4j    | Apache 2 | D23 circuit breaker pattern reference — modern replacement for Hystrix. | https://resilience4j.readme.io/                |
| 21s | Google SRE Book (Beyer et al. 2016) | O'Reilly | D23 graceful degradation, error budgets, availability budgets.          | https://sre.google/sre-book/table-of-contents/ |

### US health regulatory (data-plane context)

| #   | Regulation                                      | Origin  | Relevance                                                                                                             | URL                                                                                              |
| --- | ----------------------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| 21t | HIPAA §164.306(a) Security Rule — availability  | US DHHS | **D23 availability requirement** — complete fail-closed may itself violate the rule; must balance P1 + P3.            | https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.306 |
| 21u | 21st Century Cures Act info-blocking rule (ONC) | US ONC  | D21 + D23 — denying reasonable access when you could serve = info-blocking (civil penalties up to \$1M/instance).     | https://www.healthit.gov/topic/information-blocking                                              |
| 21v | HIPAA §164.524 Right of Access                  | US DHHS | **D21 patient-facing transparency** — patient entitled to see what data is held, basis for PermissionDenied envelope. | https://www.ecfr.gov/current/title-45/section-164.524                                            |
| 21w | HITRUST CSF 11.b.4                              | HITRUST | D23 break-glass control reference — emergency access with documented justification.                                   | https://hitrustalliance.net/csf/                                                                 |
| 21x | 42 CFR Part 2                                   | SAMHSA  | D23 strict-fail-closed override — substance use treatment records require stricter consent than general HIPAA.        | https://www.ecfr.gov/current/title-42/chapter-I/subchapter-A/part-2                              |

## How entries become citations

When citing externally (PRs, ADRs, papers, public docs):

1. **Verify canonical URL** — standards versions evolve; a 2026-canonical link may move
1. **Quote the specific section** — "FHIR R4 Patient resource, section 12.1.2" not just "FHIR"
1. **Pin the version** — FHIR R4 vs R5 differ materially; USCDI v3 vs v4 differ
1. **Link back to this file** for the full reference set supporting the decision

## Sources NOT included (and why)

Intentionally omitted:

- **Epic / Cerner proprietary schemas** — not public; interop via FHIR only
- **HL7 CDA** — document format; subsumed by FHIR Composition for new work
- **X12 EDI** — billing / claims format; deferred with billing layer
- **MedDRA** — regulatory adverse event dictionary; referenced via CSA-25 if trials pivot activates
- **NDC / RxNorm** — drug codes (RxNorm already in current schema via `ref_drug_classes`; NDC deferred)
- **CVX** — immunization codes (already used in current schema)

Historically omitted but now referenced (promoted in 2026-04-14 revision):

- **HL7 v2** — moved to ingest-pattern reference for hospital lab ingest (not storage)
- **DICOM** — moved to CSA-20 `imaging_studies` grounding
- **SMART on FHIR** — moved to `access_grants.scope` format reference
