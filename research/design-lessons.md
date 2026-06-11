# Design Lessons — Patterns, Anti-Patterns, Scorecard

**Status**: Living — updated as new schemas inform comparisons
**Purpose**: What do FHIR, OMOP, openEHR, i2b2, Fasten, HealthKit, OpenEMR/OpenMRS, and USCDI agree on, disagree on, and get wrong?
**Audience**: Engineers making schema decisions; pattern validation during review
**Companion to**: [references.md](references.md), [design-queue.md](design-queue.md), [open-questions.md](open-questions.md)

## How to read this file

- **Convergent patterns** (Section 1): where multiple schemas agree — treat as domain constraints Health OS follows
- **Divergent choices** (Section 2): where schemas disagree — Health OS's opinion documented with rationale
- **Anti-patterns** (Section 3): what to avoid, with evidence from public schemas
- Scorecard at the end grades Health OS honestly against this landscape
- Active proposals derived from these lessons live in [design-queue.md](design-queue.md); unresolved questions in [open-questions.md](open-questions.md)

## Convergent patterns — treat as true domain constraints

When multiple independent schemas arrive at the same pattern, it's not 5 schemas agreeing —
it's 5 schemas discovering a real constraint of the domain. Health OS follows these.

| Pattern                      |       FHIR       |          OMOP           |       openEHR       |      i2b2       |    Fasten    |     HealthKit     | Health OS implementation                                            |
| ---------------------------- | :--------------: | :---------------------: | :-----------------: | :-------------: | :----------: | :---------------: | ------------------------------------------------------------------- |
| Canonical + raw separation   |    Y (Binary)    | Y (src vs std concepts) |          Y          |        Y        |      Y       |         Y         | **Locked** — `health_records` + `raw_payloads`                      |
| Vocabulary tables            |  Y (CodeSystem)  |       Y (concept)       | Y (terminology svc) | Y (concept_dim) |      Y       |         —         | **Locked** — `loinc_crosswalk`, `ref_hom_mapping`                   |
| Source provenance per record |  Y (Provenance)  |   Y (type_concept_id)   |          Y          |        —        |      Y       |   Y (HKSource)    | **Locked** — `source_system`, `source_standard` columns             |
| Extension mechanism          | Y (extensions[]) |            —            |   Y (archetypes)    |        —        | Y (FHIR ext) |         —         | **Locked** — `extensions JSON` + `ref_record_type_schemas`          |
| Long-format fact tables      |        —         |            Y            |          —          |        Y        |      —       |         —         | **Locked** — single-table `health_records` + `record_type`          |
| Reference/linkage            |  Y (Reference)   |         Y (FK)          |          Y          |        Y        |      Y       |         —         | **Locked** — standard FKs                                           |
| Identifier with system+value |  Y (Identifier)  |    Y (source_value)     |          Y          |        —        |      Y       | Y (external UUID) | **Partial** — has system+value, lacks use + verified_at (see CSA-4) |

## Divergent choices — where Health OS's opinion matters

Schemas disagree on these. Document the choice + why, so future engineers do not re-litigate.

| Decision           | FHIR                            | OMOP           | Fasten                  | OpenEMR         | Health OS                                      |
| ------------------ | ------------------------------- | -------------- | ----------------------- | --------------- | ---------------------------------------------- |
| Identity root      | Patient resource                | `person` table | Patient resource        | `patient` table | **persons with role satellites (D1)**          |
| Multi-tenancy      | Not addressed                   | Not addressed  | Self-hosted             | Single-tenant   | **First-class: ref_organizations + org_roles** |
| Consent model      | Consent resource (bolt-on)      | None           | Per-connection (coarse) | Role-based only | **Architectural: access_grants first**         |
| AI integration     | None                            | None           | None                    | None            | **First-class: agent = grantee**               |
| Document structure | Composition + DocumentReference | Note (flat)    | Attachment              | document table  | **Flat with deferred Composition flag**        |
| Trust grading      | .reliability (deprecated)       | None           | None                    | None            | **First-class: trust_level (ADR-2007)**        |

## Health OS's frontier — where Health OS leads

No public schema is authoritative on these. Health OS invents; decisions here will be cited by
others later. Document carefully.

| Frontier                   | Health OS approach                                                      | Open questions                                                           |
| -------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| Multi-tenant Health OS     | `ref_organizations` + `org_roles` + path routing + per-org HOM variants | How to handle cross-org patient transfers while preserving history?      |
| Consent-first architecture | `access_grants` with categories + sources + hom_nodes + time-bounds     | Grant history (versioning) — promote from deferred to MVP? (CSA-3)       |
| AI agent consent parity    | Agent holds grants like a practitioner; same auth path                  | Agent identity lifecycle — ephemeral session vs. persistent persons row? |
| Trust-graded data          | `trust_level` on every row, ADR-2007 ordinal                            | Conflict resolution when two sources disagree at same trust level        |
| HOM semantic grouping      | `ref_hom_nodes` + `ref_hom_mapping` — user-facing "cardiovascular" view | How to extend when new HOM grouping schemes emerge?                      |

## Anti-patterns — avoid with reason

| Anti-pattern                                                         | From             | Why avoid                                      | Health OS's defense                                                                                      |
| -------------------------------------------------------------------- | ---------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Extension explosion (extensions on extensions on extensions)         | FHIR             | Debugging / querying becomes hopeless          | `ref_record_type_schemas` enforces contracts                                                             |
| Medication quartet (Request / Dispense / Statement / Administration) | FHIR             | Over-decomposes a single concept               | One `medication` record_type with lifecycle in extensions                                                |
| RelatedPerson vs FamilyMemberHistory duplication                     | FHIR             | Two ways to say "Jane's mother had diabetes"   | Family history stays clinical in `health_records`; `patient_relationships` handles identity linking only |
| Archetype resolution at query time                                   | openEHR          | Performance overhead + complexity              | `ref_record_type_schemas` is documentation, not runtime resolution                                       |
| Provider-centric identity                                            | OpenEMR, OpenMRS | Patient is not sovereign                       | `persons` root + role satellites                                                                         |
| Coarse per-connection consent                                        | Fasten           | Can not express "share labs but not wearables" | `access_grants` categories + sources + hom_nodes                                                         |
| Device-centric privacy                                               | HealthKit        | User loses control when device changes         | Patient-level consent regardless of source                                                               |
| Proprietary lock-in                                                  | HealthKit, Epic  | Exit cost is prohibitive                       | FHIR + open source adapters; content-addressed storage                                                   |

## Health OS's honest scorecard

### Strengths (confirmed by cross-schema study)

- Canonical + raw separation aligns with FHIR, OMOP, openEHR, Fasten
- Vocabulary-first via `loinc_crosswalk` + `ref_hom_mapping` aligns with OMOP + i2b2
- Extensions JSON with `ref_record_type_schemas` is the pragmatic middle between
  FHIR (too loose) and openEHR (too rigid)
- Source plurality + trust grading is ahead of the field
- Multi-tenancy from day one is an unusual advantage
- Consent architecture is genuinely differentiated

### Gaps (revealed by cross-schema study)

- No `access_log` table for HIPAA audit of data access — `provenance` tracks ETL lineage only (CSA-1)
- No narrative / text field for AI reasoning context (CSA-2)
- No `grant_history` table for consent versioning (CSA-3)
- `patient_identifiers` simpler than FHIR Identifier (CSA-4)
- `health_records` has only `effective_date`; missing `recorded_at` + `asserted_at` (CSA-5)
- `code_display` vs `code_text` semantics unclear (CSA-6)
- No Composition-equivalent for multi-section documents (CSA-7)
- Analytics tier design unspecified (CSA-9)

## See also

- **Active proposals** (CSA-N) informed by these lessons → [design-queue.md](design-queue.md)
- **Frontier open questions** (FQ-1 through FQ-5) → [open-questions.md](open-questions.md)
- **Phasing decisions** → [scoping.md](scoping.md) (pending)

The iteration log for schema proposals lives in [design-queue.md](design-queue.md).
