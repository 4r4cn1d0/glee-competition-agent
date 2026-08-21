# FINDINGS — validated empirical facts only

Each line is something measured, with its sample. Hypotheses do NOT belong here;
they go in EXPERIMENTS.md until they have evidence.

## Structure of the games
- Negotiation config mix (810 games, Test 1, 21 Aug): hidden 76% / complete 24%;
  seat 50/50; horizon 35% one-round, 31% ten-round, 33% uncapped; messages 50%.
- **48% of that sample had V_s >= V_b** (trade impossible). Sample-specific —
  do not treat as a structural constant.
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
