---
name: pd-industry
description: "Industry packs for the pd-* Pipedrive skills (real estate, SaaS, agencies, manufacturing, recruiting, financial services, construction, education, healthcare, events, nonprofits, logistics): object mapping, pipeline templates, qualification checks, risk and upsell signals, custom fields. Use when designing a pipeline for an industry or when another pd-* skill needs industry context."
---

# pd-industry

Load only the one file that matches. Never load all.

| Industry | File |
|---|---|
| Real estate (agencies, brokers, developers) | `references/real-estate.md` |
| SaaS and tech | `references/saas.md` |
| Agencies and consulting | `references/agencies.md` |
| Manufacturing and wholesale | `references/manufacturing-wholesale.md` |
| Recruiting and staffing | `references/recruiting-staffing.md` |
| Financial services and insurance | `references/financial-services-insurance.md` |
| Construction and home services | `references/construction-home-services.md` |
| Education and training | `references/education-training.md` |
| Healthcare and medtech (B2B) | `references/healthcare-medtech.md` |
| Events and hospitality | `references/events-hospitality.md` |
| Nonprofits | `references/nonprofits.md` |
| Logistics and freight | `references/logistics-freight.md` |

No match: pick the closest by sales motion (short transactional -> construction-home-services; long B2B -> healthcare-medtech or saas; project services -> agencies) and say which one you used.

## Uses

- **Pipeline design** ("set up Pipedrive for my <industry>"): show the template stages, fields and qualification checks, then compare with the real account (cached context). Output as manual steps; the connector cannot create pipelines, stages or fields.
- **Other skills**: pd-lead-qualifier (custom checks), pd-follow-up (vocabulary), pd-pipeline-review and pd-account-health (signals).
