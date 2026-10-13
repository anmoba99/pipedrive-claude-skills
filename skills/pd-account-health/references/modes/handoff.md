# Mode: handoff

1. Won deal named or found. Fetch `getDeal`, `getNotes deal_id limit=20`, `getPersons deal_id`, `getDealProducts`.
2. Brief: what they bought, why they bought (in their words), promises made, people and roles, risks, success criteria, first 30 days plan. Facts only; inference marked "likely".
3. Route: Google Doc if live, else chat; offer a pinned org note.
4. If `csm_field` is mapped and empty on the org, offer to set it (`updateOrganization`, after confirm).
