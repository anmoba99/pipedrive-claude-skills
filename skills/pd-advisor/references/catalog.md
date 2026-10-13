# Skill catalog

Format: skill: purpose. Triggers. Needs. Output. Cost (low/med/high Pipedrive calls).

## Foundation
- pd-core: shared rules (cached context, cheap queries, compact output, safe writes). Loaded by other skills. No direct use.
- pd-setup: one-time setup and health check; caches pipelines, stages, users, fields; writes config; sets industry. Triggers: "set up", "doctor", "something broke", new connector. Needs Pipedrive. Output: capability report in chat, `.pipedrive/` files. Cost low.
- pd-access: what Claude can see and change with this connection: connector permissions, who "me" is, owners and deals visible, owner-only deals, read-only fields, exact fixes. Triggers: "what can Claude see", "team report looks incomplete", "Claude doesn't know who I am". Needs Pipedrive. Output chat + `.pipedrive/access.json`. Read-only. Cost low.

## Rep
- pd-morning-brief: today's activities, overdue, idle deals, deals with no next step, top 3 actions. Triggers: "brief me", "what should I do today". Needs Pipedrive. Optional Slack DM, Calendar. Output chat. Cost low.
- pd-follow-up: draft follow-up email from deal context. Never sends. Triggers: "draft follow-up", "nudge X". Needs Pipedrive. Optional Gmail/Outlook draft. Fallback chat or Pipedrive note. Cost low.
- pd-lead-qualifier: score leads with BANT/MEDDICC/CHAMP/custom; missing info; next question; optional convert lead to deal. Triggers: "qualify my leads", "which leads are serious". Needs Pipedrive. Output chat + optional field/note (after confirm). Cost med.
- pd-ask: any plain-English question about the CRM. Triggers: questions like "which clients in Porto haven't heard from us in 60 days". Needs Pipedrive. Output chat. Cost low to med.

## Manager / owner
- pd-pipeline-review: modes review (by rep/stage, stuck deals), forecast (stage vs real signals, slipping close dates), digest (weekly owner summary). Triggers: "pipeline review", "forecast check", "weekly digest". Needs Pipedrive (manager visibility for team). Optional Slack, Google Docs. Output chat/file/Slack. Cost med to high.
- pd-win-loss: themes behind won and lost deals from lost reasons and note text; actions. Triggers: "why do we lose", "win-loss". Needs Pipedrive. Output chat/file. Cost med.

## Ops / admin
- pd-data-hygiene: modes audit (field completeness per standard and custom field, empty values, duplicates, no next step, stale, owner-only visibility; tabbed data health tracker with value at risk, owners, pipelines, bulk fix recipes and trend since last run; large accounts via sampling, scoped checks and incremental runs) and import-clean (CSV before import). Triggers: "clean my CRM", "find duplicates", "clean this CSV". Needs Pipedrive (audit) or nothing (import-clean). Output tracker HTML (artifact on claude.ai), CSV fix list, optional fill-blank updates (after confirm). Cost med to high.

## Customer success / account management
- pd-account-health: account management on orgs. Modes portfolio (book per account manager: health score, revenue, renewals, coverage, whitespace; tabbed page, scales to thousands of accounts), health (score with drivers, note signals for top 10), renewals (next 90 days with risk), coverage (single-threaded, missing roles), whitespace (products peers in the same tier buy), review (QBR brief), handoff (sales -> CS brief). Optional health score write-back to an opt-in org field (after confirm, max 200 per run). Triggers: "show my book", "accounts at risk", "renewals this quarter", "who do we know at X", "upsell", "QBR for X", "handoff for X". Needs Pipedrive, `accounts` in config (pd-setup). Optional Google Docs. Output portfolio HTML (artifact on claude.ai), CSV, chat, optional pinned note. Cost med to high.

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
- Manager: pd-access first, then pd-pipeline-review review + forecast, pd-win-loss.
- Messy CRM: pd-setup, pd-data-hygiene audit first, then everything else.
- Inbound-heavy: pd-lead-qualifier, pd-follow-up.
- Recurring revenue: pd-account-health renewals, pd-win-loss.
- CS / account team: pd-setup accounts mapping, pd-access, pd-account-health portfolio weekly + renewals monthly + review before QBRs, pd-data-hygiene for org and contact gaps.
