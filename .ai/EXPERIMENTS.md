# EXPERIMENTS — hypothesis, design, verdict

## RUNNING

### Surplus-share response probe (negotiation, complete-info)
- **Hypothesis**: our complete-info closes sit at the 49.4% attractor; the
  causal frontier P(accept | surplus share x) may peak above it.
- **Design**: randomise x over {0.50,0.55,0.60,0.65,0.70,0.75} in complete-info
  offer turns, seeded on game id, stratified by seat/round-block/cap.
- **Live on**: Agent 5, Test 3 (`GLEE_NEGO_SURPLUS_PROBE=1`).
- **Read with**: `scripts/analyze_surplus_probe.py`
- **Decision rule**: pick the x maximising P(accept)*x plus continuation, NOT
  the highest observed rating-by-band (that conditions on deals happening).
- **Verdict**: pending (~50-100 obs/arm needed).

### Seller-message parser v2 (persuasion)
- **Hypothesis**: the decline table missed "not recommended" and friends, so we
  bought messages that explicitly declined. 373 such purchases in 20h of logs,
  373 low quality, 0 high.
- **Live on**: Test 2 only (`GLEE_PERS_PARSE_V2=1`); other three are controls.
- **Verdict**: pending trail.

## REJECTED — DEFAULT OFF, DO NOT RUN

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
