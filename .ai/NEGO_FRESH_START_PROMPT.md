# Prompt: design a GLEE negotiation strategy from scratch

Copy everything below the line into a fresh chat.

---

I want you to design a negotiation strategy for the GLEE competition from first
principles. Assume nothing from any previous attempt. I will tell you what the
game is, how it is scored, what we have measured about the field, and the
mistakes we have made repeatedly — I want you to avoid those specifically.

## The game

A seller and a buyer negotiate the price of one product. Each has a private
valuation.

- **Player 1 is always the seller** (their value is their minimum acceptable price).
- **Player 2 is always the buyer** (their value is their maximum acceptable price).
- Players alternate price offers. On your turn you may **accept**, **reject with
  a counteroffer**, or **walk away**.
- **Seller payoff = price − seller value. Buyer payoff = buyer value − price.**
- No deal means **both sides get $0**.
- When the seller values the item above the buyer, no trade is the correct
  outcome and $0 is the right answer.

Move formats:

```json
{"product_price": 75, "message": "Best price"}       // offer
{"decision": "AcceptOffer"}
{"decision": "RejectOffer", "product_price": 60, "message": "Too high"}
{"decision": "RejectOffer"}    // final round only: no counteroffer exists, ends the game
{"decision": "WalkAway"}
```

Configurations vary along four axes, and they matter enormously:

- **Horizon**: single-round take-it-or-leave-it, a stated round cap, or no limit.
- **Information**: complete (both valuations visible) or hidden (only your own).
- **Messages**: allowed or not.
- **Role**: seller or buyer.

`game_state` gives you `phase`, `current_player`, `player_1_role`/`player_2_role`,
your own `{player}_value`, `max_rounds`, `horizon_known`, `complete_information`,
`messages_allowed`, `last_offer`, and `history` — every past round's offers,
messages, decisions and payoffs. In half of games `opponent` discloses
`{"type": "agent"|"human", "name": ...}`; otherwise it is hidden.

## How scoring actually works — this is the crux

**You are not maximising money. You are maximising rank.**

- After each game your payoff becomes a **percentile against every payoff earned
  on the same configuration in the same role**.
- That percentile is **adjusted for opponent strength** — beating a weak opponent
  by an ordinary margin is ordinary; matching a strong one is good.
- `game_rating = 2000 + 8000 * (percentile − 0.5)`. An average game is 2000.
- Your rating moves toward it slowly: `delta_R = eta * (game_rating − R)`, with
  eta 1% for new players decaying to 0.2% by ~120 games.
- The leaderboard shrinks your rating toward 1000 by `g / (g + 30)`, so volume
  and strength are both required.
- **An account is ranked once, by its best agent.** Improving your 2nd–5th agents
  earns no leaderboard position.
- **Abandoning a game scores it at the 5th percentile.** Never time out.

Consequences you should reason about explicitly:

1. A payoff distribution with a large **atom at $0** (everyone who fails to deal)
   means refusing collects the *middle* of that atom, while gambling lands on one
   side or the other. Sometimes the safe play is rank-optimal even when its money
   EV is worse, and sometimes the reverse. Derive which, per cell.
2. Money-optimal and rank-optimal thresholds are **different numbers**. Work out
   the rank-indifference threshold from the cell's payoff CDF, not from EV.
3. Because scoring is per-configuration, a policy that is excellent on average
   and terrible in one cell is worse than a policy that is uniformly decent.

## What we have measured about the field

- The field **accepts any terminal offer leaving it a positive cent (959/959)**
  and **rejects every offer leaving it nothing (206/206)**. Terminal-node
  behaviour is essentially deterministic.
- **Top opponents open at ~1.00 of the visible zone and settle at 0.64–0.77 of
  it, while closing MORE often than the field.** So "take less to close more" is
  not their mechanism — they do both at once. Explain how before copying it.
- Our own realised share of the zone on complete-information closes has a median
  of exactly **0.500** with p75 **0.610** — a hard shoulder, because two of our
  constants fence us in.
- Roughly **12% of games are unwinnable by construction** (no zone of agreement);
  the correct play there is $0 and every competent agent also gets $0.
- In hidden-information games the opponent's value is **reconstructible on any
  closed game**: `buyer_value = buyer_payoff + price`,
  `seller_cost = price − seller_payoff`. Use this to build a field model.

## Mistakes we have made repeatedly — do not repeat these

**On method:**

1. **We analysed only our own logs.** Our data contains only our own policy, so
   every "no improvement exists" conclusion actually meant "no improvement exists
   inside the region we already occupy." Agents rated 500 points above us prove
   the ceiling is reachable. If your analysis says the ceiling is structural,
   check whether someone is already above it.
2. **We scored ourselves against a percentile model built ~half from our own
   play.** "Below par" partly meant "below our own average." Fit any field model
   from **opponent payoffs only**.
3. **We ran between-agent A/B tests.** Rotation phase, opponent pool and hour of
   day confounded three of five findings; placebo-treating an untouched agent
   with the same time cut produced effects of −0.12. **Randomise within a single
   agent** by hashing the game id, so both arms face the same opponents in the
   same hour.
4. **We trusted small samples.** One effect measured +0.138 at n=48 and +0.0155
   at n=154. Byte-identical agents differ by **0.048 percentile at n≈300** — that
   is the noise floor, and anything smaller is unmeasurable on one agent.
5. **We confused correlation with causation in an adaptive policy.** "We conceded
   more and scored better" was reverse causation: we conceded more *because* the
   game was going well. Score fixed, non-adaptive policies against recorded
   outcomes to break this.
6. **We selected on the outcome.** Games that run 21+ rounds do so *because* they
   are not closing; comparing them to short games measures difficulty, not policy.

**On design:**

7. **We overloaded parameters.** One constant was simultaneously the ceiling on
   our ask and the floor on our reservation — so no value could open high and
   hold high. Another was simultaneously the offer floor and the acceptance veto,
   so the good value for one vetoed 98% of our accepts. **One parameter, one
   decision.**
8. **We tested one knob at a time when two were needed.** Raising our opening ask
   alone: inert. Lowering our concession floor alone: inert. **Both together:
   +0.154 percentile.** If a mechanism needs two changes, a single-flag A/B will
   report nothing for both.
9. **We layered gates that overwrite each other.** A stall detector fired on 73%
   of turns and a span veto on 92%, both rewriting the price *after* the
   concession schedule computed it — so the schedule we spent days tuning owned
   about 3% of our actual prices. **Know which component owns the output.**
10. **We built a rule that stops rather than slows.** A clamp meant to prevent
    late-game capitulation froze our price completely, so we repeated the
    identical offer a median of 38 times and 94.6% of those games died at $0.
    Guards should bound behaviour asymptotically, not halt it.

**On operations:**

11. **A flag being set is not a flag firing.** We deployed an arm, saw it in the
    config, and only discovered an hour later it was changing nothing. Always
    verify the *behaviour* changed.
12. **Code changes need a process restart; flag changes do not.** The interpreter
    imports your module at startup, so a newly written function is not in memory
    until the process cycles.

## What I want from you

1. A negotiation policy designed from first principles for a **rank** objective,
   not a money objective, covering every combination of role × information ×
   horizon.
2. Explicit reasoning about the **terminal node** (where field behaviour is
   deterministic and therefore exploitable) and about **which component owns the
   final price** in your design.
3. A parameterisation where **each parameter controls exactly one decision**, with
   the reasoning for each stated.
4. A concrete plan to **validate it against the field rather than against
   ourselves**, including what would falsify it.
5. Honest identification of the cells where **no policy can help**, so effort is
   not spent there.

Ask me for any data you need — I have roughly 17,000 logged negotiation games
with full round-by-round histories for both sides.
