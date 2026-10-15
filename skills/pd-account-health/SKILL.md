---
name: pd-account-health
description: "Account management on Pipedrive organizations: book of business per account manager, health scores, renewals, accounts with only one contact, products similar customers buy, account review (QBR) briefs and sales to customer success handoff. Optional health score saved to an organization field. Use for account health, churn risk, renewals, upsell, QBR or handoff requests."
license: MIT
metadata:
  version: "2.0.0"
---

# pd-account-health

Follow pd-core rules (load pd-core if not loaded).

Requires: Pipedrive
Optional: Google Docs (review, handoff)
Fallback: chat, optional pinned `[Claude]` note on the org (after confirm)

## Account model

Read `accounts` in `.pipedrive/config.json` (set by pd-setup, keys in `references/setup.md`). Missing: run the pd-setup accounts step, or continue with defaults and say so: accounts = orgs with a won deal, account manager = org owner, revenue = won value of the last 12 months, renewal = first won deal anniversary.

## Pick a mode

| User says | Mode | Load |
|---|---|---|
| "my book", "portfolio", "accounts at risk", "how are my accounts" | portfolio | `references/modes/portfolio.md` |
| "health of <org>", "score my accounts" | health | `references/modes/health.md` |
| "renewals this quarter", "what renews next" | renewals | `references/modes/renewals.md` |
| "single-threaded", "who do we know at", "contacts coverage" | coverage | `references/modes/coverage.md` |
| "upsell", "cross-sell", "what else could <org> buy" | whitespace | `references/modes/whitespace.md` |
| "QBR for <org>", "account review", "prep the business review" | review | `references/modes/review.md` |
| "handoff for <deal>", "brief CS on <deal>" | handoff | `references/modes/handoff.md` |

More than about 30 accounts in scope: use the portfolio flow (script) even for health, renewals, coverage or whitespace questions, then answer from its output.

## Scoring (same in every mode)

`scripts/account_rollup.py` scores 0-100 from facts: last touch 30%, activity trend 20%, next step planned 20%, people covered 20%, product breadth vs peers 10%. Green 70+, amber 40-69, red under 40. A driver with no data is left out and the others reweighted. Weights can be changed in `accounts.weights`. Always state the weights once. Notes are read by Claude only for the accounts the user asks about, capped at 10 per run, and quoted with dates.

## Write-back (opt-in)

Only when `accounts.health_field` is set. Always ask before writing.
1. Run the script with `--writeback-out`. It lists only accounts whose bucket changed or score moved 10+ points, max 200.
2. Show: count, 5 sample rows (org, old, new), the field names. Ask "Update these <n> organizations?"
3. On yes: `updateOrganization` with the `custom_fields` of each row. Log to `pipedrive-out/pd-account-health/<date>-writeback.log`. Stop on the first error and report.
4. Then say once: a Pipedrive filter on Health score plus an automation can create the follow-up activity for red accounts. Do not build that workflow in Claude.
