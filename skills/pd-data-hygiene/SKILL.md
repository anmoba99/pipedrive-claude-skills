---
name: pd-data-hygiene
description: Pipedrive data quality. Audit mode finds empty fields, duplicates, deals with no next step and stale records, and builds a data health page plus a fix list. Import-clean mode cleans and dedupes a CSV before import. Use when the user wants to clean the CRM, find duplicates, or prepare an import.
license: MIT
metadata:
  version: "2.0.0"
---

# pd-data-hygiene

Follow pd-core rules (load pd-core if not loaded).

Requires: Pipedrive (audit). import-clean works on a CSV alone, Pipedrive optional for the dedupe check.
Fallback: no filesystem -> fix list in chat (max 20 rows) and a downloadable CSV

The connector cannot delete or merge. Output is a fix list; the user merges in Pipedrive (Contacts > Merge). Claude may only fill empty fields, after confirmation.

## Mode: audit

1. Scope: persons, orgs, open deals. Size check first: one page of 500 per entity. Any `next_cursor` (more than 500) and more than about 2,000 records: follow `references/scale.md` (sample pass for fields, scope pass for issues, subagents per slice, incremental runs).
2. Fetch: `getPersons limit=500` (cursor for more), `getOrganizations limit=500`, `getDeals status=open limit=500 include_fields=[next_activity_id,undone_activities_count]`. Save each raw result to a file. Field names come from the account context (cached or `getAccountContext`).
3. Duplicates: save results to files and run `scripts/find_dupes.py persons.json` and `scripts/find_dupes.py orgs.json --kind org`. No shell: compare exact email/phone and normalized names only.
4. Gaps: persons without email and phone, orgs without owner or address (if the industry needs it), deals without value, expected close date, or next activity. Required fields from the industry pack.
5. Stale: open deals idle more than 90 days (suggest close or revive), persons with no activity in 12 months.
6. Field health and tracker: run
   ```
   python3 scripts/field_health.py --deals deals.json --persons persons.json --orgs orgs.json \
     [--sample-deals ... --sample-persons ... --sample-orgs ...] [--snapshot snapshot.json] \
     --snapshot-out pipedrive-out/pd-data-hygiene/snapshot.json --scope-note "<what was checked>" \
     --context <.pipedrive/account_context.json or a fresh getAccountContext result> --dupes-person dupes_p.csv --dupes-org dupes_o.csv \
     --prev <latest pipedrive-out/pd-data-hygiene/*-summary.json, if any> --stale-days 90 \
     --summary-out pipedrive-out/pd-data-hygiene/<date>-summary.json \
     --fixlist-out pipedrive-out/pd-data-hygiene/<date>-fixlist.csv \
     --html references/tracker.html --html-out pipedrive-out/pd-data-hygiene/<date>-tracker.html
   ```
   Add `--domain <company>` only if the user's Pipedrive address (`<company>.pipedrive.com`) is known, for record links. It shows fill rate per standard and custom field (under 50% = needs attention, 0% = never used), records with issues, duplicates, deals with no next step, stale deals, owner-only visibility, by owner, and the change since the last run. The page has tabs: Overview (counts, open deal value at risk per issue, owners, pipelines), Fields, Deals, People, Organizations, Duplicates. Each issue has a fix in bulk recipe (Pipedrive filter plus bulk edit). Record tabs hold up to 1,500 rows each; the CSV has all. Deep link a tab with `#deals`, `#fields` and so on.
   - Claude Code or Cowork: give the file path and offer to open it.
   - claude.ai or Desktop with code execution: run the same command and show the HTML as an artifact. No code execution: build the artifact from `references/tracker.html` by putting the computed JSON in place of `/*DATA*/` (same shape as the script's `--out`).
   - Read-only fields (set by Pipedrive) and fields the connector did not return are listed apart, never as empty. Records the user cannot see are not in the audit; say so if pd-access shows partial coverage.
   - The "Fixed" ticks live only in that browser. The next audit is the real check.
7. Fix list: `--fixlist-out` writes every row. No filesystem: list the top 20 in chat. Large accounts: lead with the top 3 issues by open deal value at risk and their bulk recipe, not with rows.
8. Offer safe fills only: missing org on a person when the email domain matches exactly one org; missing country from phone prefix. Show change set, write on yes.

## Mode: import-clean

1. Read the CSV. Detect columns; map to Pipedrive fields (show mapping, ask to confirm).
2. Normalize: trim, title-case names, lowercase emails, E.164 phones when the country is known, country names to one form, split full names when asked.
3. Dedupe inside the file (`scripts/find_dupes.py file.csv`), then against Pipedrive with `searchPersons` by email for up to 50 rows (more: say so, sample).
4. Output `pipedrive-out/pd-data-hygiene/<date>-import-clean.csv` + `<date>-import-issues.csv`. Recommend Pipedrive's own importer for large files; offer to add up to 25 rows via MCP (safe-write) for small ones.

## Output

```
Audit <date> | persons 1,240 | orgs 410 | open deals 186
Field completeness 62% (+4 pts since 2026-09-13) | 9 fields need attention
Never used: Legacy score, Partner tier (custom, deal)
Likely duplicates: 37 person pairs, 9 org pairs
Missing: 112 persons no email/phone, 41 deals no next step, 18 deals no value
Stale: 23 open deals idle 90+ days | Owner-only visibility: 14 deals
Tracker: pipedrive-out/pd-data-hygiene/2026-10-13-tracker.html
Fix list: pipedrive-out/pd-data-hygiene/2026-10-13-fixlist.csv
Safe fills available: 14 persons -> org by email domain. Apply?
```
