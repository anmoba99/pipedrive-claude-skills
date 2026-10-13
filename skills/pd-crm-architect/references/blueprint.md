# Blueprint rules

## Stages

| Evidence (usage.json) | Change |
|---|---|
| Dead stage: nothing open, nothing won or lost from it | Remove, or merge into the next stage |
| Two neighbor stages, open deals move through both in a few days, losses split evenly | Merge |
| Bottleneck: open deals sit far longer than in any other stage | Split it at the real decision inside it (for example Proposal sent / Proposal reviewed), or add an exit criterion |
| Leaky: one stage holds 35%+ of all losses | Add a qualification exit criterion to the stage before it |
| Stage name describes our action ("Send proposal") | Rename to the buyer's state ("Proposal under review") |

Every stage gets one exit criterion: a fact visible in Pipedrive (field filled, activity done, file attached). Target 5 to 7 stages per pipeline. Use the pd-industry pack stages as a reference shape, never as a template to copy.

## Fields

- Add: a fact repeated in 5+ notes. Type by content: dates as date, amounts as monetary, closed lists (3 to 10 values) as single option with options taken from the notes' own words, people as person field.
- Retire: under 5% filled and not required anywhere. Suggest hiding first, deleting after a quarter.
- Require at a stage: a field filled far more often on won deals than lost ones, required at the stage where wins already had it. Pipedrive supports required fields per stage in the pipeline settings.
- Never more than 3 new required fields at once. Reps route around forms.

## Lost reasons

Free text (many distinct values) or 30%+ empty: propose a picklist of 6 to 9 options built by clustering the existing values (same classes as pd-win-loss themes), plus "Other" with a note. Make the lost reason required when marking a deal lost.

## Automations

Only Pipedrive's own automations, built by an admin. Good candidates:
- Deal enters a stage -> create the activity that stage always needs.
- Deal idle N days (from playbook or premortem numbers) -> activity for the owner.
- Deal lost with reason timing or budget -> activity on the restart date (pairs with pd-win-back).
- Deal won -> handoff activity for customer success.
Write each as `Trigger: ... | Conditions: ... | Action: ...`. Never build the workflow in Claude.

## Manual steps

Write clicks the admin follows: Settings > Data fields, Pipeline > Edit pipeline, Automations. Order: add fields, update stages, picklists, automations, then retire old fields.
