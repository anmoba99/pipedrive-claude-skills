# Mode: renewals

1. Renewal date, in order: `renewal_field` on the org, open deals in `renewal_pipeline_id` (expected close date), anniversary of the first won deal. The script tags the source (`field`, `pipeline`, `anniversary`); say when dates are anniversaries, they are guesses.
2. Window default 90 days. Small scope: health mode fetch. Large scope: portfolio run, then read `renewals` from `portfolio.json`.
3. Risk = score bucket plus "nothing planned" (no next activity and no open renewal deal). Read notes for the top 10 by revenue at risk only.
4. Sort by date, then risk. Suggest: open a renewal deal in the Renewals pipeline for each renewal with nothing planned (`addDeal`, after confirm, one list for all).

Output:
```
Next 90 days: <n> renewals | <value per currency> | <n> at risk | <n> nothing planned
- <date> | <org> | <value> | <owner> | score <n> (<bucket>) | <why or signal>
```
