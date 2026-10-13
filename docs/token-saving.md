# Token saving

Every Pipedrive result goes into Claude's context in full. Big results cost money, slow answers down and push useful context out. These are the rules the skills follow, and the ones to keep if you write your own.

## 1. Cache account context

`getAccountContext` returns pipelines, stages, users and every custom field. It is large. `pd-setup` calls it once and saves a slim version to `.pipedrive/context.json` and `.pipedrive/field-map.json`. Other skills read those files. Refresh weekly or when a field error shows up.

On claude.ai there is no saved folder between chats, so it is fetched once per conversation.

## 2. Pick the cheapest call

The connector's own tool descriptions rank cost: single-record gets are cheap, lists are high, searches are very high. So:

- Have an ID: use `getDeal`, not search.
- Many IDs: one `getDeals ids=[...]` call (up to 100).
- Complex criteria: reuse a saved Pipedrive filter with `filter_id`.
- Search only with a name and no ID, with a low `limit`.

## 3. Filter at the source

Always set some of `owner_id`, `pipeline_id`, `stage_id`, `status`, `updated_since`, and a `limit`. Ask only for the custom fields you need (`custom_fields`, max 15).

## 4. Incremental runs

Daily and weekly skills store the last run time in `.pipedrive/last_run.json` and fetch with `updated_since`.

## 5. Notes last, and few

Notes are the biggest text. Fetch them only for the handful of deals that need reading (top risks, the deal you are prepping), with `limit` 3 to 10.

## 6. Short output

Fixed one-line formats, max 20 rows in chat, files for the rest. No raw JSON echo. Short output also means short follow-up context.

## 7. Scripts for math

`pd_digest.py` (totals, grouping, flags) and `find_dupes.py` (duplicates) run in Python. Claude reads a few summary lines instead of reasoning over hundreds of records. Scripts reduce reasoning and output tokens and avoid math errors; they do not shrink what was fetched.

## 8. Split big jobs

In Claude Code, large reviews run one subagent per owner or stage. Each returns up to 10 lines, so the raw data never reaches the main conversation.

## 9. Small skills

Each skill description is loaded in every conversation, so descriptions are one or two sentences. Skill bodies stay short. Industry packs and frameworks are separate files loaded only when needed.

## 10. Short answers by default

`pd-advisor` answers in a compressed style. Say "normal mode" for full sentences.
