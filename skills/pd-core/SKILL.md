---
name: pd-core
description: Shared rules for all pd-* Pipedrive skills (cached account context, cheapest queries, compact output, safe writes, output routing). Load before any other pd-* skill does Pipedrive work.
---

# pd-core

Rules every pd-* skill follows. Short on purpose; details in `references/`.

## 1. Context first, once

- Look for `.pipedrive/context.json` (written by pd-setup). If present and under 7 days old, use it for pipeline, stage and user IDs. Custom fields and stage order live in `.pipedrive/account_context.json`; pass that file to scripts that take `--context`.
- If missing, stale, or no filesystem (claude.ai chat): call `getAccountContext` once per conversation and reuse the result. Never call it twice in one conversation.
- A "field not found" or unknown stage error means the cache is stale: refresh once, then retry.
- Custom fields are hash keys. Map names to keys with `.pipedrive/field-map.json` or the context. Never guess a key. Option labels come from the account context (`options` per field) and are cached in `field-map.json`; when showing option values, add `include_option_labels=true` to `getDeals`/`getPersons`. The "Selectable options in fields" export is a fallback merged by pd-setup. Match by API key, never by field name. Skip fields with `is_writable=false` when writing.

## 2. Cheapest query wins

Load `references/query-playbook.md` when planning anything beyond a single lookup. Short version:
- Have an ID? Use `getDeal` / `getPerson` / `getOrganization`. Search is the most expensive call.
- Lists: always filter (`owner_id`, `pipeline_id`, `stage_id`, `status`, `updated_since`) and set `limit`.
- Ask only for needed custom fields (`custom_fields`, max 15) and `include_fields`.
- Pull notes only for the few deals that need them, never for a whole pipeline.
- Cap each run at about 15 Pipedrive calls. Need more? Tell the user and narrow the scope (one pipeline, one rep, last 30 days).
- Large dataset (size check shows more than one batch): always run in batches, with a plan, partial results and a stop after each batch. Load `references/batches.md`.

## 3. Compact output

- One line per record: `id | title | stage | value | owner | idle days | flag`.
- Never echo raw JSON. Never list more than 20 rows in chat; offer a file for the rest.
- Totals, grouping, date math over more than about 20 records: use `scripts/pd_digest.py` when a shell is available (see header of the script). Otherwise compute carefully and show the method.
- Reply in the user's language.

## 4. Safe writes

Load `references/safe-write.md` before any add/update call. Short version:
1. Search first to avoid duplicates.
2. Show the exact change set (record, field, old -> new).
3. Wait for an explicit yes. One yes covers the shown batch only.
4. Write. Prefix every note with `[Claude]`.
5. Report what was written with record IDs.

No deletes exist in the connector. Never try to work around that.

## 5. Output routing

Load `references/output-routing.md` when a skill produces something to keep or share. Read `.pipedrive/config.json` for user preferences. Optional connector missing: fall back, never fail. Posting to Slack/Teams requires the user to have opted in (config or explicit request). Email drafts are allowed when the skill's route in config includes them (default for pd-follow-up and pd-win-back); drafts are never sent.

## 6. Industry

If `.pipedrive/config.json` has `industry`, load only `pd-industry/references/<industry>.md` when the skill needs vocabulary, stages, qualification or signals.

## 7. Privacy

- Pipedrive access equals the user's own permissions plus the connector's granted permissions. Read `.pipedrive/access.json` if present (written by pd-access). Coverage `partial` or `own_only`: say so in the first line of any team report. Never present partial coverage as team-wide.
- Do not copy sensitive personal data (health, government IDs, bank details) into notes, files or messages.
- Never put CRM data in URLs.
