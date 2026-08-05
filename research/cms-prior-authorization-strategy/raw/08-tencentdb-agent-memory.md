# S-008: TencentDB Agent Memory

Source: https://github.com/TencentCloud/TencentDB-Agent-Memory/tree/3c6fc6425f22d24c4917dc3b7791a175d2d13545
Tools: WebFetch
Query: not applicable
Worker: research-worker-terra
Invocation route: task
Revision: 3c6fc6425f22d24c4917dc3b7791a175d2d13545
Evidence goal: Determine whether the memory system fits an authoritative PHI runtime or only bounded agent/developer use.
Rationale: Conversational memory must not be confused with authoritative health records.
Captured: 2026-08-05
Byte verification: verified
Verified by: openai/gpt-5.6-sol primary at 2026-08-05T14:43:00Z
Verification method: Reopened the approved exact revision through raw GitHub URLs for README, package metadata, license, changelog, plugin config, gateway, core, capture, recall, and storage modules.
Normalization: none
Citation verification:
- Source locator: exact revision README.md, OpenClaw quick start
  Source span: exact sentence beginning `Once enabled` and ending `the next turn.`
  Capture span: line 49
  Source span SHA-256: da42eece721c8ab6ff1a0b8fd0b3c9f4815d62f9440703a389e1f4ad0e08b582
  Capture span SHA-256: da42eece721c8ab6ff1a0b8fd0b3c9f4815d62f9440703a389e1f4ad0e08b582
Outcome: gathered

## Evidence

- TencentDB Agent Memory 0.3.6 is a Node/OpenClaw plugin with optional Hermes
  integration. Its semantic pyramid is raw conversation, extracted atom,
  scenario, and persona.
- Automatic conversation capture, background extraction, and recall are enabled
  by default. Default retention and recall-character limits are unbounded when
  configured as zero.
- Local SQLite and sqlite-vec are the default storage. Remote vector, embedding,
  LLM, and context-offload services can be configured.
- Gateway authentication is optional and disabled by default. Non-loopback
  exposure without an API key emits warnings but remains possible.
- The inspected Hermes gateway does not propagate caller `user_id` into core
  identity scoping; a constant default user appears in recall, and inspected
  search/storage paths are session-oriented rather than tenant/patient/role
  authorization boundaries.
- Failure handling favors agent continuity: initialization and vector failures
  can degrade to no-op or empty results, recall timeouts skip injection, and
  background embedding is fire-and-forget.
- The changelog documents recent data-loss, partial-write, isolation, and gateway
  security fixes. The MIT license permits use but provides no assurance.

## Verified Excerpt

```text
Once enabled, TencentDB Agent Memory automatically handles conversation capture, memory extraction, scene aggregation, persona generation, and recall before the next turn.
```

## Notes

This is conversational agent memory, not a clinical or authorization record. Its
fail-soft semantics are appropriate for optional prompt context but incompatible
with authoritative case state, audit, evidence custody, or patient/tenant access
control without a substantial surrounding system.

It should not be an HDP runtime core and should never receive PHI in the proposed
OSS project. It may be used as developer memory with public or synthetic content,
or studied as a reference for layered recall and human-readable drill-down.

## Followups

- None for the first OSS primitive. Reconsider only for non-authoritative,
  synthetic developer workflows with explicit isolation and retention limits.
