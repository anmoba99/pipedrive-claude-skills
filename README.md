<div align="center">

# Pipedrive Skills for Claude

**Tell Claude about your business. Get a sales assistant that works inside your Pipedrive.**

<a href="https://github.com/anmoba99/pipedrive-claude-skills/releases/latest"><img src="https://img.shields.io/github/v/release/anmoba99/pipedrive-claude-skills?style=flat-square&color=1A7F37&label=release" alt="Latest release"></a>
<a href="./INSTALL.md"><img src="https://img.shields.io/badge/works_with-Claude_app_%26_Claude_Code-D97757?style=flat-square" alt="Works with Claude app and Claude Code"></a>
<a href="#license"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT license"></a>

<table>
<tr>
<td align="center" width="33%"><h3>1 message</h3>to start: describe your business,<br>get a plan built for it</td>
<td align="center" width="33%"><h3>0 changes</h3>to your CRM<br>without your yes</td>
<td align="center" width="33%"><h3>19 skills</h3>plus 12 industry packs,<br>free and open</td>
</tr>
</table>

**[What changes](#what-changes) · [Install](#install) · [What you get](#what-you-get) · [How it starts](#how-it-starts) · [Safety](#safety)**

</div>

> **Disclaimer:** these skills were built by me in a personal capacity. They are not an official Pipedrive product and are not endorsed, maintained or supported by Pipedrive. Always review changes before letting Claude update your CRM.

---

## What changes

Pipedrive stores your deals well. The work around them still eats your day. These skills hand that work to Claude.

| Moment | Without | With these skills |
|---|---|---|
| **Monday, 8:30** | Open Pipedrive, scroll 60 deals, guess what matters | "brief me for today": overdue work, idle deals, your top 3 actions |
| **Following up** | Write the same nudge email again | A draft built from the deal, waiting in Gmail or Outlook. Never sent for you |
| **Which leads are real** | Gut feeling | Each lead scored with BANT, MEDDICC, CHAMP or your own checklist, plus the next question to ask |
| **Pipeline review** | Export to a sheet, chase reps for updates | "forecast check": stuck deals, slipping close dates, stage vs real activity |
| **Why you lose** | Lost reason says "Price" | Patterns from the notes your team actually wrote |
| **Messy data** | Find duplicates when reports break | A data health page: how full every field is, empty custom fields, duplicates, deals with no next step, and what improved since last time |
| **Account management** | A spreadsheet of customers, renewals found too late | "show my book": every account scored, renewals in the next 90 days, single-threaded accounts, what peers buy that they do not. Optional health score saved back to Pipedrive |
| **Which deals will slip** | Find out at quarter end | "premortem": each open deal matched to the lost deals it looks like, how it will most likely die, and the move that saves it |
| **What actually wins** | A playbook nobody follows, written from memory | The path your won deals really took: steps, order, timing, contacts. Open deals that are off it |
| **One contact per deal** | Your champion leaves, the deal dies | Who is involved, their role read from notes, single-threaded deals, past champions now at other companies |
| **Lost deals** | Gone forever | Which lost deals to reopen now and why now (timing came around, contract renewal, contact moved), with a draft built from the old conversation |
| **Who to target** | ICP written in a workshop | The customer profile your wins point to, the segments that waste time, and every open deal and lead scored by fit |
| **CRM setup** | Stages and fields nobody questions | A blueprint from real usage: stages to merge or split, fields nobody fills, fields hiding in notes, lost reason picklist, automations worth building |
| **Who sees what** | Reports quietly miss deals you cannot see | "what can Claude see?": missing permissions, owner-only deals, and the exact fix |

Ask in your own words and your own language. No setup screens, no code.

## Install

**Claude app** (claude.ai, Desktop, Cowork): download the zips from the [latest release](https://github.com/anmoba99/pipedrive-claude-skills/releases/latest), upload them in **Settings > Capabilities > Skills**, then connect Pipedrive in **Settings > Connectors**.

**Claude Code:**

```bash
claude plugin marketplace add anmoba99/pipedrive-claude-skills
claude plugin install pipedrive-skills@pipedrive-claude-skills
```

Full steps, team rollout and troubleshooting: [INSTALL.md](./INSTALL.md).

## What you get

Start with `pd-advisor`. It picks the rest for you.

| Skill | Say something like | You get |
|---|---|---|
| `pd-advisor` | "We're a 6 person agency, deals go quiet after proposals" | A short plan: which skills, what to set up once, daily and weekly rhythm |
| `pd-setup` | "set up Pipedrive" | Claude learns your pipelines, stages, users and fields once, so every later ask is faster |
| `pd-morning-brief` | "brief me for today" | Today's activities, overdue work, idle deals, top 3 actions |
| `pd-follow-up` | "draft a follow-up for Acme" | An email draft from the deal context |
| `pd-lead-qualifier` | "which leads are serious?" | Scored leads, missing info, next question |
| `pd-pipeline-review` | "weekly digest" | Review by rep and stage, forecast check, owner summary |
| `pd-win-loss` | "why are we losing deals?" | Win and loss patterns from lost reasons and notes |
| `pd-data-hygiene` | "clean my CRM" | A data health page with tabs (field completeness, empty values, duplicates, no next step, value at risk, by owner and pipeline, trend), a fix list, CSV import cleanup. Works on large accounts: samples fields, checks every open deal, trends over runs |
| `pd-access` | "what can Claude see?" | Connector permissions, whose deals are visible, owner-only deals, read-only fields, exact fixes |
| `pd-account-health` | "show my book" | A portfolio page per account manager (health score, revenue, renewals, coverage, upsell whitespace), QBR briefs, sales to customer success handoff. Optional health score write-back to a Pipedrive field you choose |
| `pd-premortem` | "which deals will we lose?" | Each open deal vs the lost deals it resembles: cause of death, proof, likely date, save move |
| `pd-playbook-miner` | "what do our wins have in common?" | A playbook mined from won deals (steps, order, timing, contacts), what losses skipped, open deals off track |
| `pd-thread-map` | "who is involved in the Acme deal?" | Buying group with roles from notes, single-threaded deals, silent champions, past champions at new companies |
| `pd-ghost-reviver` | "which lost deals should we reopen?" | Lost deals worth a call now, the reason why now, a re-opener draft from the old conversation |
| `pd-icp-discovery` | "who is our ideal customer?" | Win rate, value and cycle by segment, the profile that wins, the segments to stop chasing, fit score for open deals and leads |
| `pd-crm-architect` | "is our Pipedrive set up right?" | A before and after blueprint: stages, fields, picklists, required fields, automations, with manual steps for the admin |
| `pd-ask` | "how many deals did we win in March?" | A straight answer from your CRM |
| `pd-industry` | (used by the others) | How your industry sells: stages, vocabulary, qualification, risk signals |
| `pd-core` | (used by the others) | Shared rules: cheap queries, short answers, safe writes |

**Industry packs:** real estate, SaaS, agencies, manufacturing and wholesale, recruiting, financial services and insurance, construction and home services, education, healthcare and medtech, events and hospitality, nonprofits, logistics.

## How it starts

You type:

> We are a 6 person real estate agency in Lisbon. Agents forget to follow up after viewings and I have no idea which buyers are serious. We use Pipedrive and Gmail.

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

Short on purpose. Say "normal mode" for full sentences.

## Safety

- Claude **never writes to Pipedrive without showing you the change first** and getting a yes.
- Every note Claude writes starts with `[Claude]`, so your team can find and review them.
- No deletes. Cleanup skills give you a fix list; you merge or delete in Pipedrive.
- Email is always a draft. Nothing goes to Slack unless you turn it on.
- Claude sees only what your Pipedrive user can see. `pd-access` tells you what that is before a team report goes out. Skills never see or store passwords.

## Good to know

- Pipedrive is the only connector you need. Slack, Teams, Gmail, Outlook, Google Drive and Calendar are optional; without them, output lands in the chat or a Pipedrive note.
- Meetings, calls, WhatsApp and email: use Pipedrive's native tools (Nova, WhatsApp and email integrations). These skills build on the data they leave in Pipedrive.
- The connector cannot create pipelines, stages or custom fields. Claude tells you what to add by hand.
- Built to keep costs low: setup is cached, queries are filtered, answers are short, and math runs in small scripts.

## License

MIT. See [LICENSE](./LICENSE). Want to add an industry pack or improve a skill? See [CONTRIBUTING.md](./CONTRIBUTING.md).

---

<div align="center">
<sub>
<a href="./INSTALL.md">Install</a> ·
<a href="./CONTRIBUTING.md">Contributing</a> ·
<a href="./SECURITY.md">Security</a> ·
<a href="https://github.com/anmoba99/pipedrive-claude-skills/issues">Issues</a>
</sub>
</div>
