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

## NEXT (not built)
1. General accept/counter/walk response model (item 5 of the operator plan).
2. State-dependent price discrimination / shallow DP over the frontier.
3. Full-sequence opponent-type inference.
4. Partially pooled per-opponent profiles.
5. Message framing arms (orthogonal; only 7.1% of offers carry text).
