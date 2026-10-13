---
name: pd-access
description: Check what Claude can and cannot see or change in Pipedrive with the current connection (connector permissions, who "me" is, how many owners' deals are visible, deal visibility settings, read-only fields) and give the exact fix for each gap. Use when team reports look incomplete, Claude does not know who the user is, or before rolling the skills out to a team. Read-only.
---

# pd-access

Follow pd-core rules (load pd-core if not loaded).

Requires: Pipedrive. Read-only: never writes to the CRM.
Run by pd-setup on first setup. Run again when results look partial.

Pipedrive access has two layers: what the connector was allowed to read (permissions granted when it was connected), and what the user's Pipedrive login can see (permission sets and visibility groups set by an admin). Claude only ever sees the overlap.

## Checks

1. **Connector permissions.** Use the account context (cached or one `getAccountContext`). Read its `errors` object. Map each error:
   | Error mentions | Effect | Skills affected |
   |---|---|---|
   | `base` (user) | Claude does not know who "me" is | "my deals", pd-morning-brief, pd-follow-up sender |
   | `users:read` (companyUsers) | No user list, owners show as IDs | pd-pipeline-review by rep, pd-win-loss by rep, team digests |
   | `products:read` (productFields) | No product fields or catalog | product questions in pd-ask, deal value checks |
   Fix: "In Claude, open Settings > Connectors, disconnect Pipedrive, connect again and accept every permission it asks for. If your company limits app access, ask a Pipedrive admin to allow it."
   Missing "me" fallback: ask the user for their name as shown in Pipedrive, find a deal they own (`searchDeals` on a deal they name, or `getDeals limit=50` and ask which are theirs), take its `owner_id`, and save `me` in `.pipedrive/context.json` (or keep it for the conversation). Never guess.
2. **Record coverage.** `getDeals status=open limit=500` with no owner filter (cursor once more if `next_cursor` and the user wants the full picture). Count distinct `owner_id` and the `visible_to` mix: 1 owner only, 3 owner's visibility group, 5 group and sub-groups, 7 everyone. If the user list is known, compare owners seen with users that exist.
   - Only one owner visible while the team has more people: team reports cover only those deals.
   - Many `visible_to=1` deals: managers may miss them. Fix: change visibility on those deals, or ask an admin to review default visibility in the visibility group settings.
3. **Field access.** From the account context, list custom fields with `is_writable=false`. Skills never try to update them.
4. **Role fit.** Role from `.pipedrive/config.json` (or ask). Manager or owner with partial coverage: "Team reports will only cover what this Pipedrive user can see. Use a user whose permission set and visibility group include the team."
5. **What Claude cannot check.** Say once, as a short list for an admin: permission set of this user (Company settings > Manage users > Permission sets), visibility group and default visibility (Company settings > Visibility groups, on plans that have it), whether the user can export, delete or merge (the connector never deletes or merges anyway).

## Save

Write `.pipedrive/access.json` (or keep in conversation):
```json
{"checked": "<ISO date>", "me": {"id": 0, "known": true},
 "missing_scopes": ["users:read"], "owners_visible": 3, "users_known": 6,
 "visible_to": {"1": 4, "3": 10, "7": 120}, "read_only_fields": ["<key>"],
 "coverage": "full | partial | own_only"}
```
`coverage`: own_only if only the user's deals are visible, partial if fewer owners than users or many owner-only deals, full otherwise (or unknown when the user list is missing; say so).

## Output

```
Access check 2026-10-13
Connector: warn | missing users:read, base -> reconnect Pipedrive in Settings > Connectors, accept all permissions
Me: warn | not returned -> found via your deals: user 1234567
Coverage: ok | 4 owners, 186 open deals visible
Visibility: warn | 14 deals owner-only -> managers miss them; check default visibility
Fields: ok | 2 read-only custom fields skipped
Role: ok | manager, team reports reliable for the 4 owners above
Ask an admin: permission set and visibility group for this user
```
One line per check: `ok`, `warn` or `blocked`, then the fix. Keep it under 10 lines.
