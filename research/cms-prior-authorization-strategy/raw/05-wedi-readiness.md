# S-005: WEDI 2026 readiness survey

Source: https://www.wedi.org/2026/03/11/wedi-survey-shows-progress-in-implementing-cms-interoperability-and-prior-authorization-final-rule/
Tools: Exa web fetch
Query: not applicable
Worker: research-worker-luna
Invocation route: task
Revision: not applicable
Evidence goal: Quantify readiness and reported workflow, expertise, testing, policy-digitization, delegated-party, and training barriers.
Rationale: Operational evidence tests whether intended API architecture is deployment reality.
Captured: 2026-08-05
Byte verification: verified
Verified by: openai/gpt-5.6-sol primary at 2026-08-05T14:42:00Z
Verification method: Reopened the exact approved WEDI URL with Exa and matched every retained percentage and barrier list.
Normalization: none
Citation verification:
- Source locator: exact source URL above
  Source span: exact text beginning `A total of 86 responses` and ending `31% vendors.`
  Capture span: line 47
  Source span SHA-256: 49c3bc030d6c8f085406d1995617f86a941653ad64673130a053fb0697787e58
  Capture span SHA-256: 49c3bc030d6c8f085406d1995617f86a941653ad64673130a053fb0697787e58
Outcome: gathered

## Evidence

- WEDI received 86 responses: 52% payers, 5% providers, 12% clearinghouses, and
  31% vendors. The provider subgroup is therefore especially small.
- Ten percent of payer respondents had not started API work. Only 16% expected
  their Patient Access API work to be 75-100% complete by January 1, 2027.
- Payer barriers were delegated third parties connecting to different systems,
  digitizing prior-authorization policies, and funding.
- Thirty-three percent of provider respondents had not started implementation
  and testing; 67% were unsure of progress. No provider respondent reported
  implementation progress in this round.
- Provider barriers were internal expertise, coordinating testing with vendors
  and plans, and understanding how TEFCA, QHINs, and HIEs interact.
- Sixty percent of clearinghouse respondents planned to conduct exchanges for
  payer customers and 70% for provider customers. Eighty-two percent of vendor
  respondents planned to assist payers and providers.
- Fifty-three percent supported staggering CRD, DTR, and PAS; 33% favored that
  order. Respondents requested education on best practices, workflow design, and
  advanced API implementation.

## Verified Excerpt

```text
A total of 86 responses were completed and represented 52% payers, 5% providers, 12% clearinghouses, and 31% vendors.
```

## Notes

This is a self-selected industry survey summary, not audited market prevalence.
It does not provide subgroup confidence intervals, organization size, or raw
question denominators. It is still direct evidence that implementation work is
not only an API problem: policy digitization, testing, workflow redesign,
delegated integration, training, and expertise are reported blockers.

The article says the February 2026 survey would repeat in the first quarter of
2026, an internally inconsistent timing statement that does not affect the
retained findings.

## Followups

- A later implementation effort should recruit provider and payer design partners
  rather than extrapolate product demand from these 86 responses.
