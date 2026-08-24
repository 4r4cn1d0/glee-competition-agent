# Persuasion workstream handoff

Last updated: 2026-08-24 19:12 IST. This file is the deployment boundary for
the persuasion-owned workstream. Negotiation and bargaining owners may read it;
they must not edit persuasion strategy or flags. Persuasion work does not alter
their code, configuration, experiments, or fleet flags.

## Live persuasion boundary

- All five slots use buyer-v2, tight-prior `.65`, honest rounds `99`, lie
  shading `0`, backload off, KEEP_MSG on, token message style, and LLM off.
- Test 2's invalid `GLEE_PERS_RANK_GATE_AB` arm was explicitly set to `0` with
  `scripts/fleet.py` at unix `1787570799` (2026-08-24 16:56:39 IST). Test 3 was
  not changed. The disarm is a mechanism rejection, not a causal effect result.
- Official board at the 19:10 authenticated refresh: account-best Test 1 is
  persuasion rank 2 of 76 at `2449.4` (top 2.7%), `106.4` behind leader gill
  bates and `12.6` ahead of rank 3 expert. Test 2's persuasion component is
  `2436.3`; it is the account's overall rank-5 agent at `2328.9`, `29.9` behind
  rank 3 Clod. The prose arm remains absent on both Test 2 and Test 3.

## Rejected rank-gate mechanism

The rank gate did not implement its stated scope. It reached p=.8 cells, flipped
both buy-to-pass and pass-to-buy, used a local CDF that pooled six official
configurations, and applied a recommendation-only threshold to explicit seller
declines. Across 267 treatment games it changed 828 turns; 539 were unintended
p=.8 buy-to-pass changes. A verified threshold-zero case bought a low unit after
an explicit “I do not recommend this one” message and lost 1,000,000. No result
conditioned on changed turns, purchases, or the 83/495 locally recovered finals
is admissible. The remaining 412 unresolved outcomes also block any ITT read.

## Next safe causal experiment

`GLEE_PERS_P08_R125_PROSE_AB` is implemented default OFF. It targets only
persuasion seller/text/p=.8/seller-knows-CV/v=1.25P/20-round games. A stable
per-game SHA-256 bit leaves control messages byte-identical `yes`; treatment
uses the current six quality-neutral prose combinations. Recommendation choices,
negative messages, seller-blind cells, binary mode, buyers, bargaining, and
negotiation are unchanged.

Preflight after all three hosts loaded commit `2f4989d` used 800 seeded
persuasion games per exact live stack. Test 1 reported
`eligible=320/fired=160/action_changed=160`; Test 4 reported `220/100/100`;
Agent 5 reported `160/60/60`. Focused implementation and reader tests pass. The
full allowed suite finished with 1,061 passes and only the two pre-existing
bargaining failures.

Deployment boundary: only Test 1 (`champion`), Agent 5 (`composite`), and Test 4
(`randomized`) are research hosts. They naturally loaded commit `2f4989d` as
PIDs 68351, 68203, and 67641 respectively, with no restart or signal. Fleet
tooling then set `GLEE_PERS_P08_R125_PROSE_AB=1` and the explicit inert
`GLEE_PERS_TOKEN_MAX_P=0` on those three only. Clean common T0 is arms mtime
`1787575521` (2026-08-24 18:15:21 IST). Test 2 and Test 3 remain unarmed.

## Official transcript diagnosis at activation

The authenticated dashboard's latest 20 Test 2 persuasion games were read in
full, including every positive, negative, zero, refusal, and all-round outcome.
Buyer games contributed -13.3 official rating over 8 games (mean -1.66; 6/8
negative), while seller games contributed +7.2 over 12 (mean +0.60; 5/12
negative). This is a diagnostic window, not a treatment result.

Two mechanisms were directly visible. In the exact prose-arm cell (seller,
text, p=.8, known CV, v=1.25P, 20 rounds), the buyer bought four literal `yes`
messages, observed one low product, then passed the remaining 16 `yes` messages;
our +4P payoff still lost 5.2 official rating. Dashboard transcript setup does
not show text versus binary mode, so this classification is joined to local game
`e03c909a-2fb4-4922-bd59-9b609c042e42`; an adjacent -6.2 binary game is not in
the arm's target cohort. Separately, the legacy buyer
parser bought three seller messages saying `Not recommended.`; all three were
low, the game ended at zero, and it lost 4.0 official rating. The latter agrees
with the existing default-off `GLEE_PERS_PARSE_V2` evidence (historically 373
such purchases, 373 low, 0 high), but it is not co-armed here: any buyer-parser
trial needs its own stable per-game randomisation and official precommit.

Decision boundary: first official read at 120 resolved dashboard rating deltas
per arm, using every assigned game. Unresolved, invalid, official-join, wire, or
self-play contamination blocks promotion. Full rules and subgroups are
precommitted in `.ai/EXPERIMENTS.md`. The local percentile reader is diagnostic
only; official per-game dashboard deltas control promotion/rejection.

## First live mechanism observation

Candidate game `202cb810-c1a7-4d36-b98b-7d394842d258` on Test 1 is the first
post-T0 target draw. Its hash was candidate on all 20 rounds; all 20 plan records
carried `p08_r125_prose`, recommendation stayed `true`, and the wire contained
only five members of the approved six-message bank. The game completed normally
with 4/20 purchases (3 high, 1 low), seller payoff `4P`, no invalid/timeout, and
official dashboard rating delta `-4.3`. The buyer passed all 16 rounds after the
first bought low. This is a clean but adverse first treatment observation, not a
decision; the precommitted sample and stop rules remain unchanged.

## Expanded official failure diagnosis and next isolated arm

The authenticated dashboard was joined to the current Test 2 wire log for 37
deduplicated completed persuasion games from roughly 18:30-18:45 IST. This is
an all-outcome descriptive window, not an A/B result. The largest observed
cells were seller/binary/p=.8/known-CV/v=1.25P (`-7.6`, n=1),
buyer/p=.8/v=1.25P (`-6.9`, n=1), seller/p=.8/unknown-CV (mean `-3.70`, n=2),
buyer/p=.8/v=1.20P (mean `-2.50`, n=3), and seller/p=.33/unknown-CV (mean
`-1.12`, n=6; 4/6 negative). Small cell counts prohibit promotion, but they
localize the repeated mechanisms.

In exact seller game `6516c6b7-2a47-4919-b192-cd0484e21daa`, the current
all-yes policy sold round 1 high and round 2 low; the buyer then passed every
remaining round, including 14 highs, and the official delta was `-7.6`. Across
170 deduplicated completed comparable all-yes games, mean purchases were only
7.29 despite 16.04 high items, 35/170 sold nothing, and 42 buyers stopped
completely after a bought low. By contrast, opponents that beat us as sellers
often emit explicit negatives on bad items and make positive messages strongly
predictive; opponents that beat us as buyers stop or sharply tighten after the
first caught lie. The current stack sometimes does neither: it can recommend
every low at the p*v==price knife edge, and the legacy parser has bought literal
`Not recommended.` messages (373 historical purchases, all 373 low).

`GLEE_PERS_P08_R125_BINARY_TRUTH_AB` is implemented default OFF in pushed commit
`8372236` and remains inert pending Test 2's natural load. Test 2 rotated at
19:02:25 IST, before that commit was pushed, so it must not be armed until its
next supervisor-managed rotation. It targets
only the binary counterpart of the prose cell: seller, p=.8, visible v/u,
v=1.25P, u=0, 20 rounds. Hash controls are full-object identical; candidates
say `yes` on high and `no` on low. Test 2 exact-stack reachability over 800
seeded games reported `eligible=31/fired=21/action_changed=21`; the focused
mechanism/official-reader suite passed 31 tests. The full allowed suite passed
1,167 tests with only the same two pre-existing bargaining failures. If
activated, it is Test 2 only
with prose absent and rank-gate/backload explicit zero; Test 3 remains untouched.
The fixed read is 40 official outcomes per arm with a 20/arm harm look and at
least 8/arm at each price scale. Full precommit is in `.ai/EXPERIMENTS.md`.
