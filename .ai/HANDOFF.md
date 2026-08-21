# HANDOFF — Claude ↔ Codex

Append-only. Newest at the top. Each entry: what changed, what was measured,
what is contested.

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
