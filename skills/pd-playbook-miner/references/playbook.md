# Writing the plays

A play is a rule a new rep can follow on day one.

## Shape

`<name>: when <trigger>, <action> within <time>. Evidence: <numbers>. "<quote>" (deal <id>)`

- Trigger: a moment visible in Pipedrive (deal created, demo done, proposal sent, 5 days of silence, new contact added).
- Action: one verb, one activity type the team already uses.
- Time: from the timing numbers (first touch p50 of wins, longest gap p50 of wins).
- Evidence: share of wins vs share of losses, or won vs lost median. One quote max, under 15 words.

## Where plays come from

| Signal in playbook.json | Play it suggests |
|---|---|
| Step with high lift (in wins far more than losses) | Make it mandatory at its typical position in the won sequence |
| First touch faster in wins | Speed to first touch rule |
| Longest gap shorter in wins | Silence limit: act before the gap wins never exceeded |
| More contacts in wins | Multi-thread by a given stage (see pd-thread-map) |
| Common won opening differs from lost opening | The opening sequence to copy |
| Note language repeated in wins | Talk track: the question or proof that moved deals |

## Rules

- 4 to 7 plays. Drop any play backed by fewer than 5 deals.
- Name plays after what they do ("Second voice by proposal"), not after numbers.
- Never claim a play causes wins. "Wins had this, losses mostly did not."
- Owner-only differences (one rep does it, others do not): mention as coaching, not as a play.
- Stage exit criteria: write them so an admin can add them as a checklist or required field in Pipedrive. Do not build automations in Claude.
