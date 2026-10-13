# Output routing

## Destinations

- `chat`: default for answers, briefs, short reports.
- `pipedrive`: notes, activities, field updates (safe-write rules apply).
- `file`: markdown or CSV under `pipedrive-out/<skill>/<YYYY-MM-DD>.<ext>`. Needs a filesystem (Claude Code, Desktop, Cowork). On claude.ai, create a downloadable file instead.
- `slack:<#channel or @user>` / `teams:<channel>`: only if connected and opted in.
- `gmail-draft` / `outlook-draft`: only if connected. Drafts only, never send.
- `gdoc` / `gsheet`: only if Google Drive is connected.

## Reading preferences

`.pipedrive/config.json`:
```json
{ "outputs": { "pd-pipeline-review": ["chat", "file"] } }
```
No config: use the skill's default.

## Fallback chain

- Message: Slack -> Teams -> chat.
- Email: Gmail draft -> Outlook draft -> Pipedrive note `[Claude] Draft email` -> chat.
- Report: Google Doc -> file -> chat.
- Table: Google Sheet -> CSV file -> chat (max 20 rows).

When falling back, add one line: `Slack not connected, posted here instead.`

## File rules

- Dated, append-only. Never overwrite a previous report; the next run can diff against it.
- No sensitive personal data in files.
- Tell the user the path.
