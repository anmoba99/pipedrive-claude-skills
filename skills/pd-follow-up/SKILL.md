---
name: pd-follow-up
description: Draft follow-up or nudge emails for Pipedrive deals using deal history and last notes; saves as Gmail or Outlook draft if connected, never sends. Use when the user asks to draft a follow-up, nudge, recap email or re-engage a quiet deal.
---

# pd-follow-up

Follow pd-core rules (load pd-core if not loaded).

Requires: Pipedrive
Optional: Gmail or Outlook (save as draft)
Fallback: Pipedrive note `[Claude] Draft email` (after confirm) or chat

## Steps

1. Identify deal(s). Batch mode: "nudge my quiet deals" -> `getDeals owner_id=<me> status=open updated_until=<today - stale_days> limit=20`, then draft up to 10.
2. Per deal fetch: `getDeal`, `getNotes deal_id limit=5`, `getPersons deal_id` (recipient email). No email on file: say so, draft anyway.
3. Pick the type: recap after call, nudge after silence, proposal follow-up, re-engage lost/cold, meeting request.
4. Draft rules:
   - 60-120 words, the user's language and tone (copy tone from earlier notes or emails if visible).
   - One specific reference to the last conversation. One clear ask with a date or two time options.
   - No invented facts, prices or promises. Missing info: `[placeholder]`.
   - Subject line under 8 words.
5. Save: Gmail/Outlook draft if live (to the person's email, nothing sent). Otherwise show in chat; offer to save as a Pipedrive note.
6. Offer: create an activity "Follow up on email" due in 3 business days (safe-write).

## Output

```
Deal 1042 Acme rollout -> ana@acme.com (Gmail draft saved)
Subject: Revised quote for the October rollout
<body>
```

Batch: one line per draft plus where it was saved. Never send. Never ask the user for email passwords.
