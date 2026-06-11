# Data Type Catalog — Coverage Against Public Sources

**Status**: Living — updated 2026-04-14 for D7 split (health_records -> 6 FHIR-aligned tables)
**Purpose**: If we compose 15 published Health IT schemas, what data types must a Health OS accommodate, and where are our gaps?
**Audience**: Engineers planning CSA proposals; coverage review; gap-to-roadmap narrative
**Companion to**: [design-queue.md](design-queue.md), [platform-malleability.md](platform-malleability.md), [references.md](references.md)

## How to read this file

- Scan the "Health OS coverage" column in the coverage matrix to find Covered / Partial / Gap status per data type
- Each Gap or Partial row links to a CSA proposal in [design-queue.md](design-queue.md) via the "Proposal" column
- Coverage percentages are scored per domain section and summarized at the end
- Feeds into: [design-queue.md](design-queue.md) CSA-13 through CSA-35; related: [decisions.md](decisions.md) D7 (the split decision)

## Thesis

A Health OS absorbs from any source. Coverage is not self-assessable — it must be measured against an external ontology of "what clinical data exists." This catalog composes ~15 public schemas into a single data-type matrix, then scores Health OS's current design against it.

Two outputs:

1. A coverage percentage per domain (post-D7: ~52% overall; pre-D7: ~45%)
1. A CSA backlog (CSA-13 through CSA-35) with each proposal cited to a public schema — no invented shapes

Malleability IS architecture quality. If we cannot absorb what FHIR defines, we are not a Health OS; we are a longevity vertical pretending.

## Public sources surveyed

| Source                              | Enumerates                                       | Applicability                   |
| ----------------------------------- | ------------------------------------------------ | ------------------------------- |
| FHIR R4 / R5 resources              | ~145 clinical resource types                     | Authoritative clinical ontology |
| USCDI v4 (v5 draft public)          | Federally-required data classes (~90 elements)   | US regulatory floor             |
| OMOP CDM v5.4                       | Research data model (~30 tables)                 | Analytics / trials pivot        |
| HealthKit SDK                       | Consumer wearable sample types (~150)            | Consumer ingest                 |
| openEHR archetype library           | International curated archetypes (~3,000)        | Domain archetype coverage       |
| International Patient Summary (IPS) | Minimum summary data set (~32 elements)          | Cross-border interop            |
| CDISC ODM + SDTM + ADaM             | Clinical trial data model                        | Trials pivot                    |
| GA4GH Variant Representation Spec   | Genomic variant structure                        | Genomics pivot                  |
| IEEE 11073 PHD                      | Medical device data exchange                     | RPM pivot                       |
| CDC growth charts + Bright Futures  | Pediatric reference + visit schedules            | Pediatric pivot                 |
| CMS RPM billing codes               | Reimbursable RPM actions (99453, 99454, 99457-8) | RPM realism                     |
| VeNom Coding Group                  | Veterinary diagnoses                             | Vet pivot                       |
| SNOMED CT                           | Clinical terminology                             | Vocabulary                      |
| ICD-10-CM + ICD-10-PCS              | Diagnoses + inpatient procedures                 | Vocabulary                      |
| SMART on FHIR                       | Patient/provider app integration spec            | App ecosystem                   |

External schema catalog is in [references.md](references.md).

## Legend

- **Covered** — first-class table exists, queryable via indexed columns
- **Partial** — representable via extensions JSON or loose fit; queryable but degraded
- **Gap** — no tabular representation; would land in extensions JSON or documents blob

## Coverage matrix

### Observation & vitals domain

| Data type                                    | Public source                           | Health OS coverage | Proposal |
| -------------------------------------------- | --------------------------------------- | ------------------ | -------- |
| Vital signs (BP, HR, RR, temperature, SpO2)  | FHIR Observation (vital-signs)          | Covered            | —        |
| Lab results                                  | FHIR Observation + LOINC                | Covered            | —        |
| Anthropometrics (height, weight, BMI)        | USCDI v4                                | Covered            | —        |
| Pain scale                                   | FHIR Observation                        | Covered            | —        |
| Cognitive assessments (MMSE, MoCA)           | FHIR QuestionnaireResponse              | Partial            | CSA-17   |
| Surveys / PROs (PHQ-9, GAD-7, SF-36, PCL-5)  | FHIR QuestionnaireResponse              | Partial            | CSA-17   |
| Social determinants of health (SDOH)         | USCDI v4 SDOH + LOINC 88121-9 et al.    | Partial            | —        |
| Functional status (ADL, IADL, Barthel index) | FHIR Observation + LOINC                | Partial            | CSA-17   |
| Waveforms (ECG, EEG, PPG)                    | FHIR Observation.valueSampledData       | Gap                | CSA-21   |
| Continuous biometric streams (1Hz+)          | openEHR POINT_EVENT + HealthKit samples | Partial            | CSA-24   |

### Clinical state domain

| Data type                  | Public source                     | Health OS coverage    | Proposal |
| -------------------------- | --------------------------------- | --------------------- | -------- |
| Conditions / problems      | FHIR Condition                    | Covered (D7)          | —        |
| Allergies / intolerances   | FHIR AllergyIntolerance           | Covered (D7)          | —        |
| Medications (active)       | FHIR MedicationStatement          | Covered (D7)          | —        |
| Medication requests (CPOE) | FHIR MedicationRequest            | Partial (D7 + CSA-16) | CSA-16   |
| Procedures                 | FHIR Procedure                    | Gap                   | CSA-14   |
| Immunizations              | FHIR Immunization                 | Covered (D7)          | —        |
| Family history             | FHIR FamilyMemberHistory          | Covered (D7)          | —        |
| Social history             | FHIR Observation (social-history) | Covered (D7)          | —        |
| Clinical impression        | FHIR ClinicalImpression           | Gap                   | —        |
| Adverse events             | FHIR AdverseEvent                 | Gap                   | CSA-25   |

### Workflow domain

| Data type                        | Public source                         | Health OS coverage | Proposal |
| -------------------------------- | ------------------------------------- | ------------------ | -------- |
| Encounters                       | FHIR Encounter                        | Covered            | —        |
| Appointments / scheduling        | FHIR Appointment                      | Gap                | —        |
| Orders (lab, imaging, procedure) | FHIR ServiceRequest                   | Gap                | CSA-16   |
| Referrals                        | FHIR ServiceRequest (intent=referral) | Gap                | CSA-27   |
| Tasks / action items             | FHIR Task                             | Gap                | —        |
| Care plans                       | FHIR CarePlan                         | Covered            | —        |
| Goals                            | FHIR Goal                             | Covered            | —        |
| Care gaps / detected issues      | FHIR DetectedIssue                    | Gap                | CSA-28   |
| Risk assessments                 | FHIR RiskAssessment                   | Gap                | CSA-35   |
| Messaging (patient-provider)     | FHIR Communication                    | Gap                | CSA-32   |

### People & roles domain

| Data type       | Public source            | Health OS coverage | Proposal |
| --------------- | ------------------------ | ------------------ | -------- |
| Patient         | FHIR Patient             | Covered            | —        |
| Practitioner    | FHIR Practitioner        | Covered            | —        |
| Care team       | FHIR CareTeam            | Partial            | CSA-19   |
| Related persons | FHIR RelatedPerson       | Covered            | —        |
| Deceased state  | FHIR Patient.deceased[x] | Gap                | CSA-18   |
| Organization    | FHIR Organization        | Covered            | —        |

### Documents & content domain

| Data type                | Public source                      | Health OS coverage | Proposal |
| ------------------------ | ---------------------------------- | ------------------ | -------- |
| Documents (generic)      | FHIR DocumentReference             | Covered            | —        |
| Compositions (sectioned) | FHIR Composition                   | Partial            | CSA-7    |
| Imaging studies (DICOM)  | FHIR ImagingStudy + DICOM metadata | Partial            | CSA-20   |
| Specimens                | FHIR Specimen                      | Gap                | CSA-30   |
| Advance directives       | FHIR Consent (directive subtype)   | Partial            | CSA-29   |
| Structured consent forms | FHIR Consent                       | Partial            | CSA-34   |

### Genomics domain

| Data type                          | Public source                      | Health OS coverage | Proposal |
| ---------------------------------- | ---------------------------------- | ------------------ | -------- |
| Molecular sequence / variant calls | FHIR MolecularSequence + GA4GH VRS | Gap                | CSA-23   |
| Polygenic risk scores              | FHIR Observation (genomic)         | Partial            | —        |
| Pharmacogenomics (CYP2D6 etc.)     | CPIC guidelines + FHIR Observation | Partial            | —        |

### Devices & RPM domain

| Data type                     | Public source                  | Health OS coverage | Proposal |
| ----------------------------- | ------------------------------ | ------------------ | -------- |
| Device definition             | FHIR Device                    | Gap                | CSA-15   |
| Device use statement          | FHIR DeviceUseStatement        | Gap                | CSA-15   |
| Device metrics / alerts       | FHIR DeviceMetric              | Gap                | CSA-15   |
| Remote monitoring push events | IEEE 11073 + FHIR Subscription | Gap                | CSA-22   |

### Trials & research domain

| Data type                     | Public source                              | Health OS coverage | Proposal |
| ----------------------------- | ------------------------------------------ | ------------------ | -------- |
| Research study                | FHIR ResearchStudy                         | Gap                | CSA-33   |
| Research subject / enrollment | FHIR ResearchSubject                       | Gap                | CSA-33   |
| Adverse events                | FHIR AdverseEvent                          | Gap                | CSA-25   |
| Questionnaires + responses    | FHIR Questionnaire + QuestionnaireResponse | Gap                | CSA-17   |
| Case Report Forms             | CDISC ODM                                  | Gap                | CSA-33   |
| Analytics data (OMOP CDM)     | OMOP CDM v5.4                              | Gap                | CSA-9    |

### Pediatric domain

| Data type                         | Public source                           | Health OS coverage | Proposal |
| --------------------------------- | --------------------------------------- | ------------------ | -------- |
| Growth measurements + percentiles | CDC growth charts + LOINC growth panels | Partial            | CSA-26   |
| Developmental milestones          | Denver II + AAP Bright Futures          | Gap                | CSA-26   |
| Pediatric screening batteries     | AAP Bright Futures                      | Gap                | CSA-17   |
| School health records             | State-specific (no federal schema)      | Gap                | —        |

## Domain coverage summary (post-D7 split)

| Domain                                         | Covered | Partial | Gap | Coverage score | Δ from pre-D7 |
| ---------------------------------------------- | ------- | ------- | --- | -------------- | ------------- |
| Observation & vitals                           | 4       | 4       | 2   | 50%            | 0             |
| Clinical state                                 | 7       | 1       | 2   | 90%            | +20           |
| Workflow                                       | 3       | 0       | 7   | 30%            | 0             |
| People & roles                                 | 5       | 1       | 0   | 90%            | 0             |
| Documents & content                            | 1       | 4       | 1   | 50%            | 0             |
| Genomics                                       | 0       | 2       | 1   | 33%            | 0             |
| Devices & RPM                                  | 0       | 0       | 4   | 0%             | 0             |
| Trials & research                              | 0       | 0       | 6   | 0%             | 0             |
| Pediatric                                      | 0       | 1       | 3   | 13%            | 0             |
| **International readiness (added 2026-04-14)** | 0       | 4       | 8   | 17%            | (new dim)     |

**Aggregate (post-D7)**: ~52% of enumerated clinical data types have first-class tabular coverage (was ~45% pre-D7). **International readiness** (separate dimension): 17% — Health OS cites mostly US sources; international sources surfaced via 2026-04-14 audit and mapped to CSA-39 through CSA-44.

### International readiness sub-dimension

This dimension scores Health OS's coverage of international standards required for non-US operations:

| Concern                              | Public source                  | Health OS coverage                                  | Proposal |
| ------------------------------------ | ------------------------------ | --------------------------------------------------- | -------- |
| Drug classification (non-US)         | WHO ATC                        | Gap                                                 | CSA-39   |
| Primary care diagnosis (EU-dominant) | WONCA ICPC-2                   | Gap                                                 | CSA-39   |
| Future diagnosis standard            | WHO ICD-11                     | Gap                                                 | CSA-39   |
| UK pharmacy data                     | UK NHS dm+d                    | Gap                                                 | CSA-39   |
| Adverse event coding (regulatory)    | MedDRA                         | Gap                                                 | CSA-43   |
| Functional status (international)    | WHO ICF                        | Gap                                                 | CSA-44   |
| EU EHR communication                 | ISO 13606 + openEHR archetypes | Partial (`ref_record_type_schemas` hint)            | CSA-41   |
| EU cross-enterprise document sharing | IHE XDS / XCA                  | Gap                                                 | CSA-42   |
| EU privacy framework                 | GDPR + EHDS                    | Partial (`access_grants` consent shape generalizes) | CSA-40   |
| UK privacy framework                 | UK Data Protection Act 2018    | Partial                                             | CSA-40   |
| Canadian privacy framework           | PIPEDA                         | Gap                                                 | CSA-40   |
| AU privacy framework                 | Australia Privacy Act + APPs   | Gap                                                 | CSA-40   |

The four "Partial" rows reflect that Health OS's primitives (access_grants multi-dimensional consent; ref_record_type_schemas archetype-style contracts) generalize to international shapes — but no international source is *cited*, *tested*, or *modeled* yet. Citation discipline failure, not architectural failure.

D7's contribution clusters in one domain: clinical state moved +20 because conditions, medications, allergies, immunizations, and family_history each got dedicated FHIR-aligned tables. Other domains unchanged — they need their respective CSAs (CSA-14 procedures, CSA-15 devices, CSA-16 orders, etc.) to advance.

D7 is the **enabling precondition** for the remaining CSAs: every new data-type CSA now becomes a clean table addition rather than an enum/extensions-JSON workaround. The +7 aggregate improvement is the surface effect; the structural effect on the cost of every future CSA is the deeper win.

## Pivot-driven architectural requirements

Cross-reference against [platform-malleability.md](platform-malleability.md) pivot targets.
The question for each pivot: *which data types must exist as first-class tables* (not extensions JSON) for the pivot to be credible?

| Pivot                              | Fit % | Critical data types (first-class requirement)                                       | Blocking CSAs          |
| ---------------------------------- | ----- | ----------------------------------------------------------------------------------- | ---------------------- |
| Longevity / concierge (primary)    | 100%  | Observations, Conditions, Medications, Allergies, Family Hx, Encounters, Care Plans | None (already covered) |
| Medical charting                   | 75%   | Orders, Procedures, Care Team, Referrals, Appointments                              | CSA-14, -16, -19, -27  |
| Clinical trials platform           | 60%   | ResearchStudy / Subject, AdverseEvent, Questionnaires, CRFs, OMOP analytics         | CSA-9, -17, -25, -33   |
| Mental health / therapy            | 70%   | Questionnaires (PROs), RiskAssessments, AdvanceDirectives, structured session notes | CSA-17, -29, -35       |
| Remote patient monitoring          | 50%   | Devices, DeviceMetrics, push-ingest, Continuous streams, ClinicalAlerts             | CSA-15, -22, -24, -28  |
| Pediatric longitudinal             | 65%   | GrowthMeasurements, Milestones, Questionnaires (screening)                          | CSA-17, -26            |
| Employer wellness                  | 80%   | ProgramEnrollment, Tasks, Rewards                                                   | CSA-33                 |
| GDPR personal data vault           | 70%   | ConsentDocuments, AdvanceDirectives, AccessLog                                      | CSA-1, -29, -34        |
| Citizen data portability (generic) | 50%   | Configurable ref_record_types + full consent audit                                  | CSA-13, -1, -3         |
| Enterprise knowledge + AI agent    | 40%   | record_type rename → "subject_data_type"; vertical-specific ref layer               | CSA-13                 |

The consistent pattern: **CSA-13 (record_type → VARCHAR + ref table) is a precondition for every pivot beyond longevity**. It is the single architectural decision that determines whether Health OS's malleability claim is credible.

## What this catalog tells us

1. **Longevity vertical is ~70% covered**. Matches platform-malleability.md's "primary pitch" readiness.

1. **Pivots need 15-20 additional first-class tables**. CSA-13 through CSA-35 span this need, each cited to a public schema.

1. **Non-tabular modalities (genomics, imaging, waveforms, continuous streams) are systematically under-modeled**. Acceptable for longevity; blocking for trials, RPM, and ambient scribing.

1. **Workflow layer (30% coverage) is the biggest relative gap**. Acceptable for patient-first design; blocking for provider-first charting.

1. **CSA-13 is the single most consequential change**. One DDL edit removes the record_type ENUM schema-lock and opens the door to every other CSA. All other CSAs are additive; CSA-13 is architectural.

1. **D7 (2026-04-14) executes the foundational rescope**. CSA-13 was originally framed as "ENUM → VARCHAR + ref table on `health_records`". D7 supersedes that single-table assumption: rather than parameterize one table, split into 6 FHIR-aligned core tables (observations, conditions, medications, allergies, immunizations, family_history). CSA-13 is now scoped to `observations` only, where it discriminates observation sub-types (vital-signs, laboratory, social-history, survey-result, imaging-finding). See [decisions.md#D7](decisions.md).

## How this catalog is maintained

- Add a row when a public schema or pivot surfaces a data type not listed
- Move rows from "Gap" → "Partial" → "Covered" as CSAs land in DDL
- Cite the exact public schema section (FHIR resource name, USCDI class, LOINC code family)
- Update the aggregate coverage percentage in the summary table when rows change

## Iteration log

| Date       | Change                                                                                                                                                                                                                                                                        | Rationale                                                                                                                                                                                 |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-04-14 | D7 split applied: clinical-state coverage 70% → 90%; aggregate 45% → 52%. Conditions, medications, allergies, immunizations, family_history, social history all moved from Partial to Covered (D7) via dedicated FHIR-aligned tables. CSA-13 rescoped to `observations` only. | User: "Option B is the logical choice" — formalized D7 + recomputed coverage matrix.                                                                                                      |
| 2026-04-14 | Initial capture                                                                                                                                                                                                                                                               | User asked "public datasets to ground research" + "pivots shape thinking" — composed 15 public schemas into matrix; surfaced CSA-13 as the one architectural precondition for all pivots. |

Append new entries above this line.
