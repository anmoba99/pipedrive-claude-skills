# Pipedrive Skills for Claude

Free, open skills that turn Claude and the Pipedrive connector into a sales assistant shaped around your business.

Describe your business in plain English. Claude replies with a short plan (which skills to use, what to set up once, what to run daily or weekly) and then runs it for you.

> Community project. Not an official Pipedrive or Anthropic product. Review every change before Claude writes to your CRM.

## Contents

- [Quick start](#quick-start)
- [Install](#install)
- [The skills](#the-skills)
- [Example](#example)
- [Safety](#safety)
- [Known limits](#known-limits)
- [FAQ](#faq)

## Quick start

1. Install the skills (see [Install](#install)).
2. Connect **Pipedrive** in Claude. Optional: Slack or Teams, Gmail or Outlook, Google Drive, Google Calendar.
3. Start a chat and describe your business. `pd-advisor` replies with your plan.
4. Run `pd-setup` once. It caches your pipelines, stages and fields so later requests are faster and cheaper.
5. Ask in normal words: "brief me for today", "prep my call with Acme", "review the pipeline for this week".

## Install

### Claude app (claude.ai, Desktop, Cowork)

1. Download the skill zips from the [latest release](https://github.com/anmoba99/pipedrive-claude-skills/releases/latest).
2. In Claude, open **Settings > Capabilities > Skills** and upload each zip. At minimum: `pd-core`, `pd-advisor`, `pd-setup`. Add any others you want.
3. Open **Settings > Connectors** and connect **Pipedrive** with your own account.

On Team and Enterprise plans an admin can upload skills and enable connectors for the whole organization.

### Claude Code

```bash
claude plugin marketplace add anmoba99/pipedrive-claude-skills
claude plugin install pipedrive-skills@pipedrive-claude-skills
```

Connectors added on claude.ai also work in Claude Code when you sign in with the same account. Otherwise add a Pipedrive MCP server with `claude mcp add` and keep any API token in an environment variable.

## The skills

All skills live in [`skills/`](skills). Start with `pd-advisor`; it picks the rest for you.

| Skill | What it does | Writes to Pipedrive | Optional connectors |
|---|---|---|---|
| `pd-advisor` | Reads your business case, returns a plan | No | |
| `pd-core` | Shared rules for every skill: cheap queries, short output, safe writes | No | |
| `pd-setup` | One-time setup and health check; caches pipelines, stages, fields, users | No | |
| `pd-ask` | Answers any question about your CRM | No | |
| `pd-morning-brief` | Today's activities, overdue work, idle deals, top 3 actions | No | Calendar, Slack |
| `pd-call-prep` | One-page brief before a call or meeting | No | Calendar |
| `pd-call-to-crm` | Turns a conversation into field updates, next steps and a stage suggestion; builds on Nova call summaries | After you confirm | |
| `pd-follow-up` | Drafts follow-up emails from deal context; never sends | Optional note | Gmail, Outlook |
| `pd-lead-qualifier` | Scores leads with BANT, MEDDICC, CHAMP or your own checklist | After you confirm | |
| `pd-pipeline-review` | Manager review, forecast check, weekly owner digest | No | Slack, Teams, Docs |
| `pd-win-loss` | Why you win and lose, from lost reasons and notes | No | Docs |
| `pd-data-hygiene` | Duplicates, missing fields, deals with no next step, CSV import cleanup | Fills blanks, after you confirm | |
| `pd-account-health` | Account health, renewals, sales to customer success handoff | Optional note | Docs |
| `pd-industry` | Industry packs: vocabulary, stage templates, qualification, signals | No | |

Pipedrive is the only required connector. If an optional one is missing, the skill still works and puts the output in the chat, a Pipedrive note or a file.

**Industry packs:** real estate, SaaS, agencies, manufacturing and wholesale, recruiting, financial services and insurance, construction and home services, education, healthcare and medtech, events and hospitality, nonprofits, logistics. Each is a small file loaded only when needed.

**Built to save tokens:** setup is cached, every query is filtered at the source, daily and weekly runs fetch only what changed, and totals and duplicate matching run in small Python scripts instead of in Claude's head.

## Example

You type:

> We are a 6 person real estate agency in Lisbon. Agents forget to follow up after viewings and I have no idea which buyers are serious. We use Pipedrive and Gmail.

Claude replies (short on purpose):

```
Case: 6-agent real estate agency, follow-up gaps after viewings, weak buyer qualification.
Pain -> fix:
- No follow-up after viewing: pd-call-to-crm logs viewing notes, creates next-step activity same day.
- Unknown serious buyers: pd-lead-qualifier scores buyers (budget, financing, timeline).
- Owner blind spot: pd-pipeline-review digest every Monday.
Setup (once):
1. pd-setup, industry = real-estate.
2. Add custom fields: Budget, Mortgage pre-approved, Move-in date (manual in Pipedrive).
Rhythm:
- Daily: each agent "brief me for today" (pd-morning-brief).
- After each viewing: paste notes, "log this viewing" (pd-call-to-crm).
- Weekly: "weekly digest" (pd-pipeline-review).
Try now: "Run pd-setup for a real estate agency"
```

## Safety

- Claude never writes to Pipedrive without showing you the change first and getting a yes.
- Every note Claude writes starts with `[Claude]`, so your team can filter and review them.
- No deletes. Hygiene skills give you a fix list; you merge or delete in Pipedrive.
- Nothing is posted to Slack or sent by email unless you turn it on. Email is always a draft.
- Claude sees only what your Pipedrive user can see. Team reports need a manager or admin account.
- Skills never see or store passwords or tokens. Each user signs in to each connector with their own account.

## Known limits

- The connector cannot create pipelines, stages or custom fields. Skills tell you what to add by hand.
- Large pipelines (thousands of open deals) are slower. Filter by pipeline or rep.
- On claude.ai the setup cache lasts one conversation. In Claude Code, Desktop and Cowork it is saved to `.pipedrive/`.

## FAQ

**Do I need to code?** No. Install, connect, and talk to Claude in normal words.

**Does it work in my language?** Yes. Write in your language and Claude answers in it.

**I only want one skill.** Install `pd-core` plus that skill.

**Can I customize it?** Yes. Each skill is a plain text `SKILL.md` plus reference files. Edit them.

**Why are the advisor answers so short?** Short answers cost less and read faster. Say "normal mode" for full sentences.

## Contributing

Issues and pull requests are welcome: new industry packs, translations, skill improvements. Keep skills short, never hardcode MCP tool names, and confirm every write.

## License

MIT. See [LICENSE](LICENSE).
