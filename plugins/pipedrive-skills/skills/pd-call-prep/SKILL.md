---
name: pd-call-prep
description: One-page brief before a call or meeting with a deal, person or organization in Pipedrive: history, people, open questions, risks and suggested agenda. Use when the user says prep, brief me on, or before a meeting with a named client.
---

# pd-call-prep

Follow pd-core rules (load pd-core if not loaded).

Requires: Pipedrive
Optional: Google Calendar (find the meeting and attendees)
Works with: Pipedrive Nova (reuse its last call summary, never re-summarize)
Fallback: chat

## Steps

1. Identify the target. ID given: use it. Name given: `searchDeals term=<name> status=open limit=5` or `searchOrganization` / `searchPersons`. Several matches: ask. Calendar live and user says "my next call": take the next event and match attendees.
2. Fetch (max 5 calls):
   - `getDeal <id>` (or org/person)
   - `getNotes deal_id=<id> sort="add_time DESC" limit=10`
   - `getActivities deal_id=<id> limit=20` (done and open)
   - `getPersons deal_id=<id>`
   - optional `getDealProducts <id>` if products matter (industry pack says so or deal has products)
3. Last call: if a Nova summary is on the deal (in the notes fetched above), use it as the "last call" source. Do not fetch or re-summarize full transcripts.
4. Industry pack (if set): add its qualification checks as "Open questions" if not answered in notes.
5. Write the brief. Facts come from data; mark any inference as "likely".

## Output

```
<Deal title> | <org> | <stage> | <value> | owner <name>
Since: <created date>, last touch <n> days ago, <n> open activities
People: <name, role/title, last contact>
Story so far (3-5 lines from notes):
- ...
Open questions:
- <missing qualification item>
Risks:
- <signal, source>
Agenda (suggested):
1. ...
Goal for this call: <one line, tied to next stage>
```

Under about 25 lines. After the call: suggest "paste your notes and say log this call" (pd-call-to-crm).
