# Pipedrive Skills for Claude

A free, open set of skills that turns Claude plus the Pipedrive connector into a sales assistant shaped around your business.

You install the skills, connect Pipedrive, and describe your business in plain English. Claude replies with a short, concrete plan: which skills to use, in what order, what to set up once, and what to run daily or weekly. Then it runs them for you.

> Community project. Not an official Pipedrive or Anthropic product. Use at your own risk and review every change before Claude writes to your CRM.

---

## Why this exists

Pipedrive is great at storing and filtering deals. It is weaker at the work around the data:

- reading call notes and turning them into clean fields, notes and next steps
- judging which deals are really at risk, not just which ones are old
- explaining why you lose deals, using the text your team actually wrote
- spotting duplicates and messy data before it hurts reports
- giving each person a short, ranked list of what to do today

Claude can do this work through the Pipedrive MCP connector. These skills give Claude a tested way of doing it: the right questions, the cheapest queries, safe writes, and short answers.

---

## How it works

1. **Install** the skills (5 minutes, see below).
2. **Connect** Pipedrive in Claude. Optional: Slack, Gmail, Google Drive, Calendar.
3. **Describe your business** to Claude in plain English. The `pd-advisor` skill replies with your plan.
4. **Run setup once** (`pd-setup`). It learns your pipelines, stages and custom fields so later requests are faster and cheaper.
5. **Use the plan.** Ask in normal words: "brief me for today", "prep my call with Acme", "review the pipeline for this week".

### Example

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
Output lands: notes + activities in Pipedrive, drafts in Gmail, digest in chat.
Needs: Pipedrive (live), Gmail (optional, live).
Can't do: MCP can't create custom fields. Add them once by hand.
Try now: "Run pd-setup for a real estate agency"
```

More examples in [examples/business-cases.md](examples/business-cases.md).

---

## Install

### Option A: Claude app (claude.ai, Desktop, Cowork)

1. Download the latest release zips from the `dist/` folder (or build them, see below).
2. In Claude, go to **Settings > Capabilities > Skills** and upload each zip. At minimum upload `pd-core`, `pd-advisor` and `pd-setup`, then any others you want.
3. Go to **Settings > Connectors** and connect **Pipedrive**. Sign in with your own Pipedrive account.
4. Optional: connect Slack, Gmail or Outlook, Google Drive, Google Calendar.
5. Start a new chat and describe your business.

On Team and Enterprise plans, an admin can upload skills and enable connectors for the whole organization.

### Option B: Claude Code

```bash
claude plugin marketplace add <github-owner>/pipedrive-claude-skills
```

```bash
claude plugin install pipedrive-skills@pipedrive-claude-skills
```

Connectors added on claude.ai are available in Claude Code when you sign in with the same account. Otherwise add a Pipedrive MCP server with `claude mcp add` and authenticate with `/mcp`.

### Build the zips yourself

```bash
./scripts/build-zips.sh
```

This creates one zip per skill in `dist/`.

---

## The skills

Start with **pd-advisor**. It picks the rest for you.

| Skill | What it does | Writes to Pipedrive? |
|---|---|---|
| `pd-advisor` | Reads your business case, returns a plan using the skills below | No |
| `pd-core` | Shared rules used by every skill: cheap queries, short output, safe writes | No |
| `pd-setup` | One-time setup and health check. Caches pipelines, stages, fields, users | No |
| `pd-ask` | Answer any question about your CRM in plain English | No |
| `pd-morning-brief` | Today's activities, overdue work, idle deals, top 3 actions | No |
| `pd-call-prep` | One-page brief before a call or meeting | No |
| `pd-call-to-crm` | Turns a conversation into field updates, next steps and a stage suggestion. Builds on Nova call summaries; writes its own note only for meetings Nova did not record | Yes, after you confirm |
| `pd-follow-up` | Drafts follow-up emails from deal context. Never sends | Optional note |
| `pd-lead-qualifier` | Scores leads with BANT, MEDDICC, CHAMP or your own checklist | Yes, after you confirm |
| `pd-pipeline-review` | Manager review, forecast sanity check, weekly owner digest | No |
| `pd-win-loss` | Why you win and lose, from lost reasons and note text | No |
| `pd-data-hygiene` | Duplicates, missing fields, deals with no next step, CSV import cleanup | Only fills blanks, after you confirm |
| `pd-account-health` | Account health, renewals, sales to customer success handoff | Optional note |
| `pd-industry` | Industry packs: vocabulary, stage templates, qualification, signals | No |

### Industry packs

Real estate, SaaS and tech, agencies and consulting, manufacturing and wholesale, recruiting and staffing, financial services and insurance, construction and home services, education and training, healthcare and medtech, events and hospitality, nonprofits, logistics and freight.

Each pack tells the other skills how your industry works: what a "deal" means for you, typical stages, what to ask, and which signals mean risk or upsell. Packs are small files, loaded only when needed.

---

## Where the output goes

| Output | Where it lands |
|---|---|
| Notes, next steps, field updates | Pipedrive (always after your confirmation) |
| Quick answers and briefs | The chat |
| Reports, audits, CSV fix lists | Files in `pipedrive-out/` (Claude Code, Desktop, Cowork) or a downloadable file (claude.ai) |
| Email drafts | Gmail or Outlook drafts if connected, otherwise a Pipedrive note or the chat |
| Team posts | Slack or Teams if connected and you opt in, otherwise the chat |

You can change destinations per skill in `.pipedrive/config.json` (created by `pd-setup`). See [docs/integrations.md](docs/integrations.md).

---

## Integrations

- **Required:** Pipedrive connector.
- **Optional:** Slack or Teams, Gmail or Outlook, Google Drive or Sheets, Google Calendar.
- **Call transcription:** use Pipedrive Nova. These skills read Nova's summaries and never transcribe or re-summarize calls themselves.

Skills check what is connected each time. If an optional connector is missing, the skill still works and puts the output somewhere else. Nothing fails hard.

Each user signs in to each connector with their own account. The skills never see or store passwords or tokens.

---

## Built to save tokens

CRM data is big. These skills keep costs and wait times low:

- **Setup cache.** Pipelines, stages, users and custom fields are fetched once and saved, not on every request.
- **Filter at the source.** Every query filters by owner, pipeline, stage, status or date, and asks only for the fields it needs.
- **Incremental runs.** Daily and weekly skills fetch only what changed since the last run.
- **Short output.** Fixed one-line formats instead of raw data dumps.
- **Scripts do the math.** Totals, grouping and duplicate matching run in small Python scripts, not in Claude's head.
- **Small skill files.** Each skill is short; detail lives in reference files loaded only when needed.

Details in [docs/token-saving.md](docs/token-saving.md).

---

## Safety

- Claude **never writes to Pipedrive without showing you the change first** and getting a yes.
- Every note Claude writes starts with `[Claude]`, so your team can filter and review them.
- The connector cannot delete records. Hygiene skills give you a fix list; you merge or delete in Pipedrive.
- Nothing is posted to Slack or email unless you turn it on. Email is always a draft, never sent.
- Claude only sees what your Pipedrive user can see. Manager reports need a manager or admin account.
- Healthcare and finance users: keep sensitive personal data (health, account numbers) out of the CRM and out of chat.

---

## Known limits

- The Pipedrive MCP connector cannot create pipelines, stages or custom fields. Skills tell you what to add by hand.
- No deletes or merges through the connector.
- Large pipelines (thousands of open deals) take longer. Use filters or ask per pipeline or per rep.
- On claude.ai, the setup cache does not persist between chats, so setup runs once per conversation. In Claude Code, Desktop and Cowork it is saved to disk.

---

## FAQ

**Do I need to know how to code?** No. Install, connect, and talk to Claude in normal words.

**Does this work in my language?** Yes. Write in your language and Claude answers in it.

**I only want one skill.** Install `pd-core` plus that skill. `pd-core` holds the shared rules.

**Can I change how Claude scores leads or reviews the pipeline?** Yes. Edit the skill's `SKILL.md` or the reference files. They are plain text.

**Why are the advisor answers so short?** On purpose. Short answers cost less and are faster to read. Say "normal mode" for full sentences.

---

## Contributing

New industry packs, translations and skill improvements are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
