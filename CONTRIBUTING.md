# Contributing

Thanks for helping. Three kinds of contributions are most useful:

1. **Industry packs.** Add a file in `plugins/pipedrive-skills/skills/pd-industry/references/` using the template below, and list it in `pd-industry/SKILL.md` and `pd-advisor/references/catalog.md`.
2. **Skill improvements.** Better prompts, cheaper queries, clearer output.
3. **Example business cases.** Add to `examples/business-cases.md` with the advisor answer you got.

## Rules for every skill

- `SKILL.md` stays under about 150 lines. Put detail in `references/` and say when to load it.
- The `description` in the frontmatter is loaded in every conversation. Keep it to 1 or 2 sentences.
- Do not rebuild native Pipedrive features. Call transcription and summaries belong to Pipedrive Nova; skills may read its output, never replace it. Same for Pipedrive automations, reports and web forms.
- Follow `pd-core`: cached context, filtered queries, compact output, safe writes.
- Never hardcode MCP tool names with prefixes. Refer to tools by their base name (`getDeals`, `addNote`), because prefixes differ per install.
- Any write to Pipedrive goes through the `pd-core` safe-write steps: show the change, confirm, write, tag `[Claude]`.
- Optional connectors must have a fallback. A skill must never fail because Slack or Gmail is missing.
- Scripts: Python 3 standard library only, no network calls.
- No em dashes in user-facing copy.

## Skill template

```markdown
---
name: pd-<name>
description: <What it does in one sentence. When to use it in one sentence.>
---

# pd-<name>

Follow pd-core rules (load pd-core if not loaded).

Requires: Pipedrive
Optional: <connector> (<what for>)
Fallback: <where output goes if optional is missing>

## Steps
1. ...

## Output
<fixed compact format>
```

## Industry pack template

```markdown
# <Industry>

Object map: deal = ..., person = ..., org = ..., product = ...
Pipeline template: Stage 1 > Stage 2 > ...
Qualify: <4 to 6 checks>
Risk signals: ...
Upsell signals: ...
Custom fields worth adding: ...
Best skills: ...
Watch-outs: ...
```

## Testing

Run the scripts on the sample data before opening a pull request:

```bash
python3 plugins/pipedrive-skills/skills/pd-core/scripts/pd_digest.py examples/sample-deals.json --today 2026-10-13
```

```bash
python3 plugins/pipedrive-skills/skills/pd-data-hygiene/scripts/find_dupes.py examples/sample-persons.json
```
