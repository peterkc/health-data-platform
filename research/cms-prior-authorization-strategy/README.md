---
id: cms-prior-authorization-strategy
title: CMS prior authorization strategy for HDP
type: research
status: accepted
created: 2026-08-05
updated: 2026-08-05
hub: cms-prior-authorization-strategy
owner: peterkc
audience: [HDP product strategy, provider-side prior-authorization architecture]
direction: locked
tags: [cms, prior-authorization, fhir, ehr, denial-management, strategy]
related: [computer-use-emr-sync]
---

# CMS prior authorization strategy for HDP

## Answer

**Reposition one HDP vertical; do not broaden the platform.** The accepted first
deep OSS contribution is an **authorization evidence ledger**: an append-only,
bitemporal record of payer requirements, supporting evidence, human
attestations, submissions, requests for more information, decisions, denials,
and appeals.

The ledger sits beside an EHR, certified health IT, CDR, FHIR gateway,
clearinghouse, or portal adapter. It imports and exports CRD, DTR, PAS, and CDex
artifacts without becoming a FHIR server or claiming ONC certification. This
preserves HDP's current workflow-and-governance position and gives its designed
provenance, audit, consent, document, adapter, and human-review concepts one
working use case [F-005, F-007, F-009, F-014: raw/04-davinci-guides.md,
raw/06-hdp-revisions.md].

The CV benefit is implicit. The public value should come from a narrow OSS
component with a runnable synthetic example, exact boundaries, deterministic
tests, and honest implementation depth.

## Situation

CMS-0057-F already requires defined payer classes to meet decision-time,
specific-denial-reason, and public-metrics duties. Its APIs go live primarily in
2027. The rule excludes drugs, does not directly apply to Medicare FFS, and does
not require real-time adjudication, so API and legacy channels will coexist
[F-001, F-002: raw/01-cms-0057-f.md].

HTI-4 and the FY2027 standards update connect electronic prior authorization to
modular certified EHR functionality using CRD, DTR, PAS, CDS Hooks, SMART App
Launch, and subscriptions. Certification and provider incentive reporting are
related but distinct; the inspected sources do not establish that every external
component must itself be certified [F-004: raw/03-hti-4-ehr.md].

CMS-0062-P could later extend FHIR-based HIPAA transactions to providers, plans,
and clearinghouses that exchange electronic prior authorizations, add medical-
and pharmacy-benefit drug workflows, require currently recommended guides, and
publish payer API endpoints. It remains a proposal [F-003:
raw/02-cms-0062-p.md].

## Complication

The standards define transport and conformance, not the full operational job.
CRD discovers requirements, DTR captures structured documentation, PAS submits
and manages the transaction, and CDex exchanges supplemental data. They do not
standardize payer-policy authoring and versioning, clinical-evidence sufficiency,
local work queues, mixed-channel case state, medical-necessity judgment, or
learning from denials and remits [F-005: raw/04-davinci-guides.md].

WEDI's 86-response survey reports the same last-mile gap from another angle:
payers cite delegated-party connectivity, policy digitization, and funding;
providers cite expertise, cross-party testing, and workflow/network complexity.
The provider subgroup is small, so these are directional implementation signals,
not market prevalence [F-006: raw/05-wedi-readiness.md].

HDP also has an implementation credibility gap. Current main correctly says HDP
is a reference architecture that pairs with a CDR, but the cited canonical,
audit, provenance, identity, consent, agent, ingest, outbox, and API packages are
stubs with smoke tests. Older vault research simultaneously says HDP should build
and own its FHIR server [F-007, F-008: raw/06-hdp-revisions.md]. The OSS project
must resolve that contradiction through working depth, not another broad design.

## Question

Which payer and provider problems follow from the CMS changes, which of them
remain open after standards adoption, and what is the smallest useful OSS
primitive HDP can implement deeply without becoming an EHR, payer, clearinghouse,
FHIR server, or revenue-cycle platform?

## Approach

The source plan uses primary CMS, ASTP/ONC, and HL7 evidence for the regulatory
and technical boundary; WEDI for implementation signals; exact HDP revisions for
current capability; and official project sources for tool and provider-side
product fit. Final rules, proposals, observed behavior, interpretation, and
unknowns remain separate in `state.yaml`.

## Payer And Provider Impact Map

| Change | Payer effect | Provider effect | How HDP can help | HDP non-role |
|---|---|---|---|---|
| 2026 decision times and specific denial reasons, final | In-scope payers must change operations across all intake channels, preserve clocks, and provide specific reasons; FFE QHP timing is excluded | Providers can expect faster, more explicit outcomes from in-scope payers but still face clinical review and mixed payer rules | Record request/response clocks, channel, reason, policy snapshot, and supporting evidence in one case timeline | Enforce payer compliance or adjudicate the request |
| 2026 public metrics, final | Payers collect and publish approval, denial, appeal, extension, and elapsed-time measures | Providers gain aggregate transparency but not case-level explanation | Produce provider-side case metrics and trace every aggregate back to events | Submit or certify the payer's official CMS report |
| 2027 Prior Authorization API, final | In-scope payers expose requirements, accept requests, and return decisions or requests for more information | EHR and provider workflows must connect, test, route work, and handle payer variability | Import/export standard artifacts, validate evidence manifests, correlate retries and responses across channels | Run the payer API, replace the EHR, or claim FHIR conformance not tested by the project |
| HTI-4 effective October 1, 2025; guide replacements effective October 1, 2026, final | Payers interact with certified provider modules and newer guide versions | EHR developers may certify modular CRD/DTR/PAS capabilities; participating providers report an ePA measure | Preserve evidence and workflow state beside certified modules through explicit adapters | Claim ONC certification, CEHRT eligibility, CDS Hooks hosting, or subscriptions support without implementing and testing them |
| HIPAA FHIR transactions and drugs, proposed | More plans and clearinghouses could face FHIR/NCPDP duties; endpoint and metrics duties could expand | More providers could move from optional electronic exchange to a HIPAA-standard transaction path | Keep the domain ledger transport-neutral so new adapters do not change evidence semantics | Implement proposal-only behavior as if final or merge pharmacy- and medical-benefit standards |
| Central payer endpoint directory, proposed | Payers may publish endpoints, capability statements, and technical documentation | Providers and vendors need endpoint discovery, onboarding, and health monitoring | Add endpoint registry and conformance telemetry later if the rule finalizes and users validate the need | Build a speculative national directory before final policy and users exist |
| Payer API testing, transparency, and ONC oversight, RFI only | Payers could face a future conformance or oversight regime, but no requirement is proposed in the RFI | Providers and vendors need trustworthy conformance signals | Preserve test evidence and adapter telemetry so a later regime can consume it | Present an RFI as a proposal or certification requirement |

The impact map is grounded in the final/proposed policy captures and the guide
boundary [F-001-F-006: raw/01-cms-0057-f.md through
raw/05-wedi-readiness.md]. Rows describing what HDP can do are interpreted
recommendations, not current implementation claims.

## Shared Implementation Gaps

### Payer-side gaps

- Digitize coverage and documentation policies and maintain their effective
  versions.
- Connect delegated reviewers, utilization-management vendors, clearinghouses,
  and multiple internal systems.
- Validate endpoint, guide-version, authentication, and response behavior with
  provider partners.
- Explain requests for more information and denials in a form that can improve
  subsequent submissions.
- Reconcile case events with aggregate reporting without losing audit evidence.

### Provider-side gaps

- Integrate EHR context and prior-authorization work into clinical and back-office
  roles without duplicating data entry.
- Determine which payer/channel applies when CMS-regulated APIs, commercial
  plans, Medicare FFS, and legacy portals coexist.
- Prove that the evidence submitted was complete under the policy effective on
  the relevant date.
- Route more-information requests, denials, and appeals through a recoverable
  workflow.
- Test multiple payer implementations and guide versions with limited internal
  expertise.

### Shared gap

Our implementation hypothesis is that both sides benefit from a stable case
identity, bitemporal policy and evidence lineage, idempotent event correlation,
and a human-readable explanation of what changed. The Da Vinci guides exchange
artifacts; they do not define this cross-channel operational record. A design
partner must validate that the proposed model matches real workflows [F-005,
F-006, F-014].

## OSS Primitive

### Authorization evidence ledger

The ledger should own only these domain records:

- `AuthorizationCase`: one requested item/service and a derived view of events;
  the payer decision and EHR remain externally authoritative.
- `PolicySnapshot`: payer, plan, source, content hash, version, `valid_from`,
  `valid_until`, and `recorded_at`; the ledger proves which source it used but
  does not author or certify payer policy.
- `Requirement`: a computable or human-reviewed requirement from CRD, DTR, a
  public policy, or a synthetic fixture.
- `EvidenceItem`: a content-addressed reference to clinical or administrative
  evidence, with optional storage only when the host is authorized to retain the
  content; source systems remain the clinical record of truth.
- `Attestation`: the human judgment that evidence is accurate and may be used.
- `CaseEvent`: append-only submission, retry, request-more-information,
  approval, denial, cancellation, appeal, and supersession events.
- `EvidenceManifest`: the deterministic packet version exported for a specific
  attempt, including hashes and missing/ambiguous requirements.

```text
EHR / CEHRT / CDR                    Payer API / clearinghouse / portal
          |                                      |
          +---- CRD / DTR / PAS / CDex adapters -+
                              |
                    Authorization evidence ledger
                    policy + evidence + events
                    provenance + human attestation
                              |
                 manifest / diagnostics / timeline
```

### First tracer bullet

1. Load a synthetic payer-policy snapshot and synthetic CRD/DTR artifacts.
2. Link each requirement to synthetic chart evidence or mark it missing.
3. Require a named human attestation before freezing an evidence manifest.
4. Export a deterministic JSON manifest plus a human-readable packet.
5. Ingest a synthetic request-for-more-information or denial and connect it to
   the applicable policy, evidence, submission attempt, and next task.
6. Replay the case at any point in valid time and transaction time.

The tracer passes only with idempotent ingestion, immutable/superseding events,
content-hash verification, bitemporal tests, deterministic exports, failure and
retry tests, and synthetic data. AI, browser automation, payer submission,
medical-necessity recommendations, and production cloud deployment are excluded
from the first vertical.

The public tracer stores synthetic content only. A later PHI deployment must add
explicit tenant/patient authorization, encryption, minimum-necessary retrieval,
retention/deletion policy, and audit controls in the host deployment; this
research does not claim those controls are implemented.

### Why this is the right depth

- It proves HDP's promised provenance, audit, judgment, documents, adapters, and
  resilience instead of adding another package shell [F-007, F-009].
- It remains useful before and after payer FHIR adoption and across excluded
  payer channels [F-001, F-014].
- It complements the standards at their actual boundary rather than reimplementing
  them [F-005].
- It can later support denial triage, appeal packets, payer conformance testing,
  or a portal adapter without making any of those first-release dependencies.

## Tool Verdicts

| Tool | Verdict | Boundary |
|---|---|---|
| Semantica | Reference now; optional sidecar later | Its temporal, decision, graph, and PROV-O concepts are relevant, but broad dependencies, volatile defaults, and source-visible incomplete paths make it unsuitable as the authoritative first core [F-010: raw/07-semantica.md] |
| TencentDB Agent Memory | Reject from PHI runtime | It is fail-soft conversational memory without verified tenant/patient authorization or assured case-state semantics. Limit any use to public or synthetic developer memory [F-011: raw/08-tencentdb-agent-memory.md] |
| Gortex | Use for development only | It indexes and analyzes source code; it is not a healthcare runtime component [F-012: raw/09-control-plane-tools.md] |
| Pulumi | Defer until a service is deployed | It is a deployment control plane. The surrounding controller must own approval, IAM, audit, and separation of duties [F-012: raw/09-control-plane-tools.md] |
| Pydantic AI | Optional after deterministic core | Approval/deferred-tool and durable-workflow integrations can support later drafting or triage, but host code must retain side-effect and audit authority [F-012: raw/09-control-plane-tools.md] |

The first OSS release should have no required AI framework. An optional agent can
explain a deterministic result or draft an appeal after the ledger can produce
the same evidence packet without a model.

## Provider-Side Product Opportunities

Provider-side chart-review and revenue-integrity products already occupy the
policy and clinical-intelligence gap left by the standards [F-013:
raw/10-backbone-public.md]. The CMS changes create several adjacent problems they
could solve:

1. **CRD/DTR evidence readiness:** assess whether the chart actually supports
   every payer requirement before PAS submission.
2. **Temporal policy proof:** show which policy, contract clause, and rule version
   applied at the service or submission date.
3. **Mixed-channel continuity:** preserve one case across FHIR, clearinghouse,
   portal, fax, and phone events.
4. **Denial and more-information feedback:** connect each response to the exact
   missing or conflicting evidence and feed the outcome into future pre-service
   and pre-bill checks.
5. **EHR and payer test orchestration:** provide synthetic cases, guide-version
   compatibility checks, endpoint health, and workflow observability for
   providers with limited internal expertise.
6. **Case-level audit and measurement:** prove why a case was greenlit, who
   attested, what was sent, and how an outcome changed the policy model.

These are product hypotheses. The approved public source establishes a
provider-side vendor's stated chart-review boundary, not its internal roadmap or
unmet needs.

## Accepted Decisions

- `D-001`: Reposition one HDP vertical around a deep OSS authorization evidence
  ledger; do not build a broad prior-authorization platform.
- `D-002`: Own case events, policy snapshots, evidence lineage, human
  attestations, and deterministic manifests.
- `D-003`: Pair with the EHR/CDR/FHIR/certification ecosystem through adapters.
- `D-004`: Keep the named tools in their bounded reference, development,
  control-plane, or optional-agent roles.

The research owner accepted `D-001` through `D-004` on August 5, 2026.

## Open Questions

- `Q-001`, non-blocking: What exact CEHRT configuration satisfies the 2027
  measure when an external evidence component participates?
- `Q-002`, non-blocking: Which CMS-0062-P provisions and dates will be finalized?
- `Q-003`, non-blocking: Which provider, payer, clearinghouse, or vendor will
  validate the tracer workflow and fixtures?
- `Q-004`, non-blocking: Which permissively licensed synthetic policy and
  authorization examples can form a public conformance corpus?

## Next Actions

1. Write a specification for only the tracer bullet above.
2. Recruit one workflow reviewer before adding a second transport or an AI path.
3. Track CMS-0062-P and the final 2027 measure specification as external inputs,
   not reasons to block the transport-neutral core.

## Cross-references

- `state.yaml` records approved scope, source authority, findings, accepted
  decisions, questions, and sufficiency.
- `raw/` contains bounded, independently verified source captures.
- Beads issue `hdp-3dh` owns execution status.
