# Open Questions — Unresolved Design Items

**Status**: Closed — all 22 questions resolved as of 2026-04-15. Retained as historical record.
**Purpose**: Tracked every unresolved schema question until resolution. Now shows how open items became locked decisions.
**Audience**: Engineers tracing why a decision exists; reviewers checking that nothing was skipped.
**Companion to**: [decisions.md](decisions.md) (where resolved items landed), [design-queue.md](design-queue.md) (CSA proposals that originated here), [design-lessons.md](design-lessons.md) (patterns extracted during resolution)

## How to read this file

- All items are resolved — scan the **Resolution** column for the decision ID (e.g., D14, D16)
- Three sections by speculation level: scoped opens (OQ-N), design queue opens (CSA-N), frontier questions (FQ-N)
- Follow decision IDs back to [decisions.md](decisions.md) for the locked answer and rationale

Three categories, in increasing speculation level:

1. **Scoped opens** — specific to one table / model, answer should emerge with more design
1. **Design queue opens** — CSA-N items with `Open question` status in [design-queue.md](design-queue.md)
1. **Frontier questions** — Health OS leads; no public schema has answers (FQ-N)

## 1. Scoped opens (table / model questions)

All resolved 2026-04-15. See [decisions.md](decisions.md).

| ID   | Question                                                     | Resolution                                                                                                                             |
| ---- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| OQ-1 | `patient_identifiers` scope — patient-level or person-level? | **Resolved (D16)** — promoted to `person_identifiers` (FK persons.id). Data Vault hub owns identity.                                   |
| OQ-2 | `default_hom_id` FK on `ref_organizations`                   | **Resolved (D17)** — `ref_hom_nodes` refactored to single surrogate PK; all FKs point to `id`. Forced by D10 `access_grant_hom_nodes`. |
| OQ-3 | `patient_preferences` conceptual FK (per-person vs per-org)  | **Resolved (D16)** — promoted to `person_preferences` (FK persons.id). Preferences belong to the person, not the patient role.         |

## 2. Design queue opens (CSA-N items)

All resolved 2026-04-15. See [decisions.md](decisions.md) D8–D15 and [design-queue.md](design-queue.md) iteration log.

| ID     | Summary                                                                 | Resolution         |
| ------ | ----------------------------------------------------------------------- | ------------------ |
| CSA-6  | `code_display` vs `code_text` semantics                                 | **Resolved (D14)** |
| CSA-7  | FHIR Composition pattern for multi-section documents                    | **Resolved (D15)** |
| CSA-9  | OMOP-aligned analytics schema                                           | **Resolved (D8)**  |
| CSA-10 | PDP / PEP separation in repository layer                                | **Resolved (D9)**  |
| CSA-11 | Multi-valued JSON index vs child tables on `access_grants` multi-values | **Resolved (D10)** |
| CSA-36 | `appointments` table — own scheduling vs ingest-only                    | **Resolved (D11)** |
| CSA-37 | `tasks` table — unified vs per-table state machines                     | **Resolved (D12)** |
| CSA-38 | `clinical_impression` — encounter narrative vs dedicated table          | **Resolved (D13)** |

## 3. Frontier questions (Health OS leads, no public answer)

All resolved 2026-04-15. Remaining as historical record of Health OS's frontier positioning.
See [design-lessons.md](design-lessons.md) for the "Health OS's frontier" framing.

| ID   | Question                                                                                                          | Resolution                                                                                                                                                                                                                                                                                           |
| ---- | ----------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FQ-1 | How do cross-org patient transfers preserve history while honoring org privacy boundaries?                        | **Answered structurally** — patient owns the record (PHR first principle); `access_grants.sources` filter + `documents.org_id` as provenance-not-access-control (D3) + PDP transitive eval (D9, D20). IHE XCA (CSA-42) is the wire protocol for legacy provider retrieval. No new decision required. |
| FQ-2 | How does AI agent identity work — ephemeral session token or persistent persons row with lifecycle?               | **Resolved (D18)** — persistent persons row + `agents` satellite + `agent_sessions` log. PDP evaluates agent through the same engine as humans.                                                                                                                                                      |
| FQ-3 | How is trust-level conflict resolved when two sources at same trust level disagree?                               | **Resolved (D19)** — silver keeps all rows; gold-tier reconciles via `ref_reconciliation_rules` with per-metric priority chain + fallback strategy; patient can override via `person_preferences`.                                                                                                   |
| FQ-4 | How do new HOM grouping schemes evolve (new ontology emerges, patients grandfathered)?                            | **Resolved (D17)** — `ref_hom_nodes` versioned (tree_version) + retirement semantics (retired_at + successor_node_id); `COALESCE(current, successor)` chain.                                                                                                                                         |
| FQ-5 | How does consent on derived data work (embedding of a health record — inherits record's consent, or independent)? | **Resolved (D20)** — derived data inherits source consent through PDP transitive evaluation; structural binding via `source_table` + `source_id`; cascade-delete on source FK for HIPAA + GDPR erasure.                                                                                              |

## 4. Data-plane opens (OQ-4 through OQ-22)

Surfaced 2026-04-15 during data-plane design pass (Repository.read() sketch in [data-plane.md](data-plane.md) §1.1).
OQ-4, OQ-5, OQ-6 resolved in same session into D21, D22, D23.
OQ-7 through OQ-10 resolved into D24-D27 (Tier 1 closed — Repository interface unblocked).
OQ-11 through OQ-22 resolved across data-plane.md §1-7 (all sections locked).

### Tier 1 — resolved this session

| ID   | Question                                                                         | Resolution                                                                                                                   |
| ---- | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| OQ-4 | What defines "patient-facing endpoint" (for NotFound vs PermissionDenied split)? | **Resolved (D21)** — hybrid actor_id + on_behalf_of + `active_grant.purpose == 'patient_delegate'`.                          |
| OQ-5 | Redis self-hosted or managed (PDP cache substrate)?                              | **Resolved (D22)** — neither. OpenFGA on Postgres as PDP + in-process LRU Tier 1; Valkey deferred until measured need.       |
| OQ-6 | What does Health OS do when PDP (OpenFGA) is unavailable?                        | **Resolved (D23)** — graceful degradation + signaling + circuit breaker + 42 CFR Part 2 carve-out; RLS + break-glass phased. |

### Tier 1 — resolved (D24-D27, unblocks Repository interface)

| ID    | Question                                                     | Resolution                                                                                                                           |
| ----- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| OQ-7  | Tier 1 LRU sizing + TTL actual values                        | **Resolved (D24)** — 10k entries/worker, uniform 60s TTL, action-aware key, cache both, TTL + bulk flush, consistency tokens phased. |
| OQ-8  | Batch PDP (OpenFGA BatchCheck) — partial-permit or fail-all? | **Resolved (D25)** — hybrid per-operation: partial-permit on collections, binary on single-resource + `filtered_count`.              |
| OQ-9  | First adapter format — FHIR R4 or R5?                        | **Resolved (D26)** — R4 first per ADR-2002; R5 additive when partner requires it.                                                    |
| OQ-10 | `ClinicalRecord` envelope versioning strategy                | **Resolved (D27)** — `metadata.envelope_version: 1`; Postel's Law for additive; adapters declare supported range.                    |

### Tier 2 + 3 — resolved (data-plane.md §1-7 complete)

| ID    | Question                                                                         | Resolution                                                                                                                                       |
| ----- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| OQ-11 | `grant_context` concrete shape                                                   | **Resolved (§1.1)** — 4-field frozen dataclass (actor_id, actor_kind, purpose, on_behalf_of). Additive-safe.                                     |
| OQ-12 | Agent on-behalf-of — whose `grant_context`?                                      | **Resolved (§1.1)** — Agent carries own actor_id + on_behalf_of field (D18 + D21 hybrid classifier).                                             |
| OQ-13 | One Repository vs per-resource-type                                              | **Resolved (§1.1)** — One Repository, resource_type as parameter (P5 Focus).                                                                     |
| OQ-14 | Transactional boundary for `Repository.write()`                                  | **Resolved (§1.2)** — write() auto-commits; write_batch() one transaction; unit of work deferred.                                                |
| OQ-15 | Sync vs async reads                                                              | **Resolved (§2.5)** — Sync at MVP. Async deferred until concrete use case.                                                                       |
| OQ-16 | D20 transitive eval — read-time vs write-time?                                   | **Resolved (§3.4)** — Read-time. P1 wins: revoked consent immediately blocks derived data.                                                       |
| OQ-17 | Opaque cursor format + HMAC signing                                              | **Resolved (§4.1)** — base64 + HMAC-SHA256. Carries access_decision_id for grant re-eval. 1h expiry.                                             |
| OQ-18 | Materialized view refresh cadence                                                | **Resolved (§3.1)** — Nightly scheduled for daily_summaries. Async worker upgrade when real-time needed.                                         |
| OQ-19 | Outbox worker topology (at-least-once vs exactly-once)                           | **Resolved (§6.2)** — Transactional outbox, polling worker, at-least-once. No message broker at MVP.                                             |
| OQ-20 | FHIR Subscription / push-out channels                                            | **Resolved (§5.3)** — Included at MVP. HAPI FHIR + Synthea for local testing. ~6-9 day subscription-specific delta.                              |
| OQ-21 | Rate limit / quota placement (Repository? PEP? Gateway?)                         | **Resolved (§7.4)** — Gateway (global) + PEP (actor-specific quotas). Repository stays pure data access.                                         |
| OQ-22 | Observability depth: what's logged where (access_log / app log / audit triggers) | **Resolved (§6.4)** — Three-layer, no overlap: access_log (audit), app log (ops), audit_batches + audit_changes via Postgres triggers (lineage). |

## How to resolve an open question

1. Discuss in session → reach alignment on answer
1. Move the entry:
   - If it's a locked decision → add to [decisions.md](decisions.md), remove here
   - If it becomes a formal proposal → promote to [design-queue.md](design-queue.md) as CSA-N
   - If it needs a separate ADR → note the ADR-NNNN link, remove here
1. Update the relevant design file with the rationale
