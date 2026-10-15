# Mode: portfolio

Book of business for one account manager, a team, or the whole company. Built for thousands of accounts.

1. Load `accounts` from config (see `../setup.md`). Scope: "my book" = `csm_field` or org owner = me; team or all needs manager visibility (pd-access).
2. Size check: one `getOrganizations limit=500` page. More than one page: tell the user the rough call count (orgs, deals, activities, people, products) and continue unless they stop.
3. More than one batch of records (see `pd-core/references/batches.md`): run in batches by account manager, biggest book first. One batch = orgs, deals and activities of the same account managers, so each account is scored from its own data. Scores of accounts with deals or activities owned by someone in a later batch can still move; peer medians and whitespace are final after the last batch. Say so on partial results.
   Fetch as in `../setup.md` "Fetching". Save raw pages to files. Never paste raw pages into chat. Large accounts: follow `pd-data-hygiene/references/scale.md` (subagents, slices, caps).
4. Run:
```bash
python3 scripts/account_rollup.py \
  --orgs 'pipedrive-out/pd-account-health/raw/orgs-*.json' \
  --deals 'pipedrive-out/pd-account-health/raw/deals-*.json' \
  --activities 'pipedrive-out/pd-account-health/raw/activities-*.json' \
  [--persons 'pipedrive-out/pd-account-health/raw/persons-*.json'] \
  [--products 'pipedrive-out/pd-account-health/raw/products-*.json'] \
  --config .pipedrive/config.json --context .pipedrive/account_context.json --field-map .pipedrive/field-map.json \
  [--prev pipedrive-out/pd-account-health/portfolio.json] \
  --scope-note "<what was not fetched>" \
  --out pipedrive-out/pd-account-health/portfolio.json \
  --csv-out pipedrive-out/pd-account-health/<date>-accounts.csv \
  [--writeback-out pipedrive-out/pd-account-health/<date>-writeback.json] \
  --html references/portfolio.html --html-out pipedrive-out/pd-account-health/<date>-portfolio.html
```
   Copy the previous `portfolio.json` to a dated name before the run and pass it as `--prev`, so score changes and write-back work.
5. Page: tabs Portfolio (tiles, by account manager, by tier, score weights), Accounts, Renewals (90 days), Coverage, Whitespace. Click an account manager to filter every tab. Up to 3,000 accounts on the page, most at risk first, every account in the CSV. On claude.ai publish the HTML as an artifact.
6. Chat summary, max 8 lines:
```
Accounts <n> | red <n> | amber <n> | green <n> | revenue <per currency>, at risk <value>
Renewals 90d: <n>, <n> at risk, <n> with nothing planned
Top 3: <org> (<why>), <org> (<why>), <org> (<why>)
Coverage: <n> single-threaded | Whitespace: <best product gap>
Page: <path or artifact> | CSV: <path>
```
7. Offer: notes read for the top 10 red or renewing accounts (health mode step 3), write-back if `health_field` is set (SKILL.md), a review brief for one account.

Rhythm: weekly per account manager, monthly for the whole book.
