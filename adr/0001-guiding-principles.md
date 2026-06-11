---
status: Accepted
date: 2026-06-11
category: Foundation
tags: [principles, governance, ai-safety, foundation]
---

# ADR 0001: Guiding Principles

## Context

HDP is an AI-native workflow and governance layer for healthcare verticals.
Every technology choice (ADR 1xxx), architecture decision (2xxx), and process
(3xxx–4xxx) reflects implicit values. Without naming those values:

- Contributors cannot evaluate whether a proposed feature aligns with what HDP is
- Competing priorities have no tiebreaker — scope vs. safety debates restart from zero
- The platform primitives (audit, consent, provenance) exist as packages but
  lack the value system that explains why they are primitives and not features

### Why an LLM-Native Platform Needs This

HDP's premise is that LLMs do real clinical-adjacent work: extracting OASIS-E
assessment answers from visit recordings, drafting documentation, and syncing
records into EMRs that expose no API. A general-purpose model's safety training
does not know where this domain's lines are:

- **Authorship boundary**: model output that lands in an OASIS-E assessment
  determines case-mix payment under PDGM. A fabricated answer is not a quality
  bug — it is a false claim. The model drafts; a clinician is the author of record
- **Asymmetric calibration**: retrieval and drafting should be liberal
  (a blocked draft sends the clinician back to manual entry, bypassing every
  control); commits to the record should be conservative (fabricated data
  looks like real data). The base model applies uniform caution — this
  asymmetry is domain knowledge
- **Failure as the normal path**: LLM extraction and computer-use automation
  fail routinely. The platform's value is not that steps never fail, but that
  every failure is recoverable without corrupting the record

These principles also govern the platform's own development. HDP is built
substantially by LLM agents; the same constitution that constrains the runtime
agent constrains the engineering agents — claims need provenance, an
orchestrating human adjudicates, complexity must be earned.

### Scope

Five principles — not fifteen — because principles only work when they fit in
working memory. Single-word names; subtitles and body text carry the depth.

## Decision Drivers

- Principles replace process where process does not yet exist: no compliance
  department reviews a PR; principles guide daily judgment calls
- Health data mistakes are not technical debt — in deployment they void BAAs
  and trigger regulatory enforcement; in an assessment workflow they become
  payment-integrity findings
- LLM agents acting on clinical workflows introduce liability territory that
  generic software principles do not cover
- The existing primitives already encode implicit values; naming them prevents
  drift as the platform evolves

## Principles

```
          HDP Guiding Principles

  HOW WE MOVE
  +------------------------------------------+
  |  P5  Leverage                            |
  |                                          |
  |  HOW WE BUILD                            |
  |  +------------------------------------+  |
  |  |  P4  Resilience                    |  |
  |  |                                    |  |
  |  |  WHY WE EXIST                      |  |
  |  |  +------------------------------+  |  |
  |  |  |  P1  Provenance              |  |  |
  |  |  |  P2  Judgment                |  |  |
  |  |  |  P3  Consent                 |  |  |
  |  |  +------------------------------+  |  |
  |  |                                    |  |
  |  +------------------------------------+  |
  |                                          |
  +------------------------------------------+
```

Inner ring constrains outer ring. When principles conflict, inner wins.

> AI can only do clinical-adjacent work if every claim carries its lineage.
> Lineage only matters if a human owns the final judgment. Judgment operates
> on data that moves only with consent. Workflows built on fallible models
> must treat failure as the normal path. And a layer earns its place by
> leveraging the ecosystem, not replacing it.
>
> **Provenance. Judgment. Consent. Resilience. Leverage.**

## How to Apply

### For New Features

1. Can every value this produces be traced to its source? (P1)
1. Who attests the output, and is that gate structural? (P2)
1. What permission does this data movement rest on? (P3)
1. What happens when the step fails halfway — can it re-run safely? (P4)
1. Does this belong in HDP, or does the ecosystem already provide it? (P5)

### For New ADRs

Reference which principles the decision serves in the Decision Drivers
section. A decision that cannot name a principle it serves may not be
necessary.

### For Conflict Resolution

Inner ring wins: P1–P3 over P4 over P5. If two inner-ring principles
conflict, the one closer to record integrity wins. P5's bias for motion
explicitly defers to P1–P3 for irreversible decisions.

### For AI Agent Behavior

HDP's principles operate as a domain-specific layer on top of the model's own
safety constitution. They narrow the behavioral space — adding constraints
around authorship, lineage, and consent — and never widen it. Nothing in
HDP's principles permits what the model's constitution prohibits. When both
apply, take the more conservative position.

The same layering applies to engineering agents working on this codebase:
verify against the source before asserting; surface findings before mutating;
treat generated output as a proposal until adjudicated.

______________________________________________________________________

### P1: Provenance

*AI output is a proposal, not a record*

Nothing enters the record without lineage: which recording, which document,
which model call, which human edit produced this value. An LLM-extracted
assessment answer is a draft with a citation trail until a human attests it —
and after attestation, the trail persists.

Three constraints follow:

- **Source preservation**: original artifacts (audio, documents, transcripts)
  are immutable; derived values are computed views that reference their source
- **Model-call lineage**: every LLM invocation that contributes to a record is
  logged with inputs, model identity, and output — sufficient to reconstruct
  why the system proposed what it proposed
- **Append-only audit**: corrections supersede, they never overwrite; the
  audit trail is tamper-evident and sufficient for payment-integrity and
  breach investigation alike

**Governs**: provenance and audit primitives, the outbox pattern, extraction
citation requirements, scribe draft lifecycle.

**Sources**: [HIPAA §164.312(b) (audit controls)](https://www.ecfr.gov/current/title-45/section-164.312#p-164.312(b)),
[W3C PROV-DM](https://www.w3.org/TR/prov-dm/),
[ONC HTI-1 transparency requirements](https://www.healthit.gov/topic/laws-regulation-and-policy/health-data-technology-and-interoperability)

______________________________________________________________________

### P2: Judgment

*AI drafts, humans sign*

Human-in-the-loop is architecture, not a feature toggle. The platform's write
paths are structured so that model output cannot reach a record of consequence
without passing a human gate — and the gate is load-bearing, not ceremonial.

The calibration is asymmetric, and the asymmetry is deliberate:

- **Liberal on retrieval and drafting**: refusing to surface relevant context
  or draft a plausible answer forces the clinician to work around the system,
  bypassing every safety control it provides
- **Conservative on commit**: an OASIS-E answer determines case-mix payment
  under PDGM; a hallucinated value is indistinguishable from a real one once
  recorded. Omitting a draft answer is recoverable; committing a fabricated
  one is a false claim

The attesting human — not the model, not the platform — is the author of
record. This boundary also keeps decision-support behavior on the
non-device side of the FDA CDS exemption: the system surfaces, summarizes,
and drafts; it does not direct clinical action.

**Governs**: HITL review flow, every EMR write-back path, confidence gating,
diagnostic-language detection in scribe output.

**Sources**: [FDA CDS exemption (21st Century Cures Act §3060)](https://www.fda.gov/regulatory-information/selected-amendments-fdc-act/21st-century-cures-act),
[CMS PDGM case-mix methodology](https://www.cms.gov/medicare/payment/prospective-payment-systems/home-health),
[Anthropic Core Views on AI Safety](https://www.anthropic.com/research/core-views-on-ai-safety)

______________________________________________________________________

### P3: Consent

*Data moves only with permission, at the granularity the law requires*

Consent is a first-class primitive, not deployment-time policy. The platform
models who may see what, for what purpose, with category-level granularity —
because the strictest applicable regime, not the average one, sets the bar.

- **Minimum necessary**: collect and surface only what the workflow requires;
  smaller data surface, smaller breach surface
- **Purpose limitation**: data gathered for care documentation cannot be
  repurposed (training, analytics) without explicit consent
- **Category-level consent**: 42 CFR Part 2 protects substance-use-disorder
  records more strictly than HIPAA baseline; a consent model that cannot
  express category-level restrictions cannot serve behavioral health at all.
  Designing for the strictest category first means lesser regimes are
  configuration, not migration

**Governs**: consent and identity primitives, API access control, what
context the agent runtime is permitted to assemble per task.

**Sources**: [HIPAA minimum necessary (§164.502(b))](https://www.ecfr.gov/current/title-45/section-164.502#p-164.502(b)),
[42 CFR Part 2](https://www.ecfr.gov/current/title-42/chapter-I/subchapter-A/part-2),
[GDPR Article 5 (purpose limitation)](https://gdpr.eu/article-5-how-to-process-personal-data/)

______________________________________________________________________

### P4: Resilience

*The failing step is the normal path*

LLM extraction, browser automation, and integrations with API-less EMRs fail
routinely — timeouts, drift in target UIs, low-confidence output, partial
writes. A platform whose value proposition is automating these workflows must
treat failure as the designed-for case, not the exception:

- **Idempotent write-back**: every external mutation can be safely retried;
  re-running a workflow never duplicates or corrupts a record
- **Checkpointed orchestration**: long workflows resume from the last good
  step, with provenance intact across the retry boundary
- **Failure taxonomy**: failures are classified (transient, drift,
  low-confidence, permission) and routed — retry, re-extract, or escalate to
  a human — rather than collapsed into a generic error
- **Observability**: when a workflow dies, the system can say which step,
  why, and what state the external system was left in

A workflow that cannot be safely re-run does not ship. This is the principle
that distinguishes workflow infrastructure from a demo.

**Governs**: EMR sync orchestration, agent runtime execution model, outbox
delivery semantics, the computer-use failure taxonomy.

**Sources**: [Google SRE (embracing risk, observability)](https://sre.google/sre-book/table-of-contents/),
idempotency and exactly-once-effect patterns in distributed systems
([Helland, "Idempotence Is Not a Medical Condition"](https://queue.acm.org/detail.cfm?id=2187821))

______________________________________________________________________

### P5: Leverage

*Be the layer, not the silo; complexity must be earned*

Two faces of one discipline:

- **Leverage the ecosystem**: HDP is not a clinical data repository. FHIR R4
  is a projection HDP emits, not a storage model it reimplements; record
  storage pairs with a dedicated CDR such as [Medplum](https://www.medplum.com/)
  or [HAPI FHIR](https://hapifhir.io/). Building what the ecosystem already
  provides is scope HDP cannot afford and accountability it should not claim
- **Earn complexity**: packages, abstractions, and seams exist because the
  code demonstrates the need, not because the architecture diagram predicted
  it. Structure that outruns its use is deleted, not preserved

The heuristic: "Can this be undone in a day?" If yes, decide now and learn
from the result. If no, apply P1–P3 first.

**Governs**: positioning against CDRs, workspace package consolidation,
transport-agnostic adapter seams, build/stub/skip decisions.

**Sources**: [Shape Up (bounded bets)](https://basecamp.com/shapeup),
Anthropic "do the simple thing that works",
[Stripe on API composability](https://stripe.com/blog/payment-api-design)

______________________________________________________________________

## Considered Options

### Option 1: Five Named Principles with Hierarchy (Chosen)

Five principles in three concentric rings (why we exist, how we build, how we
move). Inner ring constrains outer ring.

**Good**:

- five fits in working memory — recitable without a reference
- hierarchy resolves conflicts — record integrity beats velocity
- each principle maps to existing primitives (every principle names what it governs)

### Option 2: Adopt a Generic Framework Wholesale

Borrow an established value set (e.g., a large company's leadership principles).

**Good**:

- battle-tested at scale

**Bad**:

- generic frameworks have no equivalent for the LLM-specific territory —
  authorship boundaries, asymmetric calibration, failure-as-normal-path —
  that is HDP's entire premise

### Option 3: Unranked Value List

Flat list without hierarchy.

**Bad**:

- "resilience" and "leverage" will eventually conflict with "provenance"
  (e.g., a retry that would duplicate an audit event); a flat list provides
  no tiebreaker, so none of the values constrain behavior

## Decision

**Chosen option**: Option 1. An LLM-native health platform needs principles
that resolve conflicts, name the AI-specific boundaries (authorship,
calibration, recoverability), and fit in working memory. The inner ring
(Provenance, Judgment, Consent) is the platform's reason to exist — those
three are the governance layer. Resilience is how it must be built to be
worth deploying. Leverage is how it stays shippable.

## Consequences

### Positive

- The platform primitives become explicit values: audit/provenance serve P1,
  HITL serves P2, consent/identity serve P3 — the package list and the value
  system are the same shape
- New ADRs gain a Decision Drivers vocabulary; proposals that serve no
  principle are flagged as possibly unnecessary
- Engineering agents inherit the same constitution as the runtime agent —
  one hierarchy governs both the product's behavior and its construction

### Negative

- Consolidation loses granularity — interoperability lives inside P5 and
  auditability inside P1 rather than headlining. Mitigated by explicit
  sub-bullets
- Principles can ossify. Revisit at stress-test milestones: first deployment
  touching real PHI, first additional vertical, first external contributor,
  first production computer-use integration
- Risk of principles becoming performative rather than generative — the "For
  New ADRs" rule exists to force contact between principles and decisions

### Neutral

- No existing decision changes. Current architecture (audit, consent,
  provenance, HITL, outbox) already aligns; the value is making alignment
  explicit and rankable for future decisions.

## Related

- `specs/package-trim/` — application of P5 Leverage
- `research/consent-model.md` — application of P3 Consent
- `research/computer-use-emr-sync/` — application of P4 Resilience

### Research Sources

- Anthropic: [Core Views on AI Safety](https://www.anthropic.com/research/core-views-on-ai-safety),
  [Responsible Scaling Policy](https://www.anthropic.com/news/anthropics-responsible-scaling-policy)
- Google: [Site Reliability Engineering](https://sre.google/sre-book/table-of-contents/)
- Basecamp: [Shape Up](https://basecamp.com/shapeup)
- Regulatory: [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html),
  [42 CFR Part 2](https://www.ecfr.gov/current/title-42/chapter-I/subchapter-A/part-2),
  [FDA 21st Century Cures Act §3060](https://www.fda.gov/regulatory-information/selected-amendments-fdc-act/21st-century-cures-act),
  [CMS Home Health PPS / PDGM](https://www.cms.gov/medicare/payment/prospective-payment-systems/home-health),
  [ONC interoperability](https://www.healthit.gov/topic/interoperability)
- Distributed systems: [Helland, "Idempotence Is Not a Medical Condition"](https://queue.acm.org/detail.cfm?id=2187821)
