# Mode: health

1. Scope: one org (search), or a list. More than 30 accounts: run portfolio mode and answer from its output.
2. Per org (max 4 calls): `getOrganization` with include_fields from `../setup.md`, `getDeals org_id`, `getActivities org_id done=true limit=50`, `getPersons org_id`. Save to files, run `scripts/account_rollup.py` on them (same flags as portfolio, no `--html`). The score is the script's, never estimated.
3. Notes, max 10 orgs per run: `getNotes org_id sort="add_time DESC" limit=5`. Read for signals only, do not change the score:
   - Upsell: growth, new teams, new locations, extra volume, other products.
   - Churn: complaints, champion left, budget cuts, competitor mentions, silence after a question.
   Quote short fragments with the note date.

Output:
```
<org> | score 62 (amber) | last touch 41d | open deals 1 | people 2 | products 2
Why: <script reasons>
Signals: + "opening second warehouse" (note 2026-09-02) | - no reply to last 2 emails
Next: <one action>
```
