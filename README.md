<div align="center">

# Pipedrive Skills for Claude (Unofficial)

<a href="https://github.com/anmoba99/pipedrive-claude-skills/releases/latest"><img src="https://img.shields.io/github/v/release/anmoba99/pipedrive-claude-skills?style=flat-square&color=1A7F37&label=release" alt="Latest release"></a>
<a href="./INSTALL.md"><img src="https://img.shields.io/badge/works_with-Claude_app_%26_Claude_Code-D97757?style=flat-square" alt="Works with Claude app and Claude Code"></a>
<a href="#license"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT license"></a>

</div>

Nineteen Claude skills that work on top of your Pipedrive. Free, MIT, no signup, no API key. The only thing to connect is the Pipedrive connector in Claude.

Pipedrive already runs a lot of your sales: pipelines and deals, the Leads Inbox, email and Campaigns, workflow automations, Insights reports and goals, Pipedrive AI and Nova for meetings, plus a Marketplace of apps for everything else. The [Pipedrive Knowledge Base](https://support.pipedrive.com/en) is full of tips worth knowing.

Some work usually means adding a third-party integration, an export or a BI tool: finding which open deals look like the ones you lost, the path your wins really took, which customer segments win most, who is really involved in each deal, which lost deals are worth reopening now. These skills do that directly in Claude, on your own Pipedrive data, so you get more out of the CRM you already use.

One of them briefs you every morning. One drafts the follow-up from the deal. One scores your leads. One tells you which open deals look like the ones you lost, and the move that saves them. One finds the customer profile your wins point to. One maps who is really involved in each deal.

And one is the advisor, which is where you start. Describe your business in one message and it picks the rest.

**Nothing changes in your CRM until you say yes.** Claude shows the change, you approve it.

> **Disclaimer:** these skills were built by me in a personal capacity. They are not an official Pipedrive product and are not endorsed, maintained or supported by Pipedrive. Always review changes before letting Claude update your CRM.
>
> Not affiliated with or endorsed by Anthropic either. Pipedrive is a trademark of Pipedrive OÜ, used here only to describe compatibility.

## Install

Paste this into Claude Code:

```
https://github.com/anmoba99/pipedrive-claude-skills

Install this plugin, then confirm /pd-advisor works.
```

Or do it yourself:

```bash
claude plugin marketplace add anmoba99/pipedrive-claude-skills
claude plugin install pipedrive-skills@pipedrive-claude-skills
```

**Claude app** (claude.ai, Desktop, Cowork): download the zips from the [latest release](https://github.com/anmoba99/pipedrive-claude-skills/releases/latest), upload them in **Settings > Capabilities > Skills** (at minimum `pd-core`, `pd-advisor` and `pd-setup`), then connect Pipedrive in **Settings > Connectors**.

Then spend two minutes on `pd-setup`. Say "set up Pipedrive" and Claude learns your pipelines, stages, users and fields once. Every other skill reads that, so later answers are faster and cheaper.

Full steps, team rollout and troubleshooting: [INSTALL.md](./INSTALL.md).

## The Basics

The daily work, done faster.

| skill | what it does |
| --- | --- |
| `pd-advisor` | Start here. One message about your business, back comes a plan: which skills, what to set up once, a daily and weekly rhythm. |
| `pd-setup` | Learns your account once: pipelines, stages, users, custom fields and dropdown labels. |
| `pd-morning-brief` | "Brief me for today." Activities, overdue work, idle deals, your top 3 actions. |
| `pd-follow-up` | A follow-up email drafted from the deal's history, waiting in Gmail or Outlook. Never sent for you. |
| `pd-lead-qualifier` | Scores leads on [BANT, CHAMP, MEDDICC](skills/pd-lead-qualifier/references/frameworks.md) or your own checklist, with the missing info and the next question to ask. |
| `pd-pipeline-review` | The weekly digest by rep and stage: stuck deals, slipping close dates, stage vs real activity. |
| `pd-ask` | Any question about your CRM in plain words. "How many deals did we win in March?" |
| `pd-access` | What Claude can see with your user, which deals are owner-only, and the exact fix before a team report goes out. |
| `pd-data-hygiene` | A data health page: how full each field is, duplicates, deals with no next step, progress since last run. Plus a fix list and CSV import cleanup. |

## The Intelligence

New ways to measure the data you already have, so you know where the next deal comes from.

| skill | what it does |
| --- | --- |
| `pd-premortem` | Matches every open deal to the closed deals it looks like, names how it will most likely die ([8 causes](skills/pd-premortem/references/obituary.md)), and the one move that changes the ending. |
| `pd-playbook-miner` | The path your won deals really took: steps, order, timing, contacts. What the losses skipped, and which open deals are off it. |
| `pd-icp-discovery` | Win rate, value and cycle by segment. The customer profile that wins, the segments to stop chasing, and every open deal scored by fit. |
| `pd-win-loss` | Why you win and lose, from lost reasons and the notes your team actually wrote. By owner, stage and value band. |
| `pd-thread-map` | Who is involved in each deal, tagged with [7 buying roles](skills/pd-thread-map/references/roles.md) from notes. Deals hanging on one person, past champions now at other companies. |
| `pd-win-back` | Lost deals worth a new conversation now, and why now ([9 reason classes](skills/pd-win-back/references/triggers.md) with timing windows). A new deal for the same company after your yes; the lost deal stays as it is. |
| `pd-account-health` | Your customer book in [7 modes](skills/pd-account-health/references/modes/): health score, renewals in the next 90 days, single-contact accounts, what similar customers buy that this one does not, review briefs, handoffs. |
| `pd-crm-architect` | A blueprint from real usage: stages to merge or split, fields nobody fills, fields hiding in notes, a lost reason picklist, automations worth building in Pipedrive. |

Two helpers run underneath: `pd-core` (cheap queries, short answers, safe writes) and `pd-industry`, with [12 industry packs](skills/pd-industry/references/): real estate, SaaS, agencies, manufacturing and wholesale, recruiting, financial services and insurance, construction and home services, education, healthcare and medtech, events and hospitality, nonprofits, logistics.

## How the intelligence works

The Intelligence skills ship small Python scripts with no dependencies. Claude fetches the records through your connector, saves them on your machine, and the script does the math there. Nothing is uploaded, and the numbers come from your data, not from a language model guessing.

| skill | what it measures |
| --- | --- |
| `pd-premortem` | Distance from each open deal to closed deals: stage, value, age, days in stage, idle days, activity pace, next step, unanswered email. Risk is the share of its nearest neighbours that were lost. |
| `pd-icp-discovery` | Win rate per attribute against your base rate (lift), with a minimum sample, then the strongest two-attribute combinations. Open deals get a 0 to 100 fit score. |
| `pd-playbook-miner` | Which activity types show up in wins vs losses, in what order, first-touch speed and the longest gap between touches. |
| `pd-thread-map` | Contacts per deal, how many were active in the last 90 days, people who sit on several open deals. |
| `pd-win-back` | Days since the loss against the window for its reason class, and whether the company already has an open deal. |
| `pd-account-health` | Revenue, activity, contact coverage and renewal dates rolled up per organization, compared with similar accounts. |
| `pd-data-hygiene` | Fill rate for every field, duplicates by email, phone and similar names, open value sitting on deals with no next step. |

Here is `icp_lift.py` on generated sample data (320 closed deals, made up for this demo, trimmed):

```
Closed 320 | won 155 | base win rate 48% | min sample 8
Best segments:
- origin=Referral | 88 deals | win 70% | lift 1.44 | avg won 11661 | cycle 45d
- Industry=Healthcare | 83 deals | win 65% | lift 1.34 | avg won 11963 | cycle 51d
Best combinations:
- Industry=Healthcare + origin=Referral | 29 deals | win 79% | lift 1.6
Worst segments:
- origin=Outbound | 79 deals | win 30% | lift 0.64
- Industry=Education | 97 deals | win 40% | lift 0.83
Scored 45 open deals and leads. Top fit:
deal 364 | Org 3 deal | fit 100 | origin=Referral, Industry=Healthcare
```

Claude turns that into the plain version: referrals from healthcare close at 79%, outbound at 30%, so here is where to spend next quarter, and here are the open deals that fit.

## How it starts

You type:

> We are a 6-person real estate agency in Lisbon. Agents forget to follow up after viewings and I have no idea which buyers are serious. We use Pipedrive and Gmail.

Claude replies:

```
Case: 6-agent real estate agency, follow-up gaps after viewings, weak buyer qualification.
Pain -> fix:
- No follow-up after viewing: pd-follow-up drafts the nudge from the deal, pd-morning-brief flags deals with no next step.
- Unknown serious buyers: pd-lead-qualifier scores buyers (budget, financing, timeline).
- Owner blind spot: pd-pipeline-review digest every Monday.
Setup (once):
1. pd-setup, industry = real-estate.
2. Add custom fields: Budget, Mortgage pre-approved, Move-in date (manual in Pipedrive).
3. pd-access, so the Monday digest covers every agent's deals.
Rhythm:
- Daily: each agent "brief me for today" (pd-morning-brief).
- After each viewing: "draft a follow-up for <buyer>" (pd-follow-up).
- Weekly: "weekly digest" (pd-pipeline-review).
Try now: "Run pd-setup for a real estate agency"
```

Short on purpose. Say "normal mode" for full sentences. Ask in your own words and your own language.

## The fine print, which is the honest part

**Every write needs your yes.** Claude shows the change set first: what changes, old value and new. Notes it writes start with `[Claude]` so your team can find them. There are no deletes: cleanup skills give you a fix list, and you merge or delete in Pipedrive.

**Email is always a draft.** Nothing is sent for you, and nothing goes to Slack or Teams unless you turn it on.

**The scores are patterns, not forecasts.** A risk of 80% means most deals that looked like this one were lost. It does not mean this one will be. The scripts need history to say anything, and say so when it is missing: the playbook miner will not write a playbook from fewer than 5 won deals with activities.

**Nothing is made up.** If an answer needs a number your CRM does not have, Claude says it is missing.

**Claude sees what your Pipedrive user sees.** No more. `pd-access` tells you exactly what that is. Skills never see or store passwords.

**Tested on sample data.** The scripts were checked on generated data, and several skills on a personal test account, not a company account. None of that data is in this repo, its history or the release zips. When you run a skill, your data stays in your Claude session, your drafts, or a local `pipedrive-out/` folder. More in [SECURITY.md](./SECURITY.md).

**Works alongside what Pipedrive already does.** Use Nova, the Pipedrive AI assistant, for meetings and calls, and the native WhatsApp and email integrations for conversations. These skills build on the data they leave in Pipedrive. Pipelines, stages and custom fields are created by an admin in Pipedrive; Claude tells you what to add.

## Files

```
skills/pd-premortem/scripts/deal_match.py           open deals vs the closed deals they resemble
skills/pd-icp-discovery/scripts/icp_lift.py         win rate and lift by segment, fit scores
skills/pd-playbook-miner/scripts/won_paths.py       activity paths of wins vs losses
skills/pd-thread-map/scripts/thread_graph.py        contacts and roles per deal
skills/pd-win-back/scripts/win_back_candidates.py   lost deals in their win-back window
skills/pd-account-health/scripts/account_rollup.py  per-account health, renewals, whitespace
skills/pd-data-hygiene/scripts/field_health.py      fill rates and the data health page
skills/pd-data-hygiene/scripts/find_dupes.py        duplicate people and organizations
skills/pd-crm-architect/scripts/usage_map.py        how stages and fields are really used
skills/pd-core/scripts/pd_digest.py                 pipeline digest numbers
skills/pd-setup/scripts/field_options.py            dropdown labels from a Pipedrive export
skills/pd-core/references/safe-write.md             the rules every write follows
```

## License

MIT. See [LICENSE](./LICENSE). Take it, change it, ship it. Want to add an industry pack or improve a skill? See [CONTRIBUTING.md](./CONTRIBUTING.md).

---

<div align="center">
<sub>
<a href="./INSTALL.md">Install</a> ·
<a href="./CONTRIBUTING.md">Contributing</a> ·
<a href="./SECURITY.md">Security</a> ·
<a href="https://github.com/anmoba99/pipedrive-claude-skills/issues">Issues</a>
</sub>
</div>
