# S-006: HDP current source and committed design corpus

Source: health-data main and vault Git revisions
Tools: native Read and Git
Query: not applicable
Worker: primary
Invocation route: primary
Revision: main@f7ab653339b4398b3fe6c833833659e3be6ccc41; vault@e8e9c4ab688cf18d0350151ab2545a4b738ff3c1
Evidence goal: Audit reusable primitives, implementation depth, and conflicting FHIR positioning.
Rationale: Project source is authoritative for what HDP is and can currently support.
Captured: 2026-08-05
Byte verification: verified
Verified by: reviewer at 2026-08-05T15:21:45Z
Verification method: Independent reviewer compared the exact committed source lines with the persisted capture lines; primary Git reads independently reproduced all three SHA-256 pairs.
Normalization: none
Citation verification:
- Source locator: main@f7ab653:README.md
  Source span: line 18
  Capture span: line 87
  Source span SHA-256: c63472299ac81103e6dec7475492e818d2cce6530371c24e28eb6deb764ecbc4
  Capture span SHA-256: c63472299ac81103e6dec7475492e818d2cce6530371c24e28eb6deb764ecbc4
- Source locator: main@f7ab653:packages/hdp-canonical/README.md
  Source span: line 7
  Capture span: line 91
  Source span SHA-256: 1b11e653a068cb9f202f356e052698621bfaf2c9ca3b654435e981b48f671703
  Capture span SHA-256: 1b11e653a068cb9f202f356e052698621bfaf2c9ca3b654435e981b48f671703
- Source locator: vault@e8e9c4ab688cf18d0350151ab2545a4b738ff3c1:research/fhir-surface.md
  Source span: line 18
  Capture span: line 95
  Source span SHA-256: 2d6755a4ff7c4e1ac16339f38698b75e949b99864bd7c626a64a5e4d309b6196
  Capture span SHA-256: 2d6755a4ff7c4e1ac16339f38698b75e949b99864bd7c626a64a5e4d309b6196
Outcome: gathered

## Evidence

### Current authority

Main positions HDP as an AI-native workflow and governance layer, not a FHIR
clinical data repository. It says HDP should pair with a CDR such as Medplum or
HAPI and treat FHIR as an edge projection. It also labels the repository a
reference architecture under active development, uses synthetic fixtures, and
processes no real patient data.

The intended reusable primitives are canonical records, consent, provenance,
audit, identity, ingest, an agent runtime, a review state machine, and resilient
EMR write-back.

### Implementation depth

The relevant packages do not yet implement those primitives:

- `hdp-canonical`, `hdp-audit`, `hdp-provenance`, `hdp-identity`,
  `hdp-consent`, `hdp-agent`, `hdp-ingest`, `hdp-outbox`, and `hdp-api` expose
  only package docstrings and version constants in their cited source modules.
- Package READMEs contain TODOs for the described models, tables, adapters, or
  interfaces.
- Smoke tests assert only `True` and explicitly say real behavior will replace
  them.
- `hdp-canonical` and `hdp-audit` are labeled `DEEP` despite the TODO-only
  implementation. Those depth labels are not reliable evidence of behavior.

HDP is therefore a design and research authority today, not a working
prior-authorization platform or implemented governance spine.

### Positioning conflict

Committed vault research says to build and own the FHIR compliance surface and
reject HAPI, Medplum, and managed services. Current main says the opposite: pair
with a CDR and avoid competing with one. The current main position is the newer
product authority and aligns with HDP's guiding principle to leverage the
ecosystem rather than recreate it.

### Reusable research

- Billing research maps identity, adapters, consent, documents, raw/canonical
  separation, trust, agent identity, provenance, outbox, and semantic search to
  claims and denials. Its “9 of 10” reuse score is a design assertion, not
  implementation evidence.
- The committed computer-use study supports deterministic Playwright plus
  durable orchestration and treats browser automation as a last-resort transport
  with idempotency, verification, checkpoints, and human gates. That can become
  a later legacy-channel adapter but should not define the first CMS-era core.

## Verified Excerpt

```text
HDP is **not** a FHIR clinical data repository, and doesn't compete with one.
```

```text
TODO: Implement base FHIR R4 model bindings (Patient, Observation, Encounter).
```

```text
**Build the FHIR compliance surface. Own it. No sidecar, no managed service, no embedded third-party server.**
```

## Notes

The cheapest coherent strategic change is not a platform rewrite. It is to make
one prior-authorization vertical implement the promised governance primitives
deeply, while keeping FHIR servers, EHR certification, and browser transports
behind explicit interfaces.

## Followups

- Correct or remove misleading package depth labels when implementation begins.
- Treat older “own the FHIR server” research as superseded if the final decision
  accepts the current pair-with-CDR boundary.
