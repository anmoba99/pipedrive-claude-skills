---
name: pd-pipeline-review
description: "Pipeline review for managers and owners in three modes: review (by rep and stage, stuck and risky deals), forecast (stage probability vs real activity, slipping close dates), digest (short weekly business summary). Use for pipeline review, forecast check, weekly digest or team performance questions."
license: MIT
metadata:
  version: "2.0.0"
---

# pd-pipeline-review

Follow pd-core rules (load pd-core if not loaded).
Team scope: if `.pipedrive/access.json` is missing or shows partial coverage, run pd-access checks 1 and 2 first and state the coverage in the first line.

Requires: Pipedrive (manager/admin visibility for team results)
Optional: Slack/Teams (post digest, opt-in), Google Docs (report)
Fallback: chat + file `pipedrive-out/pd-pipeline-review/<date>.md`

## Mode

Pick from the request: "review" (default), "forecast", "digest". Scope: pipeline (ask if more than one and not named), owner (all visible by default), period (this month/quarter for forecast).

## Steps

1. Context from cache. Note if the user cannot see other reps' deals (pd-setup records this).
2. Fetch: `getDeals pipeline_id=<id> status=open limit=500 include_fields=[next_activity_id,undone_activities_count,last_activity_id]`. 500+ open deals: split by owner; in Claude Code use one subagent per owner, each returning at most 10 lines.
3. Run `pd-core/scripts/pd_digest.py` on the result (save the result to a file first when a shell is available) with `--group stage`, then `--group owner`.
4. Mode specifics:
   - **review**: stuck = in the same stage longer than 2x the median for that stage (use `stage_change_time` if present, else `update_time`). List top 10 risky deals. Pull notes (`getNotes deal_id limit=3`) only for the top 5.
   - **forecast**: for deals with close date in the period, compare stage probability vs evidence: no activity in 14+ days, close date already pushed (notes or `expected_close_date` in the past), no next step, single contact. Produce "committed" (strong evidence), "at risk", "unlikely". Sum per bucket per currency.
   - **digest**: won/lost this week: `getDeals status=won updated_since=<monday>` and `status=lost`; new deals `getDeals sort_by=add_time sort_direction=desc updated_since=<monday>`. One-paragraph pulse plus 3 actions.
5. Compare with the last report file if present: deltas only (value change, new risks, resolved risks).
6. Route output (config). Slack/Teams only when opted in.

## Output (review)

```
Pipeline <name> | <n> open | <value per currency> | vs last week: <+/->
By stage: <stage n value> ...
By owner: <owner n value stale no_next> ...
Stuck / risky (top 10):
- <id> | <deal> | <stage> | <value> | <owner> | <reason>
Coaching points:
- <owner>: <pattern, one line>
Actions this week:
1. ...
```

## Output (forecast)

```
Period <month> | pipeline <name>
Committed: <value> (<n>) | At risk: <value> (<n>) | Unlikely: <value> (<n>)
Weighted by Pipedrive stage: <value>. Evidence-based: <value>. Gap: <value>.
At risk:
- <id> | <deal> | <value> | <owner> | <evidence>
```

## Output (digest)

```
Week <n>: won <value> (<n>), lost <value> (<n>), new <n> deals.
<2-3 sentence pulse>
Watch: <top 3 risks>
Do: <3 actions>
```

Never present the evidence-based forecast as certain. State the rules used in one line.
