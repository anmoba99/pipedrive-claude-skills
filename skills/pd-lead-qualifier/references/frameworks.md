# Qualification frameworks

## BANT (short cycles, SMB)
- Budget: amount or range stated, or price accepted.
- Authority: decision maker identified or in the conversation.
- Need: specific problem stated in their words.
- Timeline: target date or event.

## CHAMP (needs-first, consultative)
- Challenges: problem and impact.
- Authority: who decides, who signs.
- Money: budget exists or can be found.
- Prioritization: ranked against other projects, urgency.

## MEDDICC (complex B2B, long cycles)
- Metrics: measurable outcome they expect.
- Economic buyer: person who controls budget, met or named.
- Decision criteria: what they will judge on.
- Decision process: steps, approvals, legal, procurement.
- Identify pain: pain with cost of inaction.
- Champion: internal person pushing for you.
- Competition: alternatives including doing nothing.

## Custom
User gives 3 to 7 checks in plain English. Save them to `config.json` as `"custom_framework": ["check 1", "..."]` and reuse.

## Picking a default
- Deal value small, cycle under 30 days: BANT.
- Consultative services, agencies: CHAMP.
- Enterprise, multiple stakeholders, procurement: MEDDICC.
- Industry pack lists its own checks: use those as custom.
