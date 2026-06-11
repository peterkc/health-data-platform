# Decision Log — How These Designs Were Made

**Status**: Living — append after each design session
**Purpose**: Show the collaborative process behind each locked decision. Each entry captures what the human asked, what Claude proposed, where Claude was wrong or incomplete, and what the human corrected. This is evidence, not methodology — [AI-WORKFLOW.md](../AI-WORKFLOW.md) describes the method; this file shows it in action.
**Audience**: Anyone asking "how much of this was AI-generated?" The answer: Claude drafted, the human steered. Every significant direction change in this hub traces to a human prompt.
**Companion to**: [AI-WORKFLOW.md](../AI-WORKFLOW.md) (methodology), [JOURNAL.md](../JOURNAL.md) (session log), [TRACEABILITY.md](../TRACEABILITY.md) (decision → artifact map), [decisions.md](decisions.md) (locked outcomes)

## How to read this file

Each entry follows: **Human intent** → **Claude's initial framing** → **What changed** → **Final outcome**. Entries are curated for moments where human judgment altered the direction — routine confirmations ("yes, lock") are omitted. The transcript is the full record; this file is the highlight reel of collaborative reasoning.

## What makes this different from vibe coding

Vibe coding: human describes what they want → AI generates → human accepts or retries.

This research process: human sets direction, challenges assumptions, applies domain principles, catches framing errors, and makes trade-off calls Claude cannot make. Claude's role is evidence gathering, option analysis, and prose drafting. The human's role is judgment.

The entries below are ordered by theme, not chronology.

______________________________________________________________________

## Guiding Principles (P1-P5)

### "Audience is a storyteller" — principle naming

**Human**: "Guide that the audience is a storyteller, step back and look at P1-P5. Are these the principles they would choose? Are they worded correctly, how they would state them?"

**Claude proposed**: Multi-sentence taglines for each principle with explanatory subtext.

**Human corrected**: "Good direction, still not keep on the tag lines. Maybe we don't decide on the tag lines now. But just category names, i.e. 'data sovereignty'." Then later: "Not sold on the narrative example, but the single-word names are good."

**Outcome**: Privacy. Judgment. Trust. Ownership. Focus. — five single-word names that work for humans reading docs AND for Claude reading ADRs as behavioral constraints. The taglines were deferred.

**Why it matters**: Claude optimized for descriptiveness. The human optimized for memorability and audience (storyteller vs. agent). Single words won on both axes.

### "What does our core principle say?" — principle-anchored decisions

**Human** (on unit conversion strategy): "Before we decide, what does our core principle say? What about compliance and liability? We do not want to be wrong about conversions."

**Claude's initial framing**: Presented options as technical trade-offs (precision, storage, API complexity).

**What changed**: The human reframed every decision through P1-P5. This became the pattern for the entire hub — every section in data-plane.md now cites which principle(s) it serves. Unciteable choices trigger the P5 question: "do we actually need this?"

**Outcome**: ADR-2010 stores source units, converts at display. data-plane.md §1-7 all principle-anchored. The phrase "P1 wins" appears throughout as a decision shortcut.

______________________________________________________________________

## Single Table → Split (D7)

### "What if we have too many tables?"

**Human**: "1. What are the purpose-build tables? 2. Should we provide examples now? 3. Do we have enough to determine the tables? 4. What happens when we have too many tables? Can we do something similar to how health_records are stored?"

**Claude's initial framing**: Proposed splitting health_records into FHIR-aligned tables immediately.

**Human pushed back**: The concern wasn't about FHIR alignment — it was about table proliferation and operational complexity. "Too many tables" is a real operations cost.

**What changed**: Claude composed 15 public schemas (FHIR, OMOP, openEHR, Fasten, i2b2) into a coverage matrix showing that every production system separates conditions from observations. Only i2b2 unifies — and i2b2 serves a different workload (federated analytics). The evidence convinced because it covered 15 schemas across five paradigms, not because the AI said so.

**Outcome**: D7 — hybrid split. 6 FHIR-aligned silver tables, with ref_record_type_schemas (D7.1) as the extensibility contract. data-type-catalog.md holds the 15-schema evidence.

______________________________________________________________________

## Authorization Cache (D24)

### "Which aligns with P1?" — exposing a flawed option set

**Human**: Asked about TTL split options for the PDP cache. "1. Not sure, which one aligns closest with P1 from the 5 guiding principles? 2. How do other systems handle similar use cases?"

**Claude's initial framing**: Presented three options (A: uniform 60s, B: asymmetric permits-short/denies-long, C: asymmetric permits-long/denies-short). All three kept permits at 60s.

**What changed**: The human's P1 question exposed the flaw. None of the options addressed the actual P1 risk: stale *permits* (granting access after revocation). Claude then searched industry precedents — Zanzibar, Kubernetes, AWS IAM, Azure RBAC — and found that none split TTL by decision type. Every system uses uniform TTL + out-of-band invalidation.

**Outcome**: D24 — uniform 60s TTL + consistency tokens (OpenFGA-native, Zanzibar zookie pattern) phased post-MVP. The human's principle-first question caught a framing error that three technically-valid options all shared.

### "The 10K default is adjustable?"

**Human**: "The 10K default is adjustable? We are just assuming at the moment without evidence?"

**Claude's framing**: Had proposed 10k entries as a default.

**What changed**: Honest answer — yes, 10k was an educated guess based on typical worker memory budgets, not measured data. The human's challenge forced the measure-first posture into the decision: "bump to 50k before Tier 2; hit-rate + memory metrics emitted."

**Outcome**: D24 includes explicit language about configurable sizing via env var and measurement-before-scaling. No magic numbers without escape hatches.

______________________________________________________________________

## Database Substrate (Postgres recommendation)

### "We haven't implemented anything yet" — greenfield reframe

**Human**: "Challenge: We haven't implemented anything yet. So moving to postgres isn't any issue. This is a research hub that will be used to implement M3."

**Claude's initial framing**: Discussed Dolt → Postgres as a "migration" with effort estimates of 3-10 days.

**What changed**: The human pointed out there's nothing to migrate. No DDL exists. No data exists. The entire framing was wrong — this isn't a migration decision, it's a greenfield technology choice. The effort estimate dropped from "3-10 days migration tax" to "3-5 days of M3 work."

**Outcome**: database-substrate.md frames the choice as greenfield, not migration. Effort table shows 3-5 days total for audit infrastructure, not migration overhead.

### "Can that be mitigated at Postgres?" — trigger-based audit

**Human**: "Dolt's native versioning provides audibility. Can that be mitigated at Postgres. What solutions are available to get something similar?"

**Claude proposed**: Application-level audit logging (Repository writes to audit tables).

**Human pushed deeper**: "Can low level changes be done using db triggers/functions?"

**What changed**: The trigger-based approach is stronger than Dolt's opt-in DOLT_COMMIT(). Triggers fire on every INSERT/UPDATE/DELETE regardless of caller — raw SQL, ORM, admin fix. No code path can bypass audit without explicitly disabling triggers (which pgAudit logs). Dolt's audit requires explicitly calling DOLT_COMMIT() after each change — skip the call, skip the audit.

**Outcome**: database-substrate.md §"Trigger-level enforcement" — this became a selling point, not a concession. The human's question about "mitigation" led to discovering Postgres audit is *better* than what it replaces.

### "Why 3-10 days? How did you determine that estimation?"

**Human challenged effort estimates directly.**

**Claude's initial response**: Had given a range without breaking it down.

**What changed**: Forced decomposition revealed the work: audit tables (0.5 days), temporal triggers (0.5-1 day), pgvector (0.5 days), pgAudit (0.5 days), Repository integration (0.5 days), testing (1-2 days). The honest total was 3-5 days, not 8-10. The upper range had been inflated by unstated migration assumptions that the greenfield reframe already eliminated.

**Outcome**: database-substrate.md effort table with per-component estimates. No black-box estimates.

______________________________________________________________________

## Repository Design (§1)

### "Two methods vs one — not sure, let's discuss"

**Human**: "1. Two methods vs one - not sure, lets discuss 2. patient_id, recommendations? 3. GrantContext shape, provide the minimal but configurable? Any risk of exposing too much? 4. Not sure, best options? Trade-offs?"

**Claude's initial framing**: Presented read_one vs read_many as a binary choice.

**What changed**: The discussion wasn't about one-vs-two methods. It was about API shape: should the caller specify what they want precisely (type-safe, narrow) or flexibly (one-method, filters)? The human's "not sure, let's discuss" was an invitation to explore, not a request for a recommendation.

**Outcome**: D1.1 — two methods (read_one for single-record, read_many for collections). Frozen 4-field GrantContext (actor_id, actor_kind, purpose, on_behalf_of). Minimal surface, no exposed internals.

### "For delete, is it a soft delete?"

**Human**: "1. for delete, is it a soft delete? 2. Option C"

**Claude had not addressed deletion semantics** in the write interface sketch.

**What changed**: The human caught an omission. Every HIPAA-governed system needs soft delete with audit trail (right-to-delete requires proof of deletion). This connected to D3 (content-addressed documents with reference counting) and D20 (cascade to derived data).

**Outcome**: Repository.write() includes separate delete() method, soft-delete with deleted_at timestamp, D20 cascade marking on derived data. The human's one-line question filled a gap Claude's initial design missed entirely.

______________________________________________________________________

## Data-Plane Timeline (§2)

### "Alternative to MVP, trade-offs?" — challenging the recommendation

**Human**: Questioned the recommended timeline approach for §2.

**Claude had recommended**: Application-level fan-out for timeline queries.

**Human asked for alternatives**: confirm dolt server support against docs, community threads, and a local audit of the Dolt codebase.

**What changed**: Claude audited the actual Dolt codebase (local clone) and confirmed VIEW support for UNION ALL across tables. This enabled UNION VIEW as the timeline strategy — a database-level solution instead of application-level fan-out.

**Outcome**: §2 uses UNION VIEW for patient timeline, confirmed by codebase audit. The human insisted on verification before locking, which caught that the better option was available.

______________________________________________________________________

## Ingest Pipeline (§5)

### "Why defer?" — challenging FHIR Subscription

**Human**: "Why defer, trade-offs?" (about deferring FHIR Subscription to post-MVP)

**Claude's initial recommendation**: Defer FHIR Subscription, pull-only at MVP.

**Human challenged**: "What is the effort for subscription support?"

**What changed**: Claude estimated 1 week for FHIR Subscription implementation (HAPI FHIR is open-source, handles R4 Subscription, Synthea provides synthetic data for testing). The human's challenge revealed the deferral was premature — the effort was manageable and the capability was architecturally significant (real-time ingest, not just batch pull).

**Outcome**: §5 includes FHIR Subscription at MVP (HAPI + Synthea for local testing). The human caught an over-conservative recommendation.

______________________________________________________________________


## Hub Standards

### "Being consistent is important for review"

**Human**: "Prefer C, being consistent is important for review" (on whether to standardize hub file headers)

**Claude had presented three options**: (A) leave as-is, (B) standardize a few key files, (C) standardize all 16.

**What changed**: The human chose the most work but the most value for reviewers. Consistency across 16 files means any reviewer can navigate any file with the same mental model. Claude dispatched parallel agents to standardize all 16 files with the same header format (Status / Purpose / Audience / Companion to / How to read).

**Outcome**: All hub files follow the same header convention. The human's preference for consistency over convenience shaped the entire hub's review experience.

______________________________________________________________________

## Platform Strategy

### "Is the OS/Platform for EHR applicable beyond longevity?"

**Human**: "All good options. Step back, what do we know about what is being built? Is the OS/Platform for EHR applicable beyond longevity? Do we know what that looks like?"

**Claude's initial framing**: Had been focused on longevity/concierge health as the only vertical.

**What changed**: The human's question triggered platform-malleability.md — the 60/40 platform-vs-vertical analysis, pivot catalog, positioning tiers (PHR → Health CMS → Health OS), and the external positioning framing. This reframed the entire architecture conversation from "health app" to "health operating system with vertical optionality."

**Outcome**: platform-malleability.md is one of the most strategically important files in the hub. It exists because the human stepped back from implementation details and asked a positioning question Claude wasn't going to ask on its own.

### "Don't update journal, this is internal knowledge only"

**Human**: Early in the project, corrected Claude's instinct to put competitive analysis and strategic thinking into tracked files.

**What changed**: Created the `internal/` directory convention. Rate negotiations, competitive positioning, strategic notes — all gitignored. Work product (ADRs, research, code) is shared. Working context (strategy, competitive thinking, drafts) is private.

**Outcome**: Workspace visibility tiers (Shared / Private / Ephemeral) that now apply across all projects. The human's instinct about information boundaries became an architectural pattern.

______________________________________________________________________

## Meta-observations

**Pattern: Human asks "why" → Claude discovers its own assumption was wrong.** The OQ-7.2 TTL split, the Dolt-to-Postgres "migration" framing, the FHIR Subscription deferral — each time, the human's question wasn't asking for information. It was challenging a framing that Claude had adopted uncritically.

**Pattern: Human anchors on principles → decisions become consistent.** "What does P1 say?" was asked so consistently that it became the default reasoning frame. Every §2-7 section cites principles. This consistency didn't come from Claude — it came from the human establishing the pattern and enforcing it.

**Pattern: Human catches tone, not just content.** "You're right sounds too much like Claude." "Is this too long?" "Being consistent is important for review." These aren't content decisions — they're audience-awareness decisions that Claude systematically underweights.

**Pattern: "Discuss first" before drafting.** Multiple times the human said "discuss first" or "let's discuss" before any writing. The Postgres evaluation, the FHIR Subscription challenge, the billing vertical — all started as conversations, not drafts. The human treated Claude as a thinking partner, not a writing tool.

## Related

- [AI-WORKFLOW.md](../AI-WORKFLOW.md) — methodology description (this file is the evidence)
- [JOURNAL.md](../JOURNAL.md) — per-session log of what happened
- [TRACEABILITY.md](../TRACEABILITY.md) — decision → ADR → artifact → commit mapping
- [decisions.md](decisions.md) — locked outcomes (this file shows how they got locked)
