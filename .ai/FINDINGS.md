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

## Opponent identity IS available at decision time (22 Aug)
- The turn payload carries `opponent: {name, type}` from ROUND 1. Names are
  disclosed in ~50% of games: 27,860 named vs 27,869 `type=hidden` across
  55,775 games; 182 distinct opponents overall, 164 in negotiation. An earlier
  browser-side probe concluded GLEE hides opponent identity -- that is true of
  the WEB api and FALSE of the agent api. Opponent-conditioned policy is
  therefore available in half of all games, and `sim/replay_eval.py` already
  models the disclosure coin at 50%.
- We also draw our OWN agents as opponents (champion/test3/test4 appear in the
  opponent field), so cross-agent comparisons can be contaminated by self-play.

## GLEE_OPP_EXPLOIT: built, never armed, and its DEFAULT is the harmful setting
- Per-opponent bargaining accept thresholds vary enormously and really are
  exploitable: chotu accepts at 0.257 (we keep 74%), Ira 0.168, against
  Rubinstein 0.679 and test4 0.622. 33 opponents now carry a usable profile
  (n>=30) covering 4,779 games.
- Arena, bargaining, 4,000 games x 2 seeds, control = Agent 5's live 26-flag
  set. EST. PERCENTILE by `GLEE_OPP_PAD` (the safety margin above the fitted
  threshold), seed 811 / seed 4272:
      0.04 (the CODE DEFAULT)  -0.0033 / -0.0035   <- actively worse
      0.08                     +0.0037 / +0.0000
      0.12                     +0.0020 / +0.0008
      0.16                     +0.0030 / +0.0014   <- best, both seeds positive
  So arming this flag at its default would LOSE rating; the fitted thresholds
  are too aggressive and need ~4x the default padding. Effect is small but
  free: ~+0.002 average percentile, i.e. roughly +3 rating on the fitted
  calibration (12.5 pts per percentile point) or up to +18 on the raw
  affine map. Seed 4272 never reaches significance alone; the case rests on
  6/6 runs at PAD>=0.08 being >=0 against 2/2 negative at 0.04.
- `models/opponent_profiles.json` REFIT 22 Aug on current logs: usable
  bargaining profiles 27 -> 33, games 2,218 -> 4,779, 10 thresholds materially
  changed (V-Agent 0.50->0.64, theta 0.47->0.55, cobbylab 0.29->0.38). The
  refit barely moves arena outcomes; PAD dominates. Profiles should be refit
  routinely -- they were 2 days stale.
- CAUTION recorded: the refit rewrote the profile file WHILE a sweep was
  running, so that sweep mixed old and new profiles. Never refit a model file
  concurrently with an arena run that reads it.

## Bargaining assumptions that turn out NOT to matter (22 Aug)
- The real discount factors are uniform over {0.8, 0.9, 0.95, 1.0} (17,177
  games; mean 0.9133, median 0.95), and the OPPONENT'S delta is hidden in
  49.9% of bargaining games -- so `GLEE_BARG_UNKNOWN_DELTA` (assumed 0.90)
  prices half the family. It looked like a systematic mispricing: we assume
  opponents are less patient than they are.
  MEASURED NULL. Arena, bargaining, 4,000 games x 2 seeds vs the live control:
      0.9125 (the true mean)   +0.0001 / +0.0000, CI [-0.0003,+0.0007]
      0.95   (the true median) +0.0008 / -0.0009, sign-flips across seeds
  The 0.9125 CIs are tight, so this is a well-measured null rather than an
  underpowered one -- the assumed delta barely reaches the submitted numbers.
  The SPE share is dominated by the accept/offer floors instead. Do not revisit.
- Horizon: disclosed games are always max_rounds=12, undisclosed always read as
  the 99 'infinite' horizon (8,546 vs 8,631 games), so
  `GLEE_BARG_UNDISCLOSED_HORIZON=99` is already correct.

## THE STEP ACCEPTANCE FRONTIER (22 Aug) -- the strongest structural fact found
- In ONE-ROUND COMPLETE-INFO negotiation the field's acceptance is a STEP
  FUNCTION of whether it is left anything at all. Our own posted asks, live:
      share of span asked   closed / n
      [0.0,0.1)              65 / 65    100%
      [0.1,0.2)              18 / 18    100%
      [0.2,0.3)               5 / 5     100%
      [0.3,0.4)             104 / 104   100%
      [0.4,0.5)              24 / 24    100%
      [0.5,0.6)              11 / 11    100%
      [0.7,0.8)              48 / 48    100%
      [0.8,0.9)             109 / 109   100%
      >=1.05                  0 / 78      0%
  384/384 closed below 0.9; 0/78 closed at or above 1.05. Rejection pays the
  opponent exactly zero in a one-round game, so they take any positive crumb.
  We currently ask exactly 0.800 (= GLEE_NEGO_ULTIMATUM_SHARE) on Test 1,
  Agent 5 and Test 3, so the [0.80,0.90) band is free surplus we decline.
- Test 2, which does NOT carry the flag, asks a mean 1.155 of span in this cell
  -- above the whole zone, i.e. a guaranteed no-deal. That is a live diagnosis
  of why its negotiation rating (1928) trails its flagged siblings.
- HISTORICAL NOTE, not a bug: 655 of 784 logged one-round turns show
  ultimatum=False. Those predate the flag's deployment or come from Test 2.
  Verified over the last 6h on current code: mean ask 0.800 with ZERO asks
  below 15% on all three flagged agents.

## GLEE_NEGO_ZOPA_SHARE is the largest measured gain to date
- The parameter is how much of the visible span we LEAVE the opponent
  (default 0.39, i.e. we keep 61%). Arena, negotiation, 4,000 games x 2 seeds,
  control = Agent 5's live 26-flag set:
      0.30   +0.0100 / +0.0099   both CIs excluding zero
      0.22   +0.0113 / +0.0119   both CIs excluding zero
  Close rate moves only -0.001 to -0.003, so this is almost pure price capture,
  exactly as the step frontier predicts: the field accepts on positivity, not
  on fairness.
- FULL CURVE, with a clean INTERIOR OPTIMUM at 0.10 (share we leave them):
      0.39 (default)  baseline
      0.30            +0.0100 / +0.0099
      0.22            +0.0113 / +0.0119
      0.15            +0.0115 / +0.0116
      0.10            +0.0127 / +0.0123   <- peak
      0.05            +0.0111 / +0.0099   <- declines again
  Falling away on BOTH sides is the signature of a real effect, not drift.
- CONFIRMED on a THIRD seed (7777): +0.0114. Four independent measurements
  of the 0.10 setting: +0.0127, +0.0123, +0.0114, +0.0118 -> mean +0.0121,
  every CI excluding zero. Close-rate cost is -0.005.
- NO SPILLOVER: run across bargaining+negotiation, bargaining reads exactly
  +0.0000 with a zero-width CI. That is the CORRECT signature here -- the
  parameter is read only in negotiation.py (:325, :352, :1099) so the two arms
  really are the same code path in bargaining.
- DO NOT COMBINE with a raised ultimatum share. ZOPA_SHARE=0.10 plus
  GLEE_NEGO_ULTIMATUM_SHARE=0.90 gives +0.0108 / +0.0102 -- WORSE than 0.10
  alone -- and doubles the close-rate cost to -0.010. Once the zone share is
  aggressive, pushing the one-round ask too costs more than it gains. The live
  step frontier suggested 0.90 was free surplus; against the full stack it is
  not. Keep ULTIMATUM_SHARE at 0.80.
- INSTRUMENT CHECK (run independently before trusting the number): the fitted
  CDF is not extrapolating. Complete-info negotiation cells carry 115-126
  observations each; the percentile at the top of the range is the well
  determined COUNT of field payoffs below it (SE ~0.014 at n=126), and the tail
  is thin because few opponents score there -- which is the point. Bottom-up
  cross-check: the median percentile gain from asking 61% to 90% of cell max is
  +0.125 per complete-info game, and complete-info is 27% of the family, for a
  ceiling of ~+0.034. The measured +0.0121 is about a third of that ceiling,
  which is what partial capture should look like.
- `GLEE_NEGO_RECIP_DAMP` at 0.5 is NEGATIVE (-0.0002 / -0.0008) -- leave off.

## Codex red team, 22 Aug: BARG_ECON_STALL is the strongest live hole
- MECHANISM (Codex, verified by me): after three distinct offers whose
  discounted projected improvement is <=2%, the acceptance floor is ZEROED, and
  with GLEE_BARG_STONEWALL_MIN=0 the extortion guard is off. Acceptance is
  `offer >= 0.98 * realistic`, so the trigger arithmetic 0.98*1.02 = 0.9996
  effectively guarantees we accept. bargaining.py:663, arms.json.
  Codex's deterministic replay: attacker crawls 17.45% -> 17.71% -> 19.64%, we
  accept round 5, attacker percentile .9788 against our .0389; over 1,200 games
  the attacker scores .527 versus the cloned field's .306.
- IT FIRES LIVE: `econ_stall_release` appears in 91 Agent 5 plans and 25 Test 3
  plans, every sampled one ending in accept. (A first check for it in
  `gates_fired` was a FALSE NEGATIVE -- the block never calls `_gate()`, it
  writes the key straight into the plan. Absence from a trace list proves
  nothing unless the code actually records there.)
- BUT THE LIVE DAMAGE IS MODEST, not the worst case. Share we accepted,
  Agent 5 + Test 3: normal accepts mean 0.4381 / median 0.4520 (n=3,103);
  econ-stall releases mean 0.4113 / median 0.4400 (n=115). So it costs ~2.7pp
  of the pot on 3.6% of accepts, and its sub-30% accept rate (8.7%) matches the
  normal path (8.5%). The .9788/.0389 scenario needs a DELIBERATE adversary; the
  current field is not aiming at us.
- REMOVING IT IS A SMALL WIN ANYWAY. Arena, bargaining, 4,000 games x 3 seeds
  vs the live control: `GLEE_BARG_ECON_STALL=0` gives +0.0016 / +0.0017 /
  +0.0009, all positive, two CIs excluding zero. Adding STONEWALL_MIN=0.30 on
  top changes nothing (identical numbers -- same code path once econ-stall is
  off). Consistent with Test 1, which does NOT carry the flag and holds the
  fleet's best bargaining rating (2216 vs Agent 5's 2195).
  => Turning it off is better on average AND closes the exploit. Deploy it.
- Codex also reports, and this is worth keeping: DEADGAME_V1 is NOT profitably
  counterfeit-able (it needs our own 1.5xB seller / 0.8xB buyer type, which the
  attacker cannot manufacture, and harvesting the collapse requires the attacker
  to accept a loss). Other named cliffs to check later: the span veto is a
  STRICT `<0.48` so an attacker leaving 48.1% closes immediately; the real-final
  any-positive rule bypasses the span invariant entirely, so a repeated 0.801B
  bid can take 99.86% of span; and the k=2.0 Boulware walk can be waited out
  with changing-but-unprofitable asks that dodge the stall detector.
- NOT A BUG, checked and cleared: bargaining has NO zero-share accepts. 49 of
  8,087 accepts (0.6%) are under 5%, spread evenly across slots. An earlier
  "min 0.0000" was display rounding of a small positive share.
