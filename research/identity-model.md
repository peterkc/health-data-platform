# Identity Model — persons, org_roles, practitioners

**Status**: Locked (2026-04-14) — Option A: persons root + role satellites
**Purpose**: Define the persons hub + role satellite pattern (D1) with DDL for `persons`, `ref_organizations`, `org_roles`, and `practitioners`.
**Audience**: Engineers implementing identity or auth; reviewers checking how roles map to persons.
**Companion to**: [consent-model.md](consent-model.md) (access_grants FK to persons), [table-designs.md](table-designs.md) (remaining MVP tables), [decisions.md](decisions.md) (D1, D16, D18)
**Source**: ADR-2005 (Multi-tenant Organization Model)

## How to read this file

- "Decision" section explains why Option A won over Option B, with the Health OS rationale table
- "Target DDL" section has the full `CREATE TABLE` statements in FK dependency order
- D16 (person_identifiers, person_preferences) and D18 (agent identity) extend this model — see [decisions.md](decisions.md)

## Decision: D1 = Option A (satellite pattern)

`persons` holds identity (name, email, auth, DOB — universal human attributes).
`patients`, `practitioners`, and future role tables are **satellites** with
`person_id NOT NULL` FK back to persons.

### Rationale (Health OS framing)

Health OS aggregates from N sources (wearables, labs, EHR, pharmacy,
imaging, genomics, manual, future). Under source plurality, identity must be
source-agnostic. `persons` is that root. `patients` becomes the patient-role
satellite holding clinical-context attributes only.

| Requirement                                         | Why Option A delivers                                                                        |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Multi-role (doctor tracks own health)               | One persons row, rows in patients + practitioners + org_roles                                |
| Source plurality (Oura ID, Quest MRN, Epic FHIR ID) | patient_identifiers FKs to persons.id, stable across sources                                 |
| Name integrity                                      | Identity lives once in persons; no drift                                                     |
| Consent grantees (ADR-2006)                         | access_grants.grantee_id → persons.id (practitioner, app as synthetic person, agent session) |
| New roles (caregiver, researcher, admin)            | New satellite tables; obvious FK target                                                      |
| API portability                                     | persons.id survives org transfers; org_roles layer on top                                    |

### Rejected: Option B (patients-as-identity with person_id FK)

Option B was logical under the premise "preserve M1/M2 FKs." Premise wrong — M3 is
not built; M1/M2 is dev-team code, not production data. Option B would ship
dual-identity that fragments under source plurality and forces a refactor at
Series A.

## Target DDL (MVP state)

FK order matters: persons → ref_organizations → org_roles/practitioners → patients satellite.

### ref_organizations

```sql
CREATE TABLE IF NOT EXISTS ref_organizations (
    id              VARCHAR(36) NOT NULL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(50) NOT NULL,
    org_type        VARCHAR(30) NOT NULL DEFAULT 'clinic',
    default_hom_id  VARCHAR(36) NULL,
    display_labels  JSON NULL,
    timezone        VARCHAR(50) NOT NULL DEFAULT 'America/New_York',
    jurisdiction    VARCHAR(10) NULL,
    created_at      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    UNIQUE KEY uq_slug (slug)
)
```

Note: `default_hom_id` FK to `ref_hom_nodes(hom_id)` is TBD — `ref_hom_nodes` uses a
composite key. Defer the FK or refactor ref_hom_nodes first.

### persons (identity root — universal human attributes)

```sql
CREATE TABLE IF NOT EXISTS persons (
    id                  VARCHAR(36) NOT NULL PRIMARY KEY,
    given_name          VARCHAR(100) NULL,
    family_name         VARCHAR(100) NULL,
    date_of_birth       DATE NULL,
    email               VARCHAR(255) NULL,
    auth_provider_id    VARCHAR(255) NULL,
    created_at          DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    UNIQUE KEY uq_auth (auth_provider_id),
    KEY idx_email (email)
)
```

### org_roles

```sql
CREATE TABLE IF NOT EXISTS org_roles (
    id              VARCHAR(36) NOT NULL PRIMARY KEY,
    person_id       VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    role            VARCHAR(30) NOT NULL,
    permissions     JSON NULL,
    granted_at      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    granted_by      VARCHAR(36) NULL,
    FOREIGN KEY (person_id) REFERENCES persons(id),
    FOREIGN KEY (org_id) REFERENCES ref_organizations(id),
    UNIQUE KEY uq_person_org_role (person_id, org_id, role),
    KEY idx_org (org_id)
)
```

Valid `role` values: `patient`, `practitioner`, `admin`, `staff`, `caregiver`,
`researcher`, `agent`.

### practitioners (role satellite)

```sql
CREATE TABLE IF NOT EXISTS practitioners (
    id              VARCHAR(36) NOT NULL PRIMARY KEY,
    person_id       VARCHAR(36) NOT NULL,
    npi             VARCHAR(20) NULL,
    specialty       VARCHAR(100) NULL,
    credentials     VARCHAR(50) NULL,
    org_id          VARCHAR(36) NOT NULL,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (person_id) REFERENCES persons(id),
    FOREIGN KEY (org_id) REFERENCES ref_organizations(id),
    UNIQUE KEY uq_person_org (person_id, org_id),
    KEY idx_npi (npi)
)
```

### patients (revised as role satellite)

Identity fields (`given_name`, `family_name`, `email`, `auth_provider_id`,
`date_of_birth`) move out of `patients` into `persons`. `patients` keeps only
patient-role-specific attributes.

```sql
CREATE TABLE IF NOT EXISTS patients (
    id                      VARCHAR(36) NOT NULL PRIMARY KEY,
    person_id               VARCHAR(36) NOT NULL,
    sex_at_birth            VARCHAR(10) NULL,
    gender_identity         VARCHAR(30) NULL,
    pronouns                VARCHAR(30) NULL,
    medical_record_number   VARCHAR(50) NULL,  -- internal MRN, distinct from source-specific IDs
    primary_practitioner_id VARCHAR(36) NULL,
    created_at              DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (person_id) REFERENCES persons(id),
    FOREIGN KEY (primary_practitioner_id) REFERENCES practitioners(id),
    UNIQUE KEY uq_person (person_id),  -- one patient row per person
    KEY idx_person (person_id)
)
```

Query pattern for patient name:

```sql
SELECT pe.given_name, pe.family_name, p.sex_at_birth
FROM patients p JOIN persons pe ON p.person_id = pe.id
WHERE p.id = ?
```

## Migration from current M1/M2 state

M3 DDL work:

1. Create `ref_organizations`, `persons`, `org_roles`, `practitioners` (new tables)
1. For each existing `patients` row, create a `persons` row with identity fields copied
1. Drop identity columns from `patients`: `given_name`, `family_name`, `email`, `auth_provider_id`, `date_of_birth`
1. Add `person_id NOT NULL` FK column to `patients`, backfilled to match step 2
1. Regenerate seed data: persons INSERT first, then patients with person_id

No production data affected — M1/M2 seed is deterministic and re-runnable via
`just demo-reset`.

## FK Dependency Order

```
ref_organizations (no deps)
  → persons (no deps)
    → org_roles (persons, ref_organizations)
      → practitioners (persons, ref_organizations)
        → patients (persons, practitioners) [satellite; identity stripped]
```

## Impact on Existing Tables

| Table                 | Current FK  | Change                                                                             |
| --------------------- | ----------- | ---------------------------------------------------------------------------------- |
| patients              | —           | Strip identity cols, add person_id FK NOT NULL                                     |
| patient_org_access    | patients.id | Add org_id FK to ref_organizations                                                 |
| patient_preferences   | patients.id | No FK change; conceptually per-person, per-org                                     |
| patient_identifiers   | patients.id | Reconsider: patient-level or person-level?                                         |
| patient_relationships | patients.id | No change (patient ↔ patient semantic is correct)                                  |
| health_records        | patients.id | No change (clinical records belong to patient role)                                |
| encounters (new)      | —           | FK to patients.id and practitioners.id                                             |
| access_grants (new)   | —           | FK to patients.id; grantee_id → persons.id (practitioner) OR external (app, agent) |

### Open question

`patient_identifiers` scope (patient-level or person-level?) is tracked as **OQ-1** in
[open-questions.md](open-questions.md).
