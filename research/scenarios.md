# Demo Scenarios

**Status**: Current (2026-04-15) — 7 scenarios covering core MVP workflows
**Purpose**: Prove the platform handles real clinical workflows, not just lab results
**Audience**: Reviewers verifying table coverage per scenario
**Companion to**: [table-designs.md](table-designs.md), [diagrams.md](diagrams.md), [endpoint-inventory.md](endpoint-inventory.md)

## How to read this file

- Each scenario is a numbered walkthrough ending with "Tables used" and "Proves" lines
- Scan "Proves" lines to find the scenario that validates a specific capability
- Scenarios build in complexity: onboarding (1) through multi-patient analytics (7)
- Cross-check "Tables used" against [table-designs.md](table-designs.md) for column-level detail

## Scenario 1: Patient Onboarding (Identity + Multi-source)

```
1. Create org (Longevity Clinic NYC)
2. Register patient (John Doe)
3. Link identifiers: LabCorp FHIR, Quest FHIR, Oura wearable
4. Ingest: 3 FHIR bundles + Oura API sync
5. Show: 6 record types in health_records from 4 sources
```

**Tables used**: ref_organizations, persons, org_roles, patients, patient_identifiers,
patient_org_access, raw_payloads, health_records

**Proves**: Multi-source ingestion, identity resolution, trust-ranked dedup

## Scenario 2: Clinical Visit (Encounter + Documents)

```
1. Doctor logs in (practitioner role)
2. Create encounter: "Annual Executive Physical"
3. Upload: LabCorp PDF (→ S3, document record)
4. FHIR bundle arrives: 15 observations
5. Show: timeline with encounter context
```

**Tables used**: practitioners, encounters, documents, health_records, raw_payloads,
provenance

**Proves**: Encounter-linked records, document management, timeline feed

## Scenario 3: Body Explorer (HOM Grouped Query)

```
1. Navigate to cardiovascular node
2. See: lipids (LabCorp), heart rate (Oura), family history (patient),
   condition (EHR) — all grouped under one node
3. Drill into metabolic: glucose, HbA1c, metformin (medication)
4. Show: drug class query ("all statins for this patient")
```

**Tables used**: health_records, ref_hom_mapping, ref_hom_nodes, ref_drug_classes

**Proves**: HOM-as-schema, cross-source grouping, clinical meaning over data source

## Scenario 4: AI Agent Query

```
1. Patient asks: "How's my cardiovascular health?"
2. Agent calls get_hom_grouped("cardiovascular")
3. Returns: cited observations + conditions + family risk
4. Agent response: "Your LDL is within range (195 mg/dL)... Note: family
   history of MI in first-degree relative at age 52."
5. Agent does NOT diagnose — cites sources, flags risk factors
```

**Tables used**: health_records, ref_hom_mapping, ref_hom_nodes, access_grants

**Proves**: AI agent uses same data path as human users, consent-gated, cited

## Scenario 5: Consent & Privacy (42 CFR Part 2)

```
1. Patient has substance use records (record_type = 'observation',
   category = 'substance_use')
2. Default: practitioner sees all EXCEPT substance use
3. Patient grants: explicit consent for substance use category
4. Now visible — grant recorded in access_grants with expiry
5. Patient revokes: records disappear from practitioner view
```

**Tables used**: health_records, access_grants, persons

**Proves**: Two-layer auth (RBAC + consent), 42 CFR Part 2 compliance

## Scenario 6: Longevity Care Plan

```
1. Doctor creates care plan: "Cardiovascular Optimization"
2. Goals: LDL < 100 mg/dL, resting HR < 60 bpm, HRV > 50 ms
3. Link goals to HOM nodes (cardiovascular)
4. Dashboard shows progress: current values vs targets
5. Journal entry: "Started rosuvastatin, targeting LDL reduction"
```

**Tables used**: care_plans, goals, health_records, journal_entries, notes,
ref_hom_nodes

**Proves**: Beyond data aggregation — actionable clinical workflows

## Scenario 7: International Patient (Unit Conversion)

```
1. Patient preference: SI units (mmol/L)
2. LabCorp reports cholesterol in mg/dL (US conventional)
3. API returns: value_numeric=195 (source), display_value=5.04 mmol/L (converted)
4. Source value preserved, conversion at display time
```

**Tables used**: health_records, patient_preferences, ref_analyte_conversions

**Proves**: International readiness, source value preservation (ADR-2010)

## Data Flow Diagram

```
Ingest                    Store                     Query
──────                    ─────                     ─────

FHIR Bundle ──┐
              │     ┌──────────────┐
Oura API ─────┤     │ raw_payloads │ (bronze)
              ├────→│ documents    │ (S3 ref)
Lab PDF ──────┤     │ health_      │ (silver — all types)
              │     │   records    │
Patient ──────┘     │ encounters   │         ┌─── GET /readings
                    │ care_plans   │         ├─── GET /hom/.../readings
                    │ journal_     │         ├─── GET /records
                    │   entries    │         ├─── GET /timeline
                    └──────┬───────┘         ├─── GET /documents
                           │                 ├─── GET /care-plans
                    ┌──────┴───────┐         ├─── GET /journal
                    │ daily_       │ (gold)  └─── POST /agent/ask
                    │   summaries  │
                    └──────────────┘

                    ref_hom_nodes ──┐
                    ref_hom_mapping─┤ (reference)
                    ref_drug_classes┤
                    ref_organizations│
                    ref_analyte_    │
                      conversions──┘
```

## Minimum Viable Demo

Scenarios 1-4 are the core walkthrough (identity, documents, HOM query, AI agent).
Scenarios 5-7 cover edge cases and deeper capabilities.
