---
name: pd-data-hygiene
description: Pipedrive data quality in two modes: audit (duplicate persons and organizations, missing key fields, open deals with no next step, stale records) producing a fix list, and import-clean (normalize and dedupe a CSV against existing data before import). Use when the user wants to clean the CRM, find duplicates, or prepare an import.
---

# pd-data-hygiene

Follow pd-core rules (load pd-core if not loaded).

Requires: Pipedrive (audit). import-clean works on a CSV alone, Pipedrive optional for the dedupe check.
Fallback: no filesystem -> fix list in chat (max 20 rows) and a downloadable CSV

The connector cannot delete or merge. Output is a fix list; the user merges in Pipedrive (Contacts > Merge). Claude may only fill empty fields, after confirmation.

## Mode: audit

1. Scope: persons, orgs, open deals. Large account: ask to limit (one owner, or `updated_since` last 12 months).
2. Fetch: `getPersons limit=500` (cursor for more, cap 2000), `getOrganizations limit=500`, `getDeals status=open limit=500 include_fields=[next_activity_id,undone_activities_count]`.
3. Duplicates: save results to files and run `scripts/find_dupes.py persons.json` and `scripts/find_dupes.py orgs.json --kind org`. No shell: compare exact email/phone and normalized names only.
4. Gaps: persons without email and phone, orgs without owner or address (if the industry needs it), deals without value, expected close date, or next activity. Required fields from the industry pack.
5. Stale: open deals idle more than 90 days (suggest close or revive), persons with no activity in 12 months.
6. Output a summary + `pipedrive-out/pd-data-hygiene/<date>-fixlist.csv` with columns `type,id,name,issue,suggested_fix,related_id`.
7. Offer safe fills only: missing org on a person when the email domain matches exactly one org; missing country from phone prefix. Show change set, write on yes.

## Mode: import-clean

1. Read the CSV. Detect columns; map to Pipedrive fields (show mapping, ask to confirm).
2. Normalize: trim, title-case names, lowercase emails, E.164 phones when the country is known, country names to one form, split full names when asked.
3. Dedupe inside the file (`scripts/find_dupes.py file.csv`), then against Pipedrive with `searchPersons` by email for up to 50 rows (more: say so, sample).
4. Output `pipedrive-out/pd-data-hygiene/<date>-import-clean.csv` + `<date>-import-issues.csv`. Recommend Pipedrive's own importer for large files; offer to add up to 25 rows via MCP (safe-write) for small ones.

## Output

```
Audit <date> | persons 1,240 | orgs 410 | open deals 186
Likely duplicates: 37 person pairs, 9 org pairs
Missing: 112 persons no email/phone, 41 deals no next step, 18 deals no value
Stale: 23 open deals idle 90+ days
Fix list: pipedrive-out/pd-data-hygiene/2026-10-13-fixlist.csv
Safe fills available: 14 persons -> org by email domain. Apply?
```
