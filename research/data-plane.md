# Data Plane — Repository, Data API, Storage

**Status**: Active — design pass in progress (session 1 of N, started 2026-04-15)
**Purpose**: Design how application code reads, writes, and reasons about Health OS's 55+ tables. Every choice cites which of ADR-0001's five principles (P1 Privacy, P2 Judgment, P3 Trust, P4 Ownership, P5 Focus) it serves.
**Audience**: Engineers implementing the data layer; architects reviewing principle compliance; VCs asking "how does this scale without leaking data?"
**Companion to**: [table-designs.md](table-designs.md) (what), [decisions.md](decisions.md) (D-series), [design-queue.md](design-queue.md) (CSAs), [design-patterns.md](design-patterns.md) (vocabulary).

## Thesis

Three layers, strict separation, single entry point.

```
+------------------------------------------------------------+
|  Data API      (external contract)                         |
|    FHIR REST + timeline + export + HOM query               |  ← clients see this
+------------------------------------------------------------+
|  Data layer    (app-internal code)                         |
|    Repository → PDP → query composition                    |  ← enforcement lives here
+------------------------------------------------------------+
|  Data plane    (runtime + storage)                         |
|    PostgreSQL + PEP middleware + audit triggers            |  ← actual data traffic
+------------------------------------------------------------+
```

**One rule above all others**: the Data API is the only entry point. No application code, agent, or
internal service accesses storage directly. Every read and every write passes through a Repository
that invokes the PDP (D9). This is what converts compliance from hope to architecture.

## Five-principles anchor

Every design choice in this file must cite the principle(s) it serves. Unciteable choices trigger
the P5 question: "do we actually need this?"

| #   | Principle | Forces onto the data layer                                                                                                                                                   |
| --- | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P1  | Privacy   | PDP (D9) on every read + write; `access_log` write on every read; minimum-necessary = field selection + cursor pagination; CSA-47 export endpoint = interoperability right   |
| P2  | Judgment  | Liberal read surface, conservative write surface; D19 trust grading preserves source rows; D20 transitive consent marks derived data; D18 agent reads use same PDP as humans |
| P3  | Trust     | Encryption everywhere; audit middleware mandatory; FDA CDS exemption = `surface/summarize` tier ≠ `diagnose/prescribe` tier; international = multi-regime `policy_rules`     |
| P4  | Ownership | Repository IS the ownership boundary; audit triggers = write audit; middleware = read audit; CSA-45 outbox = guaranteed event publish; CSA-46 PROV-O = data lineage          |
| P5  | Focus     | MVP = FHIR REST + timeline + export + HOM query. Not GraphQL. Not federated query. One Repository interface, one PDP path, one audit middleware                              |

### Hierarchy in action

Inner ring (P1 P2 P3) constrains outer ring (P4 P5). When principles conflict, inner wins.

| Tension                                                                   | Resolution                                                                                      |
| ------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Fast timeline endpoint (P5) vs PDP on every row (P1)                      | **P1 wins** — keep PDP; optimize via materialized views + cached decisions, never by skipping   |
| Full audit log (P4) adds latency (P5)                                     | **P4 wins** — audit is architecture, not a toggle                                               |
| Liberal agent read (P2 calibration) vs HIPAA minimum-necessary (P1)       | **P1 wins** — "liberal" means "do not hide what the grant permits", not "bypass consent"        |
| International data residency (P3) vs one Repository (P5)                  | **P3 wins** — Repository must be jurisdiction-aware from day one (config, not schema migration) |
| Cursor-based pagination (P5 simple) vs re-evaluation on grant change (P1) | **P1 wins** — cursor carries `access_decision_id`; expired decisions force re-check             |

## How to read this file

1. **New to Health OS**: read the Thesis + Five-principles anchor above, then skim the Section index.
1. **Implementing a feature**: jump to the relevant section (e.g., "Writing a new silver-tier row" → Section 1.2 Repository.write).
1. **Reviewing a PR**: check that every new data-layer code path cites a principle. Uncited paths are P5 violations by default.
1. **Platform differentiation**: P1 + P4 together are the moat — PDP-enforced repository + full audit lineage is what "nobody else has, regulators require, and customers trust" means.

## Section index

Design arc across multiple sessions. Each section's status is one of: **Active** (current session), **Pending** (scheduled), **Locked** (decisions landed).

| #   | Section                                 | Status | Decides                                                                        |
| --- | --------------------------------------- | ------ | ------------------------------------------------------------------------------ |
| 1   | Repository interface                    | Locked | Read + Write signature, PDP call site, error envelope                          |
| 2   | Query composition patterns              | Locked | HOM fan-out, timeline UNION VIEW, export bundle, agent access                  |
| 3   | Materialized views + caching            | Locked | Nightly gold refresh, D24 is complete, read-time transitive eval               |
| 4   | Pagination + cursor                     | Locked | HMAC-signed opaque cursor, stable sort, grant re-eval trigger                  |
| 5   | Ingest patterns — batch vs realtime     | Locked | Hybrid pull/push, at-least-once + idempotent, FHIR Subscription at MVP         |
| 6   | Write patterns — transactions, outbox   | Locked | Transactional outbox (polling), D10 delete-reinsert, three-layer observability |
| 7   | Agent vs human parity at the data layer | Locked | Same PDP path, session_id audit, Gateway+PEP rate limiting                     |

## 1. Repository interface (Active)

Middle-out design: start at the Repository boundary because that is where P1 + P4 get enforced.
Top (Data API) and bottom (storage) become implementations of a decided contract.

> **Session 1 scope**: sketch `Repository.read()` and `Repository.write()` signatures, error envelope,
> and identify CSAs + D-series decisions that emerge. DDL-level changes come later.

*Content landing in subsequent turns this session.*

### 1.1 Repository.read()

Two methods — D25 locked different aggregation semantics for single-resource (binary permit/deny)
vs collection (partial-permit). Shared PDP evaluation in private `_evaluate_access()` helper.

**Signatures**:

```python
class Repository:

    def read_one(
        self,
        resource_type: ResourceType,   # D7 silver table enum
        resource_id: UUID,
        grant_context: GrantContext,
    ) -> ReadOneResult:
        """Single-resource fetch. Binary permit/deny (D25)."""

    def read_many(
        self,
        resource_type: ResourceType,
        patient_id: UUID,              # always required (P1 — no cross-patient at Repository level)
        grant_context: GrantContext,
        filters: ReadFilters | None = None,
        cursor: str | None = None,
        page_size: int = 50,           # default 50, max 200 (P1 minimum-necessary)
    ) -> ReadManyResult:
        """Collection fetch. Partial-permit (D25), paginated."""
```

**GrantContext** — minimal frozen input from PEP middleware (D9). Never serialized to client.

```python
@dataclass(frozen=True)
class GrantContext:
    actor_id: UUID          # persons.id — PDP subject, D24 cache key
    actor_kind: str         # 'person' | 'agent_session' — D21 classifier
    purpose: str            # access_grants.purpose value — D24 cache key
    on_behalf_of: UUID | None = None  # D18 agent delegation target
```

Four fields — minimum for D21 audience-split classifier, D24 cache key, D22 OpenFGA Check.
Extensible via optional fields (jurisdiction for P3, session_id for audit) — additive-safe,
same posture as D27 (Postel's Law). `frozen=True` prevents accidental privilege escalation
by mutation.

**ReadFilters** — per-resource-type scoping:

```python
@dataclass
class ReadFilters:
    date_from: datetime | None = None
    date_to: datetime | None = None
    code: str | None = None            # code value (LOINC, ICD-10, RxNorm)
    code_system: str | None = None     # code system qualifier
    status: str | None = None          # resource-specific status
    source_system: str | None = None   # filter by ingest source
    trust_min: int | None = None       # minimum trust_level (D19)
    hom_node_id: UUID | None = None    # HOM scope (D17, triggers cross-table in §2)
```

**Return shapes** — Repository returns DomainRecord (Health OS-native), not FHIR. Format adapter
lives at Data API edge (D26). ClinicalRecord envelope wrapping + `envelope_version` (D27) also
at API layer.

```python
@dataclass
class ReadOneResult:
    record: DomainRecord              # silver-tier row, Health OS-native shape
    access_decision: AccessDecision   # D23 degraded_mode + decision_source

@dataclass
class ReadManyResult:
    records: list[DomainRecord]       # permitted records only (D25 partial-permit)
    access_decision: AccessDecision   # aggregate decision metadata
    filtered_count: int | None        # D25 patient-facing transparency (HIPAA §164.524)
    cursor: str | None                # next page token, None if last page
    page_size: int                    # actual page size returned

@dataclass
class AccessDecision:
    decision_source: str              # 'pdp' | 'cache' | 'rls' (D23)
    degraded_mode: bool               # D23 outage flag
    evaluated_at: datetime            # for cursor staleness check (P1)
```

**Internal flow — read_one**:

```
1. Build cache key: (grant_context.actor_id, 'read', resource_type, resource_id,
   grant_context.purpose) — D24 action-aware key
2. Tier 1 LRU check (D24):
   hit  → use cached decision
   miss → OpenFGA Check (D22), cache result (60s TTL)
3. If denied:
   a. Write access_log row (always — P1 transparency + P4 audit)
   b. is_patient_facing(grant_context, record.patient_id)?  (D21)
      yes → raise PermissionDenied with grant context
      no  → raise NotFound (collapsed)
4. If permitted:
   a. Query silver table by (resource_type, resource_id)
   b. Write access_log row (always)
   c. Return ReadOneResult with AccessDecision metadata
```

**Internal flow — read_many**:

```
1. Query silver table: (resource_type, patient_id, filters, cursor) → candidate rows
2. OpenFGA BatchCheck all candidates (D22/D25)
3. Filter to permitted-only (D25 partial-permit)
4. Write access_log for ALL evaluated rows — permitted + denied (P1 + P4)
5. If is_patient_facing: set filtered_count = candidates - permitted (D25)
6. Return ReadManyResult with cursor for next page
```

**Cross-patient queries**: not a Repository.read_many concern. Patient-scoped by design (P1).
Cross-patient use cases live elsewhere:

| Use case             | Where                   | Why                                   |
| -------------------- | ----------------------- | ------------------------------------- |
| Population analytics | OMOP schema (D8)        | Different query model, pre-aggregated |
| Care team dashboard  | §3 materialized views   | PDP evaluated at materialization time |
| Research cohorts     | §2 dedicated query path | Elevated audit, IRB-scoped grants     |

**Deferred to later sections**:

| Topic                               | Section        | OQ                                     |
| ----------------------------------- | -------------- | -------------------------------------- |
| HOM UNION cross-table composition   | §2             | OQ-11 (grant_context shape refinement) |
| Opaque cursor format + HMAC signing | §4             | OQ-17                                  |
| Field selection (minimum-necessary) | §2             | future OQ                              |
| FHIR \_include (related resources)  | Data API layer | future OQ                              |

### 1.2 Repository.write()

Three methods — upsert for create/update (mirrors ingest reality where caller often doesn't know),
batch for bulk ingest, delete for soft-delete with cascade obligations.

**Signatures**:

```python
class Repository:

    def write(
        self,
        resource_type: ResourceType,
        record: DomainRecord,          # Pydantic-validated, carries source_system + external_id
        grant_context: GrantContext,
    ) -> WriteResult:
        """Single-record upsert. One transaction, one audit batch."""

    def write_batch(
        self,
        resource_type: ResourceType,
        records: list[DomainRecord],
        grant_context: GrantContext,
    ) -> WriteBatchResult:
        """Same-type batch upsert. One transaction, one audit batch."""

    def delete(
        self,
        resource_type: ResourceType,
        resource_id: UUID,
        grant_context: GrantContext,
    ) -> DeleteResult:
        """Soft-delete (deleted_at). Cascades to derived data (D20)."""
```

**Transactional boundary** (OQ-14 resolved):

- `write()` = one record, one transaction, one audit batch. API endpoint path.
- `write_batch()` = N records (same type), one transaction, one audit batch. Ingest adapter path.
  Maps to FHIR Bundle transaction semantics (all-or-nothing).
- Unit of work pattern (multi-type atomic writes) deferred to §7 agent parity — additive when needed.

**Idempotency** — structural, not opt-in:

- `(source_system, external_id)` unique constraint on all silver tables (D6 + existing DDL).
- Upsert via `INSERT ... ON DUPLICATE KEY UPDATE` — retries are safe by default.
- Ingest: adapter passes source's native ID (Epic FHIR ID, Oura UUID, Quest accession).
- Agent/manual writes: `source_system = 'hdp'`, `external_id = caller-generated UUID`.

**Trust assignment** — source default + override down only (P2 Judgment):

- `ref_source_adapters` registry (D6) carries `default_trust_level` per source_system.
- On write: omitted trust_level → use source default. Provided trust_level → accept only
  if ≥ default (numerically higher = lower trust). Reject if caller tries to elevate.
- Example: Oura adapter (default 4) can submit at 4/5/6, not 1/2/3.
- Audit log records both source default and assigned level (P4).

**Validation** — shared domain models + database constraints:

- `DomainRecord` subclasses (one per D7 resource type) carry Pydantic validation: required
  fields, type checks, enum constraints, cross-field rules (D14: `code_system` required when
  `code` present; trust_level range 1-6).
- Repository receives pre-validated `DomainRecord` — validation ran at construction time.
- API layer, ingest adapters, and agents all construct `DomainRecord` → same validation path.
- Database constraints (NOT NULL, FK, CHECK) are belt; Pydantic is suspenders.

**Soft-delete** (D3 pattern):

- `delete()` sets `deleted_at = NOW()` — record stays for audit trail (P4) + HIPAA retention.
- D20 cascade: derived data (embeddings per D5, summaries, clinical_alerts) gets cascade soft-delete.
- S3 purge only when zero active rows reference the hash (D3 reference counting).
- Separate PDP action (`action = 'delete'`) — grant may permit read/write but not delete.

**Return shapes**:

```python
@dataclass
class WriteResult:
    record_id: UUID                   # created or updated row ID
    action_taken: str                 # 'created' | 'updated' (resolved by upsert)
    access_decision: AccessDecision   # D23 metadata
    audit_batch_id: UUID | None        # audit_batches.id (P4 write audit)

@dataclass
class WriteBatchResult:
    results: list[WriteResult]        # per-record outcomes
    audit_batch_id: UUID              # single audit batch for entire transaction
    total: int                        # records processed
    created: int                      # new records
    updated: int                      # existing records updated

@dataclass
class DeleteResult:
    record_id: UUID
    cascade_count: int                # derived records also soft-deleted (D20)
    access_decision: AccessDecision
    audit_batch_id: UUID
```

**Internal flow — write()**:

```
1. Validate: DomainRecord already Pydantic-validated at construction
2. Trust check: record.trust_level >= ref_source_adapters[record.source_system].default_trust_level
   violation → reject with TrustElevationDenied error
3. PDP check: (grant_context.actor_id, 'create'|'update', resource_type, ?, grant_context.purpose)
   For new records: action='create'. For existing (external_id match): action='update'.
   Resolve by checking (source_system, external_id) existence first.
4. Begin transaction:
   a. INSERT ... ON DUPLICATE KEY UPDATE into silver table
   b. Maintain D10 child tables if applicable (access_grant_sources, _categories, _hom_nodes)
   c. Write access_log row (P1 + P4)
   d. Write outbox event row (CSA-45 — deferred but slot reserved)
   e. Trigger fires: audit_trigger_func() captures change in audit_changes (SET LOCAL hdp.audit_batch_id)
5. Return WriteResult with resolved action + audit_batch_id
```

**Internal flow — delete()**:

```
1. PDP check: (grant_context.actor_id, 'delete', resource_type, resource_id, grant_context.purpose)
2. Begin transaction:
   a. SET deleted_at = NOW() on target row
   b. Cascade: SET deleted_at = NOW() on derived rows (D20 — health_record_embeddings,
      daily_summaries, clinical_alerts where source_table + source_id match)
   c. Write access_log row (P4)
   d. Write outbox event row (deletion event for downstream consumers)
   e. Trigger fires: audit_trigger_func() captures deletion in audit_changes
3. Return DeleteResult with cascade_count
```

**Deferred to later sections**:

| Topic                                   | Section | OQ               |
| --------------------------------------- | ------- | ---------------- |
| Unit of work (multi-type atomic writes) | §7      | OQ-14 (extended) |
| Outbox worker topology                  | §6      | OQ-19            |
| D10 child table maintenance detail      | §6      | —                |
| PROV-O activity/entity records on write | §6      | —                |

### 1.3 Error envelope (D21)

Error classification is audience-split — non-patient-facing reads collapse to `NotFound` to prevent existence-leak; patient-facing reads return `PermissionDenied` with grant context for transparency. Every denial writes an `access_log` row regardless of response class.

**Classification rule** (runtime, not URL-based):

```
is_patient_facing(grant_context, target_patient_id) =
    (grant_context.actor_kind == 'person'
     AND grant_context.actor_id == target_patient_id)
  OR
    (grant_context.actor_kind == 'agent_session'
     AND agent_session.on_behalf_of == target_patient_id)
  OR
    (grant_context.active_grant.patient_id == target_patient_id
     AND grant_context.active_grant.purpose == 'patient_delegate')
```

Extends `access_grants.purpose` enum with `patient_delegate` (additive — see [consent-model.md](consent-model.md)).

**Error codes**:

| Error                  | Patient-facing response                            | Non-patient response   | Principle |
| ---------------------- | -------------------------------------------------- | ---------------------- | --------- |
| `PermissionDenied`     | `{error, reason, existing_grants, how_to_request}` | `NotFound` (collapsed) | P1        |
| `NotFound`             | same as above or `NotFound` (caller's call)        | `NotFound`             | P1 + P2   |
| `StaleCursor`          | `{error, reason: 'grant_changed', retry}`          | `NotFound`             | P1        |
| `InvalidPurpose`       | `{error, reason, permitted_purposes}`              | `NotFound`             | P1        |
| `JurisdictionMismatch` | `{error, data_jurisdiction, caller_jurisdiction}`  | `NotFound`             | P3        |
| `TrustBelowThreshold`  | `{error, min_available_trust, required}`           | same (not a leak)      | P2        |

Precedents: FHIR R4 empty Bundle convention, GitHub 404-for-private, AWS S3 (post-fix), Stripe 404-on-cross-account, Google Healthcare API, SMART on FHIR scope 403, Microsoft Graph `accessDenied`, OWASP Information Exposure guidance. See [references.md](references.md).

**Degraded-mode flag**: during OpenFGA outage (per D23), successful reads continue from Tier 1 LRU but the response envelope's `metadata.access_decision.degraded_mode = true` and `metadata.access_decision.decision_source = 'cache' | 'rls'`. Envelope shape lands in §1.1 next turn.

### 1.4 Decisions + CSAs emerging from this section

Three decisions locked in session 1 (full rationale in [decisions.md](decisions.md)):

| ID  | Decision                                                                                                                                                                            | Resolves | Detail     |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ---------- |
| D21 | Audience-split error shape (NotFound non-patient vs PermissionDenied patient-facing); hybrid classifier extending `purpose` enum with `patient_delegate`                            | OQ-4     | §1.3 above |
| D22 | **OpenFGA on Postgres** as PDP + in-process LRU Tier 1 cache; Valkey Tier 2 deferred until measured need; OPA sidecar optional                                                      | OQ-5     | §1.5 below |
| D23 | **Graceful degradation** during OpenFGA outage — Tier 1 LRU continuity + circuit breaker + degraded_mode signaling; 42 CFR Part 2 opts to strict; RLS fallback + break-glass phased | OQ-6     | §1.5 below |

Tier 1 open questions resolved into D24-D27:

| ID  | Decision                                                                                                                                                                                                    | Resolves | Detail     |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ---------- |
| D24 | LRU cache: 10k entries/worker, uniform 60s TTL, action-aware key `(actor_id, action, resource_type, resource_id, purpose)`, cache both permits+denies, TTL + bulk flush, consistency tokens phased post-MVP | OQ-7     | §1.6 below |
| D25 | Batch PDP: hybrid per-operation — partial-permit on collections (`filtered_count` in metadata), binary permit/deny on single-resource with D21 audience-split error shape                                   | OQ-8     | §1.7 below |
| D26 | First adapter: FHIR R4 (STU 4.0.1) per ADR-2002; R5 additive when concrete partner requires it; adapter interface is version-agnostic                                                                       | OQ-9     | §1.8 below |
| D27 | Envelope versioning: `metadata.envelope_version: 1`; additive fields = no bump (Postel's Law); breaking changes increment integer; adapters declare supported range                                         | OQ-10    | §1.8 below |

All Tier 1 OQs closed. Repository interface unblocked. See [open-questions.md](open-questions.md) §4.

### 1.5 PDP choice + outage behavior (D22 + D23)

**PDP substrate** — OpenFGA on Postgres. Static policies (`policy_rules` per D9 PAP) → OpenFGA type definitions; dynamic grants (`access_grants` per D10) → OpenFGA tuples; D20 transitive consent → OpenFGA computed usersets. One Postgres engine for data + authorization (per [database-substrate.md](database-substrate.md)); no new BAA chain.

**Why this shape**:

| Requirement              | How OpenFGA delivers                                                   |
| ------------------------ | ---------------------------------------------------------------------- |
| P4 Ownership (self-host) | Apache 2, CNCF sandbox, runs inside Health OS's perimeter              |
| P5 Focus (minimal deps)  | Same Postgres as main DB; no Redis required at MVP                     |
| Zero BAA expansion       | In-house software; no third party touches decisions                    |
| Portability              | Zanzibar-spec compatible with SpiceDB, Permify — tuple schema portable |
| D18 agent parity         | Agent is a tuple subject like any actor; same check API                |
| D20 transitive consent   | Native — computed usersets chain through `source_table` + `source_id`  |

**Three cache tiers** (phased, add only when measured):

```
Tier 1 — in-process LRU       always on        request-lifetime TTL
Tier 2 — Valkey (shared)       add when hit rate < 70% OR p99 exceeds budget
PDP    — OpenFGA on Postgres   always on        truth source
```

Defer Tier 2 (Valkey) until benchmarks show in-process LRU insufficient. Defer OPA sidecar until static `policy_rules` exceed OpenFGA type-system expressiveness (~20+ types).

**Outage behavior — graceful degradation ramp**:

```
                    OpenFGA health
           UP                                DOWN
            │                                  │
            ▼                                  ▼
      Normal PDP check            Circuit breaker OPEN
      (via Tier 1 LRU cache)              │
                                          ▼
                                Tier 1 LRU cache hit
                                (within 60s TTL)
                                          │
                              ┌───────────┴───────────┐
                              │ hit                    │ miss
                              ▼                        ▼
                         Serve response       503 Service Unavailable
                         with `degraded_mode  with `Retry-After` header
                         = true`,
                         `decision_source
                         = 'cache'`

Duration ramp
  0–60 s    Active users unaffected (LRU covers); new users fail-closed
  60 s–10m  Gradual degradation as TTL expires; most traffic fails-closed
  >10 min   Effectively read-only (LRU fully expired)

Every mode writes access_log (P1 transparency + P4 audit).
42 CFR Part 2 records override graceful → strict fail-closed always.
```

**Phasing**:

| Phase    | Component                                                               | Trigger                                              |
| -------- | ----------------------------------------------------------------------- | ---------------------------------------------------- |
| MVP      | Graceful degradation + circuit breaker + degraded_mode flag             | Always                                               |
| Post-MVP | Postgres RLS coarse fallback (belt-and-suspenders)                      | First audit demanding defense-in-depth evidence      |
| Post-MVP | Break-glass emergency override workflow (separate from outage handling) | Clinical demand for emergency access                 |
| Measured | Valkey Tier 2                                                           | In-process LRU hit rate < 70% OR p99 violates budget |
| Measured | OpenFGA HA (active-active pair)                                         | Single-node availability proves insufficient         |

**Precedents**: Kubernetes RBAC (kubelet TTL continuity), Zanzibar zookie staleness tolerance, SpiceDB configurable consistency (`FullyConsistent` / `AtLeastAsFresh` / `MinimizeLatency`), OAuth 2.0 token TTL isolation from IdP outage, Microsoft Entra break-glass accounts. Balanced against HIPAA §164.306(a) availability and 21C Cures info-blocking rule. See [references.md](references.md).

### 1.6 LRU cache specification (D24)

In-process LRU Tier 1 cache per worker process. One cache instance, one TTL, one eviction policy.

**Configuration** (env vars, zero code change to tune):

| Parameter               | Default | Range   | Rationale                                                                                     |
| ----------------------- | ------- | ------- | --------------------------------------------------------------------------------------------- |
| `PDP_CACHE_MAX_ENTRIES` | 10000   | 1k–100k | Working-set math: ~30k theoretical hot entries across all workers; 10k/worker covers majority |
| `PDP_CACHE_TTL_SECONDS` | 60      | 10–300  | Matches D23 stale-permit window; uniform for permits and denies                               |

**Cache key**: `(actor_id, action, resource_type, resource_id, purpose)` — ~120 bytes per key. Includes `action` (aligns with OpenFGA `relation` parameter) and `purpose` (required by D21 audience-split logic). Excludes `tree_version` (HOM changes flush entire cache — simpler than per-key versioning).

**Negative caching**: both permits and denies cached at uniform TTL. Protects PDP from deny-path flooding. 60s grant-surfacing delay matches D23's accepted staleness window.

**Invalidation**:

- **Normal**: TTL-only eviction (entries expire naturally)
- **Admin events**: bulk `cache.clear()` on HOM tree_version change or bulk access_grants migration
- **Post-MVP**: OpenFGA consistency tokens (Zanzibar zookie pattern) bypass cache on write path — when `access_grants` write occurs, subsequent reads from same session get fresh PDP evaluation

**Monitoring**: emit `cache.hit_rate` + `cache.currsize × ~200B` per worker. If hit rate < 70%, bump `PDP_CACHE_MAX_ENTRIES` to 50k before deploying Tier 2 (Valkey).

**Memory footprint**: 10k entries × ~200B = ~2MB per worker. 8 workers/node = ~16MB/node — trivial.

### 1.7 Batch PDP aggregation (D25)

OpenFGA `BatchCheck` returns per-tuple `(allowed: bool)`. Aggregation policy depends on operation type:

| Operation                                | Aggregation                                                      | Response shape                   | Transparency                                                                    |
| ---------------------------------------- | ---------------------------------------------------------------- | -------------------------------- | ------------------------------------------------------------------------------- |
| Collection read (list, search, timeline) | **Partial-permit** — return only accessible records, omit denied | Standard collection response     | Patient-facing: `metadata.filtered_count: N` (HIPAA §164.524)                   |
| Single-resource read (by ID)             | **Binary** — permit or deny                                      | Single record or D21 error shape | D21 audience-split: NotFound (non-patient) or PermissionDenied (patient-facing) |

Aligns with: FHIR Bundle/search (returns only accessible resources), Google Drive (list returns accessible files), AWS S3 ListObjects (returns only readable objects), Cedar `is_authorized_batch` (per-resource decisions, caller aggregates).

### 1.8 Format adapter + envelope versioning (D26 + D27)

**First adapter**: FHIR R4 (STU 4.0.1) per ADR-2002. Adapter interface is version-agnostic — `ClinicalRecord → format(version)` — so R5 (or custom) adapters slot in without changing the Repository read/write path. R5 added when a concrete interop partner requires it.

**Envelope versioning**: every `ClinicalRecord` response carries `metadata.envelope_version: 1`.

- **Additive changes** (new optional field in metadata): no version bump — consumers ignore unknown fields (Postel's Law)
- **Breaking changes** (field removal, type change, new required field): bump `envelope_version` integer
- **Adapter registration**: each format adapter declares `min_envelope_version` / `max_envelope_version` — Registry rejects incompatible combinations at startup
- **HTTP convenience**: `X-Envelope-Version` response header mirrors the field; envelope field is authoritative (works for async events and internal callers too)

## 2. Query composition patterns (Locked)

### 2.1 HOM query — cross-table fan-out

HOM node queries (D17) span multiple D7 silver tables. **App-level fan-out at MVP**: Repository issues parallel queries per silver table, filters by `ref_hom_mapping`, merges results in application. Each query independently PDP-evaluated.

Why not UNION VIEW for HOM: adding a silver table (CSA-14 procedures, CSA-16 orders) requires VIEW migration. App fan-out just adds a new query to the list. Materialized views added in §3 when performance data warrants.

### 2.2 Patient timeline — UNION VIEW

Timeline is the primary UI surface. **Postgres UNION VIEW** — standard CREATE VIEW with UNION ALL. Point-in-time queries use temporal columns (`valid_from`, `valid_to`) maintained by audit triggers (see [database-substrate.md](database-substrate.md)).

```sql
CREATE VIEW patient_timeline_view AS
  SELECT patient_id, effective_date, 'observation' AS resource_type, id AS resource_id,
         code, code_display, source_system FROM observations
  UNION ALL
  SELECT patient_id, effective_date, 'condition', id, code, code_display, source_system
         FROM conditions
  UNION ALL ...
```

- Zero write-path cost (VIEW reads from source tables directly).
- Always consistent — no denormalization drift.
- Standard cursor pagination works (VIEW looks like one table).
- New silver tables = `CREATE OR REPLACE VIEW` (schema migration via Alembic).
- PDP: BatchCheck the page of timeline entries, partial-permit filter (D25).
- Detail fetch: user clicks timeline entry → `read_one(resource_type, resource_id)` for full record.
- **Upgrade path**: if VIEW performance degrades at scale, materialize into a dedicated `patient_timeline` table populated on write or via async worker.

### 2.3 Export bundle (CSA-47)

**Compose from existing read paths** — export = `read_many()` per resource type for a patient → collect → wrap in FHIR Bundle (adapter at API edge per D26). IPS (International Patient Summary) Composition = subset with D15 section structure. No new query path needed. Rate limiting on export endpoint deferred to §7 (OQ-21).

### 2.4 Agent access pattern

**Same Repository methods, different GrantContext** — D18 locked agent as persons row; D9 PDP evaluates agent through same engine. Agent calls `read_one()` / `read_many()` with `actor_kind = 'agent_session'` and `on_behalf_of = patient_id`. Agent-specific scoping is filter-level, not query-path-level. Detailed in §7.

### 2.5 Sync vs async reads (OQ-15)

**Sync at MVP**. All Repository.read() calls are synchronous request-response. Async read patterns (streaming, subscriptions) deferred until concrete use case emerges. Sync is simpler (P5) and sufficient for API + agent consumers.

## 3. Materialized views + caching (Locked)

### 3.1 Gold-tier refresh cadence (OQ-18)

**Nightly scheduled at MVP**. `daily_summaries` recomputed from silver tables by batch job. 24h staleness is acceptable — summaries are historical, not real-time. No write-path coupling. Upgrade to async worker (outbox-triggered) when real-time dashboards require sub-minute freshness.

### 3.2 PDP decision caching

**D24 is complete** — no additional mechanism. 10k entries, uniform 60s TTL, in-process LRU per worker. Tier 2 (Valkey) triggered by hit rate < 70% or p99 exceeds budget. Consistency tokens phased post-MVP. Nothing new to decide here.

### 3.3 Timeline materialization

**Deferred** — §2.2 locked UNION VIEW (not materialized). If VIEW performance degrades, materialize into a dedicated table populated by nightly job or async worker (same pattern as daily_summaries).

### 3.4 D20 transitive eval timing (OQ-16)

**Read-time (P1 wins)**. When derived data (embeddings per D5, clinical_alerts per CSA-28) is read, PDP dereferences source consent at read-time — not pre-evaluated at write-time. A revoked consent must immediately block derived data. Extra PDP call is one additional OpenFGA Check per derived row, cached at Tier 1 (D24) with 60s TTL. Write-time stamping would require invalidation machinery — exactly the complexity D24 deferred to consistency tokens.

## 4. Pagination + cursor (Locked)

### 4.1 Cursor format (OQ-17)

**Opaque base64 + HMAC-SHA256** — tamper-proof. Forged cursor rejected; prevents cursor manipulation to bypass PDP (P1). Server secret from app config. HMAC is ~microseconds. Client can decode base64 (non-secret) but can't forge. Standard pattern (Stripe, Slack, GitHub).

### 4.2 Cursor payload

```python
@dataclass
class CursorPayload:
    effective_date: datetime    # sort position
    last_id: UUID               # tiebreaker (stable sort)
    page_size: int              # requested page size
    resource_type: str          # prevents cross-type cursor reuse
    access_decision_id: str     # PDP decision snapshot (for re-eval trigger)
    issued_at: datetime         # cursor expiry check
```

**Grant re-evaluation**: `access_decision_id` links cursor to PDP evaluation that produced the page. On next-page request, Repository checks: has `access_grants` changed since `issued_at`? If yes, re-evaluate from PDP. This is how P1 wins the cursor-vs-grant tension.

**Cursor expiry**: reject cursors older than 1 hour (configurable). Prevents stale cursors from serving data under revoked grants.

### 4.3 Sort stability

Primary: `effective_date DESC`. Tiebreaker: `resource_id` (UUID, globally unique). Composite index `(patient_id, effective_date DESC, id)` on each silver table.

### 4.4 Cross-table pagination (HOM fan-out)

Composite cursor carries per-table positions: `{resource_type → CursorPayload}`. K-way merge advances the table with the oldest `effective_date` first. HMAC-signed. Only used for HOM queries — single-type `read_many` uses simple cursor.

## 5. Ingest patterns — batch vs realtime (Locked)

### 5.1 Ingest topology

**Hybrid pull/push** — adapters pull by default (Oura API, Quest labs, Epic bulk export); push endpoint for sources supporting webhooks or FHIR Subscription. Both paths converge at Repository.write_batch(). D6 `ref_source_adapters` declares per-source ingest mode.

### 5.2 Ingest pipeline

```
Source → Adapter → raw_payloads (bronze, payload_hash dedup)
                 → Transform → DomainRecord (Pydantic-validated)
                             → Repository.write_batch() (silver, source_system/external_id upsert)
```

Two dedup gates: `payload_hash` at bronze (reject duplicate raw payloads) + `(source_system, external_id)` at silver (upsert). At-least-once delivery + idempotent writes = effectively-once.

### 5.3 FHIR R4 Subscription (OQ-20)

**Included at MVP** — HAPI FHIR Server + Synthea for local testing eliminates partner sandbox dependency.

| Component                                                   | Effort    |
| ----------------------------------------------------------- | --------- |
| Notification endpoint (webhook handler → existing pipeline) | ~0.5 days |
| Subscription CRUD client (outbound to EHR FHIR server)      | ~2-3 days |
| Lifecycle management (heartbeat, expiry renewal)            | ~2-3 days |
| Subscription tracking table                                 | ~1 day    |
| SMART on FHIR auth (shared — needed for pull too)           | 3-5 days  |
| HAPI + Synthea integration testing                          | 1-2 days  |

Subscription-specific delta: ~6-9 days on top of shared auth investment. Partner EHR validation layered post-MVP when partner onboards.

## 6. Write patterns — transactions, outbox (Locked)

### 6.1 D10 child table maintenance

**Delete-and-reinsert within transaction**. On upsert: delete existing child rows for the grant_id, re-insert from current JSON columns. Simpler than diff-based sync. Within a transaction, the delete+insert is invisible to concurrent readers. Access_grants typically have 1-5 sources/categories — correctness over optimization (P5).

### 6.2 Transactional outbox (CSA-45, OQ-19)

**Transactional outbox with polling worker**. Outbox row written in same transaction as data write (slot reserved in §1.2). Worker polls outbox, publishes to consumers, marks `delivered_at`.

Outbox table: `(id, resource_type, resource_id, action, payload_ref, created_at, delivered_at)`.

- At-least-once delivery — worker retries undelivered rows.
- Consumers must be idempotent (same posture as §5 ingest).
- No message broker at MVP (P5 + P4 — no new infra dependency).
- Cleanup: cron deletes delivered rows older than 7 days.

At MVP, outbox has **zero mandatory consumers** — daily_summaries is nightly batch, access_log is in-transaction, timeline VIEW reads from source. Infrastructure exists for when async consumers appear (notifications, webhooks, analytics ETL).

### 6.3 PROV-O lineage (CSA-46)

**Deferred to post-MVP**. Health OS already captures provenance signals (source_system, source_adapter_id, trust_level, access_log, audit_batches + audit_changes). Formal W3C PROV Activity/Entity/Agent records are an additive structured overlay. Build when compliance audit or partner requires PROV format.

### 6.4 Observability depth (OQ-22)

**Three-layer, no overlap**:

| Layer                | What                                                       | Where                                 | Answers                            |
| -------------------- | ---------------------------------------------------------- | ------------------------------------- | ---------------------------------- |
| `access_log` (table) | Every PDP decision — who, what, when, permit/deny, rule_id | Silver-tier, queryable (P1 + P4)      | "Who accessed what?" (HIPAA audit) |
| Application log      | Request lifecycle, errors, performance metrics             | Structured JSON → stdout → aggregator | "What's slow/broken?" (operations) |
| Audit log (triggers) | Every write — who, when, what changed (old/new JSONB)      | `audit_batches` + `audit_changes`     | "What changed and when?" (lineage) |

## 7. Agent vs human parity at the data layer (Locked)

### 7.1 Agent as grantee

**D9 + D18 + D21 + D22 composed — no new mechanism**. Agent is a persons row with `agents` satellite. Holds `access_grants` like any grantee. PDP evaluates via same OpenFGA Check. Same cache key shape (D24). Non-patient-facing → NotFound on denial (D21). Agent calls Repository with `GrantContext(actor_kind='agent_session', on_behalf_of=patient_id)`.

### 7.2 Transitive consent cost

**Same read-time evaluation (P1 wins)**. Agent reads are conversational scale (~5-20 records/turn), not batch. D24 LRU absorbs repeated checks within the session. Batch analysis uses `read_many()` with BatchCheck (D25). No fast path that skips consent.

### 7.3 Agent audit — session_id on access_log

**Add nullable `session_id` column to access_log**. Links agent actions to conversation context (`agent_sessions.id`). Human requests have NULL session_id. Enables: "show me everything the agent accessed during this conversation." Minimal schema change — one nullable column.

### 7.4 Rate limiting (OQ-21)

**Gateway + PEP hybrid**:

- **Gateway**: global rate limits per endpoint (DDoS protection, infrastructure). All callers equally.
- **PEP middleware**: actor-specific quotas. Agent sessions get per-session budget (e.g., 1000 reads/session). Purpose-scoped: `research` grants may have lower quotas than `care` grants.
- Repository stays pure — data access only, no rate logic.
- P2 (Judgment): liberal read surface, bounded by session budget.

### 7.5 Agent write restrictions

**Grant-scoped, not agent-type-scoped**. D9 PDP evaluates write permission per (actor, action, resource_type). Grants for agents are narrower by default (e.g., can write `clinical_impressions` and `tasks`, but not `medications` without elevated grant). Policy decision configured in OpenFGA type definitions, not code.

## Related

- [decisions.md](decisions.md) — D9 (XACML triad), D10 (child tables), D18 (agent identity), D19 (reconciliation), D20 (transitive consent) all inform this file
- [design-queue.md](design-queue.md) — CSA-10 (PDP/PEP), CSA-45 (outbox), CSA-46 (PROV-O), CSA-47 (export) are the active proposals
- [design-patterns.md](design-patterns.md) — Repository pattern, CQRS, Outbox, Capability-based security vocabulary
- [endpoint-inventory.md](endpoint-inventory.md) — 25 API endpoints that this data plane must serve
- `../../../adr/0001-guiding-principles.md` — the five principles this file is anchored to

## Iteration log

| Date       | Change                                                                                                                                        | Rationale                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-04-16 | Dolt→Postgres alignment pass — dolt_commit→audit_batch_id, DOLT_COMMIT()→audit triggers, Dolt VIEW→Postgres VIEW, observability layer updated | Per database-substrate.md recommendation: Postgres for M3 greenfield. WriteResult/WriteBatchResult/DeleteResult updated. §2.2 timeline uses temporal columns for point-in-time queries. §6.4 observability third layer is now audit_batches+audit_changes (trigger-based).                                                                                                                                                                                                                                                                                                |
| 2026-04-15 | §2-7 locked — query composition, materialized views, pagination, ingest, write patterns, agent parity                                         | All Tier 2/3 OQs resolved (OQ-14 through OQ-22). Timeline as Postgres UNION VIEW. HOM via app fan-out. Nightly gold refresh. HMAC-signed cursors with grant re-eval. Hybrid pull/push ingest with FHIR Subscription at MVP (HAPI+Synthea testing). Transactional outbox. Three-layer observability. Agent parity structural via D9+D18. Session_id on access_log. Gateway+PEP rate limiting.                                                                                                                                                                              |
| 2026-04-15 | §1.2 Repository.write() sketch landed — write/write_batch/delete, upsert idempotency, trust down-only, Pydantic validation                    | Hybrid transaction boundary (single auto-commit + batch one-commit). Idempotency via (source_system, external_id) upsert. Trust assignment: source default + override down only. Soft-delete with D20 cascade. Shared DomainRecord Pydantic models. Unit of work deferred to §7.                                                                                                                                                                                                                                                                                          |
| 2026-04-15 | §1.1 Repository.read() sketch landed — two methods (read_one/read_many), 4-field GrantContext, DomainRecord return, internal flow diagrams    | Two methods mirror D25 aggregation semantics. patient_id required on read_many (P1). GrantContext frozen + minimal (4 fields). Repository returns DomainRecord (Health OS-native); FHIR adapter at API edge per D26. Cross-patient queries excluded — routed to §2/§3/OMOP.                                                                                                                                                                                                                                                                                               |
| 2026-04-15 | D24 + D25 + D26 + D27 landed — LRU spec + batch PDP + FHIR R4 + envelope versioning                                                           | OQ-7 resolved as uniform 60s TTL, 10k entries, action-aware key, consistency tokens phased (measure-first). OQ-8 resolved as hybrid partial-permit/binary (FHIR search semantics). OQ-9 resolved as R4 per ADR-2002. OQ-10 resolved as envelope field + Postel's Law. All Tier 1 OQs closed — Repository interface unblocked.                                                                                                                                                                                                                                             |
| 2026-04-15 | D21 + D22 + D23 landed — error envelope + PDP choice + outage behavior                                                                        | OQ-4 (patient-facing classification) resolved as hybrid Options 6+3 — actor_id / on_behalf_of / purpose=='patient_delegate'; modeled on Microsoft OBO + Azure RBAC. OQ-5 (PDP cache) resolved as OpenFGA on Postgres + in-process LRU; Valkey Tier 2 + OPA sidecar deferred until measured need — maximum flexibility, zero new BAA. OQ-6 (outage behavior) resolved as graceful degradation with circuit breaker + degraded_mode signaling; 42 CFR Part 2 opts to strict; Postgres RLS + break-glass phased. All three audited against P1-P5, inner-ring wins preserved. |
| 2026-04-15 | Initial capture — hub file created with P1-P5 anchoring, three-layer thesis, 7-section arc                                                    | User: "data plane, data api, data layer — how data is accessed and managed." Middle-out direction chosen (start at Repository). Principle anchoring forced early so every subsequent decision cites which principle(s) it serves.                                                                                                                                                                                                                                                                                                                                         |

Append new entries above this line.
