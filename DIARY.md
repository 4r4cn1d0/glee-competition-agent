# DIARY

## CURRENT STATE

UPDATED: AUG 23 - 02:25 IST.
LEADER: Test 3, 2168 overall (Test 1 2143, Test 2 2113, Agent 5 2061, Test 4 2056). Leader flips between Test 1 and Test 3 on the hour -- always re-check from the API before deploying, never from memory.
CONTROLS: Test 1, Agent 5, Test 2 and Test 3 run the identical 39-flag `champion` baseline; no behavioural differences among them.
TREATMENT: Test 4 = baseline + hidden-info anchors (SELLER 1.8 / BUYER 0.50, FULL not arm) + complete-info OPEN_CLAIM 0.95 / CLAIM_FLOOR 0.80 (hash arm). The anchors bind only in hidden games (hidden opens 3.97x cost, complete-info 1.24x), so the two do not confound. ALSO GLEE_BARG_OBSERVED_GAIN=1 from 03:33 (bargaining, provisional).
LIVE EXPERIMENT: Test 4 open-claim/floor; prediction +0.02 to +0.06 percentile, lower close rate, genuine negative risk.
KILL RULE: At 150+ complete-information games, revert if percentile is negative with CI excluding zero, or close rate falls >20pp without a percentile gain.
DEPLOY BASELINE: Test 4 negotiation 1811.6 and already +0.0104 versus the control mean; judge by difference-in-differences, not versus zero or displayed rating.
FIRST READ: 02:00, n=24; zone share 0.544 -> 0.775, close rate 100% -> 91.7%, percentile +0.134 CI [-0.058,+0.312]; mechanism works, outcome underpowered.
BUILT BUT OFF: `BARG_NO_REGRESS`, `BARG_MSG`, `NEGO_RANK_PRICE_AB`, `NEGO_SURPLUS_PROBE`, `NEGO_ZOPA_AB`, `NEGO_CLOSE_AB`, `PERS_BACKLOAD_AB`, and the ZOPA clamp/ultimatum floor/cap guards; the knife-edge persuasion fix was not built.
WORKTREE, OFF/UNDEPLOYED: `NEGO_HIDDEN_FLOOR` and `NEGO_HIDDEN_POLICY_V1`.
LOCAL SIM: Always enable opponent clone V2; the legacy clone is invalid for pricing work.

## AUG 23 - 03:33 IST

WHAT: Turned GLEE_BARG_OBSERVED_GAIN=1 on TEST 4 only. Provisional -- revert if Codex's transcript analysis disagrees.
WHY: bargaining.py:610 already documents the defect: the haggling-gain constant G is hardcoded at 0.05 pot/round but measured at +0.0012 median over 899 games, "wrong by 40x". With G=0.05 the accept floor demands 0.20/0.45/0.50 of the pot at delta 0.8/0.9/0.95; with the real G it is 0.012/0.027/0.057. So we refuse early money and hold for a concession that never comes. Six operator transcripts show it: one ran 42 rounds and kept $609 of a $10,000 pot where the round-1 offer was worth $4,000.
RESULT: Pending. Baseline Test 4 bargaining 2379.0 (1,229 games) -- our BEST bargainer, so this is being tested on the agent with the most to lose. Flag is runtime-read, so reverting takes 3 seconds. KILL: revert if Test 4 bargaining percentile drops below the control mean by more than 0.03 over 200+ games, or if Codex names a different primary cause.

## AUG 23 - 02:53 IST

WHAT: Test 4 hidden-info opening changed FULLY (not an arm): SELLER_ANCHOR 4.0 -> 1.8, BUYER_ANCHOR 0.15 -> 0.50. Complete-info open-claim arm untouched.
WHY: Our hidden opening is 3.97x our own value; the field opens at 1.54x. Controlling for own-type, the absurd >=3x opening scored WORST in 8 of 8 cells; at buyer-1.0 a credible opening closed 25.8% vs 15.7% AND took 0.717 of the zone vs 0.500. More deals and more share at once, so this is not a trade-off.
RESULT: Pending. Baseline at deploy: Test 4 nego 1914.1 (1,133 games); controls Test 1 1912.1, Test 2 2013.3, Test 3 1947.6, Agent 5 1953.1. Anchors are config-only so this arms at Test 4's next rotation, not immediately.

## AUG 23 - 02:45 IST

WHAT: RED-TEAMED and REJECTED Codex's grid-aware hidden policy (NEGO_HIDDEN_POLICY_V1). Not deployed.
WHY: Its terminal boundaries would refuse 42.3% of deals we currently close (74% of buyer-1.0, 62% of seller-1.2). Simulating each boundary on real games, expected percentile fell in all 6 cells (-0.015 to -0.064), and the optimum in 4 of 6 was to refuse NOTHING. Its boundaries also do not overlap for feasible pairings: seller-1.2 holds 1.425 while buyer-1.5, its only feasible counterpart, holds 1.275.
RESULT: Rejected. The diagnosis that followed is the useful part: the top agents close MORE (opus 5 40.8%) AND take more (0.757) than us, so "trade closes for share" was never their mechanism. Our defect is the OPENING, not the floor.

## AUG 23 - 02:10 IST

WHAT: Proposed then withdrew a persuasion fix for p*r=1.00, our worst cell at 0.462; no flag was built.
WHY: The supporting low-lie inverted-U was a time artifact: every low-lie observation was >24h old, while the current field lies 80-100% there.
RESULT: Cell remains weak and unexplained. METHOD FAILURE: pooled history is not current behaviour; cut every field comparison by time window.

## AUG 23 - 02:00 IST

WHAT: Took the first read of Test 4's open-claim experiment, n=24 complete-information games.
WHY: Claimed zone share moved 0.544 -> 0.775, confirming that the treatment reaches and changes the intended mechanism.
RESULT: Close rate 100% -> 91.7%; percentile +0.134 CI [-0.058,+0.312]; direction right, far too few games, pending.

## AUG 23 - 01:22 IST

WHAT: Reconstructed hidden opponent values in 3,104 closed games from buyer value = payoff + price and seller cost = price - payoff.
WHY: We capture median 0.520 of the true zone; leaders capture about 0.75.
RESULT: Direction shifted from chasing already-near-ceiling close rate to taking more of deals that already close.

## AUG 23 - 00:24 IST

WHAT: Set `GLEE_NEGO_OPEN_CLAIM=0.95` and `GLEE_NEGO_CLAIM_FLOOR=0.80` on Test 4 only, complete-information games only.
WHY: Across 7 ranked opponents and 157 games, every 2195+ agent opened claiming 0.92-1.05 versus our 0.681; rating/opening correlation was +0.60, and their final positions exceeded our opening.
RESULT: Pending; predict +0.02 to +0.06 percentile with fewer closes and negative risk. Kill per the 150-game rule above; deploy baseline 1811.6 and +0.0104 versus controls.

## AUG 22 - 23:19 IST

WHAT: Put the +82-predicted parameter-search config on Test 4; reverted it at 00:24 after about one hour, before readout.
WHY: It tuned parameters inside the conceding regime that rival evidence identified as the problem.
RESULT: Withdrawn. METHOD FAILURE: searching the clone's support is not searching policy space; local optimization cannot discover an unplayed regime.

## AUG 22 - 22:30 IST

WHAT: Fixed simulated `game_id="local"` and added `sim/clone_fidelity.py`; V2 became the required negotiation opponent clone.
WHY: Every randomized arm was 100% one arm locally and half produced byte-identical false nulls; the legacy clone was worse than always guessing and +16 points optimistic where pricing decisions live.
RESULT: Seed-derived IDs restore arm variation; V2 has 86.6% accuracy and 4.9% worst calibration error.

## AUG 22 - 18:05 IST

WHAT: Self-inflicted outage, 18:05-19:41: about 31 timeouts, four 30-minute queue bans and about 90 minutes of play lost.
WHY: `fleet.py` safe-restart falsely reported success while agents spun at 99% CPU instead of draining; the watchdog then killed ban-idle agents and extended the bans.
RESULT: Both defects fixed in `a512ae3` and `628fe37`.

## AUG 22 - 16:24 IST

WHAT: Unified all five agent-slot configs on one 39-flag policy: Test 1 bargaining, Test 3 negotiation and Agent 5 persuasion, including never lying where p*r<1.
WHY: No tested A/B had won; identical behaviour was required for a clean baseline and cross-agent noise measurement.
RESULT: Baseline epoch 16:24:50 IST; four live processes completed rotation and Test 4 was configured but inactive. Every `control.json` slot maps to `champion` because PROBE overrides six env knobs; identical arms alone are insufficient.

## AUG 22 - 15:20 IST

WHAT: Enabled `GLEE_NEGO_HORIZON_V2` on Test 2, the only agent missing it.
WHY: It priced above the buyer's own value in 84.2% of complete-information seller openings.
RESULT: Post-change mechanism check fell 93.4% -> 0.0%.

## AUG 22 - 13:53 IST

WHAT: Disabled `GLEE_PERS_BACKLOAD_AB` fleet-wide and restored all-push.
WHY: In strict p*r>1 cells, all-push beat backload by +0.391 percentile, CI [+0.326,+0.455].
RESULT: Losing arm killed. METHOD FAILURE: realised q is not assigned arm; recover the randomized assignment rather than grouping by observed behaviour.
