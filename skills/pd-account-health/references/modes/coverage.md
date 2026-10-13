# Mode: coverage

Who we know at each account.

1. Data: `people_count` from orgs, people with `role_field` if mapped, last activity per person from done activities.
2. Flags: single-threaded (0 or 1 person), no decision maker or champion (when roles are mapped), contacts with no activity in 90 days, accounts with no touch in 90 days.
3. More than 30 accounts: portfolio run, Coverage tab and the CSV.
4. Per account, suggest who to add by role, never by name you do not have. Persons are added only by the user or after confirm (`addPerson`).

Output:
```
Single-threaded: <n> of <accounts> (<revenue>) | no decision maker: <n> | cold 90d: <n>
- <org> | <tier> | <revenue> | people <n> | roles <list or none> | last touch <n>d
```
