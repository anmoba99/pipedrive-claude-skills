# CLAUDE.md

Rules for AI agents editing this repo.

## Layout

- `skills/<name>/SKILL.md`: one folder per skill. `references/` and `scripts/` optional.
- `.claude-plugin/`: Claude Code marketplace and plugin manifests (plugin at repo root, `source: "./"`).
- Skill zips for the Claude app ship as GitHub release assets, never committed.

## README is the product page

- Written for sales people, not developers. Value first: the "What changes" table leads.
- The "What you get" table must match the real skills in `skills/`.
- Install commands must work. Test before changing them.
- Keep the disclaimer at the top, word for word.
- Never invent numbers or results.
- No em dashes. Use commas, colons or new sentences.

## Skills

Follow [CONTRIBUTING.md](./CONTRIBUTING.md). Run `claude plugin validate .` after changes (one expected warning: this CLAUDE.md is for repo editors, not shipped plugin context). Bump `version` in both files in `.claude-plugin/` for a release.
