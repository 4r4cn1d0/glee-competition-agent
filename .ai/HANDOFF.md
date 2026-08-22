# HANDOFF — Claude ↔ Codex

Append-only. Newest at the top. Each entry: what changed, what was measured,
what is contested.

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
