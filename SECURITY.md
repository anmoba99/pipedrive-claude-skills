# Security and privacy

## What the skills do with your data

- The skills are plain text instructions plus two small Python scripts. They run inside Claude and send nothing anywhere else.
- Claude reads your CRM through the Pipedrive connector, with your own Pipedrive login and permissions.
- Nothing is written to Pipedrive without your confirmation. Nothing is deleted.
- Email is always a draft. Slack or Teams posts happen only when you turn them on.
- The skills never ask for, see or store passwords or API tokens.
- In Claude Code, a local cache is saved in `.pipedrive/` and reports in `pipedrive-out/`. Both are git-ignored. Do not commit them.

## Sensitive data

Healthcare, finance and insurance users: keep sensitive personal data (health details, account numbers) out of the CRM and out of chat.

## Reporting a problem

Found a way a skill could leak data or change the CRM without confirmation? Please report it privately through [GitHub security advisories](https://github.com/anmoba99/pipedrive-claude-skills/security/advisories/new) instead of a public issue.
