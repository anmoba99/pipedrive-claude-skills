# Large datasets: batches

A run is large when the size check shows more than one batch of records to fetch for it. Large runs always go in batches. Never fetch a large dataset in one go.

## Batch size

- Claude Code or Cowork: up to 5,000 records per batch (10 calls of 500).
- claude.ai or Desktop: up to 1,000 records per batch (2 calls of 500), max 3 batches per chat. More: narrow the scope or use Claude Code.

## Plan first

1. Size check (one page per entity, see the skill). Estimate records per slice: an owner, a pipeline, or a time window (`updated_since` / `updated_until`).
2. Group slices into batches. Biggest first: most open deal value or most accounts, so stopping early still covers what matters most.
3. Show the plan and wait for a yes:
```
Large dataset: about <records> records in <n> batches of up to <size>.
Batch 1: <slices> | Batch 2: <slices> | ...
I stop after each batch with partial results. Say "run all" to go without stops.
```
4. Write the plan to `pipedrive-out/<skill>/batches.json`:
```json
{"run": "<date>", "skill": "<skill>", "size": 5000,
 "batches": [{"n": 1, "slices": ["owner:123"], "status": "done", "records": 4810, "cursor": null}]}
```

## Each batch

1. Fetch only that batch's slices (Claude Code: one subagent per batch, raw pages to files, one line back). Save the next cursor in `batches.json` if a slice is not finished.
2. Run the skill's script on every file fetched so far, with `--scope-note "batch <k> of <n>: <slices done>"`. The page and chat summary say the results are partial.
3. Report in 3 lines: batch done, records so far, the top finding so far. Ask "Next batch?" unless the user said "run all".
4. Mark the batch `done` in `batches.json`.

## Stop and resume

- User stops: keep the files and `batches.json`. The partial page stays valid for the slices done.
- "continue the <skill> run" in a later session: read `batches.json`, skip `done` batches, resume from the saved cursor. Plan older than 7 days: start a new plan.
- Results that need every record (duplicates across slices, peer medians, whitespace) are final only after the last batch. Say so on partial results.
