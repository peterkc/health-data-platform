# S-007: Semantica

Source: https://github.com/semantica-agi/semantica/tree/86f115d2003ff1696fae5816ca698576e850b51e
Tools: WebFetch
Query: not applicable
Worker: research-worker-terra
Invocation route: task
Revision: 86f115d2003ff1696fae5816ca698576e850b51e
Evidence goal: Determine Semantica's shipped capabilities, maturity, storage, and overlap with HDP.
Rationale: Semantica is the strongest candidate for an evidence and reasoning sidecar.
Captured: 2026-08-05
Byte verification: verified
Verified by: openai/gpt-5.6-sol primary at 2026-08-05T14:43:00Z
Verification method: Reopened the approved exact revision through raw GitHub URLs for README, package metadata, license, changelog, context, policy, temporal, and provenance modules.
Normalization: none
Citation verification:
- Source locator: exact revision CHANGELOG.md, Unreleased PROV-O trust blockers
  Source span: exact text beginning with the pipeline file path and ending `has never worked`
  Capture span: line 48
  Source span SHA-256: 3940babe7352d16d5030f480e1368200d27cf7322667972b4e6cc3bb0d61df0d
  Capture span SHA-256: 3940babe7352d16d5030f480e1368200d27cf7322667972b4e6cc3bb0d61df0d
Outcome: gathered

## Evidence

- Semantica describes itself as a deterministic context and accountability layer
  that complements rather than replaces LLMs, vector stores, and agent
  frameworks.
- Source implements in-memory context graphs, first-class decision records,
  policy objects, valid-time and transaction-time models, temporal queries, and
  provenance with W3C PROV-O export.
- Provenance defaults to in-memory storage unless a persistent path/default is
  explicitly configured; SQLite is available and includes transaction and
  checksum support.
- The policy evaluator is generic and bounded. It is not evidence of a complete
  medical-necessity or payer-policy engine.
- Version 0.6.0 declares `Production/Stable` and MIT licensing, but carries a
  large core dependency set including Torch, Transformers, spaCy, FAISS,
  RDFLib, NetworkX, Pandas, and OpenCV.
- The pinned unreleased changelog says `PipelineWithProvenance` has never worked
  and several provenance wrapper dependencies are missing or incomplete. README
  separately warns that its simple Rete matcher should be validated before
  production compliance use.

## Verified Excerpt

```text
`semantica/pipeline/pipeline_provenance.py` imports a nonexistent module and wraps a `Pipeline` dataclass with no `run()` method, so `PipelineWithProvenance` has never worked
```

## Notes

Semantica validates the usefulness of temporal facts, decision records,
provenance, conflict detection, and graph-backed explanations. It does not yet
justify becoming HDP's authoritative core. Its maturity contradictions, broad
dependencies, volatile defaults, and generic policy semantics would make the
first OSS vertical harder to audit and easier to overclaim.

The safe boundary is an optional adapter or later sidecar after HDP defines and
tests its own narrow authorization evidence model. Semantica can remain a
reference for graph and PROV-O concepts without controlling the record of truth.

## Followups

- If later evaluated as a dependency, run a bounded spike against one evidence
  timeline with persistent storage, failure injection, tenant isolation, and
  exact provenance export tests.
