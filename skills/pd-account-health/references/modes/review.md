# Mode: review

Account review or QBR brief for one org.

1. Fetch (max 6 calls): `getOrganization` (include_fields), `getDeals org_id` (all statuses), `getActivities org_id done=true limit=50`, `getPersons org_id`, `getNotes org_id sort="add_time DESC" limit=20`, `getDealProducts` for won deals.
2. Run `scripts/account_rollup.py` on the files for score and drivers.
3. Brief:
   - History: first won date, deals won and value per year, products.
   - Health: score, the 5 drivers with values, what changed since the last review if a previous `portfolio.json` exists.
   - People: who, role, last touch. Gaps by role.
   - Open items: open deals, overdue activities, promises in notes (quoted, dated).
   - Renewal: date and source.
   - Agenda (5 points): results so far, open issues, their plans, renewal or expansion, next steps with owners.
   Facts only, inference marked "likely".
4. Route: Google Doc if live, else chat. Offer a pinned `[Claude]` note on the org with the agenda (after confirm).
