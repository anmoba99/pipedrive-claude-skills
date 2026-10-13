---
name: pd-ask
description: Answer any plain-English question about the user's Pipedrive data (deals, contacts, organizations, activities, notes, leads, products) with the cheapest possible queries. Use for ad-hoc questions not covered by a more specific pd-* skill.
---

# pd-ask

Follow pd-core rules (load pd-core if not loaded).

Requires: Pipedrive
Fallback: question needs data Pipedrive does not hold -> say which data is missing.

## Steps

1. Restate the question as a query in one line: object, filters, time window, fields, aggregation.
   Example: "Clients in Porto not contacted in 60 days" -> orgs with city=Porto (custom/address field), deals or activities with no update since today-60d.
2. Check for a better skill: daily to-do -> pd-morning-brief; team or forecast -> pd-pipeline-review. If one fits, use it.
3. Plan calls with `pd-core/references/query-playbook.md`. Prefer: known ID > saved filter (`filter_id`) > filtered list > search.
4. If the plan needs more than about 15 calls or would pull 500+ records, say so and offer a narrower version first.
5. Run. Aggregate with `pd-core/scripts/pd_digest.py` when counting or summing over more than about 20 records.
6. Answer.

## Output

```
<Direct answer in 1-2 lines>
<up to 20 compact rows: id | name | key fields>
Query: <one line: what was fetched and filters used>
```

If the data is ambiguous (two "Acme" orgs, missing field), say so in one line and ask.
Never guess custom field meanings: map names via the cached context.
