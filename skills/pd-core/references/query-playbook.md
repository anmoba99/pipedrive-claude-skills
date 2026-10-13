# Query playbook

Tool names below are base names. In your session they may carry a prefix (for example `mcp__pipedrive__getDeals`). Match by base name.

## Relative cost (from the connector's own tool descriptions)

- Cheapest: `getDeal`, `getPerson`, `getOrganization`, `getLead`, `getActivity`, `getNote`, `getStage`, `getAccountContext`.
- High: `getDeals`, `getActivities`, `getNotes`, `getPersons`, `getOrganizations`, `getLeads`.
- Very high: `searchDeals`, `searchPersons`, `searchOrganization`, `searchLeads`, `searchProducts`.

Search only when you have a name and no ID. Use `exact_match: true` when the user gives a full name. Set `limit` low (5).

## Useful parameters

`getDeals`
- `owner_id`, `pipeline_id`, `stage_id`, `status` (open, won, lost), `org_id`, `person_id`
- `updated_since` / `updated_until` (RFC3339) for incremental runs and date windows
- `custom_fields`: only the keys you need (max 15)
- `include_option_labels: true`: dropdown values come back as `{id, label}` instead of bare IDs. Use it whenever option values are shown to the user.
- `include_fields`: `next_activity_id`, `last_activity_id`, `undone_activities_count`, `notes_count`, `last_incoming_mail_time`, `last_outgoing_mail_time`, `products_count`
- `sort_by` (`update_time`, `add_time`, `id`) + `sort_direction`
- `limit` up to 500, `cursor` for next page
- `filter_id`: reuse a saved Pipedrive filter the user already built. Cheapest way to express complex criteria.
- `ids`: fetch up to 100 known deals in one call instead of many `getDeal` calls.

`getActivities`
- `owner_id`, `deal_id`, `person_id`, `org_id`, `lead_id`, `done` (true/false)
- `sort_by: due_date`, `updated_since`, `limit`

`getNotes`
- `deal_id`, `person_id`, `org_id`, `lead_id`, `start_date`, `end_date`, `updated_since`
- `sort: "add_time DESC"`, `limit` (5 to 20 is usually enough)

`getPersons` / `getOrganizations`
- `owner_id`, `org_id`, `updated_since`, `custom_fields`, `include_fields` (counts, last mail times)

## Patterns

- "My open deals": `getDeals owner_id=<me> status=open limit=200 include_fields=[next_activity_id,undone_activities_count]`.
- "Deals idle 14+ days": `getDeals status=open updated_until=<today-14d>`. Cheaper than pulling everything and filtering.
- "What changed since last run": `updated_since=<last_run>` from `.pipedrive/last_run.json`.
- "Everything about one deal": `getDeal`, then `getNotes deal_id limit=10`, `getActivities deal_id`, `getPersons deal_id`. Four calls total.
- "Account rollup": `getOrganization`, `getDeals org_id`, `getNotes org_id limit=10`.
- Many known IDs: one `getDeals ids=[...]` call.
- Big pipeline (500+ open deals): split by owner or stage. In Claude Code, run one subagent per slice and have each return at most 10 summary lines so raw data stays out of the main context.

## What a call returns

MCP results enter the context in full. Filters and field selection are the only way to shrink input. Scripts help with accurate math and short output, not with the size of what was fetched.
