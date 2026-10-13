# Large accounts

Read this when an entity has more than about 2,000 records (more than 4 pages of 500). Pulling 130k deals through the connector is about 260 calls and far too much data for one conversation, so the audit samples fields and scopes record checks instead.

## 1. Size check

One call per entity: `getDeals status=open limit=500`, `getPersons limit=500`, `getOrganizations limit=500`. A `next_cursor` means more pages. Tell the user what the audit will cover before fetching more:

```
Large account: 500+ open deals, 500+ people, 500+ organizations.
Plan: fields from the 1,000 most recently updated per type, issues on every open deal and on people and organizations updated in the last 12 months.
About <N> calls. Go, or limit to one owner or pipeline?
```

Caps per entity in scope: about 20,000 records in Claude Code or Cowork, about 1,000 on claude.ai or Desktop. Over the cap: split by owner or pipeline and run the biggest slices first, or ask the user to narrow.

More than one batch of records in scope: run in batches (`pd-core/references/batches.md`). The sample pass is batch 1 for every entity. Scope pass batches follow, open deals first, biggest pipelines first. Record issues on a partial run are exact for the slices done; duplicates are final only after the last batch.

## 2. Two passes

1. **Sample pass (field completeness).** The 1,000 most recently updated records per entity, all fields: `sort_by=update_time sort_direction=desc limit=500`, 2 pages. Pass as `--sample-deals/--sample-persons/--sample-orgs`. The tracker says the rates come from that sample.
2. **Scope pass (record issues).** Every open deal: `getDeals status=open include_fields=[next_activity_id,undone_activities_count]`. People and organizations with `updated_since=<12 months ago>`. Pass as `--deals/--persons/--orgs` (several files or globs are fine, records are deduped by id, latest update wins). Add `--scope-note "open deals, people and organizations updated since <date>"` so the page states what was not checked.

## 3. Paging without filling the context

Claude Code: one subagent per slice (a pipeline, or an owner when one pipeline is too big). Each subagent pages with the cursor, writes every page to `pipedrive-out/pd-data-hygiene/raw/<entity>-<slice>-<n>.json` and replies with one line: `<slice>: <records> records, <pages> pages, done`. Raw records never enter the main conversation. Big tool results already land in files; when one comes back inline, the subagent writes it to the file itself.

Then run the script on the globs: `--deals 'pipedrive-out/pd-data-hygiene/raw/deal-*.json'`.

Duplicates at this size: `scripts/find_dupes.py` on the scope pass files only.

## 4. Next runs are incremental

Always pass `--snapshot-out pipedrive-out/pd-data-hygiene/snapshot.json`. The snapshot keeps, per record, the issue codes, owner, value and update time, plus the field rates and duplicate pairs of that run.

Next run:
- Fetch only records changed since the last run: `updated_since=<snapshot date>`, same scope rules.
- Run with `--snapshot pipedrive-out/pd-data-hygiene/snapshot.json` and the delta files. Changed records replace their old version; field rates and duplicates are reused for any entity with no new sample.
- Snapshot older than 30 days: full rescan. Deleted or merged records only disappear on a full run.

## 5. What the page shows at this size

- Overview counts cover every record in scope, not only the rows on the page.
- Each records tab holds up to 1,500 rows, shared across issue types so no issue is hidden: open deals and biggest value first, then the most recently updated. The tab says how many more exist.
- Every row is in `--fixlist-out pipedrive-out/pd-data-hygiene/<date>-fixlist.csv`.
- At this size the value is the bulk fix, not the row: each issue has a recipe for the Pipedrive filter and bulk edit that fixes all of them at once. Lead the chat summary with the top 3 issues by open deal value at risk and their recipe.
