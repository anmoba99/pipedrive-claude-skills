# Integrations

Pipedrive is the only required connector. Everything else is optional, and every skill has a fallback.

## Per skill

| Skill | Required | Optional | Fallback when optional is missing |
|---|---|---|---|
| pd-advisor | none | Pipedrive (to tailor the plan) | Generic plan |
| pd-setup | Pipedrive | none | Cache kept in the conversation only (claude.ai) |
| pd-ask | Pipedrive | none | none |
| pd-morning-brief | Pipedrive | Google Calendar, Slack DM | Chat |
| pd-call-prep | Pipedrive | Google Calendar | Chat |
| pd-call-to-crm | Pipedrive | none (reads Nova summaries) | Paste Nova's summary or your notes |
| pd-follow-up | Pipedrive | Gmail or Outlook | Pipedrive note or chat |
| pd-lead-qualifier | Pipedrive | none | Score in chat or note if no score field |
| pd-pipeline-review | Pipedrive | Slack or Teams, Google Docs | Chat and file |
| pd-win-loss | Pipedrive | Google Docs | Chat and file |
| pd-data-hygiene | Pipedrive (audit) | none | CSV fix list |
| pd-account-health | Pipedrive | Google Docs | Chat or pinned note |
| pd-industry | none | none | none |

## How connectors are found

Skills never use fixed tool names, because names differ per install (for example `mcp__pipedrive__getDeals` in one place and a long ID prefix in another). Skills describe the capability ("a tool that saves a Gmail draft") and Claude matches it to the tools in the session.

## Sign-in and permissions

- Each user connects each app with their own account (OAuth). Skills never handle passwords or tokens.
- Pipedrive access equals the user's Pipedrive permissions. A rep sees their own deals; a manager or admin sees the team. Team reports need the second kind of user.
- Company admins may restrict which connectors are allowed. Ask IT to allow the Pipedrive connector, and any optional ones you want.

## Claude Code with a self-hosted MCP server

If you run your own Pipedrive MCP server instead of the Claude connector, add it with `claude mcp add`. Keep any API token in an environment variable, never in this repo:

```json
{
  "mcpServers": {
    "pipedrive": {
      "command": "<your server command>",
      "env": { "PIPEDRIVE_API_TOKEN": "${PIPEDRIVE_API_TOKEN}" }
    }
  }
}
```

## Privacy defaults

- Posting to Slack or Teams is off until the user sets a channel in `.pipedrive/config.json` or asks explicitly.
- Email is always a draft. Nothing is sent.
- EU and regulated users: decide which CRM data may go to chat tools before enabling posts.
