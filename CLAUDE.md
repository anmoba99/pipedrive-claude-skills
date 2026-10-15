# CLAUDE.md

Rules for AI agents editing this repo.

## Layout

- `skills/<name>/SKILL.md`: one folder per skill. `references/` and `scripts/` optional.
- `.claude-plugin/`: Claude Code marketplace and plugin manifests (plugin at repo root, `source: "./"`).
- Skill zips for the Claude app ship as GitHub release assets, never committed.

## README is the product page

- Written for sales people, not developers. Value first: the prose opening and the Basics / Intelligence tables lead.
- Every skill in `skills/` appears in exactly one of those tables, or in the helpers line under them.
- Frame Pipedrive positively: these skills build on Pipedrive data. Never write that Pipedrive "can't" or "fails at" something.
- Install commands must work. Test before changing them.
- Keep the disclaimer at the top, word for word.
- Never invent numbers or results.
- No em dashes. Use commas, colons or new sentences.

## Skills

Follow [CONTRIBUTING.md](./CONTRIBUTING.md). Run `claude plugin validate .` after changes (one expected warning: this CLAUDE.md is for repo editors, not shipped plugin context). Bump `version` in both files in `.claude-plugin/` and `metadata.version` in every `SKILL.md` for a release.
