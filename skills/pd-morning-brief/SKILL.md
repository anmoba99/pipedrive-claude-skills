---
name: pd-morning-brief
description: "Daily brief for a Pipedrive user: today's and overdue activities, idle deals, deals with no next step, and a ranked top 3 actions. Use when the user asks what to do today, for a brief, or for a daily plan."
license: MIT
metadata:
  version: "2.0.0"
---

# pd-morning-brief

Follow pd-core rules (load pd-core if not loaded).

Requires: Pipedrive
Optional: Google Calendar (merge today's meetings), Slack (DM the brief, if opted in)
Fallback: chat

## Steps

1. Context: `me.id` and stage names from cache (or `getAccountContext` once).
2. Activities: `getActivities owner_id=<me> done=false sort_by=due_date sort_direction=asc limit=50`. Split into overdue, today, next 2 days. Ignore later.
3. Deals: `getDeals owner_id=<me> status=open sort_by=update_time sort_direction=asc limit=200 include_fields=[next_activity_id,undone_activities_count]`.
   - Incremental: if `.pipedrive/last_run.json` has `pd-morning-brief` from today, reuse and fetch only `updated_since=<last_run>`.
4. Flags: idle >= `stale_days` (config, default 14), no next activity, expected close date passed. Use `pd-core/scripts/pd_digest.py` when more than about 20 deals.
5. Calendar (if live): today's meetings, matched to deals by attendee email or org name. No match is fine.
6. Rank top 3 actions: overdue on high-value deals first, then close-date-passed, then no-next-step on biggest deals. Industry pack (if set) may add signals, for example trial end dates for saas.
7. Save `last_run.json` timestamp (if filesystem). Output.

## Output

```
<Weekday date>. <n> due today, <n> overdue, <n> deals need attention.
Top 3:
1. <action verb> <deal/person> (<why, short>)
2. ...
3. ...
Today:
- 10:00 call Ana Silva, deal 1042 Acme rollout
Overdue:
- <activity> | deal | days late
Attention:
- <id> | <deal> | <stage> | <value> | idle <n>d | <flag>
```

Max 10 lines per section. More: "and <n> more, ask for full list".
Manager asking for the team: suggest pd-pipeline-review instead.
