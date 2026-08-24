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
- **Decision rule, frozen before the first official outcome join**: fixed final
  read at 100 resolved official games per arm and at least 10 per arm in every
  scale x message cell. Promote only if official per-game score delta 95% CI is
  above zero; close-rate point estimate is positive with lower 95% bound above
  -2pp; scale and message point estimates are all nonnegative; every fired wire
  is exactly `base+$0.01`; and mechanism/join/outcome failures are zero. One
  harm look at 30 official games per arm rejects if the official CI is wholly
  negative. Reject immediately on any mechanism failure. This prospective
  clarification was made after local diagnostic outcomes were visible but
  before harvesting any official terminal-arm records; it prevents repeated
  official-score peeking.
- **Read with**: `scripts/live_percentile.py --ab hi-terminal --since T0
  --until T1 --official-json FILE`. The reader now joins authenticated official
  rating deltas, retains the all-assigned ITT and unresolved outcomes, audits
  exact terminal wires, excludes cross-fleet duplicates, and enforces the fixed
  rule above. Its local hidden-value-pooled percentile remains diagnostic.
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

## STOPPED BY OPERATOR — NO CAUSAL VERDICT

### Broad direct-leader hidden cap-10 buyer trajectory
- **Flag / assignment**: `GLEE_NEGO_HI_CAP10_BUYER_CURVE_AB=1`;
  `sha256("nego_hi_cap10_buyer_curve_v1|" + game_id) & 1`.
- **Why this replaces the slow loop**: the posted 63-game official window was
  `-24.4` on the buyer side and `+47.9` on the seller side; buyer no-deals alone
  contributed `-22.5`. The old terminal-only arm reaches one own type on one
  counter. This arm covers every hidden cap-10 buyer with own type
  `1.0B/1.2B/1.5B`, approximately 9% of negotiation games, and changes the first
  four price opportunities while leaving terminal price, AcceptOffer, and
  WalkAway byte-identical.
- **Candidate**: the frozen fraction-of-own-value early curve
  `[.6786404167,.6788316667,.6838475000,.7167462500]`. It is the first-four
  pointwise midpoint of two completed, type-identified Clod buyer-`1.2B` paths;
  both later ended at exactly `1.008B`, but that terminal is not copied. Scaling
  the early curve to buyer `1.0B/1.5B` is part of the treatment: matching
  `.677B/1.015B` literal opening families exist in direct top-agent traces, but
  their hidden private types are not identified in no-deals.
- **Isolation**: the mechanism fails closed if the old buyer-1.2 terminal arm,
  HIDDEN_POLICY, HIDDEN_FLOOR, HIDDEN_MIN_SHARE_VETO, TABLE_VCONT_PRECEDENCE,
  STALL_CURRENT_BREAK, CLOSE_AB, or PROBE_V1 is armed. Unknown-horizon opening
  probes are disjoint. Hash controls return before any later hidden-price writer
  and keep the current wire byte-for-byte.
- **Cohort / reader**: every matching game from its first buyer decision before
  action, including immediate accepts and games that never emit a candidate
  price. Read with `scripts/live_percentile.py --ab hi-buyer-curve --since T0
  --slots SLOTS --official-json FILE`. It audits every candidate counter against
  the frozen four-point early curve, retains unresolved/all outcomes, and removes
  cross-fleet duplicate IDs.
- **Frozen decision rule before deployment**: one harm look at 30 official
  games/arm rejects if either official-score or close-rate CI is wholly
  negative. Final read at 100 official games/arm and at least 15/arm per own
  type. Promote only if official-delta 95% CI is above zero, close lower CI is
  above -2pp, every own-type point is nonnegative, no scale/message point is
  `<=-1` rating/game, and wire/join/outcome failures are zero.
- **Verification**: exact intended-stack reachability over 1,500 paired games,
  seed 2601, produced 549 eligible states / 227 fired / 227 changed wire
  actions. Focused arm/terminal/opening tests are 125/125;
  negotiation/action/reader tests are 530/530. Before deployment the default-OFF
  flag left behavior unchanged. Full suite: 1,269 passed with only the two
  predeclared bargaining failures; no bargaining behavior or configuration
  changed.
- **Live boundary / stop**: briefly enabled on Test 1 (`champion`), Test 3
  (`conceder`), Test 4 (`randomized`), and Agent 5 (`composite`) at
  `T0=1787584628` (2026-08-24 20:47:08 IST), then explicitly set back to `0`
  on all four at the operator's direction before a meaningful sample arrived.
  Do not interpret this as a positive or negative result.

## READY — ONE-SLOT OBSERVED-LEADER BUYER CLONE

### Top-four/five observable negotiation behavior, buyer only
- **Flag / assignment**: `GLEE_NEGO_TOP_BUYER_CLONE_AB=1`; SHA-256 of
  `nego_top_buyer_clone_v1|<game_id>`, low bit 1 = candidate. Default OFF.
- **Target**: Test 3 (`conceder`) only. Seller behavior and every bargaining
  action/configuration remain byte-for-byte control.
- **Why buyer only**: the operator's 63-game official window had sellers
  `+47.9` but buyers `-24.4`; buyer no-deals were `-22.5`. Replacing the winning
  seller half would add risk with no diagnosis supporting it.
- **Candidate**: copy the wire behavior identified across 70 games from
  7aidara, Alpha, Beta, and Gamma. All four labels share the same exact complete
  buyer zone path: claim `[.960,.898,.836,.774,.774]` in cap-10 and end at
  `.712` in unknown horizons. Hidden buyer paths are literal price/base tables
  by own type, including buyer 1.5
  `[.905,.905,1.075,1.075,1.245×4]`. Mapping the three hidden path classes
  whose private payoff was not revealed to monotone own types is the explicit
  randomized hypothesis. Any-positive terminal acceptance and Athena's
  observed ninth-decision hidden-uncapped walk remain state-specific. Gill
  bates and Mythos01 do not yet have enough complete local buyer transcripts to
  identify a competing path. This is an exact behavioral clone where wire
  moves are observed; it is not a claim to possess competitors' private source.
- **Control**: the entire current Test 3 stack, selected by the opposite hash
  bit. The treatment owns both offer and acceptance policy so downstream gates
  cannot silently rewrite half the mechanism.
- **Primary outcome**: official per-game negotiation percentile/rating change,
  candidate minus contemporaneous hash control, buyer games only. Report hidden
  type, complete-information status, horizon status, terminal outcome, and
  opponent separately; never condition the estimate on agreement.
- **Emergency stop**: after at least 10 scored buyer games per arm, stop if the
  candidate is at least `-1.0 rating/game` below control or candidate live-game
  no-deal rate is 15 percentage points higher. Three consecutive candidate
  losses of `-6` or worse also stop immediately.
- **Promote**: at least 30 scored buyer games per arm, candidate official mean
  percentile at least `+0.03` above control, 95% bootstrap interval not crossing
  `-0.01`, and no-deal rate no more than 5 percentage points worse. A 30-game
  harm read is an early stop, not permission to declare success.
- **Verification**: focused clone tests 11/11; all negotiation tests 563/563;
  intended Test 3 stack reachability over 1,000 simulated games yielded 3,827
  eligible / 1,575 fired / 1,575 changed wire actions. Full suite 1,280 passed
  with only the two predeclared bargaining failures.

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

## BUILT — DEFAULT OFF, WAITING FOR AN UNCONTAMINATED WINDOW

### Current-offer stale-stall break (negotiation)
- **Flag / assignment**: `GLEE_NEGO_STALL_CURRENT_BREAK_AB=1`;
  `sha256("nego_stall_current_break_v1|" + game_id) & 1`.
- **Trigger**: the existing historical helper reports a three-offer <=1% stall,
  the current standing opponent offer has improved for our seat by strictly
  more than 1% of `max(abs(stale), abs(current), 1)`, and suppressing the stale
  writer would make our counter strictly more favorable (seller asks more;
  buyer bids less). Wrong-direction schedule states are shadowed but ineligible.
- **Candidate**: suppress only `stall_park`'s target rewrite on that turn.
  Control retains the exact existing target. Dead-game walk, stall acceptance,
  and every non-triggered state keep the original helper and behavior.
- **Identification**: cohort on the globally first qualifying pre-action turn;
  the arm has no earlier behavioral path, so trigger reach is pre-treatment.
  Keep immediate accepts, emitted counters, walks, no-deals, cold missing
  finals, and all later outcomes. Exclude cross-fleet duplicate game IDs.
- **Safety**: fail closed unless `CONTINUATION_ACCEPT=1`; refuse co-arming with
  either first-offer probe, the terminal-counter probe, hidden-policy,
  hidden-floor, or either first-principles switch. Close the cohort if the
  accept stack or anchors change.
- **Decision rule**: first decision at 100 resolved official games/arm and
  20/arm per role. Promote only if official per-game rating-delta CI >0,
  close-rate lower CI >-2pp, all role/information/horizon/scale/message point
  estimates >=0, and mechanism failures=0. Reject on official CI <0 or any
  mechanism failure. Local pooled-CDF percentile is diagnostic only.
- **Read with**: `scripts/live_percentile.py --ab stall-current-break --since
  T0 --until T1 --slots SLOTS --official-json FILE`.
- **Live on**: nowhere. Do not arm until the overlapping opening/terminal
  experiments are closed or an uncontaminated slot is deliberately selected.

### Hidden support minimum-share acceptance veto (negotiation)
- **Flag / assignment**: `GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB=1`, default OFF;
  `sha256("nego_hidden_min_share_veto_v1|" + game_id) & 1` assigns control or
  candidate once per game. Missing ids fail closed.
- **Structural signal**: validated hidden values are
  `{.8,1.0,1.2,1.5}*B`. From our observed own type, the smallest strictly
  positive ZOPA is `.2B` for seller-.8/1.0 and buyer-1.0/1.2, `.3B` for
  seller-1.2 and buyer-1.5, and nonexistent for seller-1.5/buyer-.8. On a real
  nonfinal hidden decision, mark an offer only when it is profitable and our
  surplus is strictly below 40% of that minimum, with a scale tolerance that
  excludes exact-boundary float artefacts. The share bound is conditional on a
  positive-ZOPA latent cell; irrational loss-making opponent offers are legal
  and remain part of the randomized outcome.
- **Pre-treatment eligibility**: the globally first marked offer that the exact
  current stack is otherwise about to accept through direct table acceptance,
  stall acceptance, or continuation acceptance. States the control already
  rejects are never assigned, so the estimand is the decision-level effect of
  holding instead of accepting—not a diluted universal state cohort. Control
  remains byte-identical. Candidate returns `RejectOffer` through the existing
  profitable-side counter construction; no concession parameter is bundled.
- **Scope / safety**: requires `HORIZON_V2=1`, `CONTINUATION_ACCEPT=1`, and
  `TABLE=1`; refuses the live first-offer, extreme-open, terminal-counter,
  hidden-policy/floor, stale-current-break, rank-price, close, uncapped, and
  surplus probes. First-principles is not a flag-level conflict: its only hidden
  cell is single-round and its owner returns before this nonfinal path. The real
  final-round any-positive rule is dominant and unreachable by the veto.
- **Historical motivation, not effect evidence**: five-slot turn streams contain
  1,473 matching accepted offers (1,243 below-table fallthroughs and 230 direct
  table accepts). Of 479 locally recovered finals, 474 captured <40% of realised
  positive surplus; two were exact-boundary float cases and three were irrational
  negative-opponent-payoff deals. Conditioning on accepted deals cannot identify
  what rejection would have earned.
- **Primary cohort/outcome**: include every first assignment and every eventual
  agreement, no-deal, walk, invalid, cold-missing, and pending outcome. Exclude
  cross-fleet duplicate game ids from the pooled causal estimate but retain them
  for mechanism auditing. Primary is official dashboard per-game `rating_delta`;
  local hidden-value-pooled percentile is diagnostic only. Freeze the exact
  accept stack and activation boundary for the whole window.
- **Decision rule**: efficacy only at 100 resolved official games per arm and 20
  per arm in each role. Promote only if candidate-control official-rating 95% CI
  is wholly above zero, close-rate point delta is at least -5pp, both role point
  estimates are nonnegative, and mechanism failures are zero. At the single
  preplanned harm look after 30 official games per arm, reject if the official
  95% CI is wholly below zero. Reject immediately for any scope/hash/wire failure;
  unresolved or official-missing outcomes block promotion.
- **Reader**: `scripts/live_percentile.py --ab hidden-min-share-veto --since T0
  --until T1 --slots conceder --official-json FILE`. It recomputes the production
  signal and assignment, verifies control `AcceptOffer` and candidate
  `RejectOffer`/counter wires, and enforces the decision rule by exit status.
- **Exact-stack reachability**: Test 3 (`conceder`) control stack, 1,500 paired
  negotiation games, seed 2309: 55 eligible, 26 fired, 26 changed submitted
  actions. Focused impacted suite: 444 passed; dedicated mechanism/reader suite:
  50 passed.
- **Live on**: nowhere pending inert commit/push and a natural Test 3 rotation.
  Test 3 is the only current uncontaminated slot; never alter its bargaining flags.

## NEXT (not built)
1. General accept/counter/walk response model (item 5 of the operator plan).
2. State-dependent price discrimination / shallow DP over the frontier.
3. Full-sequence opponent-type inference.
4. Partially pooled per-opponent profiles.
5. Message framing arms (orthogonal; only 7.1% of offers carry text).

## RUNNING — LIVE CAUSAL MEASUREMENT

### Exact weak-cell token versus non-leaking prose (persuasion seller)
- **Falsifiable hypothesis**: in the official persuasion seller cell
  `seller_message_type=text`, `p=.8`, seller knows `v/u`, `v=1.25*price`, and
  `total_rounds=20`, replacing the current literal positive token `yes` with
  the current quality-neutral prose template raises mean official per-game
  rating delta. The recommendation policy and negative token `no` do not
  change. A non-positive official result falsifies the hypothesis; conversion
  alone cannot promote it.
- **Why this cell**: in the clean common token window
  `[1787402777.668, 1787484376.458)`, this was the largest scoreable seller/text
  weakness: 118 games assigned, 30 locally recovered finals, local diagnostic
  percentile `.4847`, 47.5% purchase rate, and 16.7% zero outcomes. The wider
  historical positive-message contrast (token 60.8% versus prose 69.3%) is
  observational and post-action-selected; it motivates randomisation only.
  The authenticated dashboard immediately before activation also contained an
  exact text-cell game: after one observed low, the hidden buyer stopped at
  4/20 purchases and the official delta was -5.2. A superficially matching
  5/20, -6.2 transcript was binary when joined to the wire log and is excluded;
  the dashboard does not display message mode. This is pre-treatment mechanism
  evidence, not a causal estimate.
- **Flag / assignment**: `GLEE_PERS_P08_R125_PROSE_AB=1`, default OFF.
  `int(sha256("pers_p08_r125_prose_v1|" + game_id).hexdigest(), 16) & 1` assigns the
  game. No game id fails closed. The bit is read only after `seller_plan`, so it
  cannot enter any recommendation decision or another arm.
- **Pre-treatment cohort**: every target game's globally first seller-message
  turn, before inspecting the outgoing message or any purchase. The untreated
  baseline begins at the rank-gate disarm boundary `1787570799`; it ends at the
  prospective clean common activation T0. The experimental cohort begins at T0
  and includes every assignment: purchases, refusals, zero payoffs, timeouts,
  invalid/abandoned games, unresolved outcomes, and any immediate terminal
  result. Result-fetch timestamps never define the cohort.
- **Control / candidate**: hash control remains byte-identical to the live
  `yes`/`no` stack. Candidate changes only positive text to one of the six
  combinations in the current non-leaking template bank, selected by a stable
  game-id/round RNG independent of private quality. No LLM. Binary persuasion,
  buyers, other priors/ratios, seller-blind cells, and all bargaining and
  negotiation actions are unreachable.
- **Hosts / boundary**: commit `2f4989d` naturally loaded as Test 1 PID 68351,
  Agent 5 PID 68203, and Test 4 PID 67641. Fleet tooling armed those three with
  `PERS_TOKEN_MAX_P=0`; clean common `T0=1787575521` (2026-08-24 18:15:21
  IST). Test 2 and Test 3 stay unarmed. The rest of each exact live stack,
  including LLM off, KEEP_MSG=1 and MSG_STYLE=token, was preserved.
- **Reachability contract**: after process load, 800 seeded persuasion games on
  each exact live stack reported Test 1 `eligible=320/fired=160/changed=160`,
  Test 4 `220/100/100`, and Agent 5 `160/60/60`. During the first 20 games per
  arm require a stable game bit on all 20 rounds, literal `yes` for every
  control message, only current-bank prose for every candidate message, no
  recommendation mismatch, no third wording, and no invalid/timeout. Any
  failure is an immediate disarm and mechanism rejection.
- **Primary / diagnostics**: join every resolved assignment to the official
  dashboard's per-game `rating_delta`; the local same-cell percentile is
  diagnostic only. Report purchase rate, zero rate, payoff/price and bought
  high/low counts without conditioning the primary analysis on purchases or
  recommendations. Exclude detected cross-fleet game ids and reject any
  self-play-contaminated read; hidden-opponent contamination remains explicit.
- **Sample and rules**: no outcome decision before 120 resolved official games
  per arm. At the observed three-host arrival rate this is about 3.2 days.
  Extend once to 200/arm only if the official CI crosses zero and competition
  time permits. Promote only if the official candidate-control 95% CI is wholly
  above zero, the purchase-rate point estimate is nonnegative with lower bound
  above -2pp, all three price-scale point estimates are nonnegative, and there
  are zero unresolved, invalid, duplicate/self-play, official-join, or wire
  failures. Reject immediately for any mechanism/scope failure; after at least
  50 official games/arm reject if the official-score CI is wholly below zero or
  the purchase-rate CI is wholly negative. Otherwise remain research-only.
- **Subgroups**: predeclared price scale `{100, 10_000, 1_000_000}`, named
  versus hidden opponent, host slot, and activation era. Exact-cell scale rows
  are diagnostic unless powered; no subgroup cherry-picking can override the
  pooled official rule.
- **Read with**: `scripts/live_percentile.py --ab pers-prose --since T0
  --until T1 --slots champion,composite,randomized --official-json FILE` where
  FILE contains dashboard-exported `slot`, `game_id`, `rating_delta` records.
- **First live observations (no decision)**: Test 1 candidate game
  `202cb810-c1a7-4d36-b98b-7d394842d258` fired on all 20 rounds with stable hash,
  unchanged recommendations, approved prose only, and no terminal failure. It
  closed 4/20 purchases (3 high, 1 low), payoff `4P`, official delta `-4.3`;
  the buyer passed all 16 rounds after the low purchase. This clean adverse
  observation does not alter the precommitted sample or stop boundary. Agent 5
  candidate game `36053a1f-16a3-4fb3-94cb-2d580cc1764d`, against named opponent
  `expert`, fired approved prose for all 20 rounds, sold 13/20 (7 high, 6 low),
  earned `13P`, and received official delta `-1.4`. Pooled candidate-only n=2
  is official mean `-2.85`, purchase rate `42.5%`, zero rate 0%, with no wire
  failure. No control has resolved, so neither the point nor its tiny-sample CI
  may trigger a decision. Complete dashboard transcripts are frozen in
  `.ai/PERSUASION_OFFICIAL.json`; the reader requires all 20 messages,
  qualities, decisions, exact setup, and seller-payoff identity before an
  authenticated transcript may recover a locally missing final.

### Exact zero-margin binary seller truthfulness (LIVE on Test 2)
- **Falsifiable hypothesis**: in persuasion seller/binary games with `p=.8`,
  seller-visible `v/u`, `v=1.25*price`, `u=0`, and 20 rounds, recommending only
  high-quality items raises mean official per-game rating delta versus the live
  all-`yes` control. A non-positive official intent-to-treat result falsifies
  the hypothesis. Purchase conversion or selected post-lie games cannot promote
  it.
- **Exact official cells**: seller role, binary protocol,
  seller-knows-consumer-values, p=.8, v=1.25P, u=0, 20 rounds, at each price
  scale `{100, 10_000, 1_000_000}`. Text mode is excluded, making this arm
  behaviorally disjoint from the running prose experiment.
- **Why this is not the rejected broad backload idea**: the published
  all-push advantage `+.391` was measured only in strict `p*r>1` cells. This
  experiment targets only the equality `p*r=1` branch, which never reached the
  live never-lie/shading path. A tiny recovered subset of the old backload arm
  favored its mostly truthful candidate (14.17 versus 5.29 purchases, n=6/7)
  in this exact cell, but result-time selection, missing official deltas, and
  the terminal push make that diagnostic non-causal.
- **Mechanism evidence, not an effect estimate**: 170 deduplicated completed
  all-yes exact-cell games averaged 7.29 purchases despite 16.04 high items;
  35/170 sold nothing. Of 123 games with a bought low, 42 buyers stopped
  completely and left a mean 12.38 later high opportunities. Official game
  `6516c6b7-2a47-4919-b192-cd0484e21daa` sold a round-1 high and round-2 low,
  then lost 14 later high opportunities and scored `-7.6`. The first text-prose
  candidate showed the same stop-after-low mechanism and scored `-4.3`, so
  stronger positive wording alone did not repair credibility in that draw.
- **Flag / assignment**: `GLEE_PERS_P08_R125_BINARY_TRUTH_AB=1`, default OFF.
  `int(sha256("pers_p08_r125_binary_truth_v1|" + game_id).hexdigest(), 16) & 1`
  assigns treatment. Missing game ids fail closed. Eligibility is fixed at the
  globally first seller recommendation and never conditions cohort membership
  on private quality, buyer response, purchase, payoff, or completion.
- **Control / candidate**: hash control returns the complete current plan and
  submitted `yes` action byte-identically. Candidate returns `yes` on high and
  `no` on low in every round. Candidate-high actions remain unchanged and only
  candidate-low turns append `p08_r125_binary_truth` to `gates_fired`. There is
  no adaptive trigger, terminal exception, prose, LLM, buyer change, or reach
  into any other seller cell.
- **Pre-treatment cohort**: Test 2 exact-cell games whose first seller turn is
  in `[1787570799, 1787582397)`, beginning at the rank-gate disarm. The
  experimental cohort begins at clean `T0=1787582397` (2026-08-24 20:09:57
  IST) and includes every assignment: purchases, refusals, zero outcomes,
  timeouts, invalid/abandoned, unresolved, and immediate terminal outcomes.
  Result-fetch time never defines the cohort.
- **Preflight**: Test 2's exact hardliner stack, 800 seeded persuasion games,
  seed 2417, reported `eligible=31`, `fired=21`, and `action_changed=21`.
  Focused mechanism/reader suite: 31 passed. The full allowed suite passed 1,167
  tests with only the same two pre-existing bargaining failures
  (`test_bargaining_horizon_floor` and `test_sim_grid[bargaining]`).
- **First-20 mechanism contract**: verify all 20 rounds of each of the first 20
  assigned games. The game bit must be stable; controls must emit `yes` every
  round; candidate action must equal private quality (`high -> yes`, `low ->
  no`); no third action, non-target fire, invalid action, timeout, or prose/rank/
  backload interaction is permitted. Any failure causes immediate disarm and
  mechanism rejection.
- **Primary / sample / rules**: authenticated dashboard per-game rating delta,
  full-game ITT, fixed final read at 40 resolved official games per arm and at
  least 8 per arm per price scale. One harm look at 20 official games per arm;
  reject if the official 95% CI is wholly negative. Promote only if the final
  official CI is wholly positive, purchase-count point delta is positive,
  zero-outcome point delta is nonpositive, all three scale point estimates are
  nonnegative, every deployed host point estimate is nonnegative, and mechanism,
  scope, wire, self-play/duplicate, unresolved, invalid, and official-join
  failures are zero. A final CI crossing zero remains research-only.
- **Subgroups**: price scale, named versus hidden opponent, host slot, and
  activation era. No subgroup can override the pooled official rule. Local
  percentile and post-lie continuation counts remain diagnostic only.
- **Deployment boundary**: Test 2 (`hardliner`) naturally drained PID 71871 and
  loaded pushed code `d79ca92` as PID 76676 at 20:08:48 IST. Fleet tooling set
  only `GLEE_PERS_P08_R125_BINARY_TRUTH_AB=1` at clean arms mtime
  `T0=1787582397`, without a restart or signal. The post-load exact-stack rerun
  reported `eligible=29/fired=14/action_changed=14`. Test 3 stays untouched;
  prose and buyer-parser flags are absent on Test 2; rank gate and backload are
  explicit zero. A real candidate low-quality `no` remains required before the
  live mechanism is behavior-verified.
- **Prospective research-host expansion (frozen before any truth assignment or
  outcome)**: the first 14 post-T0 minutes on Test 2 produced zero eligible
  games. To reach the unchanged fixed 40/arm official boundary without peeking
  at any treatment outcome, Agent 5 (`composite`) and Test 4 (`randomized`) may
  be armed after each naturally loads `d79ca92` or later. Their live prose arm
  is text-only, while truth is binary-only, so the eligibility sets are
  disjoint. Exact-stack preflight at seed 2431 reported
  `eligible=32/fired=18/action_changed=18` on each host over 800 games. Record a
  host-specific clean T0; pool all declared hosts by stable game hash, retain
  host/activation-era diagnostics, require every host point estimate
  nonnegative for promotion, and reject detected cross-fleet duplicates. Test 3
  remains untouched.
- **Research-host activation**: Agent 5 (`composite`) naturally loaded pushed
  code as PID 79006 at 20:42:18 IST and fleet tooling set only the truth flag at
  `T0=1787584351` (20:42:31). Test 4 (`randomized`) naturally loaded as PID
  79064 at 20:42:58 and was armed at `T0=1787584425` (20:43:45). At the 20:50
  read, all three host-specific readers reported zero exact assigned games.
  Therefore no observed rating movement is treatment evidence and the required
  first candidate low-quality `no` remains outstanding.
- **Operational era split**: an external whole-fleet supervisor restart at
  `1787584628` (20:47:08 IST) timed out 14 persuasion games across Test 2,
  Agent 5, and Test 4 for `-109.4` official rating in total. Host-specific truth
  readers and the prose reader show that none was an exact assigned experiment
  game, so they do not enter either arm. Preserve the original cohorts, record
  `1787584628` as a deployment-era subgroup boundary, and never attribute this
  rating discontinuity to persuasion behavior. The timeouts also caused a
  server-enforced crash-loop queue suspension on every slot until approximately
  `1787586428` (21:17 IST); no experiment exposure can accrue during that
  interval. The live processes retry in place every 60 seconds and must not be
  restarted again.
- **Read with**: run `scripts/live_percentile.py --ab pers-truth` separately for
  `hardliner --since 1787582397`, `composite --since 1787584351`, and
  `randomized --since 1787584425`, always with `--official-json FILE`. Do not
  pool from a common earlier timestamp: that would admit pre-activation games
  from the later research hosts.

### Exact buyer/text explicit-decline veto (built default OFF)
- **Falsifiable hypothesis**: in persuasion buyer/text games with `p=.8`,
  `v=1.25*price`, `u=0`, and 20 rounds, treating every
  expanded-parser explicit decline as a final pass raises mean authenticated
  official per-game rating delta versus the complete live buyer-v2 control.
  A non-positive all-assigned official result falsifies the hypothesis;
  decline-conditioned payoff or local percentile cannot promote it.
- **Why this is isolated**: `GLEE_PERS_PARSE_V2` only expands phrases, while
  `GLEE_PERS_PARSE_TRI` changes abstentions and posterior updates broadly; TRI
  alone still reads `Not recommended.` as abstention when V2 is absent.  This
  arm uses the expanded decline table only for its final candidate veto and
  changes neither current nor historical parsing anywhere else.  It leaves all
  positive-message and pre-decline purchases intact, so it does not retry the
  rejected buyer-selectivity/strike/LCB arms.
- **Mechanism evidence, not effect evidence**: among 395 deduplicated completed
  exact games across both official seller-knowledge configurations, 196
  contained an expanded-parser decline and 199 did not.  The live buyer
  purchased such declines in 22 games / 44 turns; all 44 revealed low.
  Frozen-stream savings averaged `.1114P` and the within-configuration local
  diagnostic percentile changed `+.0172` over all 395.  In the known-CV cell
  alone the corresponding figures were `.1456P` and `+.0228` (bootstrap 95%
  interval `[+.0109,+.0374]`).  Passed-item quality is unobserved and seller adaptation
  invalidates that counterfactual.  Authenticated game `f2bed4f4-b9f2-47d3-
  b397-7dc41c919673` bought three `Not recommended.` lows, finished at zero,
  and scored `-4.0`; its fixed sequence would save `3P`, but is not causal.
- **Flag / assignment**:
  `GLEE_PERS_P08_R125_TEXT_DECLINE_VETO_AB=1`, default OFF;
  `int(sha256("pers_p08_r125_text_decline_veto_v1|" + game_id).hexdigest(),
  16) & 1` assigns the game.  Missing ids fail closed.  Eligibility is fixed at
  the globally first buyer decision from structural buyer seat, text mode,
  exact numeric cell, and horizon only—never message, decline, purchase,
  payoff, or completion.
- **Two official configuration cells**: the production-observable gate is the
  union of `is_seller_know_cv=true` and `is_seller_know_cv=false`.  The
  documented active state withholds that configuration flag (and the simulator
  enforces the omission), so conditioning assignment on it would be an
  unreachable hidden-state policy.  Official rating deltas are already scored
  within their own configuration.  The reader reports both final/config labels
  separately and never infers a missing label from messages, purchases, or
  outcomes; unavailable labels block promotion.
- **Control / candidate**: hash control returns the entire flag-off buyer plan
  and action byte-identically, without arm metadata.  Candidate first computes
  that same complete plan, including optional rank-buy, then final-overlays
  `yes -> no` only when the current message is an expanded-parser explicit
  decline.  Positive messages, abstentions, already-refused actions, history,
  posterior, sellers, binary mode, other cells, bargaining, and negotiation are
  unreachable.  Only a real changed action appends
  `p08_r125_text_decline_veto` to `gates_fired`.
- **Pre-treatment / ITT cohort**: Test 2 first exact buyer turns in
  `[1787570799, prospective T0)`, beginning at rank-gate disarm.  The
  experimental cohort begins at a clean future T0 and includes every assigned
  game: no-decline paths, purchases, refusals, zero and negative outcomes,
  timeouts, invalid/abandoned, unresolved, and immediate terminal outcomes.
  First-turn time, never result-fetch time, defines membership.
- **Preflight and live mechanism contract**: on Test 2's exact stack require
  `eligible>0`, `fired>0`, and `action_changed>0`.  Audit all rounds of the
  first 20 assignments for a stable bit, byte-identical controls, no change on
  positive/abstaining messages, and candidate pass on every target decline.
  Any control difference, non-target fire, candidate decline purchase, hash
  drift, invalid wire, or trace/action mismatch is immediate mechanism
  rejection.  Activation is not behavior-verified until a real changed-action
  trace appears; no trace by 50 exact assignments is a reach failure.
- **Primary / sample / rules**: authenticated dashboard per-game rating delta,
  full-game ITT.  One harm look at 50 resolved official games per arm rejects
  if the official 95% CI is wholly negative.  Fixed final read at 120/arm and
  at least 20/arm per price scale.  Promote only if the official CI is wholly
  positive, normalized-payoff point delta is positive, zero- and negative-
  outcome point deltas are nonpositive, all scale and both seller-knowledge-
  cell points are nonnegative, and
  mechanism, scope, wire, duplicate/self-play, unresolved, invalid, and
  official-join failures are zero.  A final CI crossing zero stays research-
  only.
- **Subgroups / boundary**: seller-knowledge configuration (when present in
  final/config evidence), price scale, named versus hidden opponent, legacy-
  recognized versus V2-only decline phrase, and first-decline round are
  diagnostic only.  Build/push inert code now; arm Test 2 only after the binary
  truth decision/disarm at a clean timestamp, with prose/parser/selectivity
  absent and rank/backload explicit zero.  Test 3 remains untouched.  Exclude
  observed cross-fleet duplicates; hidden self-play risk blocks promotion.
- **Read with**: `scripts/live_percentile.py --ab pers-decline-veto --since T0
  --slots hardliner --official-json FILE`.

## MECHANISM REJECTED — DISARMED

### Continuation-aware persuasion rank gate (Test 2)
- **Live window**: first observed fire `1787484376.458`; explicitly disarmed
  through `scripts/fleet.py` at `T1=1787570799` by setting
  `GLEE_PERS_RANK_GATE_AB=0`. Clearing the key was not a safe disarm because a
  launch environment could retain it. Test 3 was untouched.
- **Failure**: the arm reached all 12 tight buyer cells rather than the claimed
  eight, including every p=.8 treatment game; it could flip both directions,
  applied a recommendation-only DP to explicit declines, and pooled six
  official configurations per local CDF key. Live census: 267 treatment games,
  828 turn flips; 539 were unintended p=.8 buy-to-pass changes. One verified
  threshold-zero flip bought a low unit after “I do not recommend this one” and
  lost the full 1,000,000 unit price.
- **Decision**: mechanism rejection, not an effect estimate. Only 83/495 first-
  round eligible games have local finals and 412 remain unresolved. Do not use
  resolved-only local percentile or Test 2's aggregate rating to promote or
  salvage this arm.

## RUNNING — LIVE CAUSAL MEASUREMENT

### Hidden support-minimum share veto (negotiation, Test 3)
- **Flag / assignment**: `GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB=1` on Test 3 only;
  `sha256("nego_hidden_min_share_veto_v1|" + game_id) & 1` gives control or
  candidate per game.
- **Eligible decision**: hidden, nonfinal, profitable offers below 40% of the
  minimum positive feasible ZOPA implied by our own type, and only when the
  frozen table/stall/continuation stack would otherwise accept. Control accepts
  byte-for-byte. Candidate rejects and uses the existing profitable-side
  counter. The terminal any-positive-cent rule is outside scope.
- **Deployment state / causal boundary**: pushed inert mechanism commit
  `6f7e79b`; Test 3 process naturally rotated onto it at 2026-08-24 19:22:14 IST
  (PID 73157). The first qualifying pre-action assignment is therefore the clean
  `T0=1787581117.643784` (2026-08-24 19:48:37 IST), not process start or overlay
  mtime. Game `99c476fc-5bce-44b0-af07-57382aec6160` was hash control, hidden
  cap-10 seller-.8, round 6: buyer offered `.85666667B`, paying `.05666667B`
  against the `.08B` support floor; direct TABLE accepted. The production/reader
  parity audit reports `mechanism_ok=true`.
- **Primary cohort / outcome**: every game from its first qualifying pre-action
  decision, with all agreements, zeros, walks, timeouts, invalid and unresolved
  outcomes retained. Primary outcome is authenticated-dashboard per-game rating
  delta joined by exact modal fingerprint and minute; local pooled percentiles
  are diagnostic only.
- **Decision rule**: final read at 100 resolved official games per arm and at
  least 20 per role per arm. Promote only if official-delta 95% CI is above zero,
  close-rate point delta is at least -5pp, both role point estimates are
  nonnegative, and mechanism/join failures are zero. One harm look at 30 official
  games per arm rejects if the official CI is wholly negative.
- **Read with**: `scripts/live_percentile.py --ab hidden-min-share-veto --since
  T0 --slots conceder --official-json FILE`.

## BUILT — DEFAULT OFF, WAITING FOR AN UNCONTAMINATED WINDOW

### Trend-confirmed TABLE versus continuation precedence (negotiation)
- **Flag / assignment**: `GLEE_NEGO_TABLE_VCONT_PRECEDENCE_AB=1`, default OFF;
  `sha256("nego_table_vcont_precedence_v1|" + game_id) & 1` gives direct-TABLE
  control or continuation candidate per game.
- **Identified trigger**: a hidden, profitable, nonfinal offer directly clears
  TABLE; at least three distinct echo-collapsed opponent prices show a positive
  concession trend; the existing continuation value exceeds accept-now surplus;
  the support-minimum signal is absent; and the next stall branch would not
  accept anyway. No-trend extrapolations from our own unplayed target are
  excluded.
- **Candidate**: suppress only TABLE's early return, then use the existing
  continuation rejection and existing profitable-side counter. Control remains
  byte-identical. The arm freezes HORIZON_V2, CONTINUATION_ACCEPT, TABLE,
  STALL_POLICY, and FINAL_OPTION=0.60, and fails closed against every overlapping
  negotiation experiment, including the running Test 3 arm.
- **Reachability / evidence**: latest 100,000 Test 3 turns contained 76 first-
  eligible games (about 25.5 per 1,000 negotiation games). Test 3's future
  control stack with the running veto explicitly absent produced 47 eligible,
  19 fired, and 19 changed actions over 1,500 paired games (seed 2411). Focused
  and all negotiation tests passed (79 and 363 respectively). The prospective
  official reader is now implemented as `--ab table-vcont-precedence`; it
  independently recomputes the trigger from state/plan, verifies direct-TABLE
  control and exact candidate counter wires, retains unresolved and every
  terminal outcome, rejects cross-fleet duplicates, and enforces the frozen
  official/close/stratum decision rule. Combined precedence/veto focused suite:
  83 passed.
- **Precommitted future rule**: do not co-arm with the support-minimum trial.
  After a clean window, final read at 100 resolved official games per arm and
  20 per role; one harm look at 30/arm. Promotion requires official-delta CI
  above zero, close-rate lower bound above -2pp, nonnegative role/horizon/type
  point estimates, and zero mechanism/join failures. Completed historical deals
  do not identify whether rejecting the guaranteed offer is beneficial.
