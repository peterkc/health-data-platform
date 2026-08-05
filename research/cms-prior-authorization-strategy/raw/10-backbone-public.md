# S-010: Backbone public product claims

Source: https://www.backbonesystems.ai/ and https://www.backbonesystems.ai/contact
Tools: Exa web fetch
Query: not applicable
Worker: research-worker-luna
Invocation route: task
Revision: not applicable
Evidence goal: Ground conversation preparation in Backbone's public product boundary.
Rationale: Public company claims ground provider-side product analysis in first-party material.
Captured: 2026-08-05
Byte verification: verified
Verified by: openai/gpt-5.6-sol primary at 2026-08-05T14:42:00Z
Verification method: Reopened both exact approved company URLs with Exa and matched retained headings, bullets, and FAQs.
Normalization: none
Citation verification:
- Source locator: https://www.backbonesystems.ai/contact
  Source span: FAQ `How does Backbone learn over time?`, first sentence
  Capture span: line 46
  Source span SHA-256: 483fb05a467b1941121e8ea8bb11d8fef3eaed66dc1067f318e90156400350fd
  Capture span SHA-256: 483fb05a467b1941121e8ea8bb11d8fef3eaed66dc1067f318e90156400350fd
Outcome: gathered

## Evidence

- Backbone publicly positions itself as an AI chart reviewer for revenue
  integrity that checks full clinical records against live payer policies,
  authorization requirements, and contracts before submission.
- Pre-service functions include commercial and LCD/NCD checks, denial-risk
  alerts, targeted next steps, referrals, longitudinal chart context, and
  medical-necessity support.
- Pre-bill functions include plan edits, coding and modifier validation,
  bundling/carve-out detection, denial prevention, and first-pass-yield work.
- Public commercial claims include a 100% review rate, anti-clawback guarantees,
  and paid-or-credit coverage. The approved pages do not establish terms or
  independent performance evidence.
- Backbone says it learns from denials, payer requests, remits, and appeal
  outcomes and integrates through EHR, practice-management, and billing
  workflows, returning worklists, flags, or tasks.
- Its suggested pilot is one specialty, one to three payers, and a narrow claim
  set measured against denial drivers and first-pass yield.

## Verified Excerpt

```text
Backbone learns from outcomes: denials, payer requests, remits, and appeals results.
```

## Notes

Backbone's public boundary already covers the policy and clinical-intelligence
layer that the standards leave open. The useful conversation is therefore not
“FHIR will replace the product.” It is how the company will connect that
intelligence to certified EHR workflows and payer APIs, preserve mixed-channel
case state, validate changing policy versions, and turn structured denial and
request-more-information outcomes into better pre-service and pre-bill review.

Guarantee language and implementation details are company claims and unknowns,
not accepted facts.

## Followups

- Ask provider-side vendors about these boundaries rather than infer how they
  have implemented them.
