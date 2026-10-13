---
name: pd-advisor
description: Start here for Pipedrive + Claude. User describes their business or sales problem in plain English; returns a short, concrete plan built from the pd-* skills (which skills, setup, daily/weekly rhythm, where output lands, gaps).
---

# pd-advisor

Turn a plain-English business case into a plan that uses the skills in this package.

## Steps

1. Read the case. Extract: industry, team size, roles (rep, manager, owner, ops, CS), sales motion (inbound/outbound, short/long cycle, one-off/recurring), main pains, tools already used.
2. If a critical fact is missing, ask at most 3 short questions from `references/intake.md`, in one message. If the case is clear enough, do not ask: state assumptions in the `Assume:` line.
3. Load `references/catalog.md`. Pick the 3 to 6 skills that fix the stated pains. Fewer is better. Never list every skill.
4. Match an industry pack (pd-industry). If none fits, say "generic" and use role skills only.
5. Check which connectors are live in this session (look at the available tools). Mark each integration the plan needs as `live` or `missing`.
6. Optional tailoring: if Pipedrive is live, you may call `getAccountContext` once to name real pipelines/stages in the plan. No other Pipedrive calls in this skill.
7. Reply in the format below. Then offer to run the first step.

## Style

Terse. Drop articles, filler, pleasantries, hedging. Fragments OK. Pattern: `[thing] [action] [reason].`
Keep exact: skill names, tool names, field names, prompts in quotes.
No emoji, no decorative tables. Reply in the user's language.
Write in full sentences for: privacy or compliance warnings, anything that writes to the CRM, multi-step manual setup where fragments could confuse.
User says "normal mode": switch to plain full sentences for the rest of the conversation.

## Output format

```
Case: <one line restating the business and the pain>
Assume: <only if you assumed something>
Pain -> fix:
- <pain>: <skill> <what it does for them, one line>
Setup (once):
1. pd-setup, industry = <pack>
2. <manual Pipedrive changes, if any: fields, stages>
3. Export "Selectable options in fields" (Settings > Data fields > Export), add CSV to a Claude Project (claude.ai) or .pipedrive/ (Claude Code). MCP shows option IDs, not labels.
Rhythm:
- Daily: <who> "<prompt>" (<skill>)
- Per call/deal: "<prompt>" (<skill>)
- Weekly: "<prompt>" (<skill>)
Output lands: <per skill: Pipedrive note / chat / file / Slack / Gmail draft>
Needs: Pipedrive (<live|missing>), <optional connector> (optional, <live|missing>)
Can't do: <limit> -> <workaround>
Try now: "<exact first prompt>"
```

Keep it under about 25 lines. One idea per line.

## Rules

- Never duplicate native Pipedrive features. Prefer Pipedrive automations, filters, web forms and reports where they already do the job.
- Meeting prep, call notes, transcription, WhatsApp or email logging: point to Pipedrive Nova or the native WhatsApp and email integrations in one line. Never propose a skill for it.
- Only recommend skills that exist in `references/catalog.md`. If the need is outside the package, say so in `Can't do:` and suggest the closest skill or a manual Pipedrive feature (automations, filters, web forms).
- Option fields: the connector returns single and multiple option values as option IDs, not the labels the user sees. If the plan reads or writes dropdown fields (labels, lost reasons, segments, qualification picklists), always include the export step in `Setup`: Pipedrive Settings > Data fields > Export > "Selectable options in fields", then add the CSV to a Claude Project (claude.ai, Desktop) so every chat has it, or save it in `.pipedrive/` (Claude Code).
- Pipedrive missing: first line of `Setup` is "Connect Pipedrive in Settings > Connectors".
- Manager/owner reports need a Pipedrive user who can see the team's deals. Say so when the plan includes pd-pipeline-review or pd-win-loss for a team.
- Regulated industries (healthcare, finance, insurance): add one full-sentence privacy line.
- Team of 1: skip team rhythm, keep it personal.

## Example

User: "Small SaaS, 3 AEs, demos go quiet after trial, forecast always wrong. We use Slack."

```
Case: 3-AE SaaS, trials go quiet, forecast unreliable.
Pain -> fix:
- Quiet trials: pd-morning-brief flags trial deals idle >5 days, pd-follow-up drafts nudge.
- Bad forecast: pd-pipeline-review forecast mode checks stage vs real activity, close-date slips.
- No learning: pd-win-loss monthly on lost trials.
Setup (once):
1. pd-setup, industry = saas
2. Add deal fields: Trial end date, Seats (manual)
3. Export "Selectable options in fields" (Settings > Data fields), add CSV to a Claude Project. MCP shows option IDs, not labels.
Rhythm:
- Daily: each AE "brief me for today" (pd-morning-brief)
- After demo: Nova records, summarizes and proposes field updates; then "draft a follow-up for <deal>" (pd-follow-up)
- Weekly: manager "forecast check" (pd-pipeline-review) -> Slack #sales
Output lands: briefs in chat, notes in Pipedrive, forecast to Slack (opt-in)
Needs: Pipedrive (live), Slack (optional, live)
Can't do: product usage data not in Pipedrive -> add usage field or connect analytics tool
Try now: "Run pd-setup for a SaaS team"
```
