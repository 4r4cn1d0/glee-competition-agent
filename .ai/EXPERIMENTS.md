# EXPERIMENTS — hypothesis, design, verdict

## RUNNING

### First-principles terminal cells (negotiation, Test 4)
- **Hypothesis**: in cells where our seat owns the final offer, bypassing every
  downstream price rewriter and leaving the counterparty one positive cent
  improves same-cell percentile.
- **Design**: 50/50 per-game hash arm, `sha256("nego_fp|" + game_id) & 1`, on
  Test 4.  Corrected cohort starts at timestamp `1787534215` after commit
  `f32c334`; do not mix earlier games into this read.
- **Corrected ITT status (2026-08-24 ~14:15 IST)**: the earlier result-only
  analysis is not promotion-grade because the separate outcome collector
  stopped at 06:00 with 11,737 games outstanding.  The supervisor kills a
  process only after the server reports `active_games=0`, but may do so while
  `GameLog.finalize()` is still fetching results; a missing local final is
  therefore not an identified server abandonment.  The complete first-turn
  cohort has only 18 locally recovered outcomes and 64 unresolved.  Do not
  impute the 64 as `.05`, and do not select the 18 as if complete.
- **Read with**: `scripts/live_percentile.py --ab fp-complete --since
  1787534215 --slots randomized`.  It cohorts before action, leaves cold/fresh
  missing finals unresolved, and uses the checked-in exact 1,152-cell official
  seed CDF rather than the hidden-value-pooled local model.
- **Decision rule**: do not promote while any outcome is unresolved or either
  cell's official-score CI crosses zero. `GLEE_NEGO_FP_COMPLETE_ONLY` remains a
  default-off mechanism switch, not a deployment recommendation. Any larger
  terminal crumb is a separate experiment.
- **Verdict**: promotion withdrawn; complete-info and hidden both pending.

## DISABLED / INVALID — NOT LIVE

### Surplus-share response probe (negotiation, complete-info)
- **Hypothesis**: our complete-info closes sit at the 49.4% attractor; the
  causal frontier P(accept | surplus share x) may peak above it.
- **Design**: randomise x over {0.50,0.55,0.60,0.65,0.70,0.75} in complete-info
  offer turns, seeded on game id, stratified by seat/round-block/cap.
- **Live on**: nowhere; `GLEE_NEGO_SURPLUS_PROBE=0` on all five slots.
- **Read with**: `scripts/analyze_surplus_probe.py`
- **Decision rule**: pick the x maximising P(accept)*x plus continuation, NOT
  the highest observed rating-by-band (that conditions on deals happening).
- **Verdict**: invalid as run. Assignment leaked into the accept/reject target,
  and its analyzer joined the wrong response turn. Do not restore this design.

### Seller-message parser v2 (persuasion)
- **Hypothesis**: the decline table missed "not recommended" and friends, so we
  bought messages that explicitly declined. 373 such purchases in 20h of logs,
  373 low quality, 0 high.
- **Live on**: nowhere; the flag is absent from all five live arm stacks.
- **Verdict**: historical candidate only, not a running experiment. The newer
  tri-state parser is a separate default-off mechanism.

## RUNNING — LIVE CAUSAL MEASUREMENT

### Hidden unknown-horizon first-offer greed probe (negotiation)
- **Flag / assignment**: `GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB=1`;
  `sha256("nego_hi_uncapped_first_offer_v1|" + game_id) % 3`, yielding
  `control`, `share80`, or `share95`.
- **Why this cell**: Test 2's latest 100 official dashboard results put hidden
  unknown-horizon games at `-1.604` rating/game (n=27), versus `-0.189` in
  hidden cap-10 and `+0.489` in hidden single-round. This is the only horizon
  the arm can change.
- **Candidate**: only the two own types with exactly one feasible counterpart
  are eligible: seller 1.2B (only buyer 1.5B can trade) and buyer 1.0B (only
  seller .8B can trade). On the first outgoing price, share80 uses 1.44B/.84B
  and share95 uses 1.485B/.81B respectively. Every later price and every
  accept/reject/walk decision is current control.
- **Why narrower**: the rejected ladder bundled greed, support ordering, and a
  four-offer hold. This trial isolates multi-round greed elasticity without
  assuming a rejected crumb reveals type or causes the opponent to wait through
  a deterministic concession schedule.
- **Primary cohort / rule**: every matching first turn before action, including
  buyers that immediately accept and never emit a price; retain all no-deals,
  walks, timeouts, and unresolved outcomes. Compare each greed arm with control
  and share95 with share80. Promotion requires official per-game score 95% CI
  above zero, close-rate lower bound above -2pp, zero wire failures, and no
  material role/scale sign reversal. Conditional deal share is diagnostic only.
- **Live on / boundary**: Test 1 (`champion`), Agent 5 (`composite`), and Test 4
  (`randomized`), all cleanly on pushed code by `T0=1787567218` (2026-08-24
  15:56:58 IST). Test 2 is protected pending evidence; Test 3 is untouched.
- **Read with**: `scripts/live_percentile.py --ab hi-first-offer --since
  1787567218 --slots champion,composite,randomized`. It labels its
  hidden-value-pooled metric diagnostic and never emits a promotion verdict.
- **Reachability / first wire evidence**: Test 2's latest 20,000-turn shadow had
  47 eligible, 35 candidate-fired, and 35 changed actions. Before the common
  boundary, Test 4 emitted exact share95 wires at 1.485B and .81B and Agent 5
  emitted a hash control, all with `wire_ok=true`. The runtime refuses to
  activate if `HIDDEN_POLICY_V1` or `HIDDEN_FLOOR` is armed.
- **Early common-cohort read (2026-08-24 ~16:17 IST)**: 12 assigned, 7 resolved,
  5 unresolved, zero agreements among the seven resolved, zero wire failures.
  Local diagnostic percentile: control .4028 (n=1), share80 .4028 (n=1),
  share95 .3852 (n=5). No inference: each eligible own type has only 25% structural
  feasibility, and the first counteroffers sat far outside our reservation
  values. Continue to the precommitted sample/rule; do not react to this draw.

## RUNNING — LIVE CAUSAL MEASUREMENT

### Hidden cap-10 buyer-1.2 terminal counter (negotiation)
- **Flag / assignment**: `GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB=1`;
  `sha256("nego_hi_cap10_buyer12_terminal_v1|" + game_id) & 1`.
- **Candidate**: on the round-9 buyer rejection/counter only, replace the
  terminal counter with `base+$0.01`.  Control and every noneligible action are
  unchanged.
- **Primary cohort**: every matching game from its first buyer decision, not
  only games that reach round 9.  Include all terminal outcomes and block while
  any assigned outcome is unresolved.
- **Decision rule**: official per-game score delta 95% CI above zero; close-rate
  point estimate positive with lower 95% bound above -2pp; every fired wire
  exactly `base+$0.01`; no material scale/message sign reversal.  Reject on
  negative official-score CI or any mechanism failure.
- **Read with**: `scripts/live_percentile.py --ab hi-terminal --since T0 --until T1`.
  Its local hidden-value-pooled percentile is diagnostic, not promotion-grade.
- **Reachability**: 57 eligible / 20 fired / 20 changed on 3,000 paired games.
- **Live on / boundary**: Test 1 (`champion`), Agent 5 (`composite`), and Test 4
  (`randomized`) from the clean common boundary `T0=1787568551` (2026-08-24
  16:19:11 IST). Test 2 and Test 3 are unarmed. The first-offer probe is
  disjoint because it requires an unknown horizon; Test 4's first-principles
  module does not own hidden cap-10 buyer cells.
- **Exact-stack preflight**: champion's live stack produced 19 eligible, 10
  fired, and 10 changed wires in 1,000 paired games (seed 1701), including
  literal `B+$0.01` at 100, 10,000, and 1,000,000 scales. The existing 3,000
  paired check remains the higher-sample reachability result above.

Do not co-arm this experiment with `GLEE_NEGO_HIDDEN_POLICY_V1` in its first
measurement. Codex owns deployment under the operator's 2026-08-24 directive.

## RUNNING — LIVE CAUSAL MEASUREMENT

### Direct-leader hidden unknown-horizon opening copy (negotiation)
- **Flag / assignment**: `GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB=1`;
  `sha256("nego_hi_uncapped_extreme_open_v1|" + game_id) & 1` gives control or
  candidate per game.
- **Behavior evidence**: across all direct hidden multi-round encounters, not
  only agreements, Clod/Athena/doodod opened as sellers at median
  1.488/1.490/1.485B (n=10/8/12) and as buyers at .8108/.8075/.810B
  (n=9/7/14). Their current negotiation ratings were
  2918.75/2840.38/2649.25.
- **Candidate**: in explicitly unknown-horizon hidden games, copy the literal
  1.485B seller ask or .81B buyer bid on the first outgoing price only, then
  return to the complete current policy. Eligibility is restricted to seller
  own types .8B/1.0B and buyer own types 1.2B/1.5B. The running identified-cell
  probe owns seller 1.2B/buyer 1.0B, while DEADGAME_V1 already owns seller
  1.5B/buyer .8B; all scopes are disjoint.
- **Why one wire**: the direct evidence identifies the opening boundary but not
  whether the leaders' later holds cause their rating. A persistent copy is a
  separate mechanism. This arm tests imitation without bundling a concession
  schedule or changing accept/reject/walk decisions.
- **Cohort**: every matching first action before treatment, including buyers
  that accept without emitting a counter. Keep every agreement, no-deal, walk,
  timeout, and unresolved game; exclude cross-fleet duplicate game IDs from the
  pooled estimate.
- **Decision rule**: do not decide before 100 resolved games per arm and at
  least 15 per arm in each own-type cell. Promote only if official per-game
  score candidate-control 95% CI is above zero, close-rate lower 95% bound is
  above -2pp, every role/type/scale/message point estimate is nonnegative, and
  wire failures are zero. Reject on an official-score CI below zero or any
  mechanism failure. Conditional agreement share is diagnostic only.
- **Read with**: `scripts/live_percentile.py --ab hi-extreme-open --since T0
  --until T1 --slots champion,composite,hardliner,randomized`. The local
  hidden-value-pooled percentile never authorizes promotion.
- **Live on / boundary**: Test 1 (`champion`), Test 2 (`hardliner`), Test 4
  (`randomized`), and Agent 5 (`composite`) from the clean common boundary
  `T0=1787571320` (2026-08-24 17:05:20 IST). All four processes naturally
  rotated onto pushed commit `8a21e8e` before the flag was set; the overlay
  mtime was `1787571316`, four seconds before T0. Test 3 remains unarmed.
- **Preflight**: champion's exact live stack, 1,000 paired negotiation games,
  seed 1907: 100 eligible / 49 fired / 49 changed final wire actions. Focused
  suite 88 passed; full suite 1,048 passed with only the two predeclared
  bargaining failures.

The first post-boundary assignment was a composite hash control in buyer-1.2;
its ordinary first counter remained unchanged. The first emitted treatment wire
was composite seller-.8 at exactly 1.485B, and a Test 4 candidate buyer-1.5
immediately accepted before emitting a price while remaining in the ITT. All
eight initial assignments reported `wire_ok=true`. This verifies live control,
treatment, and immediate-accept cohort semantics, not outcome value. Do not arm
Test 3 before causal promotion evidence.

## REJECTED — DEFAULT OFF, DO NOT RUN

### Hidden unknown-horizon 95%-share support ladder (negotiation)
- **Rejected before deployment**: the proposed three-rung/four-hold schedule
  bundled unproved greed and timing constants. Several transcript landmarks
  used as imitation evidence came from no-deal/walk trajectories, and a rational
  opponent can reject the 5% first rung knowing a deterministic concession is
  coming. The mechanism also initially disabled broader hidden guards in
  ineligible states; independent review caught that control contamination.
- **Verdict**: implementation and reader removed. Replaced by the one-price,
  three-arm identified-cell probe above.

### Hidden unknown-horizon accept-all-profitable (negotiation)
- **Corrected counterfactual**: exact replay of all 32,403 public trajectories
  compared accept-now with each game's actual continuation after rejection,
  rather than treating a rejected bid as a zero. In the matching cohort
  (4,050 games), 375 decisions were exposed and 156 would change.
- **Result**: exposed exact-percentile delta `-0.06628`, bootstrap 95% CI
  `[-0.08183,-0.05096]`; cohort ITT `-0.00614` (sum `-24.85` percentile).
- **Why the old estimate was wrong**: it ignored later agreements at better
  prices. The prior `+0.07138` result was not the policy counterfactual.
- **Verdict**: implementation, reader, and reachability hook removed before
  deployment. Never arm this mechanism.

### Buyer selectivity safety arm (persuasion, prior EV <= price)
- **Hypothesis**: in cells where the prior does not beat price, the existing
  buyer's early and repeated purchases from sellers with no demonstrated
  selectivity create enough bottom-tail outcomes that a conservative veto
  improves same-cell percentile despite giving up substantial raw payoff.
- **Design**: `GLEE_PERS_BUYER_SELECTIVITY_AB=1` assigns each eligible game by
  `sha256("pers_buyer_selectivity_v1|" + game_id) & 1`. Control is the current
  buyer. Candidate is veto-only: wait for a historical explicit decline,
  require a current explicit recommendation, require the existing fitted
  q-grid posterior mean to strictly exceed money breakeven. The one-bought-low
  stop is no longer bundled: `GLEE_PERS_BUYER_SELECTIVITY_STRIKE_AB=1` assigns
  it independently per game with salt `pers_buyer_selectivity_strike_v1|`, so
  the ITT reader can score the gate with and without that insurance. Both flags
  are absent/default OFF. The first-arm margin is exactly `0.0`; a positive
  `GLEE_PERS_BUYER_SELECTIVITY_MARGIN` is a separate, unmeasured parameter and
  must not be changed during the window.
- **Eligibility**: buyer persuasion games with `v>u`, `price>u`, and
  `p*v+(1-p)*u <= price`. Prior-positive games are not assigned and cannot be
  changed. Cohort on the globally first eligible buyer decision and record exact
  activation/disarm timestamps; exclude games whose first exposure predates T0.
- **Primary outcome**: candidate-control mean same-cell percentile over ALL
  assigned eligible games, including no-decline games, terminal zeros and cold
  abandonments. Never condition the primary analysis on an eventual decline.
- **Decision rule**: promote only if the candidate-control percentile 95% CI is
  entirely above zero; reject if entirely below zero; otherwise continue or call
  inconclusive. Pending/invalid outcomes block promotion. A mechanism failure
  (any candidate buy before a prior explicit decline, or any second bought low
  in the independently strike-assigned cell) rejects regardless of percentile.
  Stratify, without changing the primary
  rule, by exact `(p, v/price, message mode)`, equality versus strict-negative
  prior EV, and one-decline sellers. Freeze and record hashes of both the q prior
  and percentile CDF for the whole window.
- **Cost diagnostics**: report payoff/price, purchase rate, pre-first-decline
  buys, bought highs/lows, and the one-decline subgroup. These are secondary:
  the competition scores percentile, while a seller may adapt its messages to
  treatment.
- **Rank-threshold red team**: the proposed one-step `q_rank` is not uniformly
  below money breakeven once accumulated payoff moves across CDF atoms. At the
  empirical cell medians it is lower in 8/18 cells, higher in 9/18, and tied in
  one; over the 27,493 actual purchase states it is stricter 16,973 times versus
  money's 9,843. The full candidate blocks 8,572 one-step-rank-positive buys,
  including 6,283 highs, but only 13 blocks are caused by the money cutoff after
  earlier gates. Raw `F(S)` is also a terminal/fixed-continuation calculation,
  not the dynamic threshold in a 20-round game where buying changes later payoff
  and information. Do not replace money breakeven with that myopic threshold.
- **Historical shadow, not causal evidence**: on the frozen oldest 5,181
  eligible results, full gate changes buys `27,493 -> 8,683`, payoff
  `1.1555P -> 0.7774P`, and fitted percentile `+0.01209` (normal 95% CI
  `[+0.00718,+0.01701]`). Without strike it retains 14,287 buys, payoff is
  `0.9123P`, and the proxy is `+0.01445`; the strike removes 5,604 more buys and
  costs `0.00236` percentile. The money cutoff itself removes only 56 buys in
  the sequential reconstruction and changes the proxy `+0.01484 -> +0.01445`.
  Text framing supplies `+0.01248` of the full overall delta while binary
  framing contributes `-0.00039`.
- **Held-out failure**: deterministic chronological 70/30 cross-fit, cutoff
  `2026-08-21 16:52:32Z`. The q prior uses 6,013 earlier buyer games and the CDF
  9,048 earlier persuasion games; all later cells have CDF n=270-351. On 1,555
  strictly later eligible games, full gate is `-0.00131` with 95% CI
  `[-0.01111,+0.00848]`; no-strike is `+0.00684`
  `[-0.00113,+0.01482]`. The early in-sample estimate is `+0.01442`
  `[+0.00890,+0.01994]`. The gain does not survive.
- **No-look-ahead motivation**: the observable state is "any explicit decline
  before this decision", not eventual seller type. Explicit-yes purchases after
  a prior decline outperform those before one after exact cell+round adjustment
  (`+11.72pp` high, `+0.2355P` per buy, local rank `+0.01554`), so the predictive
  gradient reproduces. But pre-decline explicit-yes buys themselves are
  money-positive (`+0.1455P/buy`) and locally rank-neutral (`+0.00036`, CI spans
  zero). This observational, action-selected contrast does not establish that
  vetoing them helps final rank.
- **Verdict**: reject the historical performance claim and do not arm either
  flag. The implementation remains inert for auditability; any reconsideration
  needs a new prospective design, not another fit to this corpus.

## NEXT (not built)
1. General accept/counter/walk response model (item 5 of the operator plan).
2. State-dependent price discrimination / shallow DP over the frontier.
3. Full-sequence opponent-type inference.
4. Partially pooled per-opponent profiles.
5. Message framing arms (orthogonal; only 7.1% of offers carry text).
