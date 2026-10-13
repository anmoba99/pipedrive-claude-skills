# Mode: whitespace

What peers buy that this account does not. Facts only.

1. Needs products: `getDealsProducts` for won deal ids (max 100 per call), last 24 months.
2. Peers: same tier, else same segment, else all accounts. Groups under 5 accounts are skipped.
3. A product counts when at least half the peer group owns it. The script lists accounts missing it, by revenue.
4. Say it as a fact: "8 of 10 Gold accounts bought Onboarding, Acme did not." Never claim the account needs it.
5. Suggest: an Expansion pipeline deal per top account (`addDeal`, after confirm).

Output:
```
<product> | <group>: <owned>/<members> own it | <n> missing, <revenue>
- <org> | <revenue> | score <n> | owner <name>
```
