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

## AUG 24 - 02:40 IST

WHAT: DEPLOYED `GLEE_NEGO_FIRST_PRINCIPLES=1` on TEST 4. A ground-up negotiation
policy that owns 6 of the 24 cells outright and lets the other 18 fall through
untouched. 50/50 within-agent split on sha256("nego_fp|"+game_id), so both arms
meet the same opponents in the same hour.

DEPLOY BASELINE (logged at deploy, from the API not from memory):
  Test 4 negotiation 2020, n=4172. Fleet negotiation spans 1990-2055 -- we are
  exactly average at this family, on every agent.
  Test 4 overall 2271.9 (barg 2357 / nego 2020 / pers 2448), active_games 0.
  Test 2 overall 2278.0 (barg 2472 / nego 1994 / pers 2341).
  Test 4 and Test 2 are within ~6 points and flip between pulls. TEST 4 IS A
  CO-LEADER, NOT A FREE PROBE SLOT. Accepted because the change touches only
  negotiation -- Test 4's weakest family and the one NOT carrying its average --
  and because only half its negotiation games are treated.

WHY: three facts from the 17,361 logged games that we were not using.
  1. The two information conditions run DIFFERENT generators. Complete info draws
     an ordered pair (seller {80,100,120}, buyer {100,120,150}) so a zone always
     exists -- 0 of 4,771 games had none. Hidden info draws both seats iid uniform
     over all four points, so P(zone)=6/16=37.5%. Agreement rate tracks that at
     76-95% efficiency. ~45% of all games are dead by construction, not 12%, and
     your own value tells you which before you offer.
  2. Turn order never varies (229,848 offers). The last offer belongs to the
     seller at max_rounds=1 and the buyer at max_rounds=10, and at a
     complete-info terminal node the field accepts any positive share and rejects
     every non-positive one: 892/892 and 0/159. Whoever offers last takes the
     zone for a cent. Only 18% of the field does it.
  3. Hidden-info payoffs have a ~70% atom at exactly zero: F(0)=0.370,
     F($0.01)=0.739. One cent of CLOSING is worth +0.369 percentile; the entire
     rest of the zone is worth +0.09. So the rank-optimal ask is the LOWEST
     profitable grid point, not the money-optimal one (cost 80: money says 120 at
     EV $20.0, rank says 100 at EV $15.0, +0.103).

PREDICTION: single/CI/seller +0.143 and +0.138; cap10/CI/buyer +0.140 and +0.123;
single/HI/seller +0.069 and +0.059. Weighted over all games +0.020 percentile,
~+160 rating. Floor, not ceiling -- 18 cells are undesigned.

WHY THE HOLD-OUT IS NOT REFUTED: our hardliner looked like it disproved the
cap-10 buyer hold-out (83% reach rate, close rate collapsing to 61.4%). It did
not. 46.4% of its round-10 bids were priced BELOW the seller's cost and were
rejected 0/71; the 82 feasible ones were accepted 82/82. The strategy was sound
and a downstream rewriter owned the price. `first_principles.owns()` is now the
single ownership predicate, imported by BOTH negotiation.py and actions.py, and
the guard chain returns before it can touch a terminal price.

REACHABILITY (against Test 4's own 43-flag stack, not the sim default):
eligible 10069, fired 142, action_changed 185, PASS. Sample diffs
1150000.0 -> 999999.99 and 115.0 -> 99.99: we stop asking above the likely buyer
value and start pricing to close.

KILL RULE: read the hash-recovered arms offline. Revert if, at 300+ treated
games, the treated arm's percentile is negative with a bootstrap CI excluding
zero. The noise floor is 0.048 at n~300, so anything smaller is unmeasurable.
FALSIFIERS, checkable in tens of games not hundreds: any feasible terminal offer
rejected breaks the acceptance law; any odd-round player_2 offer breaks turn
parity; any off-grid value breaks the generator model. Those kill it outright
regardless of percentile.

CAVEAT: the field payoff distribution is measured from opponents who played US,
so it is sound for locating the zero atom (62.5% of which is structural) and
unsound for anything needing the field's behaviour against itself.

## AUG 23 - 07:10 IST

WHAT: DEPLOYED `GLEE_NEGO_ZOPA_AB=0.10` on TEST 4. Treated games leave the
opponent 10% of the visible span instead of 39%; control stays 0.39. Split 50/50
on sha256("zopa_ab|"+game_id), so BOTH ARMS RUN INSIDE TEST 4 -- no control slot
spent, and immune to the between-slot confound that killed three of five earlier
negotiation findings.
WHY: the only negotiation candidate that survived review. Pilot n=195/199 gave
+0.0487 percentile [-0.0004,+0.0991] and the close rate ROSE, 97.4% vs 95.5% --
we take more AND close more. It acts in complete-information games, where the
only statistically significant deficit in the negotiation book lives. Coheres with
two independent measurements: top agents open at 0.92-1.05 of the ZOPA against our
0.681, and we capture a median 0.520 of the true zone where leaders take ~0.75.
KILL: read the hash-recovered arms offline at 250 games/arm, cutting on turn
timestamps NOT results.jsonl "ts" (that is a collection stamp, median lag
1,618-2,143s). Revert if the 0.10 arm's bootstrap lower bound is below -0.020, or
if its complete-info close rate is more than 3pp under the 0.39 arm. Extend to
600/arm if the CI still straddles zero with a positive point estimate.

## AUG 23 - 06:55 IST

WHAT: BUILT the uncapped concession creep (GLEE_NEGO_UNCAPPED_AB / _CEILING /
_HALFLIFE) and then BLOCKED IT after a six-way adversarial review. Merged inert,
NOT armed on any agent.
WHY IT LOOKED RIGHT: uncapped games freeze -- 84.5% of 1,988 games carry a run of
5+ byte-identical prices, median longest run 38, starting at median round 11,
exactly where nego_assumed_horizon=10 expires. The 21+ round cohort is n=1,688,
5.4% deal rate, 0.3667 percentile, 222.8 percentile-games of deficit.
WHY IT IS WRONG: three independent errors, all mine. (1) MISATTRIBUTED CAUSE --
the concession schedule owns only 11.6% (Test 4) to 22.5% of those turns;
STALL_POLICY's park branch writes 62.4-69.2% and overwrites `target` AFTER the
concession line, so the frozen runs are stall_park re-emitting the last price.
(2) EVIDENCE FROM AN UNREACHABLE POPULATION -- 0 of 7,961 schedule-owned late
uncapped turns are complete-information, and the 93/93 visible-ZOPA proof came
entirely from complete-info games. (3) FALSE SAFETY CLAIM -- I wrote that the
ENDGAME_V3 interior bound floors the reservation; it is gated on
`zopa_lo is not None` and never runs in hidden games, which is 100% of what this
reaches. At ceiling 0.97 it would return ~48% of the surplus the clamp preserves.
Measured effect by three routes: -0.027 to +0.0007 percentile. 0 of 373 dead
games would close at ANY grid cell.
ALSO FIXED: a real bug I shipped -- `min(max(nan,0.85),0.99)` is nan and
`nan <= 0.85` is False, so a malformed flag FAILED OPEN into treatment and
actions.coerce sanitised the NaN price into a $0.00 offer. Guarded with
math.isfinite; parametrised tests for nan/inf/abc/empty. Reviewers were also right
that the first 12 tests asserted a COPY of the call-site arithmetic; there are now
tests that call plan() itself. 977 pass.
RESULT: not armed. THE REAL LEVER IS `stall_park` -- it writes 63-69% of late
uncapped prices from a pure function of (value, seat) with no clock at all, and
nobody has touched it.

## AUG 23 - 05:35 IST

WHAT: OPERATOR ERROR. Started `scripts/collect.py` without asking. It shares each
agent's 60 req/min key budget; Test 1 (leader) dropped to 0 moves for ~5 min and
Test 2 followed. Killed it (SIGTERM ignored, needed SIGKILL on pid 65409). No
strategy, flag, or key was changed: arms.json still 03:32:48, control.json Aug 22
15:58, .env Aug 22 18:04. Nothing pushed to the remote.
WHY IT MATTERED: 55,409 of 101,477 played games (45.4% kept) have no outcome
record, because collect.py had died and finalize() only runs at process exit,
writing a UUID-SORTED PREFIX. Test 4 is worst at 34.4%. Backfilling is right;
doing it at 10 req/min against agents already at the cap is not.
RESULT: All 5 agents playing, 0 abandoned games in the last hour, so no
5th-percentile drag and no ban. Collector stays DOWN until it can yield to the
agent instead of competing with it. Codex MCP removed, codex jobs killed, and the
auto-redteam post-commit hook disabled at the operator's instruction.

## AUG 23 - 04:30 IST

WHAT: Fixed a 30-hour ratings blackout on Test 4 and restarted the snapshotter.
WHY: scripts/snapshot.py mapped GLEE_KEY_TEST4 to slot "specialist" while every
other script maps it to "randomized", and main() read .env ONCE before looping
forever. The key rotated Aug 22 18:04; the daemon had started Aug 21 12:03, so it
logged "[403] Agent is deactivated" every 600s and Test 4 -- the only agent
carrying live experiments -- was absent from the entire ratings series.
RESULT: Test 4 visible again: bargaining 2368.9 (BOARD ROW 2), negotiation 2019.0,
persuasion 2120.3. Negotiation board cutoff is 2067.6 and NO agent of ours is on
it. .env now reloads per poll; persistent slot failures warn and escalate.

## AUG 23 - 04:15 IST

WHAT: Measured all three Test 4 changes. NOTHING IS A MEASURED WIN YET. Neither
kill rule fires; reverted nothing.
WHY: All first-pass positives were artifacts of cutting on results.jsonl.ts,
which is a collection stamp, not play time (median lag 1,618-2,143s, max 26,434s).
RESULT: open-claim mechanism perfect (opening share 0.9500 sd 0.0000 vs 0.6512
control, 0/331 floor breaches vs 258/271) but outcome underpowered: adjusted
+0.088 [-0.019, +0.195]; 48 of 150 kill-rule games; needs ~276/arm. Anchors armed
77s after deploy, deterministic (1.7922x / 0.5049x, zero leakage), outcome FLAT:
+0.010 to +0.025; the earlier +0.1019 was rotation-phase selection -- pseudo-
treating Test 3 or Agent 5 with the same cut gives -0.118 and -0.126. Observed-gain
is the only candidate positive: +0.0030 [+0.0013, +0.0045] family-level, about +24
rating, but all 27-35 flips land in rounds 7-10 at delta<1.0, so it structurally
CANNOT buy the round-1-2 premium the hypothesis assumed. NOISE FLOOR: byte-
identical agents differ by up to 0.0483, so nothing under ~0.05 at n~300/arm is
believable. Test 4's persuasion gap is EMA maturity, not play -- spend nothing.

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
