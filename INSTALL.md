# Install

Five minutes. No code.

## Claude app (claude.ai, Desktop, Cowork)

1. Download the zips from the [latest release](https://github.com/anmoba99/pipedrive-claude-skills/releases/latest).
2. In Claude, open **Settings > Capabilities > Skills** and upload them. At minimum: `pd-core`, `pd-advisor`, `pd-setup`. Add the others you want.
3. Open **Settings > Connectors** and connect **Pipedrive** with your own account.
4. Optional: connect Slack or Teams, Gmail or Outlook, Google Drive, Google Calendar.
5. Start a chat and describe your business.

**Teams and Enterprise:** an admin can upload the skills and enable the connectors for the whole organization.

## Claude Code

```bash
claude plugin marketplace add anmoba99/pipedrive-claude-skills
claude plugin install pipedrive-skills@pipedrive-claude-skills
```

Already inside Claude Code? Type `/plugin marketplace add anmoba99/pipedrive-claude-skills`, then `/plugin install pipedrive-skills@pipedrive-claude-skills`.

Connectors you added on claude.ai also work in Claude Code when you sign in with the same account. Otherwise add a Pipedrive MCP server with `claude mcp add` and keep any API token in an environment variable, never in a file you commit.

## If dropdown values show as numbers

Claude normally reads your field names and dropdown labels straight from Pipedrive. If `pd-setup` says option labels are missing, give it the export instead:

1. In Pipedrive, open **Settings > Data fields**, click **Export** and choose **Selectable options in fields**. You get `data_fields_options_<date>.csv` with option name and ID, field name and API key. Other field types are not included and not needed.
2. **Claude app:** create a Project, add the CSV to the Project's files, and chat inside that Project. Every chat in it can see the file.
3. **Claude Code:** save the CSV in `.pipedrive/` in your working folder (it is git-ignored).
4. Run `pd-setup`. It matches the export to your fields and saves the mapping.

Re-export when you add or rename dropdown options.

## First run

1. Describe your business. `pd-advisor` replies with a plan.
2. Say "run pd-setup". It caches your pipelines, stages, users and fields, and checks what Claude can see (`pd-access`).
3. Use the plan: "brief me for today", "prep my call with Acme", "weekly digest".

## Only want one skill?

Install `pd-core` plus that skill. `pd-core` holds the shared rules.

## Troubleshooting

| Problem | Fix |
|---|---|
| "Pipedrive not connected" | Connect it in **Settings > Connectors** (or `claude mcp add` in Claude Code), then run `pd-setup` again |
| Dropdown values show as numbers | Upload the "Selectable options in fields" export (above) |
| Team reports show only your deals | Say "what can Claude see?" (`pd-access`). Your user or the connector may be limited; it tells you which and the fix |
| Claude doesn't know who I am | The connector is missing a permission. Reconnect Pipedrive in **Settings > Connectors** and accept every permission, or let `pd-access` find you from your deals |
| Field or stage errors | Say "pd-setup doctor". It refreshes the cache |
| Setup runs again in every new chat | On claude.ai the cache lasts one conversation. Work inside a Project with your export |

## Update or remove

- **Claude app:** upload the new zips over the old ones, or delete the skills in **Settings > Capabilities > Skills**.
- **Claude Code:** update with `claude plugin marketplace update pipedrive-claude-skills` then `claude plugin update pipedrive-skills@pipedrive-claude-skills`. Remove with `claude plugin uninstall pipedrive-skills@pipedrive-claude-skills`.
