# HANDOFF — Claude ↔ Codex

Append-only. Newest at the top. Each entry: what changed, what was measured,
what is contested.

## 2026-08-24 — direct-leader opening copy activated on research slots

Codex activated `GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB=1` on `champion`,
`hardliner`, `randomized`, and `composite` at the clean common first-action
boundary `T0=1787571320` (17:05:20 IST). Every target process had naturally
rotated onto pushed commit `8a21e8e`; no process was signalled, drained, or
restarted for deployment. The final overlay write was at `1787571316`, four
seconds before T0. `conceder` / Test 3 remains unarmed, and no bargaining flag
or bargaining code was changed.

This is the default-off per-game 50/50 direct-leader arm described below. It
changes only the first hidden unknown-horizon outgoing price in seller
.8B/1.0B and buyer 1.2B/1.5B cells, to 1.485B or .81B respectively. The running
seller-1.2/buyer-1.0 first-offer probe and cap-10 terminal probe are disjoint;
`HIDDEN_POLICY_V1` and `HIDDEN_FLOOR` were absent on all four slots at
activation. The first post-T0 assignment was a composite buyer-1.2 hash control
and retained its ordinary counter. The first emitted treatment wire was a
composite seller-.8 ask at exactly 1.485B; a Test 4 candidate buyer-1.5 accepted
immediately and correctly stayed in the ITT without emitting a treatment price.
Across the first eight assignments, every applicable wire reported
`wire_ok=true`. This verifies live mechanism and cohort semantics, not value.

Read with `scripts/live_percentile.py --ab hi-extreme-open --since 1787571320
--slots champion,composite,hardliner,randomized`. Do not decide before 100
resolved games per arm and 15 per own-type/arm, and never promote from its local
hidden-pooled diagnostic. Official per-game score CI, close-rate noninferiority,
all subgroup signs, unresolved outcomes, cross-fleet duplicate IDs, and exact
wire integrity remain the precommitted gates.

## 2026-08-24 — direct-leader opening copy built, default OFF

Codex reconstructed the current top negotiation agents from direct encounters,
without conditioning on deals. Clod/Athena/doodod are at
2918.75/2840.38/2649.25 and appear in 47/38/69 of our negotiation games. In
hidden cap-10 plus unknown-horizon games their seller opening medians are
1.488/1.490/1.485B (n=10/8/12) and buyer medians are
.8108/.8075/.810B (n=9/7/14). This validates the literal behavior to copy, not
the causal value of copying it.

`GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB=1` is a default-off 50/50 per-game arm
that copies 1.485B/.81B on the first outgoing hidden unknown-horizon price in
seller .8B/1.0B and buyer 1.2B/1.5B cells only. It changes no decision and
falls back to the full current policy after one rejection. These types exclude
the running first-offer probe's seller 1.2B/buyer 1.0B cells and the dead
seller 1.5B/buyer .8B cells, so all live negotiation measurements remain
disjoint. Broad hidden policy/floor flags make the arm inert rather than
contaminate its hash control.

Exact champion-stack reachability on 1,000 paired games (seed 1907) passed at
100 eligible / 49 fired / 49 changed final wires. Focused tests are 88 passed;
the full suite is 1,048 passed with only the two predeclared bargaining
failures. The reader cohorts at the first pre-action turn, verifies literal
wires, retains unresolved outcomes, guards cross-fleet duplicate IDs, and
labels its hidden-pooled score non-promotion-grade. The code must land inert and
load through natural rotations before any arm boundary is recorded. Test 3 is
not a research slot. No bargaining code or flag was changed.

## 2026-08-24 — hidden cap-10 terminal counter deployed on research slots

Codex activated `GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB=1` on `champion`,
`composite`, and `randomized` at the clean common cohort boundary
`T0=1787568551` (16:19:11 IST). `hardliner` and the overall contender
`conceder` remain unarmed. This is a negotiation-only, per-game 50/50 arm. It
changes exactly the round-9 counter attached to a hidden cap-10 buyer-1.2
rejection to `B+$0.01`; accept, walk, seller, earlier-round, complete-info, and
all bargaining actions remain unchanged.

The experiment is disjoint from the running hidden unknown-horizon first-offer
probe. Test 4's first-principles module owns only complete single seller,
complete cap-10 buyer, and hidden single seller cells, so it cannot shadow this
hidden cap-10 buyer arm. Champion's exact live-stack reachability preflight
(1,000 paired games, seed 1701) reported 19 eligible, 10 fired, and 10 changed
wire actions; representative changes were `.989676B -> B+$0.01` at three
scales. The earlier 3,000-game paired check reported 57/20/20.

The primary cohort begins at the first matching buyer decision, not at terminal
reach, and includes agreements, no-deals, walks, timeouts, and unresolved games.
Promotion still requires official per-game score candidate-control 95% CI above
zero, close-rate point estimate positive with lower bound above -2pp, exact wire
integrity, and no material scale/message reversal. Read with
`scripts/live_percentile.py --ab hi-terminal --since 1787568551 --slots
champion,composite,randomized`. Bargaining code and bargaining flags were not
changed.

## 2026-08-24 — support ladder rejected; clean first-offer probe replaces it

This entry explicitly supersedes the support-ladder entry immediately below.
Independent mechanism review found that the ladder bundled an unproved 95%
claim, a four-offer hold, and deterministic support ordering; several apparent
"strong opponent" landmarks also came from failed no-deal/walk trajectories.
The ladder implementation, reader, flag, and tests were removed before any live
deployment.

The replacement is `GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB=1`, assigned per game
as `sha256("nego_hi_uncapped_first_offer_v1|" + game_id) % 3` to `control`,
`share80`, or `share95`. It is eligible only in hidden, explicitly
unknown-horizon negotiation for seller 1.2B and buyer 1.0B—the two own types
with exactly one strictly feasible counterpart. It changes only the first
outgoing price (seller: 1.44B/1.485B; buyer: .84B/.81B) and falls back to the
current policy after a rejection. Buyers who accept before emitting a price
remain in the intent-to-treat cohort. Broad hidden-policy/floor flags make the
probe inert so its control cannot be silently contaminated.

Deployment is now live on `champion`, `composite`, and `randomized`, with the
clean common cohort boundary `T0=1787567218` (15:56:58 IST). `hardliner` remains
unarmed pending evidence and `conceder` remains untouched. Pre-boundary wire
confirmation observed exact share95 prices at 1.485B (seller) and .81B (buyer)
on Test 4 plus an unchanged hash-control buyer action on Agent 5; all three
reported `wire_ok=true`. Test 4 entered the negotiation top-50 at rating
2077.54 / displayed rank 24 before any eligible probe exposure, so that move is
baseline variance and must not be attributed to treatment.

The first common-boundary read had 7 assigned games, 4 resolved and 3 active.
All four resolved without agreement; hidden-pooled diagnostic percentile was
control .4028 (n=1), share80 .4028 (n=1), and share95 .3807 (n=2), with zero
wire failures. This is explicitly no decision. Structural feasibility is only
25% in both eligible own-type cells, and the observed opposing bids/asks were
far outside our reservation values, so an early all-zero draw is unsurprising.

Production-context shadowing over Test 2's latest 20,000 turns found 47 eligible
first-turn games: 12 control, 18 share80, and 17 share95, split 24 seller / 23
buyer. All 35 candidate price opportunities fired and changed the wire action;
examples reproduced .81B, 1.44B, and 1.485B exactly. Focused verification is
139 passed; the latest full suite is 1,016 passed with only the two predeclared
bargaining failures. No bargaining code or configuration was changed.

Promotion requires joined official per-game scores: candidate-control 95% CI
above zero, close-rate lower bound above -2pp, zero wire failures, and no
material role/scale reversal. The local hidden-value-pooled report is explicitly
diagnostic and cannot promote the arm. The operator transferred deployment
ownership to Codex on 2026-08-24. Deployment must use natural process rotation;
do not signal or drain live agents and do not arm Test 3, preserving its
rank-one bargaining configuration.

Direct `pending_ids` remeasurement found 93,336 locally missing outcome
artifacts across the five slots; the older collector line saying 11,737
"outstanding before pass" is therefore not a reliable fleet-total estimate.
The collector now recognizes both `results.jsonl` and `games/<id>.json`, and
splits each API budget evenly between the oldest and newest missing IDs. The
store deduplication is a correctness fix but barely changed the current count
because those stores overlap heavily; newest-first capacity is what prevents a
fresh experiment from waiting behind the historical queue.

The official outcome collector was relaunched in detached screen
`glee-collector` as PID 37837 at 10 requests/minute/agent, with 50-call passes
and a 30-second inter-pass interval. Newest IDs run before the historical half,
so fresh outcomes land after roughly a five-minute API phase rather than waiting
behind a 20-minute pass; hourly request capacity is unchanged. The older
supervisor process predates collector supervision, so collector health must be
monitored directly until a safe supervisor refresh is available.

## 2026-08-24 — hidden no-limit support ladder implemented, default OFF

`GLEE_NEGO_HI_UNCAPPED_LADDER_AB=1` now arms an independent per-game experiment
with assignment `sha256("nego_hi_uncapped_ladder_v1|" + game_id) & 1`. It is
eligible only for hidden-information, explicitly unknown-horizon negotiation
with a supported own grid value and at least one strictly feasible counterpart
type. Complete-information, cap-10, single-round, seller-1.5, buyer-.8, missing
id, and off-grid states are unchanged. When armed it owns both hash arms in this
scope, preventing `HIDDEN_POLICY_V1` or `HIDDEN_FLOOR` from contaminating its
control.

The localization is from Test 2's latest 100 official dashboard results: hidden
unknown-horizon n=27 averaged `-1.604` rating/game, while hidden cap-10 n=19 was
`-0.189`, hidden single n=27 was `+0.489`, complete cap-10 n=8 was `+2.588`, and
complete single n=8 was `+4.525`. The broad `HIDDEN_POLICY_V1` is therefore not
recommended: a 6,043-turn shadow shows it makes five of six own-type/role cells
harder and would unnecessarily touch the non-negative capped horizon.

The candidate is a support-screening ladder, not a smooth concession curve. It
starts with the feasible hidden type giving us the largest zone, offers that
type 5% of its zone for four of our outgoing price opportunities, then advances
one grid type inward. Examples in B units: seller .8 uses 1.465, 1.18, .99;
seller 1.2 holds 1.485; buyer 1.2 uses .82 then 1.01; buyer 1.5 uses .835, 1.025,
1.215. These numbers reproduce observable landmarks from disclosed strong
no-limit opponents (approximately 1.484-1.485, .8205, and 1.212) while leaving
both sides strictly profitable at every compatible rung. The code never reads a
hidden opponent value and never changes AcceptOffer/RejectOffer/WalkAway.

On a recent Test 2 turn shadow, the runtime predicate found 316 eligible games,
159 hash candidates, and 159 candidates with a changed wire price. Representative
first prices move seller-1.0 `3.9706B -> 1.475B`, buyer-1.0 `.15833B -> .81B`,
and seller-1.2 `4.76472B -> 1.485B`. This establishes mechanism reachability on
live states, not outcome value. `scripts/live_percentile.py --ab hi-ladder
--since T0 --until T1` cohorts at first outgoing price and reports all assigned
outcomes plus reconstructed-zone diagnostics. Its pooled hidden CDF is diagnostic
only; promotion requires official per-game score.

Claude must run the prescribed `check_reachability.py` against the exact intended
stack before arming; Codex did not run it because it imports and executes the
explicitly prohibited replay/arena machinery. Restore/backfill the collector
before measuring. Do not co-arm this with `HIDDEN_POLICY_V1` or the cap-10
terminal arm. The precommitted rule is official-score 95% CI above zero,
close-rate lower bound above -2pp, positive reconstructed capture ITT, no
mechanism failure, and no material role/type sign reversal. The 95% claim and
four-offer hold are judgments under test, not validated constants.

Focused support-ladder/reader/legacy-policy/terminal/bargaining-isolation tests:
118 passed. Full suite: 1,004 passed; only the two AGENTS.md-predeclared
bargaining failures remain (`test_bargaining_horizon_floor` and the bargaining
live-grid drift alarm). No bargaining behavior, live configuration, fleet
process, API key, deployment file, or log was changed.

## 2026-08-24 — hidden late-accept arm rejected and removed

This entry explicitly supersedes the hidden unknown-horizon late seller
acceptance section below. The original public-corpus calculation did not compare
accept-now with the control trajectory's actual continuation; in effect it
rewarded rescuing a rejected bid without charging the candidate for later deals
the control secured at a better price.

The corrected replay used the exact official full-configuration CDF over all
32,403 public trajectories. In the matching hidden unknown-horizon seller cohort
(4,050 games), 375 decisions were exposed and 156 would change. Accepting every
strictly profitable bid on an even round at or after round 4 changes exact
percentile by `-0.06628` per exposed decision, bootstrap 95% CI
`[-0.08183,-0.05096]`; cohort ITT is `-0.00614`, a total loss of `-24.85`
percentile points. Example: a 1.0B-cost seller accepting 1.1B gets a 0.218
percentile, while the observed continuation closes at 1.2B for 0.364.

`GLEE_NEGO_HI_UNKNOWN_ACCEPT_AB`, its assignment helper, live reader,
reachability hook, and dedicated tests have been removed before deployment.
The cap-10 buyer-1.2 terminal-counter arm remains intact and prospective. Do not
restore or arm broad profitable-bid acceptance. No bargaining behavior, live
configuration, fleet process, API key, deployment file, or log was touched.

## 2026-08-24 — cold finals are collector backlog, not identified abandonments

This corrects the immediately following ITT entry's `.05` imputation while
preserving its conclusion: first-principles promotion is blocked.

The separate outcome collector is not running.  `logs/collector.out` stops at
06:00 after three 2,000-record passes and reports 11,737 games still outstanding;
its stale singleton PID has no live process.  Meanwhile the supervisor log
shows the repeated sequence: server `active_games=0` for 365 seconds, then
SIGKILL.  At zero server games this does not strand play, but SIGKILL skips the
child's `finally: GameLog.finalize()`.  The process may in fact be spending those
365 seconds fetching hundreds of final states under the per-key rate limit.
Therefore “old turn + later results watermark + no local final” mixes actual
forfeits with completed server games whose local backfill was interrupted.

`scripts/live_percentile.py` no longer manufactures a `.05` score or non-close
for that state.  It emits `cold-missing` with score/outcome unresolved and blocks
promotion.  `scripts/orphan_watch.py` now includes collector-only
`games/<id>.json` records in its completed set and reports **cold missing local
outcomes**, not rating drag or known abandonments.  Explicit terminal timeouts
and server no-deals remain real outcomes.

`scripts/supervise.py` now owns `scripts/collect.py` as a read-only sidecar.  It
adopts an existing collector by PID, starts one at 10 requests/minute/key when
absent, records its PID in supervisor state, restarts it after exit, and stops it
gracefully with the supervisor.  This code is not live until Claude deploys the
new supervisor; Codex did not start, stop, or signal the current fleet or stale
collector.  A one-time authorized collector restart/backfill is still required
for the existing backlog.

For the first-principles complete cohort this means 18 locally recovered
outcomes and 64 unresolved, not 70 outcomes with 52 synthetic abandonments.
The result-only positive estimate and the synthetic-negative estimate are both
invalid for promotion.  Claude should restart/backfill `scripts/collect.py`
through the authorized operational workflow, let the 64 outcomes recover, then
rerun `--ab fp-complete --since 1787534215 --slots randomized`.  No fleet process,
log, restricted config, or key was touched by Codex.

The new exact open-claim reader is
`scripts/live_percentile.py --ab open-claim-official --since
1787425367.073369 --slots randomized`.  Before the backlog correction it exposed
996 synthetic/terminal observations and a candidate-control `+0.0662`, but that
number must also be rerun after backfill.  The locally recovered subset and the
ongoing randomization still point to the already-live policy's strongest cells
(cap-10 buyer and unknown seller); no new unknown-buyer floor promotion is
claimed.

## 2026-08-24 — first-principles promotion withdrawn after ITT survivorship audit

This entry supersedes the “corrected Test 4 promotes complete-information
cells” entry below.  That read still selected games with fetched terminal
artifacts.  A first-turn cohort reveals the omitted mass and does not support
promotion.

`scripts/fit_official_negotiation_seed.py` now builds
`models/negotiation_seed_cdf_full.json` from the official 32,403-game public
corpus.  The checked-in artifact has all 1,152 literal role cells:
3 horizons x 2 information conditions x 2 message modes x 3 scales x 16 value
pairs x 2 roles, with 53-58 observations per cell.  The corresponding
`sim/official_negotiation_seed.py` scorer requires both values and never pools
a hidden counterpart value.  This closes the old local-CDF error where “same
configuration” silently omitted the valuation pair.

`scripts/live_percentile.py --ab fp-complete --since 1787534215 --slots
randomized` is the reproducible corrected reader.  It cohorts at our first turn
before the randomized action, uses the action path's pure `nego_fp|` assignment,
joins both terminal stores, counts calibrated cold omissions as `.05`
abandonments, leaves fresh omissions unresolved, excludes fleet self-play from
the pooled estimate, and scores complete cells against the full official seed
key.

At about 14:00 IST the complete-information cohort contained 82 assigned games.
Seventy were scoreable under the existing cold-omission rule, including 52
aged missing finals classified as abandonments, and 12 remained unresolved:

- cap-10 buyer: control `0.2028` (n=20) vs candidate `0.2760` (n=7), delta
  `+0.0732`, normal 95% CI `[-0.2488,+0.3953]`; close `20.0% -> 28.6%`;
- single seller: control `0.3023` (n=18) vs candidate `0.2595` (n=25), delta
  `-0.0428`, CI `[-0.2701,+0.1844]`; close `33.3% -> 24.0%`;
- pooled complete: `0.2499 -> 0.2631`, delta `+0.0132`, CI
  `[-0.1574,+0.1838]`; close `26.3% -> 25.0%`.

The prior `+0.3221` / `+0.1018` promotion claim came from the minority of games
that had terminal records and therefore selected away the dominant failure
mode.  Whether a cold omission is ultimately an opponent stall, collector gap,
or competition abandonment remains operationally worth diagnosing, but it
cannot be dropped from an ITT policy comparison.  `GLEE_NEGO_FP_COMPLETE_ONLY`
remains default OFF and is no longer recommended for Test 2.  Continue the Test
4 randomization until unresolved outcomes settle; promotion again requires the
per-cell exact-score CI above zero with no close regression.

The two disjoint hidden-information arms in the next entry are unaffected and
remain prospective/default OFF.  Focused exact-CDF/reader/first-principles/
bargaining-isolation verification: 46 tests passed.  No bargaining behavior,
live flag/configuration, fleet process, API key, deployment file, or log was
changed.

## 2026-08-24 — two hidden-information negotiation arms ready, default OFF

Two independent, per-game randomized mechanisms are implemented.  Neither is
live, neither shares a salt with an existing experiment, and they must not be
co-armed with `GLEE_NEGO_HIDDEN_POLICY_V1` during their first measurement.

### Hidden cap-10 buyer 1.2B terminal counter

`GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB=1` assigns by
`sha256("nego_hi_cap10_buyer12_terminal_v1|" + game_id) & 1`.  It is eligible
only on a hidden-information, known cap-10, round-9 buyer `RejectOffer` carrying
a counter, with our value exactly `1.2*base`.  Treatment makes the final wire
counter exactly `base+$0.01` and returns before broader price guards; control is
byte-identical to the existing stack.  Accept/walk and every earlier action are
unchanged, and no hidden seller value is read.

Measured Aug 22-24: 234 matching games, 85 agreements, 118 no-deals, 31 walks.
Structural feasibility is 50% (about 117 games), but about 32 feasible games
were not closed.  Eighty-one no-deals carried a terminal bid below the `1.0B`
seller grid point; median terminal bid was `0.989676B`.  `base+$0.01` is
strictly profitable for both seller types that can trade with a `1.2B` buyer.
This response is not point-identified—current opponents can still reject—so it
is a randomized trial, not an immediate promotion.

`scripts/live_percentile.py --ab hi-terminal --since T0 --until T1` cohorts at
the buyer's first decision, before terminal reach or outcome, and therefore
keeps early agreements, walks, no-deals, timeouts, and unresolved results in
the ITT.  It verifies every candidate terminal counter equals `base+$0.01`.
Its local percentile is explicitly labeled a hidden-value-pooled diagnostic;
it is not the official full-configuration score.

Reachability on 3,000 paired negotiation games: eligible 57, fired 20, wire
action changed 20.  Examples moved `0.989676B -> 1.0B+$0.01` at all observed
scales.

Precommitted promotion: official candidate-control per-game score 95% CI above
zero; close-rate point estimate positive and lower 95% bound above -2pp; zero
wire failures; no material sign reversal by scale or message mode.  Negative
official-score CI or any wire/mechanism failure rejects.  Rough sample need is
205-280 games/arm (about four to six days at the observed rate).

### Hidden unknown-horizon late seller acceptance

`GLEE_NEGO_HI_UNKNOWN_ACCEPT_AB=1` assigns by
`sha256("nego_hi_unknown_accept_v1|" + game_id) & 1`.  In treatment only, a
hidden-information unknown-horizon seller with cost multiplier in
`{1.0,1.2,1.5}` accepts the first strictly profitable buyer bid on an even
round at or after round 4.  The override changes only the decision; offers,
targets, continuation values, and hidden values are untouched.

On all 32,403 official public negotiation games, the deterministic accept
counterfactual gained `+0.07138` exact percentile across 352 eligible games
(bootstrap 95% CI `[+0.04940,+0.09616]`), `+0.004654` ITT inside hidden
unknown-horizon games, and about `+0.000775` over negotiation (roughly +6.2
long-run rating points).  A chronological 70/30 design chose the rule on the
early corpus and reproduced `+0.09745` across 99 untouched later eligible games
(`+0.005955` hidden-cell ITT); signs were positive across message modes and all
three scales.

Reachability on 3,000 paired negotiation games: eligible 90, gate fired 48,
wire action changed 9.  The gap is expected because many eligible profitable
bids are already accepted in control.  Read with
`scripts/live_percentile.py --ab hi-accept --since T0 --until T1`, cohorting on
the first eligible incoming bid before our action.  Promote only if the
prospective official per-game score CI is above zero.  The local pooled-CDF
number is diagnostic only.

Focused verification for both mechanisms, their readers, production/analyzer
hash parity, and bargaining isolation: 75 tests passed.  No bargaining code,
live flag/configuration, API key, fleet process, or deployment file was touched.
Full suite: 980 passed; only the two AGENTS.md-predeclared bargaining failures
remain (`test_bargaining_horizon_floor` and the bargaining live-grid drift
alarm).  Scoped `git diff --check` passes.  Claude remains the only deployer.

## 2026-08-24 — corrected Test 4 promotes complete-information cells only

Test 4's first-principles A/B was re-read only after commit `f32c334`, using
timestamp `1787534215` as the cohort boundary.  The finished cohort has 157
eligible games (83 control, 74 treatment).  Complete-information outcomes use
the exact official seed CDF for the full value-pair configuration; the hidden
cell is reported as expectation across the four possible counterpart-value
CDFs because a hidden no-deal does not reveal that value.

- cap-10 complete-info buyer: n=27, percentile `0.5706 -> 0.8927`, delta
  `+0.3221` (bootstrap 95% CI `[+0.1825,+0.4677]`), close rate 100% in both;
- single-round complete-info seller: n=45, `0.8086 -> 0.9104`, delta `+0.1018`
  (`[+0.0254,+0.1618]`), with one treatment no-deal;
- single-round hidden seller: n=85, `0.5936 -> 0.5843`, delta `-0.0093`
  (`[-0.1005,+0.0823]`), unresolved;
- all eligible: `0.6373 -> 0.7280`, delta `+0.0907`
  (`[+0.0144,+0.1666]`).  Reweighting by observed eligible-cell frequency gives
  `+0.0795`, about +636 game-rating points inside eligible cells.

`GLEE_NEGO_FP_COMPLETE_ONLY` is now a default-OFF promotion gate in
`first_principles.owns`.  When explicitly enabled it lets hidden games fall
through to the existing strategy while retaining the two measured-positive
complete-information cells.  It does not change Test 4 or any current agent
while absent.  Intended Test 2 promotion configuration is
`GLEE_NEGO_FIRST_PRINCIPLES=1`, `GLEE_NEGO_FP_ALWAYS=1`, and
`GLEE_NEGO_FP_COMPLETE_ONLY=1`; Claude remains the only fleet deployer.

Focused verification: 31/31 first-principles, wire-integrity, and bargaining-
isolation tests pass.  No bargaining code, live flag/configuration, fleet
process, API key, or deployment file was touched.

**Objections / next falsifiable tests:**

1. The official docs say percentile is against the same configuration and role,
   and define the 960-cell grid as including valuations.  Therefore the local
   pooled hidden-value percentile model is not a promotion oracle.  Keep hidden
   randomized and score against the exact latent value-pair once recoverable.
2. Game `e6765abc-2cc5-4998-b5be-77a5695f204d` is a current counterexample to
   the old absolute crumb rule: Scarlett rejected a seller ask of 1,199,999.99
   with buyer value 1,200,000.  Do not increase `EPS` from one cent globally;
   test any larger crumb as a separate game-hashed arm.
3. Eligible cells were about 21% of recent negotiation games, so complete-only
   promotion is expected to add roughly 135-145 overall negotiation rating
   points, not enough by itself to reach the 0.55 target (rating 2400).  The
   already-implemented, default-off hidden-policy V1 should be the next disjoint
   randomized arm after its reachability and scoring reader are revalidated.

## 2026-08-23 — buyer-selectivity red team rejects the historical gain

The user's `q_rank=0.4987` calculation for text `p=.5,r=1.2,S=0` is correct,
but it is not a stable policy threshold.  The exact frozen shadow was reproduced
from the five active-slot `results.jsonl` files only: first-seen game-id
deduplication, completed persuasion buyer records, prior value no greater than
price, sorted by `(ts, game_id)`, oldest 5,181.  Window:
`2026-08-19T11:42:58.172361Z` through `2026-08-22T22:25:54.865690Z`.  Frozen
q-prior and CDF hashes still match the precommit.

At logged pre-decision accumulated-payoff quartiles, the one-step rank threshold
is below money breakeven at 35/54 displayed state points and above it at 17/54,
with two ties.  At the cell median the split is 8 lower / 9 higher / 1 tie.
Weighting the 27,493 actual purchase states reverses the S=0 intuition:
`q_rank>q_money` 16,973 times, `q_money>q_rank` 9,843, 664 ties, 13 flat.
Large empirical-CDF atoms make the sign move with S.  More importantly, raw
`F(S)` is a terminal/fixed-continuation identity; before the last round the
correct value includes future payoff, posterior transitions, and information
revealed by a purchase.  It is not valid to substitute the raw threshold into
all 20 rounds.

The old full candidate still reproduces exactly: 27,493 historical buys become
8,683; 12,720 highs and 6,090 lows are blocked.  Under the requested one-step
proxy and the candidate's counterfactual S, 8,572 blocked buys are rank-positive,
including 6,283 highs.  Reason precedence:

- bought-low strike: 5,816 blocked / 4,305 rank-positive;
- no prior decline: 11,974 / 4,208;
- current signal not explicit yes: 1,007 / 50;
- posterior below money cutoff: 13 / 9.

So the mass error is not caused by the money threshold.  A sequential shadow
also shows the cutoff is nearly inert: prior-decline-only `+.01337`, adding
explicit yes `+.01484`, adding money cutoff `+.01445`, adding strike `+.01209`.
The fitted gain comes almost entirely from text (`+.01248` overall contribution);
binary contributes `-.00039`.  Largest positive cells are text `.8/1.25`,
`.5/2`, and `1/3,3`; binary `.8/1.25`, `1/3,2`, and `.8/1.2` drag.

The overfit objection is decisive.  A chronological 70/30 artifact cross-fit at
`2026-08-21T16:52:32Z` fitted the q prior on 6,013 earlier buyer games and the
CDF on 9,048 earlier persuasion games, then scored 1,555 strictly later eligible
games with every CDF cell supported (n=270-351).  Early in-sample was `+.01442`
`[+.00890,+.01994]`; later full gate was `-.00131`
`[-.01111,+.00848]`, and no-strike was `+.00684`
`[-.00113,+.01482]`.  Neither survives.  This is artifact-disjoint but not a
pristine model-selection holdout because the policy itself was designed after
viewing the full corpus; that limitation makes the failure stronger, not weaker.

The no-look-ahead state is "has an explicit decline occurred before this
decision", never eventual seller type.  In explicit-current-yes purchases,
post-decline beats pre-decline after exact cell+round adjustment by +11.72pp
high rate, +.2355 price-units per buy, and +.01554 local fitted rank.  The
predictive gradient therefore reproduces.  But pre-decline explicit-yes buys
themselves earn +.1455P/buy and local rank +.00036 with a CI spanning zero.
This action-selected observation does not identify a benefit from vetoing them.

Implementation response: do NOT replace money breakeven with the myopic raw-rank
threshold, and do NOT run the main arm.  The one-low stop is no longer bundled.
`GLEE_PERS_BUYER_SELECTIVITY_STRIKE_AB` is a separate default-off, independent
per-game hash arm (`pers_buyer_selectivity_strike_v1|`).  When both experiments
are armed this creates strike/no-strike cells inside candidate and matching
behaviorally inert controls.  `scripts/live_percentile.py` records and reports
those pre-treatment variants separately; more than one bought low is a
falsification only in the strike-assigned cell.  Neither flag was armed and no
live fleet/process or restricted file was changed.

Verification: 24 focused selectivity/ITT tests pass.  The mandated full suite is
843 passed with only the two failures pre-declared by AGENTS.md: bargaining's
450-vs-468 horizon-floor expectation and the live `horizon_known` grid drift.
Scoped `git diff --check` and compilation pass.  No replay-eval, arena, red-team,
fleet, or reachability command was run.

## 2026-08-23 — persuasion buyer selectivity arm implemented, default OFF

`GLEE_PERS_BUYER_SELECTIVITY_AB=1` arms a per-game A/B only in persuasion buyer
games with `v>u`, `price>u`, and prior money value
`p*v+(1-p)*u <= price`. Assignment is
`sha256("pers_buyer_selectivity_v1|" + game_id) & 1`. The flag is absent/OFF by
default. Candidate is strictly an extra veto over the current buyer; it cannot
revive an existing rejection. Prior-positive games return before assignment,
so the protected `p*r>1` corpus (3,452 games, 84.08% of rounds bought, mean
payoff `21.429P`) is byte-identical with the arm armed.

The candidate requires all four conditions for a purchase:

1. at least one historical message is an explicit decline;
2. the current message is an explicit recommendation under the tri-state
   parser, independent of the fleet's legacy-parser flag;
3. the fitted posterior `P(high | current recommendation)` strictly exceeds
   `(price-u)/(v-u) + margin`;
4. no previously purchased unit in the game was low.

The permanent one-low strike is deliberate. A decline is not a costly or
directional signal under this gate: while the buyer waits, a pre-decline yes
would also make no sale, so the seller can decline a low at zero on-path cost
and unlock 19 later rounds. One decline only proves
`P(no|high)>0` or `P(no|low)>0`; it does not prove recommendations favor highs.
The strike caps direct post-unlock loss at one price. Hard never-buy is the only
zero-loss minimax rule, but it discards every selective-seller winner; the
strike is a bounded-loss hypothesis whose effect must be randomized.

The probability estimator is the existing six-point seller-type mixture over
low-quality recommendation rate `q={0,.125,.25,.5,.75,1}`, with a 2% high-unit
decline likelihood and mode/prior-bin weights fitted on 4,191 games. Candidate
recomputes it with parser abstentions preserved even when control uses the
legacy optimistic coercion. A single Beta/Laplace count model was rejected: the
fitted population is bimodal, and the declined unit's hidden quality supplies
no Bernoulli success/failure with which to bootstrap a Beta posterior. The
first-arm probability margin is `0.0` plus strict `>` because no measurement
identifies a positive margin and the blanket guard/LCB family is already
measured negative. `GLEE_PERS_BUYER_SELECTIVITY_MARGIN` exists only inside
candidate and must remain `0.0` in the first window.

The motivating money-EV algebra is valid with an important scope correction:
for posterior `q`, buyer payoff is
`q(v-price)+(1-q)(u-price)`, so buy iff
`q>(price-u)/(v-u)`; live `u=0` gives `q>1/r`. A genuinely always-recommend
seller has `P(high|yes)=p`. Therefore `p*r<1` is strictly negative money EV,
while `p*r=1` is zero EV, not negative. T2 and T3 are equality cells (`.8*1.25
= 1`, `(1/3)*3 = 1`). T6's stated 11 highs / 8 lows yields `+25P`, not `+13P`;
`+13P` corresponds to 8 highs / 11 lows. T3's five initial lows are not seller
front-loading if it said yes on every unit: nature draws iid and the event has
probability `(2/3)^5 = 13.17%`.

The universal claim is also false for the competition objective. Rank applies a
nonlinear same-cell CDF `F` to total payoff. In the fitted text `p=.5,r=1.2`
cell at zero accumulated payoff, `F(-P)=.0284`, `F(0)=.4498`, and
`F(+.2P)=.8734`; one blind buy has expected percentile
`.5*.0284+.5*.8734=.4509`, narrowly above passing, despite money EV `-.4P`.
This is a counterexample, not evidence to buy that cell.

Read-only shadow reconstruction of the oldest 5,181 eligible games found
27,493 historical buys. The full candidate retains 8,683, blocking 12,720 high
winners and 6,090 lows. Mean payoff falls `1.1555P -> .7774P`, while fitted
percentile changes `+0.01209`, normal 95% CI `[+.00718,+.01701]` over 5,170
scoreable paired games. The pure pre-decline veto alone blocks 11,974 buys
(8,605 highs, 3,369 lows) and forgoes a net 1,150.9 price-units of historical
payoff. The one-strike insurance removes 5,604 additional buys and reduces the
shadow percentile gain from `+.01445` to `+.01209`. This replay holds seller
messages fixed and observes no quality on skipped rounds, so it is screening
evidence only, not a causal estimate.

The supplied never/sometimes split is not exactly reproducible without its
semantic classifier. On the same 5,181 games, explicit tri-state parsing yields
1,443 never-decline / 3,738 eventual-decline games; alternate committed parsers
yield 1,174/4,007 or 1,266/3,915, not 1,058/4,123. More importantly, eventual
decline is future, post-treatment information and cannot define the primary
policy comparison.

**Pre-committed falsification:** arm only after recording exact T0 and hashes
`pers_buyer_prior_v1.json=173e00273db5b2d5121080be0e6192c4ab12e1ea553b61ab22896bfb4a31787a`
and
`percentile_cdf_v3.json=bd3b313792951465624543612b09fb0ca5cc1708aee08a7a3dfb85f269e58ff9`;
do not refit either mid-window. Use
`scripts/live_percentile.py --ab pers-selectivity --since T0 --until T1`.
Primary is candidate-control mean percentile over every assigned eligible game,
never the eventual-decline subgroup. Promote only if the 95% CI is wholly above
zero; reject if wholly below; unresolved outcomes block promotion. Any candidate
pre-decline purchase or second bought-low is a mechanism failure. Report exact
cell/equality strata and one-decline sellers as diagnostics. The one-decline
attack is decline a low, then recommend 19 indiscriminately: a permanent unlock
would cost `19P(p*r-1)` in expectation (`-.76P` at `.8*1.2`, `-6.333P` at
`(1/3)*2`); this candidate permits at most one low purchase.

The prescribed `check_reachability.py` was not run because its import path uses
the explicitly prohibited replay/arena modules and it has no persuasion family.
Focused decision tests instead require eligible>0, veto-fired>0, and
action-changed>0, alongside default-off/hash-control identity and protected-cell
identity. Claude still owns independent verification and any live deployment.

Verification: 173 focused persuasion tests and 95 live-percentile tests passed.
The mandated full suite produced 840 passed and only the two failures explicitly
pre-declared by AGENTS.md: the bargaining horizon-floor expectation is
450/current 468, and the live bargaining `horizon_known` grid drift remains
significant. Scoped `git diff --check` and `py_compile` pass. No replay-eval,
arena, red-team, fleet, or reachability command was run; no live flag was armed,
and no restricted file or running process was changed.

## 2026-08-23 — grid-aware hidden negotiation policy implemented, default OFF

`GLEE_NEGO_HIDDEN_POLICY_V1=1` arms a new offer-only experiment.  The default
is absent/OFF.  Eligible games require `complete_information=false`, a
multi-round horizon, a supported own value/base, a present game id, and an own
type with positive prior probability of a strict ZOPA.  Each eligible game is
assigned by `sha256("hidden_policy_v1|" + game_id) & 1`, an independent salt.
Complete-information games, one-round games, seller `1.5B`, and buyer `0.8B`
are unchanged.  When the new flag is armed, it owns both hash arms and
suppresses the older `GLEE_NEGO_HIDDEN_FLOOR` path, so an accidental second
flag cannot contaminate control.

The candidate is a grid-aware screening curve:

| Role / own type | assumed P(strict ZOPA) | opening | prior terminal boundary |
|---|---:|---:|---:|
| seller `0.8B` | 75% | `1.395B` | `0.950B` |
| seller `1.0B` | 50% | `1.425B` | `1.150B` |
| seller `1.2B` | 25% | `1.455B` | `1.425B` |
| seller `1.5B` | 0% | unchanged | existing dead-game path |
| buyer `1.0B` | 25% | `0.830B` | `0.850B` |
| buyer `1.2B` | 50% | `0.860B` | `1.050B` |
| buyer `1.5B` | 75% | `0.905B` | `1.275B` |
| buyer `0.8B` | 0% | unchanged | existing dead-game path |

The opening claims 85% of the largest support-compatible positive zone.  Its
purpose is screening: it is inside a possible opponent's support, unlike the
measured 3.97x-own-limit opening, so a favorable type can accept while paying
us a high share.  The terminal boundary claims 75% of the narrowest still
compatible positive zone.  This makes the answer to “higher or lower than flat
1.15?” type-dependent: seller `0.8B` must go lower (`0.95B`) to retain the
buyer-`1.0B` zone, while seller `1.2B` can hold higher (`1.425B`) because only
buyer `1.5B` is feasible.  The buyer side is the exact zone-share analogue.

For capped games, the five H=10 price opportunities follow a squared clock
with progress `0, .0625, .25, .5625, 1`; both seats reach their boundary on
their last price opportunity.  In an uncapped game the linear clock is capped
at `.85`, so its square traverses at most 72.25% of the opening-to-boundary
distance.  The uncapped cap, squared timing, `.85` opening share, and `.75`
boundary share are judgments, not identified constants.

The schedule never reads opponent concession speed.  A static price therefore
cannot make us concede faster.  It uses only the best price level as a rational
one-sided type bound (`buyer bid <= buyer value`, `seller ask >= seller cost`):
crossing a grid threshold can harden the terminal boundary, and a favorable
opponent price is never given back.  This is also a judgment: an irrational or
strategic loss-making offer invalidates the type inference, which the live arm
must test.

The implementation is a final `actions.coerce()` postcondition after strategy
and LLM planning.  It replaces an emitted candidate `product_price` but never
changes the selected decision or any plan/acceptance input.  Tests cover both
roles, every 75/50/25/0 own signal, the full H=10 wire sequence, uncapped cap,
history echo counting, static opponents, crossed type bounds, favorable offers,
hash parity, hidden-value sentinels, complete-info/one-round/dead exclusions,
default-off identity, and legacy-arm isolation.

`scripts/live_percentile.py --ab hidden-policy --since T0 --until T1` now
reports, per slot and pooled:

- mean same-cell percentile with 95% CI;
- close rate with 95% CI;
- median/IQR reconstructed-zone share among positive-zone agreements;
- mean zone-capture ITT, where every non-close/abandonment contributes zero;
- role, own type, P(ZOPA), and horizon strata plus reconstructed closed-pair
  composition.

For an agreement, the seller and buyer payoffs sum to the true zone, so own
share is `own_payoff / (p1_payoff + p2_payoff)`.  Missing payoffs, off-grid
reconstructions, and zero/negative zones are counted explicitly and cannot
silently enter that ratio.  Cross-slot fleet self-play ids are detected before
eligibility and `--slots` filtering and excluded from the pooled independent
estimate.  First-exposure signal metadata survives abandonment, keeping its
zero in the correct stratum.  Conditional share remains selected on closing;
the ITT capture metric exists specifically to expose a false “share gain” made
by deleting low-share deals.

**Evidence versus judgment:** the evidence supports replacing the off-support
journey, conditioning on our own feasibility signal, avoiding reciprocal
concession, and targeting more than the measured 0.520 median closed-zone
share.  The 319 no-deal opening comparison is selected on failure and does not
prove openings have no causal effect.  The four-value axis is official, but
uniform independent hidden draws and the current joint support are local
reconstructions.  The field's move from 0.776 to 0.830 says any fixed constants
must be tested in a short contemporaneous window; it does not identify 0.85 or
0.75 as optimal.

**Pre-committed falsification / promotion rule:**

1. Primary outcome is candidate-control mean percentile.  Promote only if its
   95% CI is above zero; reject if its 95% CI is below zero; otherwise continue
   or call the arm inconclusive.
2. Close-rate non-inferiority margin is -2 percentage points (judgment, chosen
   because close rate is near its structural ceiling).  Promotion requires the
   delta's lower 95% bound above -2pp; reject if its upper bound is below -2pp.
3. Mechanism requires positive zone-capture ITT and at least +0.05 conditional
   median closed-zone share.  A higher conditional share with lower ITT capture
   is survivorship, not success.  Treat a non-positive median-share delta as a
   mechanism rejection after at least 200 reconstructed positive-zone closes
   per arm; the +0.05 and n=200 thresholds are judgments.
4. Inspect pair composition and role/horizon strata before promotion.  A gain
   produced only by dropping narrow zones, a seller/buyer sign split, or an H=10
   gain paired with an uncapped loss falsifies the proposed mechanism even if a
   pooled descriptive metric looks good.

Verification: prescribed reachability at 200 negotiation draws against
`replay_eval.DEFAULT_CONTROL` reported eligible 1,168, fired 589,
action_changed 589, PASS; the checker warns that this is a simulator snapshot,
so Claude must repeat against the exact intended live stack.  Focused
policy/reporting/floor tests passed 104/104.  The mandated full suite produced
811 passed and only the two AGENTS.md-declared bargaining failures
(`test_bargaining_horizon_floor`, expected 450/current 468, and
`test_sim_grid[bargaining]`, live `horizon_known` drift).  No live flag, fleet
process, `arms.json`, `control.json`, `.env`, or file under `logs/` was changed.
No replay-eval, arena, or red-team command was run; only the prescribed
reachability checker was invoked.  Claude still owns verification and deploy.

## 2026-08-23 — hidden-information concession floor implemented, default OFF

`GLEE_NEGO_HIDDEN_FLOOR=<F>` is a float flag with inert default `0.0`.  It is
eligible only when `complete_information` is literally false, our public role
is seller/buyer, our own visible value maps to a supported base through
`pricing.infer_base`, the game id is present, and
`sha256("hidden_floor|" + game_id) & 1` assigns treatment.  Hash-control games,
missing/off-grid inputs, non-finite/non-positive settings, and `F > 2` retain
the existing wire price.

The implementation is a final `actions.coerce()` price postcondition, after
heuristic/full-LLM choice and action repair.  For every emitted treatment
`product_price`, a seller submits `max(price, F*B)` and a buyer submits
`min(price, (2-F)*B)`.  The buyer expression is the additive reflection of
`F*B` around `B`: `B-(F-1)B=(2-F)B`; using `max` there would silently reverse
the protection.  The boundary is reapplied after cent rounding.  An
`AcceptOffer` has no price and returns before the flag is read, so neither the
plan nor any accept/reject threshold changes.  Complete-information games
continue through OPEN_CLAIM/CLAIM_FLOOR and are tested identical with this flag
armed.  A sentinel test also proves no hidden opponent-value key is read.

`scripts/live_percentile.py --ab hidden-floor` recovers the same hash and
reports mean percentile AND close rate for each arm, per agent and pooled.  It
uses the existing robust first-outgoing-price exposure cohort rather than the
results-only A/B path: both seats/all horizons are eligible; the result join
covers `results.jsonl` plus collector `games/<id>.json`; unknown-CDF outcomes
remain in the close denominator; cold abandonments count as percentile `.05`
non-closes; pending/invalid finals block promotion; and any negative terminal
close-rate point estimate prints the veto.  `--since/--until` bound the first
price exposure, so Claude must record the exact activation/disarm timestamps.

The generic reachability checker had its own hash-arm defect: its control play
left every game id at the simulator literal `local`, assigning all banked
states to one bit.  It now supplies the stable per-draw `sim-<seed>` id already
used by the paired harness.  Required checker result at `F=1.15`, 200
negotiation draws against `replay_eval.DEFAULT_CONTROL`: eligible 1,354, fired
301, action_changed 301, PASS.  The checker warned that this control is a
simulator snapshot, so Claude must repeat it against the intended live stack
before deployment.

Read-only 30h calibration over five active result streams, deduplicated by
game id: 4,074 hidden negotiations, 1,300 closes.  Recommended first treatment
is **F=1.15** (seller `>=1.15B`, buyer `<=0.85B`), chosen from the observed
accepted-price support rather than a midpoint:

| F | buyer cap | games whose historical price would change | existing closes whose accepted own price would change |
|---:|---:|---:|---:|
| 1.10 | 0.90B | 553 / 4,074 | 168 / 1,300 |
| 1.15 | 0.85B | 713 / 4,074 | 183 / 1,300 |
| 1.175 | 0.825B | 894 / 4,074 | 257 / 1,300 |
| 1.20 | 0.80B | 944 / 4,074 | 262 / 1,300 |

Moving 1.10 -> 1.15 buys another `.05B` while exposing only 15 additional
historical closes; moving just above 1.15 crosses a large accepted-price atom
and exposes 74 more.  At 1.15, sellers expose 146/2,053 games and 52 accepted
own offers; buyers expose 567/2,021 and 131 accepted own offers.  The buyer arm
is the veto: 131/143 accepted buyer-originated offers would have been clipped,
and observational logs cannot say whether those unplayed prices would close.

**Objections / proposed validation:**
1. The supplied “field seller 1.449” row is actually counterparty buyer bids in
   games where we sell, and “field buyer 0.826” is counterparty seller asks in
   games where we buy; neither is a same-role policy path.  Round buckets also
   change type composition as games close.  Use them as price-support context,
   not causal proof that matching either endpoint wins.
2. Retrospective hash balance before treatment is control n=2,050, close 31.32%,
   percentile .4939 versus candidate n=2,024, close 32.51%, percentile .4960.
   Thirty hours leaves roughly +/-2.9pp uncertainty on the close-rate
   difference.  Use a clean activation boundary and do not call a sub-1pp close
   difference identified at that sample size.
3. Any credible candidate close-rate loss, especially in buyer games, rejects
   or lowers 1.15 regardless of mean percentile.  If percentile improves with
   no close-rate penalty, test 1.175 in a separate randomized window; do not
   extrapolate through the accepted-price cliff.

Verification: 88 focused hidden/open-claim tests passed; the mandated full
suite produced 741 passed and only the two AGENTS.md-declared bargaining
failures (`test_bargaining_horizon_floor`, expected 450/current 468, and
`test_sim_grid[bargaining]`, live `horizon_known` drift).  No live flag, fleet
process, `arms.json`, `control.json`, `.env`, or file under `logs/` was changed.
No replay-eval, arena, or red-team command was run; only the prescribed
reachability checker was invoked.  Claude still owns verification and deploy.

## 2026-08-23 — complete-info opening claim + concession floor implemented, default OFF

This supersedes the never-deployed `GLEE_NEGO_CI_ASK_AB` entry immediately
below; there is one mechanism, not two.  The old flag and `ci_ask|` assignment
were removed.  `GLEE_NEGO_OPEN_CLAIM=<share>` and
`GLEE_NEGO_CLAIM_FLOOR=<share>` are independent floats with inert `0.0`
defaults, but both use the same per-game treatment assignment:
`sha256("open_claim|" + game_id) & 1`.  Hash-control games retain the existing
wire price.  A non-finite/non-positive value is inert, and a missing game id is
inert.

On a treatment game, OPEN_CLAIM replaces our first outgoing price in either
seat: the seller's standalone round-1 offer or, on the live protocol, the
buyer's first `RejectOffer` counterprice.  It includes one-round games.  The
price is `seller_value + share * span` for a seller and
`buyer_value - share * span` for a buyer.  CLAIM_FLOOR is then a lower bound on
our claimed share for every emitted `product_price`, including late rejection
counters; an already more ambitious price is retained.  Every price affected
by either knob is clamped to `[seller_value, buyer_value]`, including shares
above 1 and fractional ZOPA endpoints.  The action postcondition runs after the
strategy/LLM and only when the normalized action contains `product_price`.
`AcceptOffer` has no price and returns before either flag is read, so neither
the flags nor their assignment can change an acceptance threshold.

The complete-information marker is checked before role/value mapping.  A test
uses a hidden-state dict that raises if the opponent-value key is read, arms
both flags, and verifies that the unchanged price returns without that read.
This keeps hidden-information games entirely outside the mechanism.

`scripts/live_percentile.py --ab open-claim` recovers the exact `open_claim|`
hash and reports mean percentile plus close rate for each arm, per agent and
pooled.  It cohorts on each game's globally earliest logged outgoing price,
then applies `--since/--until`; a later counter cannot pull a pre-window game
into the cohort.  This includes both seats, every horizon, and every round with
a positive visible ZOPA.  The result join still covers both `results.jsonl` and
collector-only `games/<id>.json`; unknown-CDF terminals stay in the close-rate
denominator, unresolved outcomes are bounded and block promotion, and cold
missing results count as .05-percentile non-closes.  A negative candidate close
delta prints the close-rate veto.

Reachability registers both flags as final-action postconditions.  Codex did
not run `scripts/check_reachability.py`, because it imports and executes the
explicitly prohibited replay/arena path; Claude should later require
eligible>0, fired>0, action_changed>0 against the intended control stack.

Verification: 67 focused open-claim/ZOPA tests passed.  The mandated full suite
produced 707 passed and only the two failures pre-declared in AGENTS.md:
`test_bargaining_horizon_floor` (expected 450, current 468) and
`test_sim_grid[bargaining]` (`horizon_known` live-grid drift).  No live flag,
fleet process, `arms.json`, `control.json`, `.env`, or file under `logs/` was
changed; replay evaluation, arena, red-team, and reachability scripts were not
run.

**Objections / proposed validation:**
1. With both floats armed in one interval, `--ab open-claim` identifies the
   joint opening-plus-floor policy, not the contribution of either component.
   Separate homogeneous windows (one nonzero float at a time) are needed for
   component attribution; the requested bundle is still the primary test.
2. Arm exposure is not persisted.  Record the exact per-slot arm/value `T0`
   and disarm/value-change `T1`, then analyze that first-price interval.  Games
   whose first outgoing price predates T0 are deliberately excluded even if a
   later floor would have changed them after a mid-game arm.
3. A hidden-information analogue cannot use ZOPA share.  If built, randomize it
   under an independent salt and key the schedule on role, own value normalized
   by the public money scale, round/horizon, and bounds or a posterior inferred
   from opponent offers; do not infer an opponent value that the payload hides.

## 2026-08-22 — complete-info seller opening-ask arm implemented, default OFF

`GLEE_NEGO_CI_ASK_AB=<share>` is a float flag with an inert `0.0` default.  It
is consulted only for a standalone opening offer when `complete_information` is
literally true, both role-mapped values are finite and form a positive visible
ZOPA, our current player is the seller, the action type is `offer`, round is 1,
history and `last_offer` are empty, the horizon is not 1, and the game id is
present.  Every eligible game is assigned by
`sha256("ci_ask|" + game_id) & 1`.  Hash control keeps the already-computed wire
opening unchanged.  Treatment replaces only that opening with
`seller_value + flag_share * (buyer_value - seller_value)`, rounds it, then
clamps the literal wire price to `[seller_value, buyer_value]`; a flag share
above 1 therefore cannot submit an ask above the visible buyer value.  The arm
runs as a final action postcondition after heuristic/full-LLM pricing.  Decision
turns, reject/counter prices, acceptance thresholds, and every offer after the
opening do not read it.

The motivating longer-horizon observations remain hypothesis-generating only:
horizon 10 had 94.1% closes at the existing 0.50-0.65-span opening (n=188,
mean percentile .5571), and unbounded had 97.7% (n=217, .5024).  Horizon and ask
band were perfectly confounded, so the implementation comment explicitly says
that these observations establish no ask effect and that the hash experiment is
the identifying variation.

`scripts/live_percentile.py --ab ci-ask` recovers the identical pure hash and
cohorts from the actual eligible round-1 turn timestamp, not a later result-fetch
timestamp.  Use `--since T0 --until T1` (opening-time bounds, upper exclusive)
and `--slots` to isolate the period in which a chosen value was armed.  It joins
both `results.jsonl` and the continuous collector's `games/<id>.json`, prefers a
recognized terminal record over an active snapshot, and reports mean percentile
and close rate separately for each arm and pooled.  Agreement is a close;
`no_deal`, `timeout`, and `walked_away` are non-closes.  Unknown-CDF games remain
in the close denominator.  Missing results older than the calibrated 6,000s
orphan threshold and behind a later collection watermark count as percentile
.05 abandonments and non-closes.  Fresh pending and malformed terminal records
are shown separately with arm-wise best/worst close-rate bounds and make the
read non-promotion-grade.  A zero-eligible window exits nonzero.  Strategy
exception fallbacks now write the actual returned action as an ordinary turn in
addition to the error record, so fallback openings cannot disappear from this
intent-to-treat cohort; this changes logging only, not the returned action.

Reachability knows `GLEE_NEGO_CI_ASK_AB` as a final-action postcondition and its
eligibility predicate reuses the live visible-ZOPA coercion.  Codex did not run
the checker because it imports `replay_eval`/`sim.arena`, which the operator
explicitly prohibited.  Claude should later run the registered check with the
real target control stack and require eligible>0, fired>0, action_changed>0.

Verification: 97 focused/interaction tests passed.  The exact mandated full
suite produced 702 passed and only the two pre-existing AGENTS.md failures:
`test_bargaining_horizon_floor` (expected 450, current 468) and
`test_sim_grid[bargaining]` (`horizon_known` live-grid drift).  Tests cover flag
absent/0 and hash-control identity, both horizon 10 and unbounded treatment,
64-game runtime/analyzer hash parity, horizon-1 and hidden-information
exclusions, missing visible value, buyer and later-turn exclusions, history-only
and `last_offer`-only opening guards, decision/accept/counter isolation, a share
1.5 fractional-boundary clamp, non-finite flag behavior, exception-fallback
cohorting, exact opening-time bounds, collector-only results, duplicate finals,
terminal labels, unknown CDFs, aged abandonment, unresolved bounds, and the
zero-eligible exit.  The stale current-state snapshot was regenerated before
review; no live flag or process was changed, and no file under `arms.json`,
`control.json`, `.env`, or `logs/` was modified.  Arena, replay evaluation, and
red-team scripts were not run.

**Objections / proposed validation:**
1. Arm exposure is not persisted by design.  The operator must record the exact
   per-slot code-deploy/flag-arm `T0`, disarm/value-change `T1`, and analyze each
   homogeneous interval with `--since T0 --until T1`; a broad `--hours` window
   can hash control-only games into a false treatment after disarm.
2. Promotion requires unresolved=0 and no treatment close-rate loss.  No sample
   size or uncertainty rule was supplied, so none was invented; pre-commit it
   before inspecting the live arm contrast.
3. A missing outcome becomes an abandonment only under the repository's
   measured 6,000s-plus-watermark rule.  Inspect the reported abandonment count
   per arm and backfill/fetch questionable outcomes before the final verdict.
4. Historical strategy-error records created before this patch lack the state
   needed for opening-time eligibility.  Start `T0` after this code is live so
   those records cannot enter the experiment cohort.

## 2026-08-22 — bargaining no-regression guard and message arms implemented, default OFF

`GLEE_BARG_NO_REGRESS=1` now changes only a decision that every existing rule
still leaves as `reject`. It deep-copies the deterministic post-rejection state
(records the live offer, advances the round, makes the rejecter proposer) and
runs that projected offer through the public bargaining `decide()` plus action
coercion. The comparison therefore uses the SAME endgame cap, opponent floor,
Bob fitted-offer writer and opponent-profile writer that will make the next real
offer; it is not a second derivation of aspiration. If the wire-coerced planned
own share is no greater than the live offered share plus
`GLEE_BARG_NO_REGRESS_EPS`, the move becomes `accept`. EPS is in share units,
defaults to 0.0 and is clamped to [0,1]. Projection errors keep the reject.

The measured defect was nine games, -44.9 rating and 17.36 pot-points strictly
forfeited. The regression reproduces Bob rejecting a 70% live share and then
asking for 61%; flag OFF rejects, flag ON accepts, and the projected 61% is
equal to the real next observation's offer after an actual simulator rejection.
Boundary tests cover 60%<61% remaining a reject, exact equality accepting, and
60.9% accepting only with EPS>=0.001. A later-writer test forces Bob pricing to
80% and proves the guard sees 80%, not the earlier aspiration.

`GLEE_BARG_MSG=1` now assigns every game by
`sha256("barg_msg|" + game_id) mod 4` to `BARG_ARMS` for its full lifetime:
`B0` silent fleet control; `B1` length-matched neutral split recap; `B2` the
public no-agreement-pays-zero rule; `B3` a movement statement only when public
offer history proves a concession, otherwise public allocation arithmetic.
`BARG_ARM_SEMANTICS` records those meanings. B1-B3 use the same frame, request
and filler pools and target 300 characters: a 30,000-composition fuzz across
arms, seats, public movement/no movement and pots from 1 to 123,456,789.12 had
zero composition failures, with B1/B2 exactly 300 characters and B3 299-301.
Messages quote the wire-coerced split, not a pre-rounding float. The numeric
action is fingerprinted before/after attachment; B0 and failed compositions are
logged as assigned arms and cannot be back-filled. Dispatch excludes bargaining
from both LLM action and LLM message hooks, even under a stale allowlist: every
bargaining message is from this hand-written bank.

Mandatory leak audit of the former bank found seven gated families: inferred
last-round text; discount-asymmetry text; generic inflation text; exact
rounds-left text; internal non-concession-classifier text; "priced off discount
rates"; and the share<0.45 concession closers. The first six were removed from
the bargaining arms because pooling them would be false or disclose discount,
synthetic horizon or solver state. The two concession closers now require a
publicly verifiable prior move. Over 1,000 deterministic seeds each emitted on
B3 at BOTH 40% and 60% current own share: "serious move" 503/503 and "come a
long way" 497/497. Plan-metamorphic tests vary private deltas, rounds-left,
aspiration, floor, continuation, planned counter and internal evidence while
holding public state fixed; a second side varies hidden/complete-information and
horizon fields. Every arm stays byte-identical because the composer never reads
`plan` or those game-state fields. Paired true/false old-gate tests emit every
retired phrase 0/0. Those six phrase families could not be moved across both
sides truthfully: doing so would make false deadline/discount claims, so they are
retired rather than pooled.

Message rating impact is **UNMEASURED**. The only measured result is reachability:
Test 1 sent 0/1,851 texts while opponents sent 1,583/1,830 in 493
message-enabled games. `GLEE_BARG_MSG` must therefore run as the per-game arm
experiment against B0 silence, never as a default-on template policy.
`scripts/live_percentile.py --ab barg-msg` recovers the same four-way hash,
filters to `messages_allowed=true`, reports the primary B0-versus-pooled-text
contrast and exploratory B1/B2/B3 contrasts, and warns that `--hours`/`--slots`
must be scoped to an era where the flag was armed because result records do not
carry flag exposure.

Verification: the 31 focused regressions pass. Full suite: 640 passed; only the
two pre-existing failures named in AGENTS.md remain
(`test_bargaining_horizon_floor`, `test_sim_grid[bargaining]`). Reachability now
registers both flags and treats message changes as action changes, but Codex did
not execute that replay/arena-backed checker because the operator explicitly
forbade replay and arena runs. No arena, replay evaluation, red-team script,
live flag, fleet process, `arms.json`, `control.json`, `.env` or `logs/` was
touched.

**Objections / proposed validation:**
1. Code-path reuse is exact for one policy snapshot. A live flag or hot-reloaded
   model changing between rejection and the next turn can change the later real
   offer; no pre-reject projection can freeze an external mutation.
2. Before deployment, Claude should run the registered reachability checks and
   require eligible>0, fired>0, action_changed>0. For messages, verify all four
   hash arms and analyze B0 versus pooled text before comparing registers.
3. Do not select B1/B2/B3 from observational phrase conversion. Arm assignment,
   including silence, is the identifying variation; promotion needs live
   game-level outcomes under a pre-committed decision rule.
4. The live `randomized`/Test 4 slot uses `probes.py`'s custom bargaining policy
   and bypasses `bargaining.decide`, so both flags are intentionally inert there.
   Do not arm that slot without a separate probe-policy design and test.

## 2026-08-22 — terminal rank-price arm implemented, default OFF

`GLEE_NEGO_RANK_PRICE_AB=1` now hash-assigns each game to control or treatment
with the independent `rank_price_ab|<game_id>` salt.  Only an outgoing offer on
a REAL final round (`capped and rounds_left <= 1`) can move.  The treatment is
the final target writer, after ultimatum/posterior/curve/stall logic, and bypasses
the later split transform; decision turns never read its price, so the arm cannot
contaminate acceptance as the surplus probe did.  Flag off and hash control keep
the previous path exactly.  `scripts/live_percentile.py --ab rank-price` recovers
the assignment; the reachability registry knows the `rank_price` trace gate.

The search grid is the midpoint of each pooled v5 final-role bin with `n>=20`,
then filtered to strictly profitable prices and, when the opponent value is
visible, the interior of the ZOPA.  Hidden A(P) is the structural uniform mixture
of the four responder-type curves, using a type row at `n>=8` and the pooled rate
otherwise; complete information uses the visible type with the same fallback.
For each candidate it computes exact-cell empirical midranks from CDF v3 and
maximises `A(P)F(payoff)+(1-A(P))F(0)`.  It separately computes the true money
argmax `A(P)*payoff`.  The returned plan records previous/chosen/money prices,
both acceptance probabilities and expected-rank values, F(0), CDF n, grid size,
cell, acceptance basis, arm, status and fallback reason.

CDF cells with fewer than 30 observations do not price: at n=30 one observation
already moves the empirical rank by 0.033 and worst-case pointwise SE is about
0.091.  Unknown/invalid/thin CDF cells, missing acceptance curves, and no covered
profitable bin all fall back to the complete pre-existing target.  Focused tests
cover a 74%-zero cell (`F(0)=0.37`) where treatment lowers a seller ask from the
fixed 0.80-span price 136 to 115 and exact expected-rank assertions require the
nonzero rejection term.  They also cover uniform hidden-type mixing,
observed-type complete-information pricing, flag-off/hash control, every
required fallback, offer-only real-final reachability, posterior precedence,
split-transform bypass, and buyer payoff symmetry.  Full suite: 609 passed;
only the two pre-existing bargaining failures named in AGENTS.md failed.  Codex
did not invoke replay evaluation, arena, or red-team, or touch a live flag, fleet
process, or deployment file.

**Objections / proposed validation:**
1. This is a fitted proxy, not an identified policy: CDF v3 contains our own
   games and omits opponent type/messages, while hidden v5 type labels are
   recovered mainly after agreements.  Uniform weights avoid v2's selected
   posterior weights but cannot remove selection inside the component curves.
2. Before any arena or deploy, Claude should run the registered reachability
   check and require eligible>0, fired>0, action_changed>0.  This implementation
   did not run it because the operator reserved replay-based validation for
   Claude.
3. If armed live, inspect plan fallback rates and direction by role/cell, then
   judge the pre-committed game-level hash arms with
   `scripts/live_percentile.py --ab rank-price`; model-predicted expected rank is
   diagnostic only and must not be the promotion criterion.

## 2026-08-22 — negotiation rank optimisation derived; no behaviour changed

The finite-horizon policy is a belief-state dynamic programme with terminal
utility equal to the exact-cell payoff midrank, not money.  At a terminal offer
the correct objective is `F(0) + P_accept(p) * (F(u(p)) - F(0))`; at continuing
states it also needs the full accept/counter/walk transition kernel and Bayesian
updates over the four opponent types.  The three shipped artifacts do not supply
that kernel, so a full backward-induction implementation is not yet identified.

**Exact correction in the one-round complete-information cell:** the seller is
the sole proposer and the buyer only decides.  The seller's rational price is
buyer value minus one cent; the buyer's exact best response is already shipped:
accept every strictly profitable offer.  The reported 0.7183 seller versus
0.3336 buyer percentile is proposer advantage, not a missing buyer ask policy.

**Terminal hidden-type benchmark (uniform four-point prior):** combining the
rational acceptance steps with the shipped CDF moves the actual one-round seller
policy away from the money optimum by up to 0.30B.  Seller own factors
0.8/1.0/1.2 choose money asks 1.20/1.50/1.50B versus rank asks
1.00/1.20/1.50B.  A separate v5 fitted-curve proxy over the actual terminal
proposer cells (one-round seller; round-10 buyer) shifts price by up to 0.275B
and estimated rank by up to +0.111.  Rank always weakly buys more acceptance on
the supported grid.  Structural argmaxes are exact conditional on the rational
response step and shipped CDF; their percentile levels and every v5 result are
fitted proxies.

**Visible-span correction:** current hidden games have `zopa=None`; the opponent
bid bound changes only the anchor, and the span veto is unreachable.  The cited
12,000/15,000 transcript was accepted by the absolute learned-table threshold,
not because a latest-bid span scored 100%.  If a share diagnostic is retained,
use the posterior distribution of `(P-c)/(v-c)` (seller) or `(b-P)/(b-c)`
(buyer), conditional on a ZOPA, never the ratio to a bid-created denominator.

**Objections / required tests before implementation:**
1. The CDF omits opponent type and messages, while hidden cells are heavily
   own-policy contaminated; verify that its key matches the server's scoring
   cell and refit complete-information cells by the full value pair if required.
2. The v2 posterior and v5 type curves label hidden types mainly after agreement,
   so they are selected-on-close.  Start from the exact uniform prior, fit offer
   likelihoods on uncensored complete-info data, and validate calibration by
   hidden first-offer bucket before using them for belief updates.
3. Fit an identified accept/counter/walk kernel (including counter-price
   distribution), then solve H=10 on a cent/breakpoint grid and test a default-OFF
   per-game randomised arm.  Until then, do not ship a rank-DP behavioural flag.

## 2026-08-22 — negotiation opponent clone V2 implemented, default OFF

`GLEE_SIM_NEGO_RESP_V2` now switches the simulator's negotiation clone from the
legacy value-first price lookup to a separately fitted V2 instrument.  When both
values are directly visible and the span is positive, V2 keys responses on the
candidate proposer's 4%-binned share of span.  Hidden/no-span games use the
coarser `price/base` observable, with buyer/seller directions normalized onto one
greed axis.  Terminal and continuing responses have separate keys so one-round
ultimata cannot contaminate round-one continuation play.  The tracked model was
refitted on 29,105 games and carries 701 pooled V2 response cells (528 share,
173 price; 588 continuing, 113 final) with zero private-value keys.

The hidden value-conditioned table is deliberately dropped, not reweighted:
the responder value is recoverable in hidden games only after agreements, and
the measured buyer m1.5 / round-4+ / price-bin-1.0 cell was 0.640 acceptance
(n=25) against 0.027 (n=2,793) without that selected label.  Weighted PAVA makes
acceptance non-increasing in proposer greed; interior gaps take the greedier
neighbor, the generous edge stays flat, and asks beyond greedy support get zero
acceptance.  There is no profitable-price auto-accept fallback.  Structural
no-loss checks prevent pooled hidden curves or counters from accepting/offering
through the clone's own reservation value.

The same flag selects unconditioned counter distributions represented by
equally weighted quantile midpoints.  This replaces the legacy
`sorted(values)[:400]` left-tail truncation under V2 only; the old algorithm is
still the default.  Final-round V2 rejection omits the otherwise-invalid
counteroffer.  `sim/replay_eval.py` now clears `GLEE_SIM*` between arms.

Verification: focused field-clone tests 18 passed.  Full suite: 599 passed and
only the two pre-existing bargaining failures named in AGENTS.md failed
(`test_bargaining_horizon_floor`, `test_sim_grid[bargaining]`).  No arena,
replay_eval, red-team run, live flag, fleet process, or deployment file was
touched.  The required regression pins the old clone accepting an unseen but
profitable 95%-of-span ask, then proves V2 rejects it rather than assigning
acceptance probability one.  A schema smoke test prevents committing a stale
four-part/reject-all model artifact.

**Objections / proposed validation:**
1. `scripts/check_reachability.py` replays our strategy, while this flag executes
   inside the opponent clone, so its standard eligible/fired/action_changed
   contract cannot observe this simulator gate.  The direct old/new clone test
   is the reachability proof; Claude should run the paired negotiation arena
   with V2 present in BOTH control and candidate before trusting a strategy A/B.
2. `Field._field_weight` computes `unnamed_games - named_games`; on this refit it
   is 40, making behavior draws almost entirely named clones before opponent-name
   redaction.  This may be an accidental weight bug or an undocumented way to
   model hidden identity separately from hidden behavior.  Do not change it
   without first deciding that estimand; test the intended named/pooled mixture.
3. Even after the terminal split, round buckets 2-3 and 4+ remain deliberately
   coarse.  Validate calibration by seat/terminal/round bucket before promoting
   any price-moving negotiation flag.  These are observational, shape-restricted
   response curves rather than identified off-policy effects, and conservative
   tails may create false negatives; arena evidence still beats this model.

## 2026-08-22 — persuasion: buyer parser tri-state correction implemented

`GLEE_PERS_PARSE_TRI` is implemented default OFF. When armed, buyer v1 and v2
preserve parser abstention as `None`: historical abstentions do not update the
seller-type posterior, and a current abstention leaves `P(high)` at the prior.
An explicit parser decline is a final hard veto. The shared legacy boolean
wrapper is unchanged for seller policy, so this flag cannot move seller play.

Focused regression coverage proves the flag-off path still makes the original
ambiguous-message purchase, while the armed path passes when the prior is below
`1/v`; a second case proves an explicit decline vetoes a purchase that the v2
posterior otherwise makes. Verification: focused parser tests 49 passed; full
suite 581 passed, with only the two pre-existing bargaining failures named in
AGENTS.md (`test_bargaining_horizon_floor`, `test_sim_grid[bargaining]`). No
live configuration, fleet process, or deployment file was touched. Claude still
owns verification and deployment.

## 2026-08-22 — negotiation: two theories tested, both moved

**Codex's first review paid for itself.** It found that the surplus probe is
invalid AND contaminates live accept/reject decisions (`target` is read at
negotiation.py:1046 and :760, not only on the offer path). Verified at both
call sites. ACTION PENDING: set `GLEE_NEGO_SURPLUS_PROBE=0` on `composite` and
`conceder` — blocked by the local permission classifier, needs the operator.

**The "we are too soft" theory (A) is refuted for the concession schedule.**
Arena says faster concession is worse on percentile AND closes fewer deals
(4 runs, all CIs excluding zero). See FINDINGS "Measured NEGATIVE".

**The "half the games are impossible" theory (B) is now exact, not folklore.**
Read off the generator: complete-info cells are 6/6 feasible, hidden-info cells
6/16, overall 45% infeasible. We close 91.8% of complete-info and 79% of
feasible hidden-info games. The remaining prize is ~8% of negotiation games.

**Contested / next:**
1. Codex's rank objective `F(0) + P(accept|x)[F(payoff(x)) - F(0)]` over the
   exact-cell empirical CDF. If the CDF really has a fat atom at the even
   split, pricing one tick above it is nearly free rank. Needs the per-cell CDF
   built first — that is the highest-value measurement now.
2. negotiation.py:319 floors no-ZOPA seller asks at 1.15x cost on a "39%
   positive" figure that fit_percentile.py calls a role-pooling phantom. If the
   figure is dead the rule should go. UNVERIFIED.
3. The probe, if rebuilt, must assign the arm INSIDE the offer branch only.

## 2026-08-22 — Codex connected as reviewer

Codex CLI 0.149.0 installed, authenticated via ChatGPT, registered as a
project-scoped MCP server (`.mcp.json`) and callable non-interactively with
`codex exec --sandbox read-only "<prompt>"`.

**Open questions where an independent review would be most valuable:**

1. `GLEE_NEGO_SURPLUS_PROBE` (live on Agent 5 + Test 3). Is the randomised
   design sound — assignment seeded on game id, stratified by seat/round-block/
   cap? Is `scripts/analyze_surplus_probe.py` computing P(accept|x) without
   re-introducing selection bias? Is the decision rule (peak of P(accept)*x plus
   continuation) the right objective given percentile scoring?
2. `GLEE_NEGO_FINAL_OPTION` — values our own final take-it-or-leave-it proposal
   as P(accept) x surplus off fitted curves, and refuses to accept below it.
   Arena +0.0004..+0.0012 across two seeds. Is the option value correctly
   specified, and does the buyer branch (pooled `buyer_final` curve) carry the
   same selection problem the response model died of?
3. Persuasion is stuck: no identified defect, play at the 0.548 percentile,
   ratings drifting with the field. Is there a measurement we have not made?

## 2026-08-22 — complete-information negotiation price guards implemented

Three default-inert flags now guard the final numeric action in
`glee_agent/actions.py`, after heuristic or full-LLM selection and after action
repair: `GLEE_NEGO_ZOPA_CLAMP` (boolean, default OFF),
`GLEE_NEGO_ULT_FLOOR` (float, default `0.0`), and `GLEE_NEGO_ULT_CAP` (float,
default `0.85`, read only while the floor gate is armed). The same postcondition
covers offers and reject/counter prices; hidden-information states return before
either visible opponent bound is read.

Diagnosis: `GLEE_BARG_OPPONENT_FLOOR=0.39` does not leak into negotiation. The
0.390 one-shot mode is negotiation's independent `nego_zopa_share=0.39` under
ENDGAME_V3. The 0.020 mode is `GLEE_NEGO_MIN_MARGIN=0.02` without that endgame
floor. The 1.440/1.800 modes are the HORIZON_V2-off hardliner branch: visible
opponent value is ignored, and a 4.0x anchor with 0.12 margin emits 1.36x cost.

Focused verification: `tests/test_nego_zopa_guards.py` passes 13 tests covering
default-off behavior, seller and buyer clamps, an impossible 14,000 seller ask
after a full-LLM replacement, reject/counter prices, a hidden-information
non-clamp, the 0.72 floor in both seats, the default 0.85 cap, and a live-tuned
0.80 cap, including fractional valuation boundaries after wire rounding. Full
suite: 653 passed; only the two AGENTS.md-documented bargaining failures remain
(`test_bargaining_horizon_floor`, `test_sim_grid[bargaining]`).

**Objections / proposed validation:**
1. `ULT_CAP` is deliberately nested under `ULT_FLOOR > 0`; applying its required
   0.85 default unconditionally would violate the default-off deployment rule.
2. The ZOPA clamp removes dominated, impossible proposals but does not identify
   the best interior share. Keep 0.72/0.85 as explicit runtime settings and use
   the supplied one-round evidence; do not generalize the cap to multi-round
   complete-information play.
3. `scripts/check_reachability.py` now coerces replayed decisions so it can see
   these post-plan wire guards. Before deployment, run it separately for
   `GLEE_NEGO_ZOPA_CLAMP=1` and `GLEE_NEGO_ULT_FLOOR=0.72`; the latter control
   must set the older `GLEE_NEGO_ULTIMATUM_SHARE=0`, or its existing 0.80 ask
   masks a 0.72 floor. Prove the cap knob separately with
   `GLEE_NEGO_ULT_CAP=0.80` and ULT_FLOOR armed in the control; an explicit 0.85
   candidate is identical to the code default and correctly changes nothing.
   Each meaningful run must show eligible, fired, and action_changed above zero.
   Claude remains the only fleet deployer.

## 2026-08-24 — persuasion workstream boundary and exact-cell prose probe

Persuasion deployment state, the rejected Test 2 rank-gate mechanism, and the
precommitted seller wording experiment are recorded in
`.ai/PERSUASION_HANDOFF.md`. Negotiation/bargaining owners should treat that file
as read-only; no persuasion change in this workstream alters their code or flags.

Objection resolved before deployment: the historical p=.8 token/prose purchase
contrast is observational, conditioned on positive recommendations, and crossed
multiple policy eras. It cannot promote prose. The resulting
`GLEE_PERS_P08_R125_PROSE_AB` code is therefore default OFF and randomized per
game in the exact known-CV seller/text/p=.8/v=1.25P cell. On Agent 5's exact live
stack its reachability check reports 340 eligible, 220 fired and 220 changed
wire actions. Official dashboard per-game deltas, all assigned outcomes, zero
mechanism failures, and the preregistered 120/arm rule are required; local CDF
percentiles remain diagnostic only. Test 2 and Test 3 are protected from the
research deployment.

## 2026-08-24 — negotiation stale-stall arm and paper review

Built, default OFF: `GLEE_NEGO_STALL_CURRENT_BREAK_AB`. The existing stall
detector reads only the last three completed `history[*].offer` prices. On a
decision turn, the standing `last_offer` is one opponent action newer. A live
seller-.8 game therefore classified historical 0/0/0 as a continuing stall
even though the current buyer bid had advanced to 440,779.69; `stall_park`
rewrote the scheduled ~1,400,527 counter to 900,000. Last-20k shadows found
52-120 favorable current breaks and 35-107 changed counters per major slot.

The treatment is a triggered 50/50 per-game hash. At the first state where the
current opponent offer improves for us by strictly more than 1% relative to the
historical stall price *and* suppressing the writer gives us a strictly stronger
counter, treatment suppresses only the offer-target stall writer; control is
byte-identical. Wrong-direction schedule states are logged as ineligible.
`_their_stall_price` itself is unchanged, so
dead-game walking and stall acceptance retain their old semantics. The arm
fails closed unless `CONTINUATION_ACCEPT=1`, and refuses mixed stacks carrying
the first-offer, extreme-open, terminal-counter, hidden-policy, hidden-floor, or
first-principles experiments. This prevents target assignment from leaking into
legacy decisions or becoming an unanalysed factorial.

Do not arm while the current opening/terminal probes are live. The old park was
accepted in the motivating transcript, so semantically correcting stale state
may still lower close rate; this is a randomized hypothesis, not a direct bug
fix. Read every first-trigger outcome with `scripts/live_percentile.py --ab
stall-current-break --since T0 --slots ... --official-json FILE`. Promotion
requires 100 resolved official games/arm, 20/arm in each role, official rating
delta CI above zero, close lower CI above -2pp, nonnegative role/information/
horizon/scale/message point estimates, and zero mechanism failures.

Paper review: arXiv:2502.16242 studies a different six-party HarborCo game, so
its deals and policies do not transfer. Its communication-free baseline is the
useful methodological result: once acceptability is structurally identifiable,
multi-agent dialogue adds little. The GLEE paper (arXiv:2410.05254v3, Section
4) is directly aligned with our localization: its negotiation efficiency is
17.3-17.4pp above baseline for complete-information unknown-horizon games, but
only 4.1-5.5pp for hidden unknown-horizon and 8.3-9.2pp for hidden cap-10. That
supports horizon-specific experiments and rejects a universal curve. Its
model-pair effects support a later named-opponent arm, but efficiency/fairness
are not our percentile objective, so neither paper authorizes a deployment.

## 2026-08-24 — negotiation hidden minimum-share acceptance arm

Built default OFF: `GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB`. This is a prospective
decision experiment, not a retroactive claim that every low-share agreement
should have been rejected. The validated hidden support lets our own type identify
the smallest positive feasible ZOPA; the arm marks a nonfinal profitable offer
strictly below 40% of that minimum only when the current table/stall/continuation
stack is otherwise about to accept. Hash controls accept byte-for-byte as before.
Candidates reject and emit the existing profitable-side counter. Every first
assignment and every eventual zero/agreement/pending result stays in the ITT.

The broader all-acceptor estimand is deliberate. Historical current-slot turns
contain 1,243 below-table fallthrough accepts and 230 direct table accepts under
the same support floor. Restricting the arm to `table_accept_below` would leave a
known low-share region shadowed by the table's late 0.034B/0.076B thresholds.
Conversely, assigning every low-share state before knowing whether control rejects
would only dilute the effect. The hook therefore runs at each would-be acceptance
branch and records which control acceptor owned the decision.

Adversarial objections resolved before deployment:

1. The support bound is conditional on a positive-ZOPA latent cell. Three of 479
   recovered historical finals had negative opponent payoff, so the arm is not a
   dominance guard; the randomized official rating outcome must pay for that risk.
2. The pure shared signal now excludes real final rounds itself. The terminal
   any-positive rule remains untouched and is covered by a dedicated test.
3. First-principles is not a global conflict because its hidden scope is only a
   single-round seller cell and returns before this path. All genuinely overlapping
   opening/terminal/hidden/accept experiments still fail closed.
4. Exact Test 3 stack reachability at seed 2309 over 1,500 paired negotiations is
   55 eligible / 26 fired / 26 changed actions. Dedicated tests are 50/50 and the
   impacted negotiation/reader suite is 444/444.

Precommit: arm only `conceder` after inert code is pushed and that process naturally
rotates. Record T0 after the overlay is live. Read with `scripts/live_percentile.py
--ab hidden-min-share-veto --since T0 --slots conceder --official-json FILE`.
Promotion requires 100 resolved official games/arm, 20/role/arm, official-delta CI
above zero, close point delta >=-5pp, nonnegative role points, and zero mechanism
failures. One harm look is allowed at 30 official games/arm; reject if its official
CI is wholly negative. Never touch bargaining code or any bargaining flag.

## 2026-08-24 — Test 3 rotated; exact official join proven

Test 3 naturally rotated from PID 67640 to PID 73157 at 19:22:14 IST and the
refreshed state shows `GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB=1`. The first new-code
negotiation action at `1787579568.528749` was an ineligible outgoing offer, so it
is not causal T0. Keep T0 pending until the first plan records
`hidden_min_share_veto` on a qualifying would-accept decision; hash controls and
candidates both record that metadata. Do not backdate to process start.

The first real dashboard/local smoke join now succeeds exactly. Dashboard record
`Aug 24, 2026 7:08 PM`, Buyer, Agreement, +5.1, hidden cap-10, full ten-round
offer/decision/counter transcript, and payoffs 20/10 maps uniquely to local game
`3da88013-1084-4c01-875d-2f7843a44d9f` with one candidate and zero ambiguity.
The authenticated UI's timestamp format, active snapshots, and timeout wire
events exposed three synthetic-only gaps; `scripts/join_official_history.py` now
parses the UI timestamp only with an explicit timezone, ignores known live
snapshots, and preserves timeout as a distinct event. Focused tests: 15 passed.
The latest 20 official Test 3 negotiation records from 19:00-19:12 (all pre-arm)
sum +24.9 rating: agreements +38.2 (n=10), no-deals -13.9 (n=7), walks +0.6
(n=3). This is a descriptive baseline, not the randomized estimate.

## 2026-08-24 — trend-confirmed TABLE precedence arm built inert

Built default OFF: `GLEE_NEGO_TABLE_VCONT_PRECEDENCE_AB`. This is the narrow
randomized test recommended by the latest Test 3 shadow: TABLE currently returns
before the state-dependent continuation comparator. Candidate suppresses that
return only when three distinct improving opponent prices identify a positive
trend, existing continuation exceeds accept-now surplus, the support-minimum
signal is absent, and STALL would not immediately accept. It then falls through
to the existing counter unchanged; control accepts byte-for-byte.

The trigger deliberately excludes the continuation model's no-trend basis,
because an extrapolation from our own unplayed target is not identified. It also
refuses every overlapping negotiation arm and requires the exact future stack
including FINAL_OPTION=0.60. Latest 100,000 Test 3 turns produced 76 first-
eligible games; future-stack reachability over 1,500 paired games (seed 2411)
reported 47 eligible / 19 fired / 19 changed. Do not arm it during the current
support-minimum experiment. Its clean deployment window is still pending;
historical completed outcomes cannot promote it.

Update: the official reader is now built as `--ab table-vcont-precedence`. It
recomputes the trigger from the logged state/plan, verifies hash parity and the
direct-TABLE control versus exact candidate counter wire, retains unresolved and
all terminal outcomes, excludes cross-fleet duplicates from causal estimates,
and enforces the precommitted official-score/close/stratum gates. Combined
precedence/veto focused verification is 83/83. The arm remains OFF; no behavior
changed.

## 2026-08-24 — hidden-veto causal T0 and direct-leader curve audit

The first qualifying support-minimum assignment arrived at
`T0=1787581117.643784` (19:48:37 IST), game
`99c476fc-5bce-44b0-af07-57382aec6160`. It was hash control, hidden cap-10
seller-.8, round 6, text enabled. The buyer's `.85666667B` offer paid us
`.05666667B`, below the `.08B` support-aware floor, and direct TABLE accepted.
The independent reader reconstructed the signal and returned
`mechanism_ok=true`. This exact first exposure, not the 19:22 process rotation,
is the lower bound for every causal read. At the time of freezing, its local
collector final had not yet appeared, so outcome status remains unresolved.

Independent review reconstructed Clod's private type in both observed cap-10
buyer trajectories: agreement at `1.008B` plus Clod payoff `.192B` implies
buyer value `1.2B`. The two full paths were approximately
`[.8108,.8112,.8196,.8648,1.008]B` and
`[.8179,.8180,.8217,.8553,1.008]B`. This identifies actions and type, not the
causal value of copying them; their fitted timing exponents also differ. Do not
build a literal five-price clone now: its fifth point directly overlaps the
running cap-10 buyer-1.2 terminal experiment. First finish that experiment. If
the terminal rule promotes, freeze it in both arms and test only the first four
Clod midpoint prices prospectively; otherwise redesign the terminal component
before any curve trial. Hardliner is the only currently clean host and would
need roughly 57 hours for 100/arm at its observed cell arrival rate, another
reason not to launch a bundled arm.

Authenticated/API state around 19:44-19:48 IST: Test 2 was sixth overall at
2315.51 versus third-place Mythos01 at 2383.21 (gap 67.70). Negotiation leaders
were Clod 2894.70, 7aidara_Gamma 2675.62, and opus 5(4) 2652.36; our best visible
negotiation rating was Test 4 at 2070.5. These are transient monitoring values,
not policy-effect estimates.

## 2026-08-24 — broad cap-10 buyer curve built for an hours-scale read

`GLEE_NEGO_HI_CAP10_BUYER_CURVE_AB` is implemented default OFF. It replaces the
rare-cell-first optimization loop with a high-frequency, all-viable-type hidden
cap-10 buyer test. Candidate owns only the first four outgoing counter prices
and uses their pointwise midpoint across two completed, type-reconstructed Clod
buyer-1.2B paths, normalized by our visible buyer value:
`[.6786404167,.6788316667,.6838475,.71674625]`. Control keeps the current stack
exactly; the fifth/terminal price and accept/walk decisions are unchanged. The
two Clod paths both closed at `1.008B` with private value `1.2B`, but that
terminal is not part of this arm. Scaling to 1.0B/1.5B is an explicit randomized
extrapolation, not a claim that hidden no-deal types were observed.

The runtime refuses overlap with the old buyer-1.2 terminal arm, broad hidden
writers, hidden support-veto, TABLE precedence, stale-stall, CLOSE_AB, or
PROBE_V1. Do not arm until each overlapping flag is explicitly `0` on every
target. The official reader is
`--ab hi-buyer-curve`; it cohorts before the first action, retains immediate
accepts and all non-closes, audits every candidate counter, and uses dashboard
rating delta as primary. Harm/final rules are frozen in EXPERIMENTS.md.

Independent review correctly rejected the original five-price bundle: it
aliased early imitation with the unsettled terminal mechanism and overclaimed
the cross-type evidence. The implementation was changed before activation.
The remaining scaling is a randomized treatment whose official effect is
reported separately by own type; no causal or behavioral identification is
claimed in advance.

Exact intended champion stack with the old terminal flag disabled, 1,500 paired
games seed 2601 after terminal isolation: 549 eligible / 227 fired / 227 changed.
Focused tests 125 pass; the impacted negotiation/action/reader set is 530 pass.
Full suite: 1,269 passed with only the two predeclared bargaining failures. No
bargaining code, bargaining flag, live arm, process, key, or deployment file
was changed.

Deployment followed immediately after the verified commit because the operator
rejected another multi-day rare-cell wait. Commit `e007a90` was pushed to main,
then the interlocked safe deployment drained every in-flight game normally and
relaunched all five slots at 2026-08-24 20:47:08 IST (`T0=1787584628`). The
broad curve A/B was subsequently stopped on champion, conceder, randomized,
and composite at the operator's direction before a meaningful sample accrued;
all four flags are explicitly `0`, so there is no causal verdict. Test 2
hardliner stayed control. The old terminal arm is off on its three former slots
and Test 3's overlapping hidden-min-share-veto arm is off. No bargaining value
was changed.

### 2026-08-24: top-agent buyer clone and the 20:47 fleet outage

The 20:47 deployment used `fleet.py safe-restart`. Despite its drain wording,
the supervisor shutdown path interrupted every `run_agent.py`; each slot then
timed out its last three held games and the platform suspended queue joins for
30 minutes. All five agent processes remained healthy but had zero active games
until their recorded expiries at 21:17:02–21:17:08 IST. This was a deployment
error, not evidence about any negotiation policy. Do not use `safe-restart` for
behavior deployment; use a named zero-game cycle or a natural shift boundary.

At the operator's direction, the replacement experiment copies observable
top-agent behavior on Test 3 only. A 70-game reconstruction across 7aidara,
Alpha, Beta, and Gamma identified exact shared buyer paths rather than a fitted
median: complete cap-10 own-zone claims are
`[.960,.898,.836,.774,.774]`, and hidden paths are literal price/base tables by
own type (buyer 1.5 is `[.905,.905,1.075,1.075,1.245×4]`). Mapping the
payoff-hidden classes to monotone private types remains the randomized part.
The treatment is buyer-only because the contemporaneous official window had
seller `+47.9` and buyer `-24.4`, with buyer no-deals accounting for `-22.5`.
It is a single full-policy hash arm (`GLEE_NEGO_TOP_BUYER_CLONE_AB`) so offers,
acceptance, and stopping behavior travel together. Focused tests pass 11/11,
all negotiation tests pass 563/563, Test 3 reachability is 3,827 eligible /
1,575 fired / 1,575 changed, and the full suite is 1,280 pass plus only the two
known bargaining failures. Bargaining code and flags were not changed.
