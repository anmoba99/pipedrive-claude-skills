---
name: pd-lead-qualifier
description: Score Pipedrive leads or early-stage deals against BANT, MEDDICC, CHAMP or a custom checklist, list missing info and the next question to ask, and optionally write the score or convert leads to deals after confirmation. Use when the user asks which leads are serious, to qualify or score leads, or to clean the lead inbox.
---

# pd-lead-qualifier

Follow pd-core rules (load pd-core if not loaded).

Requires: Pipedrive
Fallback: no score field in Pipedrive -> score goes in a `[Claude]` note (after confirm) or chat only

## Steps

1. Framework: from `config.json` `qualification_framework`, the user's request, or the industry pack. Load `references/frameworks.md` for criteria.
2. Scope: `getLeads limit=50` (newest first), or early-stage deals `getDeals stage_id=<first stages> status=open limit=50`. Single lead named: search it.
3. Evidence per lead: lead/deal fields plus `getNotes lead_id|deal_id limit=5`. Do not fetch notes for more than 25 records per run; say how many remain.
4. Score each criterion 0 (unknown), 1 (weak), 2 (confirmed), only from evidence. Total as a percentage. Grade: A >= 75%, B 50-74%, C 25-49%, D < 25%.
5. For each lead: biggest gap and the single next question that closes it.
6. Offer writes (safe-write): score to a custom field if one exists (field map: "Lead score", "Qualification"), else a note; `convertLeadToDeal` for A leads only if the user asks.

## Output

```
Framework: BANT | scored 18 leads | 7 have no notes (scored on fields only)
A (3):
- <lead> | <org> | 88% | gap: timeline | ask: "When do you need this live?"
B (6): ...
C/D (9): <names only, one line>
Offer: write scores to field "Lead score"? convert A leads to deals?
```

Never mark a criterion confirmed without a quote or field value backing it.
