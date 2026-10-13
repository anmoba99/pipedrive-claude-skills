# Writing the ICP

## Read icp.json in this order

1. `segments`: single traits by lift. Lift 1.3+ with 8+ deals is a real signal; 1.1 to 1.3 is weak.
2. `pairs`: combinations. A pair beating both of its parts is the profile core.
3. Value and cycle per segment: rank segments by expected value per month of selling, roughly `win_rate x avg_won_value / won_cycle_p50`. Show this when it changes the order.
4. `scored`: fit is a percentile among the current open deals and leads, not a probability.

## Profile sentence

`<type of organization> in <where>, <size>, coming from <source>, buying <deal size> to <goal from notes>.`

Use the account's own labels. Only traits with lift 1.3+ go in the sentence.

## Must have, nice to have, red flags

- Must have: traits in the best pair, or lift 1.5+.
- Nice to have: lift 1.2 to 1.5.
- Red flags: lift under 0.7 with 8+ deals, and anything the loser notes repeat (no budget owner, wrong use case).

## Stop chasing

A segment with lift under 0.6 and real volume: show how many deals and how much rep time (count of activities if known) it takes. Suggest a change the team makes in Pipedrive by hand: a lead source to pause, a web form question to add, a qualification field to require.

## Rules

- Never infer protected traits about people (age, gender, ethnicity, religion, health). Organizations and deal facts only.
- "(empty)" segments are a data gap, not a profile: point to pd-data-hygiene when a key field is mostly empty.
- Owner as a dimension is coaching information. Show it only to managers, never as part of the ICP.
