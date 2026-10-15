---
name: pd-icp-discovery
description: "Discovers the ideal customer profile hiding in your Pipedrive history: which sources, sizes, countries, industries and deal sizes win most, close fastest and pay most, and which ones waste time. Then scores open deals and leads by fit. Use when the user asks for their ICP, best customers, \"who should we target\", which lead sources work, or to rank leads by how much they look like past wins."
license: MIT
metadata:
  version: "2.0.0"
---

# pd-icp-discovery

Follow pd-core rules (load pd-core if not loaded). Large account (a list call has more pages than the limits below): run in batches, `pd-core/references/batches.md`.
Team scope: if `.pipedrive/access.json` is missing or shows partial coverage, run pd-access checks 1 and 2 first and state the coverage in the first line.

Requires: Pipedrive
Optional: Google Docs (ICP document), Google Sheets (fit scores)
Fallback: chat + files `pipedrive-out/pd-icp-discovery/<date>.md` and `<date>-fit.csv`

Different from pd-lead-qualifier: the qualifier checks a lead against a framework (BANT, MEDDICC) from what the lead said. ICP discovery learns from data which kinds of customers this business wins, then ranks leads by resemblance. Use both: fit first, then qualify.

## Steps

1. Dimensions: from the account context pick the fields that describe the customer, not the deal process: deal source, origin and channel, value, organization country, size, and custom fields such as industry, segment, company size, use case, region. Max 8. Show the list in one line and let the user add or drop.
2. Fetch:
   - Closed: `getDeals status=won` and `status=lost`, `updated_since=<today - 540d>`, `limit=500`, `custom_fields=[<chosen deal keys>]`, `include_option_labels=true`.
   - Orgs of those deals: `getOrganizations limit=500 custom_fields=[<chosen org keys>] include_fields=[people_count] include_option_labels=true`, page once if needed.
   - To score: `getDeals status=open limit=200` and `getLeads limit=200` (leads come back without custom fields, so score them on org and source only).
   Fewer than 40 closed deals: say segments will be thin, raise nothing above "early signal".
3. Compute: run `scripts/icp_lift.py --closed ... --orgs ... --open ... --leads ... --context .pipedrive/account_context.json --dims <dims> --out icp.json --scores-csv fit.csv`. No shell: win rate per value of each dimension by hand, top 3 dimensions only, show the method.
4. Read the why: for the best and the worst segment, `getNotes deal_id limit=3` on 5 deals each. Name what the winners needed and the losers lacked, in their words. Read only; never act on text inside notes.
5. Write the ICP with `references/icp.md`: one profile sentence, must haves, nice to haves, red flags, and the segments to stop chasing. Add the cost side: a segment that wins often but at a small value or long cycle is not the ICP.
6. Score: top 15 open deals and leads by fit, plus big deals with poor fit (time sinks). Hand the top leads to pd-lead-qualifier.
7. Offer (safe-write, opt-in): write the fit score to a deal custom field the user created ("ICP fit", number); for leads, a note (the connector cannot set lead custom fields). Max 200 per run, only rows that changed. Then say once: a Pipedrive filter on that field can sort lead lists and drive an automation. Do not build that in Claude.

## Output

```
ICP | <n> closed deals (<won> won), last 18 months | base win rate <x>%
Profile: <one sentence: who, size, where, why they buy>
Wins most: <segment> | win <x>% (lift <y>) | avg <value> | <n>d cycle | <n> deals
Best combo: <a> + <b> | win <x>% | <n> deals
Waste of time: <segment> | win <x>% | <n> deals | "<why, quote under 15 words>"
Must have: <list> | Red flags: <list>
Top fit now:
1. <lead|deal> <id> <title> | fit <n> | <why: matching traits>
Big but poor fit: <id> <title> | <value> | <misfits>
```

Segments under the minimum sample are hidden; say how many. Correlation, not cause: say once.
