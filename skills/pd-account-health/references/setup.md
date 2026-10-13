# Account management setup

pd-setup asks "Do you manage existing customers in Pipedrive?" On yes, it maps these keys into `accounts` in `.pipedrive/config.json`. Match fields by name from the account context, show the mapping, confirm. Never guess a key.

```json
"accounts": {
  "enabled": true,
  "customer_rule": "won_or_field",
  "csm_field": null,
  "tier_field": "<org field key>",
  "segment_field": null,
  "arr_field": "<org money field key>",
  "renewal_field": "<org date field key>",
  "renewal_pipeline_id": null,
  "expansion_pipeline_id": null,
  "health_field": null,
  "health_date_field": null,
  "role_field": "<person option field key>",
  "anniversary_renewals": true,
  "weights": {"touch": 30, "trend": 20, "next_step": 20, "coverage": 20, "breadth": 10}
}
```

- `customer_rule`: `won` (org has a won deal) or `won_or_field` (also orgs with tier or revenue filled).
- `csm_field`: a user field on the org when the account manager is not the org owner. Null = org owner.
- `arr_field`: money or number field. Null = won deal value of the last 12 months.
- `renewal_field`: date field on the org. Else open deals in `renewal_pipeline_id` (expected close date). Else the anniversary of the first won deal, when `anniversary_renewals` is true.
- `health_field`: number field (score 0-100) or single option field with options named Green, Amber, Red. `health_date_field`: date field. Both only for write-back. Leave null to keep the CRM untouched.
- `role_field`: person option field like "Role in account" (Decision maker, Champion, User).

## Recommended Pipedrive setup (manual, the connector cannot create fields or pipelines)

1. Organization fields: Tier (single option), ARR or Contract value (monetary), Renewal date (date), Health score (numeric), Health updated (date).
2. Person field: Role in account (single option: Decision maker, Champion, User, Billing).
3. Pipelines: Renewals (stages: Upcoming, In talks, Committed, Renewed) and Expansion. New deals there carry the org, so renewals and upsell show in forecasts too.
4. Optional: a filter "Health score below 40" and an automation that creates an activity for the account owner when Health score changes.

## Fetching (portfolio)

Large books run in batches by account manager (`pd-core/references/batches.md`). Use the slim calls below, cursor through every page, and save each page to `pipedrive-out/pd-account-health/raw/<entity>-<n>.json`. In Claude Code, one subagent per entity (or per account manager when one entity passes about 20,000 records), each replying with one line. On claude.ai, cap about 1,000 orgs and say so.
- Orgs: `getOrganizations limit=500 include_fields=[people_count,open_deals_count,won_deals_count,next_activity_id]`, `custom_fields=[<mapped org keys>]`. Large accounts: `owner_id=<csm>` slices.
- Deals: `getDeals status=[won,open] limit=500`, `custom_fields` only the mapped deal keys (max 15), else omit.
- Activities: `getActivities done=true updated_since=<today minus 180 days> limit=500`.
- People: `getPersons limit=500 custom_fields=[<role_field>]`. Large accounts: only with `updated_since` 24 months, or skip and use `people_count` (coverage then has no roles).
- Products (optional): `getDealsProducts deal_ids=[<up to 100 won deal ids>]`, batched, won deals of the last 24 months.
