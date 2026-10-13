# Skill catalog

Format: skill: purpose. Triggers. Needs. Output. Cost (low/med/high Pipedrive calls).

## Foundation
- pd-core: shared rules (cached context, cheap queries, compact output, safe writes). Loaded by other skills. No direct use.
- pd-setup: one-time setup and health check; caches pipelines, stages, users, fields; writes config; sets industry. Triggers: "set up", "doctor", "something broke", new connector. Needs Pipedrive. Output: capability report in chat, `.pipedrive/` files. Cost low.

## Rep
- pd-morning-brief: today's activities, overdue, idle deals, deals with no next step, top 3 actions. Triggers: "brief me", "what should I do today". Needs Pipedrive. Optional Slack DM, Calendar. Output chat. Cost low.
- pd-follow-up: draft follow-up email from deal context. Never sends. Triggers: "draft follow-up", "nudge X". Needs Pipedrive. Optional Gmail/Outlook draft. Fallback chat or Pipedrive note. Cost low.
- pd-lead-qualifier: score leads with BANT/MEDDICC/CHAMP/custom; missing info; next question; optional convert lead to deal. Triggers: "qualify my leads", "which leads are serious". Needs Pipedrive. Output chat + optional field/note (after confirm). Cost med.
- pd-ask: any plain-English question about the CRM. Triggers: questions like "which clients in Porto haven't heard from us in 60 days". Needs Pipedrive. Output chat. Cost low to med.

## Manager / owner
- pd-pipeline-review: modes review (by rep/stage, stuck deals), forecast (stage vs real signals, slipping close dates), digest (weekly owner summary). Triggers: "pipeline review", "forecast check", "weekly digest". Needs Pipedrive (manager visibility for team). Optional Slack, Google Docs. Output chat/file/Slack. Cost med to high.
- pd-win-loss: themes behind won and lost deals from lost reasons and note text; actions. Triggers: "why do we lose", "win-loss". Needs Pipedrive. Output chat/file. Cost med.

## Ops / admin
- pd-data-hygiene: modes audit (duplicates, missing fields, no next step, stale) and import-clean (CSV before import). Triggers: "clean my CRM", "find duplicates", "clean this CSV". Needs Pipedrive (audit) or nothing (import-clean). Output CSV fix list, optional fill-blank updates (after confirm). Cost med to high.

## Customer success / account management
- pd-account-health: modes health (org score), renewals (upcoming renewal deals), handoff (sales -> CS brief). Triggers: "account health", "renewals this quarter", "handoff for X". Needs Pipedrive. Optional Google Docs. Output chat/file/optional pinned note. Cost med.

## Industry packs (pd-industry)
Files in pd-industry/references/. Set once via pd-setup; other skills load the matching file.
- real-estate: buyers, sellers, listings, viewings.
- saas: trials, demos, seats, expansion.
- agencies: briefs, proposals, retainers.
- manufacturing-wholesale: quotes, volumes, reorders, distributors.
- recruiting-staffing: roles as deals, candidates, placements, fees.
- financial-services-insurance: policies, renewals, households, compliance notes.
- construction-home-services: site visits, quotes, jobs, seasonality.
- education-training: enrollments, cohorts, corporate training.
- healthcare-medtech: long procurement, committees, tenders.
- events-hospitality: RFPs, dates, group bookings.
- nonprofits: donors, gifts, grants, lapsed donors.
- logistics-freight: lanes, rate quotes, contract expiry.

## Common combos
- Solo founder: pd-morning-brief, pd-follow-up, pd-pipeline-review digest.
- Rep team: pd-morning-brief, pd-follow-up, pd-lead-qualifier.
- Manager: pd-pipeline-review review + forecast, pd-win-loss.
- Messy CRM: pd-setup, pd-data-hygiene audit first, then everything else.
- Inbound-heavy: pd-lead-qualifier, pd-follow-up.
- Recurring revenue: pd-account-health renewals, pd-win-loss.
