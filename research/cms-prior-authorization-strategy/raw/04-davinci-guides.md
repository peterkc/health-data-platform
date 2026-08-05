# S-004: Da Vinci CRD, DTR, PAS, and CDex guides

Source: Official HL7 permanent guide roots for CRD 2.2.1, DTR 2.2.0, PAS 2.2.1, and CDex 2.1.0
Tools: Exa web fetch
Query: not applicable
Worker: research-worker-terra
Invocation route: task
Revision: CRD 2.2.1; DTR 2.2.0; PAS 2.2.1; CDex 2.1.0
Evidence goal: Define actor, workflow, data, API, and conformance boundaries and identify functions outside the standards.
Rationale: The guides distinguish standards transport from workflow and evidence value.
Captured: 2026-08-05
Byte verification: verified
Verified by: openai/gpt-5.6-sol primary at 2026-08-05T14:36:00Z
Verification method: Reopened all four user-approved corrected HL7 permanent-version roots with Exa.
Normalization: none
Citation verification:
- Source locator: https://hl7.org/fhir/us/davinci-cdex/STU2.1/
  Source span: exact text beginning `This IG provides detailed guidance` and ending `(or other providers).`
  Capture span: line 73
  Source span SHA-256: bd3444c61091d477d9c5a9e0b84e1c9f9f51a14f422f6f0f8dd86e2522c0834d
  Capture span SHA-256: bd3444c61091d477d9c5a9e0b84e1c9f9f51a14f422f6f0f8dd86e2522c0834d
Outcome: gathered

## Evidence

### CRD: discover requirements

CRD lets a payer-side CDS Hooks service return coverage requirements to an EHR,
practice-management, scheduling, or registration client at a user-facing event.
It can indicate authorization requirements, documentation rules, alternatives,
forms, and an already-satisfied authorization identifier. It does not standardize
local orchestration among provider applications or staff.

### DTR: capture documentation

DTR expresses payer documentation requirements with FHIR Questionnaire,
QuestionnaireResponse, CQL, and value sets. It can prepopulate existing EHR data,
adapt questions, and run as a SMART application or embedded functionality. It
standardizes data capture and conformance roles, not local business operations or
medical-necessity judgment.

### PAS: submit and manage the request

PAS exchanges FHIR request and response Bundles for submission, status inquiry,
updates, and cancellation. It can use an intermediary for X12 278 translation,
or use intact FHIR Bundles under CMS enforcement discretion. It standardizes the
transaction lifecycle, not payer coverage policy or adjudication criteria.

### CDex: exchange additional clinical data

CDex defines direct query, task-based, and attachment exchanges. Data sources can
be EHR, HIM, practice-management, population-health, or registration systems.
Artifacts can include FHIR resources and Bundles, QuestionnaireResponse, C-CDA,
PDF, and text. It does not determine whether evidence proves medical necessity.

### Composition

```text
CRD: surface payer requirements at the care decision
  -> DTR: capture required structured documentation
  -> PAS: submit and manage the authorization transaction
  -> CDex: exchange supplemental clinical data or attachments
```

All four are trial-use implementation guides. They define interoperable roles,
payloads, APIs, and conformance. They leave payer policy authoring and versioning,
clinical-evidence sufficiency, local staffing and work queues, adjudication,
cross-channel case state, and outcome learning outside the technical standard.

## Verified Excerpt

```text
This IG provides detailed guidance that helps implementers use FHIR-based interactions to support specific clinical data exchanges between providers and payers (or other providers).
```

## Notes

The first approved HL7 paths used nonexistent `STU...` directories. After a
forced checkpoint, the user approved the permanent numeric-version paths used in
this capture.

## Followups

- Profile-level cardinalities and complete X12 rules require separate approved
  sources if implementation reaches those boundaries.
