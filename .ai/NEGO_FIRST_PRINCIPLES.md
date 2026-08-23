# Negotiation, designed from the game's structure

Built from the 17,361 logged negotiation games, ignoring every prior strategy
conclusion. Where this contradicts the brief in `NEGO_FRESH_START_PROMPT.md`,
the contradiction is stated and evidenced.

---

## 0. Four claims in the brief that the data does not support

**"Roughly 12% of games are unwinnable by construction."**
Wrong in both directions, because the two information conditions use *different
generators*.

| | seller value drawn from | buyer value drawn from | P(zone exists) |
|---|---|---|---|
| complete info | {80,100,120} | {100,120,150} | **100%** |
| hidden info | {80,100,120,150} iid uniform | {80,100,120,150} iid uniform | **37.5%** |

Complete info: 0 of 4,771 games had seller value ≥ buyer value. Hidden info: our
own value is uniform over all four grid points (25.2/25.1/24.1/25.5 as seller),
which is only possible if draws are independent — so P(v₁<v₂) = 6/16. Confirmed
against outcomes: agreement rate tracks the structural P(zone) at 76–95%
efficiency, and in the two impossible cells (seller@150, buyer@80) agreement is
1.68% and 0.58%.

So ~45% of all games are dead by construction, not 12% — and **you can tell
which ones from your own value alone, before making a single offer.**

**"The field accepts any terminal offer leaving a positive cent (959/959)."**
True, but only under complete information at a genuine terminal node. Our
measurement: 892/892 accepted at any positive share (including 25/25 below a 5%
share), 159/159 rejected at non-positive. Under hidden information the law is
weaker in one direction and *breaks* in the other — 145 games closed at a price
giving one side a **negative** payoff (102 buyers, 46 sellers). Zero such cases
in complete information.

**"Fit any field model from opponent payoffs only."**
Insufficient for anything inside the zone. Realised shares sum to 1.0000 by
construction, so the opponents' share *is* our own policy mirrored. Fitting to it
re-reads our own behaviour with the sign flipped. The non-circular object is the
opponent's **response to a price we chose**: we own the stimulus, they own the
response.

**"Our median share is exactly 0.500 with a hard shoulder at 0.610."**
An artifact of pooling six cells with opposite structure. Per cell our medians
run 0.15 to 0.80. There is no shoulder; there are six different games.

---

## 1. The structure

**Value grid.** Values are always `base × scale`, `base ∈ {80,100,120,150}`,
`scale ∈ {1,100,10⁴}`, both sides on the same scale. Twelve distinct values, ever.

**Turn order is exceptionless.** Odd rounds → player_1 (seller), even rounds →
player_2 (buyer). 229,848 offers, no violations.

**Therefore the terminal offer is owned by:**

| horizon | last round | owner | who is a dictator |
|---|---|---|---|
| single (max_rounds=1) | 1 | player_1 | **seller** |
| cap-10 | 10 | player_2 | **buyer** |
| "unknown" | **99** (hard cap, undisclosed) | player_1 | **seller** |

The horizon is never actually unlimited: 1,225 games reached round 99 and every
one of them had player_1 making that final offer.

---

## 2. The rank calculus — why this is not a negotiation problem

Percentile against the field payoff distribution in `single/HI/nomsg`, seller:

| your payoff | percentile |
|---|---|
| $0 | 0.370 |
| **$0.01** | **0.739** |
| $20 | 0.804 |
| $70 (the entire zone) | 0.830 |

**One cent of closing buys +0.369. Everything else you could ever win buys +0.09.**

That is the whole strategic content of the hidden-information cells, and it is a
direct consequence of the 62.5% structural no-zone rate creating a 70% atom at
exactly zero. Money-optimal and rank-optimal prices genuinely diverge:

| your cost | money-optimal ask | rank-optimal ask | rank gain |
|---|---|---|---|
| 80 | 120 (EV $20.0) | **100** (EV $15.0) | **+0.103** |
| 100 | 150 (EV $12.5) | **120** (EV $10.0) | **+0.105** |

Verified identical at all three value scales, so **the policy never conditions on
scale.**

---

## 3. The policy

### 3.1 Complete information — take the terminal node

The opponent's acceptance at a terminal node is deterministic (892/892 / 0/159).
So whoever offers last takes the entire zone.

- **single / seller** → price = `buyer_value − ε`. Closes with certainty.
  Currently we realise share 0.617 and fail outright in 11% of these games by
  asking *above* the buyer's value.
- **cap-10 / buyer** → reject rounds 1–9; at round 10 bid `seller_cost + ε`.
- **cap-10 / seller, single / buyer** → you do not own the terminal node. You are
  structurally short. Close early at the best share the opponent will take; only
  18% of the field actually exploits its round-10 dictatorship (mean claim 0.663),
  so early closes are worth more than the theory says.

**The hold-out is not what failed before.** Our `hardliner` held to round 10 in
83% of cap-10 buyer games and its close rate collapsed to 61.4% — which reads as
a refutation. It isn't. Of its round-10 bids, 46.4% were priced *below the
seller's cost*, and those were rejected 0/71. The 82 feasible ones were accepted
**82/82**. The strategy was sound and the price was computed by the wrong
component.

### 3.2 Hidden information — price to close

Responders are clean threshold acceptors. Observed acceptance vs the rational
benchmark, single-round, n=2,107:

| ask | observed P(accept) | P(buyer value > ask) |
|---|---|---|
| [80,100) | 0.774 | 0.75 |
| [100,120) | 0.460 | 0.50 |
| [120,150) | 0.266 | 0.25 |
| [150,∞) | 0.000 | 0.00 |

So P(accept) is fully determined by the grid, and the rule is:

> **ask the lowest grid point strictly above your own value, minus ε.**

Not a concession schedule. Not a share of an estimated zone. One grid point.

**Multi-round hidden info:** the opponent's most extreme offer bounds their value
— field sellers never ask below cost (96.9%), buyers never bid above value
(94.3%), with median slack of about one grid step. Two offers usually identify
their value exactly on a four-point grid.

**Provably dead cells:** if you are a hidden-info seller at 150, or a buyer at 80,
P(zone) = 0 exactly. 25% of hidden games. Both outcomes pay $0, so **never walk
away** — grinding keeps alive the ~1.7% chance the opponent accepts a losing
deal, and in a cell where 70% of the field is pinned at zero, that pays +0.35
percentile when it lands.

### 3.3 Horizon-unknown

Seller owns round 99. **Untested** — our stubbornest agent does not currently
grind there and ranks near the bottom of our fleet in that cell (E[share] 0.424
vs 0.467 for the conceder). Do not deploy the grind on theory alone; it is the
first thing to test, not the first thing to ship.

---

## 4. Parameterisation — one parameter, one decision

The design is nearly parameter-free, which is the point. Four constants:

| parameter | owns exactly one decision | value | why |
|---|---|---|---|
| `EPS` | the crumb left to the opponent at a terminal node | 0.01 | acceptance is deterministic above 0; nothing is gained by leaving more |
| `HOLD_ACCEPT` | take an early offer instead of waiting for our terminal turn | 0.994 | = 1 − measured 0.57% walk-away risk |
| `NEVER_WALK` | the walk-away decision | always false | walking and grinding both pay $0; grinding retains the 1.7% |
| `PRE_ASK` | prices strictly before the terminal round | grid point above own value | never allowed to touch the terminal price |

**Ownership rule:** the terminal price is computed in exactly one place, from the
opponent's value, and no schedule, stall detector, or span veto may rewrite it.
That is the specific failure that cost `hardliner` 46% of its round-10 games.

---

## 5. What it is worth

Per-cell mean percentile, current vs designed, evaluated against the field
distribution (opponent payoffs, same cell and role):

| cell | role | n | now | designed | gain |
|---|---|---|---|---|---|
| single/CI/msg | seller | 380 | 0.478 | 0.621 | **+0.143** |
| single/CI/nomsg | seller | 372 | 0.491 | 0.630 | **+0.138** |
| cap10/CI/nomsg | buyer | 398 | 0.501 | 0.641 | **+0.140** |
| cap10/CI/msg | buyer | 399 | 0.515 | 0.638 | **+0.123** |
| single/HI/msg | seller | 1073 | 0.512 | 0.581 | **+0.069** |
| single/HI/nomsg | seller | 1034 | 0.507 | 0.565 | **+0.059** |

Weighted over all 17,249 completed games: **+0.020 percentile ≈ +160 rating.**
Six of 24 cells are designed; the other 18 are held at current behaviour, so this
is a floor, not a ceiling. Per-cell effects of 0.06–0.14 at n≈400 sit far above
the stated 0.048 noise floor.

---

## 6. Validation — and what would falsify it

The design rests on **deterministic laws, not effect sizes**, so it is falsifiable
in tens of games rather than hundreds. Test the laws directly:

1. **Terminal-acceptance law.** Every feasible terminal offer is accepted.
   Prediction: 100%, no exceptions. *One* rejected feasible terminal offer breaks
   it. Current evidence 892/892 and 82/82.
2. **Turn parity.** Odd → player_1. One counterexample breaks every dictator play.
3. **Hidden-info uniformity.** Our own value should stay uniform over four points
   in hidden games and stay confined to three in complete-info games. Re-check
   weekly; if the generator changes, P(zone)=37.5% changes with it.
4. **Grid membership.** Every value is `base × scale`. An off-grid value means
   the generator moved.

Only then measure percentile, and measure it **within one agent**: hash `game_id`
to assign arm, so both arms meet the same opponents in the same hour. Never
between agents.

**Pre-registered:** `single/CI/seller` should move ≥ +0.10 at n=400. If the
deterministic laws hold and the percentile does not move, the fault is in the
percentile model, not the policy.

**Honest limits.** The field payoff distribution is measured from opponents who
played *us*, so it inherits our selection. It is sound for locating the zero atom
(62.5% of which is structural and policy-independent) and unsound for anything
requiring the field's behaviour against itself.
