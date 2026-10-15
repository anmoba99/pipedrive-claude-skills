# Contributing

Issues and pull requests are welcome: new industry packs, translations, fixes, better skills. Questions and ideas: use [Discussions](https://github.com/anmoba99/pipedrive-claude-skills/discussions). By contributing you agree your work is licensed under MIT, like the rest of the repo, and to follow the [code of conduct](./CODE_OF_CONDUCT.md).

## How a skill folder works

Each skill is one folder in `skills/`, named after the skill:

```
skills/pd-advisor/
  SKILL.md          the skill: when to use it and the steps Claude follows
  references/       extra detail Claude reads only when needed
skills/pd-core/
  SKILL.md
  scripts/          small Python helpers (standard library only)
```

The file is always called `SKILL.md`; the Claude skill format requires that name. `references/` and `scripts/` are optional.

## Rules for skills

- Keep `SKILL.md` short. Move detail into `references/`.
- The `description` in the frontmatter is loaded in every chat. One or two sentences.
- Never hardcode MCP tool prefixes. Describe the capability ("a tool that saves a Gmail draft").
- Every CRM write is shown to the user and confirmed first. Notes start with `[Claude]`.
- Filter every query and ask only for the fields you need.
- Do not rebuild what Pipedrive already does. Check Pipedrive's native features first (Nova, the WhatsApp and email integrations, automations, filters and reports) and build on the data they leave in Pipedrive.
- No real customer data in examples.

## New industry pack

Copy any file in `skills/pd-industry/references/`, keep the same headings, and add it to the list in `skills/pd-industry/SKILL.md` and the README.

## Before you open a pull request

```bash
claude plugin validate .
```

Then try your change in a real chat with the Pipedrive connector, and describe what you tested in the pull request.
