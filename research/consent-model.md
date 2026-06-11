# Consent Model — access_grants + 42 CFR Part 2

**Status**: Locked (2026-04-14) — adds `sources` JSON for per-source consent (Health OS requirement)
**Purpose**: Define the two-layer authorization model (RBAC + consent) with DDL for `access_grants`, sensitive category rules, and 42 CFR Part 2 fail-closed behavior.
**Audience**: Engineers implementing consent logic or PDP integration; compliance reviewers checking 42 CFR Part 2 coverage.
**Companion to**: [identity-model.md](identity-model.md) (persons that grants FK to), [data-plane.md](data-plane.md) (PDP/PEP runtime that evaluates grants), [decisions.md](decisions.md) (D9, D10, D20-D25)
**Source**: ADR-2006 (Two-Layer Authorization)

## How to read this file

- "Architecture" section explains the two-layer AND gate (RBAC + consent)
- "Sensitive Categories" table lists 42 CFR Part 2 categories and their default exclusion behavior
- "Purpose enum" section defines grant intents that drive both PDP evaluation and API response shape (D21)
- DDL section has the full `CREATE TABLE` for `access_grants`

## Architecture (from ADR-2006)

Two-layer AND gate:

1. **RBAC** (Layer 1): JWT permissions claim → role-based capabilities
1. **Consent** (Layer 2): access_grants table → patient-controlled data access

Both layers must pass. A role permits the action type; a grant permits the data scope.

## Sensitive Categories (42 CFR Part 2)

Categories that require explicit opt-in consent:

| Category            | Regulation      | Default  |
| ------------------- | --------------- | -------- |
| Substance use       | 42 CFR Part 2   | Excluded |
| Mental health       | State laws vary | Excluded |
| Reproductive health | State laws vary | Excluded |
| Genetic/genomic     | GINA            | Excluded |
| HIV/STI             | State laws vary | Excluded |

`categories: NULL` in a grant covers all non-sensitive data. Sensitive categories
must be explicitly listed to be included.

### 42 CFR Part 2 strict fail-closed override (D23)

Records marked with sensitive categories (substance use, mental health, reproductive health, genetic/genomic, HIV/STI) **opt out of graceful degradation during OpenFGA outage**. Other record types fall through to Tier 1 LRU cache during outage (per D23); 42 CFR Part 2 records always route through the full PDP evaluation path and return 503 Service Unavailable when the PDP is unreachable.

Rationale: 42 CFR Part 2 imposes stricter consent requirements than general HIPAA. A cached stale permit that would be tolerable for a routine lab result is not tolerable for substance use treatment records. Strict-fail-closed for these categories is a P1 + P3 compliance choice, not a performance trade-off.

Mechanically: the Repository inspects the record's `sensitive_category` before consulting the Tier 1 LRU cache. Sensitive records bypass the cache regardless of PDP availability.

## Purpose enum (D9 + D21)

`access_grants.purpose` discriminates the intent of the grant. The enum determines both PDP evaluation semantics and Data API response shape (per D21 audience-split).

| Purpose            | Who grants to whom                                                                    | Response on denial                    | Patient-facing? |
| ------------------ | ------------------------------------------------------------------------------------- | ------------------------------------- | --------------- |
| `care`             | Patient → practitioner for treatment                                                  | `NotFound`                            | No              |
| `operations`       | Patient → org for billing, QI, care coordination                                      | `NotFound`                            | No              |
| `research`         | Patient → research study (often de-identified downstream)                             | `NotFound`                            | No              |
| `payer`            | Patient → insurance claims processing                                                 | `NotFound`                            | No              |
| `public_health`    | Patient → authority for reportable conditions                                         | `NotFound`                            | No              |
| `patient_delegate` | Patient → trusted delegate (spouse, guardian, advocate, coach) reading AS the patient | `PermissionDenied` with grant context | **Yes**         |

**Important**: `patient_delegate` is what distinguishes "my spouse reads for me" (patient-facing, transparency owed per GDPR Art 15 + HIPAA §164.524) from "my physician reads" (practitioner-facing, info-leak protection). The grant creation UX must treat these as different mental models and route the patient through a distinct flow for delegate grants.

Emergency access is **never** `patient_delegate` — break-glass is always `care` purpose (practitioner-scope) even under emergency conditions. This prevents a break-glass response revealing "this record exists but requires emergency override" (an info leak).

## Table Design (from ADR-2006)

```sql
CREATE TABLE IF NOT EXISTS access_grants (
    id              VARCHAR(36) NOT NULL PRIMARY KEY,
    patient_id      VARCHAR(36) NOT NULL,
    grantee_id      VARCHAR(36) NOT NULL,
    grantee_type    VARCHAR(30) NOT NULL,
    scope           VARCHAR(100) NOT NULL,
    categories      JSON NULL,
    hom_nodes       JSON NULL,
    sources         JSON NULL,  -- source_system list; NULL = all sources
    granted_at      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    expires_at      DATETIME(3) NULL,
    revoked_at      DATETIME(3) NULL,
    granted_by      VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    KEY idx_patient (patient_id),
    KEY idx_grantee (grantee_id, grantee_type),
    KEY idx_active (patient_id, grantee_id, revoked_at)
)
```

### Key Fields

| Field          | Purpose                    | Example                                                 |
| -------------- | -------------------------- | ------------------------------------------------------- |
| `grantee_id`   | Who gets access            | practitioner person_id, app client_id, agent session_id |
| `grantee_type` | Type of grantee            | `practitioner`, `app`, `agent`                          |
| `scope`        | SMART on FHIR scope        | `patient/Observation.read`                              |
| `categories`   | Data categories included   | `["labs", "vitals"]` or NULL (all non-sensitive)        |
| `hom_nodes`    | HOM nodes included         | `["cardiovascular"]` or NULL (all)                      |
| `sources`      | Source systems included    | `["quest", "oura"]` or NULL (all sources)               |
| `revoked_at`   | Soft delete for revocation | NULL = active, timestamp = revoked                      |

### Why `sources` matters (Health OS)

Health OS aggregates from N sources. A patient may want to share lab data with Dr. X but
NOT their wearable data. Consent filters must support source-level inclusion/exclusion.
Adding `sources` JSON now is trivially additive; retrofitting at Series A would be painful
since every grant would need backfill interpretation.

Query pattern including source filter:

```sql
SELECT id FROM access_grants
WHERE patient_id = ?
  AND grantee_id = ?
  AND revoked_at IS NULL
  AND (expires_at IS NULL OR expires_at > NOW())
  AND (categories IS NULL OR JSON_CONTAINS(categories, '"labs"'))
  AND (sources IS NULL OR JSON_CONTAINS(sources, '"quest"'))
```

### Query Pattern (authorization check)

```sql
-- Does grantee X have access to patient Y's labs?
SELECT id FROM access_grants
WHERE patient_id = ?
  AND grantee_id = ?
  AND revoked_at IS NULL
  AND (expires_at IS NULL OR expires_at > NOW())
  AND (categories IS NULL OR JSON_CONTAINS(categories, '"labs"'))
```

## Resolved Questions

- **grantee_id FK policy** (was D1): `grantee_id` is logically a persons.id reference
  for human grantees (practitioners). For non-human grantees (apps, AI agent sessions),
  `grantee_type` discriminates and `grantee_id` is an external string (client_id,
  session_id). No FK constraint — the discriminator handles type resolution.
- **HOM-node scoping**: The three-table JOIN for HOM grouping is query-side. Grant
  filter uses JSON_CONTAINS against `hom_nodes` — no extra JOIN. Performance is fine
  at MVP scale.

## Scoping pass pending

Phasing for consent-related additions (grant history, audit access log, de-ID pipeline,
jurisdiction filtering logic) is deferred to the single scoping pass after design is
complete. Each is designed as correct-by-construction in this file or in
`cross-schema-analysis.md` (CSA-3 covers grant_history; CSA-1 covers access_log). None
of them modify existing decisions — they add capability.

Scoping lands in `scoping.md` (to be created).

## AI Agent Parity

ADR-2006: "AI agents hold grants like practitioners. Same path, no backdoor."

```
POST /v1/agent/ask
  1. Validate agent session token → agent_id
  2. RBAC: agent role has observation:read → pass
  3. Consent: access_grants WHERE grantee_id = agent_id → scope
  4. Query: health_records filtered by grant scope
```

The agent never sees data the patient hasn't consented to share. This is the
key differentiator from competitors who give AI full chart access.

## Break-glass emergency access (D23 — phased, post-MVP)

Scheduled for post-MVP; recorded here so grant architecture anticipates it.

Break-glass is a workflow affordance for genuine clinical emergencies (ED consult, code blue, unresponsive patient). It is **independent of** OpenFGA outage behavior — break-glass operates identically whether the PDP is healthy or degraded.

Mechanism:

1. Practitioner self-asserts emergency with typed justification (free text, logged immutably)
1. Bypasses PDP via static emergency policy evaluated locally (no OpenFGA round-trip)
1. Every invocation writes `audit_log` row with `break_glass = true`, justification text, reviewer queue flag
1. Compliance team reviews all break-glass events within 48 hours
1. Patient notified post-hoc (HIPAA breach notification workflow if misused)

Anchored to:

- Microsoft Entra Conditional Access "break-glass accounts" (excluded from conditional access policies)
- HITRUST control 11.b.4 (emergency access with documented justification)
- Joint Commission standards for emergency clinical access

Modeled as a separate policy in `policy_rules` (D9 PAP) with heavy audit obligations; never as a bypass toggle on `access_grants`.
