# FINDINGS — validated empirical facts only

Each line is something measured, with its sample. Hypotheses do NOT belong here;
they go in EXPERIMENTS.md until they have evidence.

## Structure of the games
- Negotiation config mix (810 games, Test 1, 21 Aug): hidden 76% / complete 24%;
  seat 50/50; horizon 35% one-round, 31% ten-round, 33% uncapped; messages 50%.
- **Feasibility is a STRUCTURAL CONSTANT of the grid, now read off the
  generator** (`sim/grid.py:244 NEGOTIATION_VALUE_CONDITIONS`, a 22-point axis):
  * **complete-information cells: 6 of 6 have a ZOPA.** A deal is ALWAYS
    available when we can see the opponent's value. Confirmed empirically:
    911 of 911 live complete-info games had V_b > V_s, zero exceptions
    (4 slots, 10h, 22 Aug). Min span 20, median 3,000.
  * **hidden-information cells: only 6 of 16 have a ZOPA (37.5%).**
  * Overall 10/22 = **45% of negotiation games are structurally infeasible**.
    The earlier "48% of that sample" line was this constant, measured noisily.
  * The opponent's value is NEVER revealed in a hidden-info game, not even in
    the final game_state. Per-game feasibility there is UNIDENTIFIABLE from our
    own logs; only the 37.5% cell rate is knowable.
- Only ~7.1% of offers in recent exports carry any text at all.

## Where rating is won and lost
- Bargaining responder seat ("Bob") was at the 28.8th percentile vs Alice's
  71.5th across 4,001 games. Fixed by the accept-floor; Bob is now the better
  seat (+0.474/game vs +0.020 in a 500-game export).
- Negotiation: complete-info games -0.91/game vs hidden-info +0.29/game
  (810 games, spans policy changes — direction credible, magnitudes need
  era-controlled replication).
- Complete-info closes capture a MEDIAN 49.4% of available surplus (n=192);
  only 14% land in the 45-55% band. Strong evidence of a 50/50 attractor.
- **Deal rates by information condition** (Agent 5 + Test 1 + Test 2, 3,100
  negotiation games, 10h, 22 Aug): complete-info **91.8%** closed (n=805),
  hidden-info **29.6%** closed (n=2,295). Against the structural ceilings above
  that is ~92% of feasible complete-info deals and **~79% of feasible
  hidden-info deals** — NOT the 30% a raw close-rate reading suggests. Total
  remaining prize is ~8% of negotiation games, not ~50%.
- **We are not rejecting profitable offers.** Across 14,732 decision turns in
  hidden-info games that ended in no deal, only **89 (0.6%)** had an opponent
  offer that was profitable for us. The no-deal outcome is the opponent never
  reaching a feasible price, not our accept threshold being too high.
- **Our concession path is outcome-blind until round 8** (Agent 5, hidden-info,
  10h). As seller we open at 3.97x our own cost and are still at 2.94x by round
  6; as buyer we open at 0.16x our own value and reach 0.82x only by round 9.
  Medians for eventually-deal and eventually-no-deal games are IDENTICAL for
  rounds 1-6 and only diverge at round 8. max_rounds is 10 in 84% of games.
- Persuasion p=0.8 buyer cells all beat their breakeven when measured POOLED
  (good% 83-92% vs breakeven 80-83%). An earlier per-game average said
  otherwise and was biased by games with few purchases.

## Instrument calibration
- EST. PERCENTILE vs real rating deltas: bargaining R^2=0.667, ~12.5 rating
  points per percentile point, monotone across all deciles.
- Persuasion percentile cells: R^2=0.329, non-monotone above the 70th — coarse
  screening only, never promotion-grade.
- Cross-agent noise floor on IDENTICAL code: ~+/-125 rating in persuasion
  (measured over 10h). Any smaller cross-agent gap is uninformative.

## Things that measured NEGATIVE (do not retry without new reasoning)
- LLM-worded persuasion messages: 46.3% conversion vs 55.3% for templates.
- Ultimatum share 0.90/0.95 (vs 0.80): -0.003 and -0.012/-0.015, closes -1.6 to
  -2.0pp. The "field takes 88%" statistic that motivated it was survivorship-
  biased — agreed prices exist only for ACCEPTED asks.
- Stonewall release (unguarded): -200 rating live over ~5h, reverted.
- Per-opponent bargaining exploitation: -0.0043, stripped.
- Response-model offer engine: sign-flipping across two V_cont fits — the causal
  continuation value of an unplayed ask is not identifiable from our own logs.
- High-water regret guard, LCB buyer, freeze-probe, boulware glide, margin 0.55.

## Known traps in this codebase
- The record ECHO: a counteroffer is re-recorded as the next round's offer.
- The SYNTHETIC planning clock: rounds_left/elapsed are fiction when not capped.
- Flags nested under a gate the arena control omits read as clean +0.0000 nulls.
- Clearing an arms.json key does not disarm a RUNNING agent.
- `models/nego_policy_v1.json` has ZERO ask cells — GLEE_NEGO_TABLE is four
  acceptance thresholds and nothing more.

## Measured NEGATIVE — do not re-propose without new reasoning
- **Faster concession (`GLEE_NEGO_BOULWARE` 1.2 vs the 2.0 default) is WORSE:
  -0.0166 / -0.0182, both seeds, CIs excluding zero, close rate -0.025.**
  CORRECTED 22 Aug: the first run of this reported -0.041/-0.050 and was
  measured through the replay_eval overlay bug below, which stripped the whole
  flag stack from the candidate arm. Direction unchanged, magnitude was
  overstated ~2.5x. Re-measured against Agent 5's real 26-flag live set. Crucially the **close rate FELL 4-5 points** as well, so
  the intuition "concede sooner and you close more" is exactly backwards
  against this field — the cloned opponents pace against our curve and harden
  when we soften early. The `k~1.18` figure in the source comment describes the
  FIELD's schedule; it is not the best reply to it. Reachability note: BOULWARE
  is a continuous `as_float`, never a traced `_gate()`, so `fired_count` is
  structurally 0 and only `action_changed` (3,595/6,257) is meaningful.

## Instrument defects found
- **`GLEE_NEGO_SURPLUS_PROBE` is INVALID as run, and contaminates live play.**
  The arm is assigned inside `plan()` (negotiation.py:404) BEFORE the offer /
  decision branch, and it overwrites `p["target"]`. But `target` also drives
  the ACCEPT path: `negotiation.py:1046` compares the incoming offer directly
  against `p["target"]`, and `negotiation.py:760` uses it as the continuation
  ceiling. So the randomiser moves our accept/reject threshold in complete-info
  decision turns where nothing was ever offered — the treatment leaks into the
  outcome channel, and the experiment cannot identify P(accept | x).
  Found by Codex on its first review; verified independently at both call sites.
  Live on Agent 5 and Test 3 (~0.6% of negotiation turns). Only 5 assignments
  banked, so nothing is lost by disabling it.
- `scripts/analyze_surplus_probe.py` compounds this: it joins the SAME round's
  decision rather than the opponent's response to a transmitted price, never
  checks `decided_by`, and computes only `P(accept)*x` despite the docstring
  promising a continuation term.
- Codex flags a live no-ZOPA seller rule (negotiation.py:319, floors asks at
  1.15x cost) whose justifying "39% positive" figure `scripts/fit_percentile.py`
  itself calls a phantom from pooling buyer and seller roles. UNVERIFIED by me
  — next thing to check.

## Better objective for any surplus-share experiment (Codex, unverified)
Rating is affine in percentile, so there is no variance premium; and a no-ZOPA
cell where everyone scores 0 gives every player midrank 0.5, which dilutes
signal but cannot lower rating. The quantity to maximise is therefore rank, not
surplus: `F(0) + P_accept(x) * [F(payoff(x)) - F(0)]`, where F is the empirical
payoff CDF for the exact cell. Because F has large atoms at 0 and at the even
split, landing one tick above an atom can buy a lot of rank for almost no extra
rejection risk — an effect a coarse 0.05 grid on x can step straight over.

## Instrument defects found and FIXED
- **`sim/replay_eval.py` REPLACED the control flag set with the candidate
  instead of overlaying it.** `_set_flags` clears every GLEE_ key before
  applying an arm, so `--candidate '{"GLEE_NEGO_BOULWARE":"1.2"}'` played an arm
  carrying that one flag and NOTHING else. Every such run measured "strategy
  with no flags vs strategy with fifteen", which swamps the flag under test and
  reads as a large spurious negative; it also silently disarms gates the
  candidate needs, so a sweep nested under `GLEE_NEGO_ENDGAME_V3` returned
  BIT-IDENTICAL numbers for three different settings because the gate was off in
  all three. FIXED 22 Aug: candidate = {**control, **overrides}, both printed,
  plus warnings for an empty override set and for overrides equal to the
  control. Prefer `--control` = the live arms entry so results transfer.
  DIAGNOSTIC: identical numbers across genuinely different settings, or a
  zero-width CI, means the arms are the same code path -- not a null result.

## Measured NEGATIVE (continued)
- **Fishing earlier in dead games is worse.** `GLEE_NEGO_DEADGAME_MINOFF` 1 and
  2 against the hardcoded 4: -0.0022 / -0.0017, both seeds, CIs excluding zero,
  close rate -0.003. The reasoning that the arithmetic own-draw gate makes the
  evidence threshold redundant is WRONG in measurement. 1 and 2 are equivalent
  in practice (the effective offer count is never exactly 1, since `last_offer`
  is counted alongside history), verified directly. Flag left in at default 4.

## Already implemented -- do not "discover" again
- **Infeasible-cell harvesting is DONE, both seats, by `GLEE_NEGO_DEADGAME_V1`**
  (negotiation.py ~line 565). It gates on exactly the structurally dominated
  draws (1.5xB seller, 0.8xB buyer), cites the same 97-100% zero-rates, and
  prices at `max(0.10*(1-elapsed), 0.02)` above own value -- an ask of ~1.013x
  cost late, which is already the acceptance-maximising play.
  A 22 Aug proposal to add a `GLEE_NEGO_HARVEST_MARGIN` and "the missing buyer
  branch" was redundant on both counts and measured EXACTLY +0.0000; reverted.
  The `1.15 * my_value` reservation at negotiation.py:336 that Codex flagged is
  real but INERT in the games that matter -- deadgame overrides it with a far
  lower ask, so the phantom "39%" it was calibrated on costs nothing in practice.
