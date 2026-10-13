---
name: pd-setup
description: One-time setup and health check ("doctor") for the pd-* Pipedrive skills. Caches pipelines, stages, users and custom fields, records industry and output preferences, and reports which skills are ready. Use on first install, when something breaks, or after adding a connector.
---

# pd-setup

Follow pd-core rules (load pd-core if not loaded).

Requires: Pipedrive
Optional: none
Fallback: no filesystem (claude.ai chat) -> keep context in this conversation only and say so.

## Steps

1. **Connectors.** List which integrations are live in this session by checking available tools: Pipedrive, Slack, Teams, Gmail, Outlook, Google Drive, Google Calendar. Ask once whether the team uses Pipedrive Nova for calls; save `"call_ai": "nova"` or `null` in config. Pipedrive missing: stop and say "Connect Pipedrive in Settings > Connectors (or `claude mcp add` in Claude Code), then run pd-setup again."
2. **Account context.** Call `getAccountContext` once.
3. **Field export.** The connector returns custom fields as hash keys and option IDs, not the names and labels the user sees. Look for the user's field export from Pipedrive Settings > Data fields: Project files, a chat attachment, or `.pipedrive/fields.*` (CSV or XLSX). Found: match each row to a field by key, else by name, and take name, type and option labels from it. Not found and the account has custom fields: ask once, "Export your fields from Pipedrive Settings > Data fields and upload the file (add it to a Claude Project so every chat has it)." Continue without it if the user skips.
4. **Write cache** (if filesystem available) to `.pipedrive/` in the working folder:
   - `context.json`: slim version only:
     ```json
     {"fetched": "<ISO date>", "me": {"id": 0, "name": ""},
      "pipelines": {"<id>": {"name": "", "stages": {"<id>": ""}}},
      "stages": {"<id>": "<name>"}, "users": {"<id>": "<name>"}}
     ```
   - `field-map.json`: `{"deal": {"<Field name>": {"key": "<hash>", "type": "", "options": {"<label>": <id>}}}, "person": {}, "org": {}}`
   - `config.json`: from `references/config.template.json`, filled with answers from step 5.
   - `last_run.json`: `{}`
5. **Ask once** (one message, skip what is known):
   - Industry (offer the pd-industry list, or "generic").
   - Your role: rep, manager, owner, ops, CS.
   - Where team posts go, if Slack/Teams is live (channel name or "chat only").
   - Stale threshold in days (default 14).
6. **Industry check.** If an industry is chosen, load `pd-industry/references/<industry>.md`. Compare its "Custom fields worth adding" and pipeline template with the real account. List what is missing as manual steps (the connector cannot create fields or stages).
7. **Visibility check.** If role is manager/owner, call `getDeals status=open limit=100` with no owner filter and count distinct `owner_id` values. If only the user's own ID appears while the account has other users, warn: "Team reports will only cover your own deals with this Pipedrive user."
8. **Report** in this format:

```
Setup done. Cache: .pipedrive/ (fields: 34, pipelines: 2, users: 6)
Fields: from export (34) | from MCP only, upload export for real names
Connectors: Pipedrive live | Slack live | Gmail missing | Calendar missing
Ready: pd-morning-brief, pd-call-prep, pd-call-to-crm, pd-pipeline-review, ...
Fallback: pd-follow-up -> drafts in chat (connect Gmail for drafts)
Manual Pipedrive steps for <industry>:
1. Add deal field "Trial end date" (date)
2. ...
Try: "brief me for today"
```

## Doctor mode

User says "doctor", "something broke" or a skill hit a field/stage error: re-run steps 1 to 4 (overwrite cache), keep `config.json`, report only what changed.
