---
name: pd-account-health
description: Account management on Pipedrive organizations in three modes: health (score per account from deals, activity, notes and products), renewals (upcoming renewal or reorder deals with risk and upsell signals), handoff (sales to customer success brief for a won deal). Use for account health, renewals, churn risk, upsell or handoff requests.
---

# pd-account-health

Follow pd-core rules (load pd-core if not loaded).

Requires: Pipedrive
Optional: Google Docs (handoff doc)
Fallback: chat, optional pinned `[Claude]` note on the org (after confirm)

## Mode: health

1. Scope: one org (search), or "my accounts" = orgs with won deals owned by the user: `getDeals owner_id=<me> status=won limit=500`, group by org. Cap 30 orgs per run.
2. Per org (max 3 calls): `getDeals org_id`, `getActivities org_id done=true limit=20`, `getNotes org_id sort="add_time DESC" limit=5`.
3. Score 0-100 from: days since last touch (30%), open deal or renewal in progress (20%), activity trend last 90 vs previous 90 days (20%), note sentiment and complaints (20%), product breadth (10%). State weights in output.
4. Upsell signals: mentions of growth, new teams, new locations, extra volume, other products. Churn signals: complaints, champion left, budget cuts, competitor mentions, silence.

## Mode: renewals

1. Renewal source, in order: `renewal_field` in config (a date custom field), deals in a "Renewal" pipeline, won deals with an anniversary in the window (default next 90 days).
2. For each: health score (light version: last touch + notes), value, owner, signals.
3. Sort by date, then risk.

## Mode: handoff

1. Won deal named or found. Fetch `getDeal`, `getNotes deal_id limit=20`, `getPersons deal_id`, `getDealProducts`.
2. Brief: what they bought, why they bought (in their words), promises made, people and roles, risks, success criteria, first 30 days plan. Facts only; inference marked "likely".
3. Route: Google Doc if live, else chat; offer a pinned org note.

## Output (health)

```
<org> | score 62 (amber) | last touch 41d | open deals 1 | products 2
Signals: + "opening second warehouse" (note 2026-09-02) | - no reply to last 2 emails
Next: <one action>
```

## Output (renewals)

```
Next 90 days: <n> renewals | <value per currency> | <n> at risk
- <date> | <org> | <value> | <owner> | score <n> | <signal>
```
