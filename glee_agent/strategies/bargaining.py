"""Bargaining (divide the dollar) — alternating offers under inflation.

The spine is the exact alternating-offers solution. With per-round discount
multipliers d_me/d_opp, the share the round's proposer can secure satisfies

    f(k) = 1 - d_responder * f(k-1),      f(1) = 1

where k counts rounds remaining including this one (in the final round a
rejection pays both sides $0, so the last proposer takes everything). Let the
horizon run and this converges to Rubinstein's

    f = (1 - d_opp) / (1 - d_me * d_opp).

No game here is uncapped, so the recursion — not the limit — is the right
object. Disclosed games state max_rounds = 12; undisclosed ones hide a cap of
99 (live game 4ff134c5 ran to round 99 and terminated `no_deal` /
`round_cap_reached`, and across 5,127 live bargaining turns `max_rounds` is
present exactly when `horizon_known` is true, no exceptions). Modelling the
undisclosed cap as infinite threw away parity, the last word and the endgame
rules in the 48% of bargaining games that carry it, so the cap is counted
explicitly — see ``Config.barg_undisclosed_horizon``.

Playing the equilibrium share outright is optimal against a rational opponent
and risky against a field of LLMs anchored on 50/50 — a no-deal pays $0, which
lands at the bottom of the percentile scale. So the aspiration sits a
configurable fraction of the way from an even split toward the subgame-perfect
share, and the acceptance threshold decays to "take anything positive" at the
deadline.

The equilibrium is not enough on its own, because it has a degenerate corner.
At d_opp = 1.0 the opponent loses nothing by waiting: the share we can secure
is exactly 0 whenever they hold the last word, so the solver proposed itself
17.5% of the pot (0% at full SPE weight — four live games were agreed at
exactly $0) and its acceptance threshold fell to zero, clearing any offer at
all. The equilibrium is telling the truth and the field does not play it: in
that cell we realised 39.3% of the pot against 52.8% everywhere else (n=58 vs
155, difference -13.5% of pot [-21.1,-5.8]). So the equilibrium is floored by
what the field measurably accepts — see ``Config.barg_offer_floor``.
"""

from __future__ import annotations

from .. import runtime_flags

import math

from ..actions import _num

# Rubinstein converges geometrically; past this many rounds the finite and
# infinite horizon answers are identical to well beyond float precision.
_INFINITE_HORIZON_CUTOFF = 200


def proposer_share(delta_me: float, delta_opp: float, rounds_left: int | None) -> float:
    """Fraction of the pot the player proposing *now* secures in equilibrium."""
    delta_me = min(max(delta_me, 0.0), 1.0)
    delta_opp = min(max(delta_opp, 0.0), 1.0)

    if rounds_left is not None and rounds_left <= 0:
        return 0.0                         # no round left to propose in

    if rounds_left is None or rounds_left > _INFINITE_HORIZON_CUTOFF:
        product = delta_me * delta_opp
        if product >= 1.0:                 # no inflation either side: indeterminate
            return 0.5
        return (1.0 - delta_opp) / (1.0 - product)

    share = 1.0                            # the final round's proposer takes all
    for k in range(1, int(rounds_left)):
        # The responder at level k+1 is the proposer at level k; the turns
        # alternate, so parity against `rounds_left` says whose discount applies.
        responder_is_me = (rounds_left - k) % 2 == 0
        share = 1.0 - (delta_me if responder_is_me else delta_opp) * share
    return min(max(share, 0.0), 1.0)


def _offers_to_me(state: dict, me: str) -> list[tuple[int, float]]:
    """Every gain the opponent has proposed for me, oldest first.

    Their offers are the only hard evidence of what they will actually concede,
    which is what makes the equilibrium continuation value realisable or not.
    """
    seen: list[tuple[int, float]] = []
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        offer = entry.get("offer") or {}
        if not isinstance(offer, dict):
            continue
        proposer = offer.get("proposer") or entry.get("proposer")
        if proposer == me:
            continue                       # our own offer, not evidence
        gain = offer.get(f"{me}_gain")
        if gain is not None:
            seen.append((int(_num(entry.get("round"), 0)), _num(gain)))
    last = state.get("last_offer") or {}
    if last.get("proposer") and last["proposer"] != me and last.get(f"{me}_gain") is not None:
        entry = (int(_num(last.get("round"), 0)), _num(last[f"{me}_gain"]))
        if entry not in seen:
            seen.append(entry)
    seen.sort()
    return seen


def realistic_continuation(
    state: dict, me: str, delta_me: float, spe_continuation: float,
    rounds_left: int | None, field_ceiling: float | None = None,
) -> tuple[float, dict]:
    """What continuing is *actually* worth, given how this opponent behaves.

    The subgame-perfect continuation value assumes the opponent concedes to
    equilibrium. Against one who does not, holding out for it yields nothing:
    a live game deadlocked for 99 rounds against a static offer and both sides
    scored zero. So the equilibrium value is treated as a CEILING and the
    opponent's own concession trend supplies the estimate.

    `field_ceiling` replaces that ceiling in the one corner where the model
    returns no usable number. Rubinstein's closed form assumes at least one
    discount factor strictly below 1. At d_opp = 1.0 the equilibrium share is
    exactly 0 whenever the opponent holds the last word and delta_me**((k-1)/2)
    when we do — 0.000 / 0.006 / 0.081 / 1.000 at k = 99 rounds for the four
    grid values of delta_me. That is a knife edge on parity spanning the whole
    interval, and both ends are wrong in practice: a ceiling of 0 turns the
    acceptance test into "accept anything, $0 included", and a ceiling of 1
    turns it into "reject everything short of the pot for 97 more rounds". The
    field, measured, opens at 41.2% of the pot [33.1,49.3] in exactly this cell
    (n=47 of its own offers to us), so callers pass the measured level there
    and nothing anywhere else.

    Deliberately not applied where the theory is well posed. Over the randomized
    probe's 89 live rejections — the only ones in the corpus whose threshold was
    drawn exogenously — rejecting an offer worth 0.35-0.45 of the pot returned
    0.248 [0.179,0.317] and rejecting 0.45-0.55 returned 0.400 [0.276,0.524].
    Both are worse than accepting, so a blanket lift of the acceptance threshold
    is not supported by the data.

    Returns (value, diagnostics).
    """
    offers = _offers_to_me(state, me)
    ceiling = spe_continuation if field_ceiling is None else field_ceiling
    info: dict = {"offers_seen": len(offers)}
    if field_ceiling is not None:
        info["ceiling"] = "measured field level (equilibrium ceiling degenerate)"
    if len(offers) < 2:
        info["basis"] = "no evidence yet; equilibrium value stands"
        return ceiling, info

    first_round, first_gain = offers[0]
    last_round, last_gain = offers[-1]
    span = max(1, last_round - first_round)
    rate = (last_gain - first_gain) / span      # gain per round they concede

    # How far ahead it is worth projecting: never past the deadline, and never
    # so far that discounting makes the projection meaningless anyway.
    horizon = 5 if rounds_left is None else max(1, min(5, rounds_left - 1))

    if rate <= 0:
        # They are not conceding — they have repeated or worsened their offer.
        # The best realistic future is the same offer, one round later, worth
        # less. Anything they are offering now beats that.
        value = last_gain * delta_me
        info.update(basis="opponent not conceding", rate=rate, projected=value)
        return min(ceiling, value), info

    # They are conceding. Project their trend and discount it, taking the best
    # round to wait for rather than assuming the furthest is best.
    best = max((last_gain + rate * k) * (delta_me ** k) for k in range(1, horizon + 1))
    info.update(basis="projected from concession trend", rate=rate, projected=best)
    return min(ceiling, best), info


def _effective_horizon(delta_me: float, cfg) -> int:
    """The round by which our own share has lost most of its value.

    A 99-round cap is not a usable deadline: inflation destroys the pot long
    before it. The round at which our share is worth 5% of its opening value is
    the real one, so concession is paced against that instead.
    """
    if delta_me >= 1.0:
        return cfg.barg_uncapped_horizon    # no inflation: use a plain planning horizon
    rounds = math.ceil(math.log(0.05) / math.log(delta_me))
    return int(max(4, min(rounds, cfg.barg_uncapped_horizon)))


def _deltas(state: dict, me_is_alice: bool, unknown_delta: float) -> tuple[float, float]:
    """My and my opponent's per-round discount multipliers.

    Under incomplete information the opponent's is absent; assume a middling
    value rather than guessing an extreme in either direction.
    """
    d1 = state.get("delta_1")
    d2 = state.get("delta_2")
    mine_raw, theirs_raw = (d1, d2) if me_is_alice else (d2, d1)
    mine = _num(mine_raw, 1.0) if mine_raw is not None else 1.0
    theirs = _num(theirs_raw, unknown_delta) if theirs_raw is not None else unknown_delta
    return mine, theirs


def _rounds_left(state: dict, undisclosed_horizon: int) -> tuple[int, bool]:
    """(rounds remaining including this one, whether the cap was disclosed).

    No bargaining game is uncapped. When `horizon_known` is false the server
    withholds `max_rounds`, but the cap is still there — 99 rounds, observed
    directly when a live game terminated `no_deal` with `round_cap_reached` at
    round 99. Counting against the real cap is what gives parity, and therefore
    the last word, any meaning in those games.
    """
    disclosed = not (state.get("horizon_known") is False or state.get("max_rounds") is None)
    cap = int(_num(state.get("max_rounds"), 1)) if disclosed else int(undisclosed_horizon)
    return max(1, cap - int(_num(state.get("round"), 1)) + 1), disclosed


def plan(game: dict, cfg) -> dict:
    """Compute this turn's numbers and the reasoning behind them.

    Returned separately from the action so the LLM message layer and the game
    log can both see *why* the agent moved as it did.
    """
    state = game["game_state"]
    money = _num(state.get("money_to_divide"), 0.0)
    me_is_alice = game["your_player"] == "player_1"
    delta_me, delta_opp = _deltas(state, me_is_alice, cfg.barg_unknown_delta)
    rounds_left, horizon_known = _rounds_left(state, cfg.barg_undisclosed_horizon)

    # The share below which conceding buys nothing. Measured over 497 of our own
    # live proposals: the field accepts 4-11% of offers that leave it under 40%
    # of the pot and 47-64% of everything from 45% up, so its acceptance curve
    # is flat from an even split onward and whatever we hand over past that
    # point is a transfer, not a concession.
    # Read live so the floor can be moved without restarting an agent.
    #
    # This floor must never sit at exactly 0.50. The field's outcomes pile up on
    # the even split -- 24.6% of our 1,417 completed bargaining games ended within
    # 0.02 of exactly half, and 20% of the offers we make ARE exactly half, with
    # the highest acceptance rate of any bin (64.5%). Because the rating is a
    # PERCENTILE against the field on the same configuration, landing on that atom
    # is the worst possible outcome per dollar: a 0.500 share beats 45.5% of the
    # distribution while 0.520 beats 67.1%. Two percent of the pot buys twenty-one
    # percentile points, because it steps over the pile instead of joining it.
    #
    # Clamping to 0.50 was manufacturing that outcome: whenever the equilibrium
    # asked for less than half, the clamp put us exactly on the atom.
    floor_share = runtime_flags.as_float("GLEE_BARG_OFFER_FLOOR", cfg.barg_offer_floor)
    floor_share = min(max(floor_share, 0.0), 1.0)

    # Continuing is worth different amounts depending on who proposes next,
    # and that depends on which phase we are in — the turn alternates either way.
    next_rounds_left = rounds_left - 1

    # I am the receiver now: rejecting makes me next round's proposer.
    continuation = delta_me * proposer_share(delta_me, delta_opp, next_rounds_left) * money

    # I am the proposer now: if they reject, THEY propose next round and I am
    # the receiver, so I get whatever their equilibrium offer leaves me.
    if next_rounds_left <= 0:
        continuation_if_refused = 0.0      # nothing follows a final-round refusal
    else:
        opp_share_next = proposer_share(delta_opp, delta_me, next_rounds_left)
        continuation_if_refused = delta_me * (1.0 - opp_share_next) * money

    # The acceptance threshold falls back on the measured field level only in
    # the degenerate corner, and only while the last word is still far off: at
    # two rounds or fewer the endgame rules below own the decision, and the
    # equilibrium there is a real, checkable ultimatum rather than a knife edge.
    me = game.get("your_player", "player_1")
    degenerate = delta_opp >= 1.0 and rounds_left > 2
    realistic, evidence = realistic_continuation(
        state, me, delta_me, continuation, rounds_left,
        field_ceiling=(floor_share * money * delta_me) if degenerate else None)

    spe_now = proposer_share(delta_me, delta_opp, rounds_left) * money
    # Blend toward an even split: the field anchors there, and a no-deal is
    # worth far less than the extra few percent that full SPE aggression buys.
    w = min(max(cfg.barg_spe_weight, 0.0), 1.0)
    aspiration = w * spe_now + (1.0 - w) * (money / 2.0)
    # Never open below what the field will actually concede. This is the guard
    # on the degenerate corner, where the equilibrium share is 0 and the blend
    # alone opened at 17.5% of the pot — 0% at full SPE weight, which agreed
    # four live games at exactly $0.
    aspiration = max(aspiration, floor_share * money)
    # Never propose myself less than a refusal would be worth.
    aspiration = min(max(aspiration, continuation_if_refused), money)

    # The cap is not always the binding deadline, and in an undisclosed game it
    # never is: the cap is 99 rounds away while at delta_me = 0.9 the pot is
    # worth 5% of its opening value by round 29 (round 14 at 0.8, and no probe
    # plans past 60). Concede against inflation there — without that both sides
    # hold, and the game dies at the cap paying zero, which is what happened
    # live. A disclosed 12-round game always ends first and the recursion above
    # already prices that, so the clock stays off.
    effective_horizon = None
    this_round = _num(state.get("round"), 1)
    if not horizon_known:
        effective_horizon = _effective_horizon(delta_me, cfg)
        elapsed = min(1.0, max(0.0, (this_round - 1) / effective_horizon))
        offers = _offers_to_me(state, me)
        floor = max([realistic] + [g for _, g in offers]) if offers else realistic
        floor = min(floor, money)
        if aspiration > floor:
            aspiration = floor + (aspiration - floor) * (1.0 - elapsed) ** 2

    return {
        "money": money,
        "me_is_alice": me_is_alice,
        "delta_me": delta_me,
        "delta_opp": delta_opp,
        "rounds_left": rounds_left,
        "horizon_known": horizon_known,
        "continuation": continuation,
        "continuation_if_refused": continuation_if_refused,
        "realistic_continuation": realistic,
        "opponent_evidence": evidence,
        "effective_horizon": effective_horizon,
        "offer_floor": floor_share * money,
        "spe_share": spe_now / money if money else 0.5,
        "aspiration": aspiration,
    }


def decide(game: dict, cfg) -> dict:
    state = game["game_state"]
    p = plan(game, cfg)
    money, mine = p["money"], p["me_is_alice"]

    if game["valid_actions"]["type"] == "offer":
        my_gain = p["aspiration"]
        rl = p["rounds_left"]
        if rl == 1:
            # A true ultimatum: rejecting pays them nothing, so in theory they
            # take any crumb. In practice humans and LLMs reject offers that
            # read as insulting, and a spite rejection costs the whole pot —
            # so leave a share big enough to be worth taking.
            my_gain = money * 0.75
        elif rl <= 2:
            # The opponent gets the last word after this. Cap the ask so the
            # offer stays acceptable, floored by what a refusal is worth.
            my_gain = max(p["continuation_if_refused"], min(my_gain, money * 0.62))
        # Cap the ask so the opponent is never pushed under the measured
        # acceptance cliff. barg_offer_floor bounds OUR share from below; this
        # bounds it from above. Live check found every probe proposing 26-38%
        # to the opponent in some configurations — inside the region where
        # acceptance collapses to 5-13% and is flat, so the extra share we were
        # demanding bought a rejection rather than a better deal.
        opp_floor = runtime_flags.as_float("GLEE_BARG_OPPONENT_FLOOR",
                                           cfg.barg_opponent_floor)
        opp_floor = min(max(opp_floor, 0.0), 0.5)
        if opp_floor > 0.0:
            my_gain = min(my_gain, (1.0 - opp_floor) * money)
            p["opponent_floor_applied"] = opp_floor

        return {"alice_gain": my_gain if mine else money - my_gain,
                "bob_gain": money - my_gain if mine else my_gain,
                "_plan": p}

    # --- decision phase: current_player is always the offer's receiver ---
    offer = state.get("last_offer") or {}
    my_gain = _num(offer.get(f"{state.get('current_player')}_gain"), 0.0)

    if p["rounds_left"] <= 1:
        # Final round. Rejecting pays $0, so anything above nothing beats it.
        decision = "accept" if my_gain > 0 else "reject"
    elif my_gain <= 0:
        # Rounds remain, so playing on cannot pay less than this does. Without
        # this the degenerate corner's zero threshold cleared an offer of $0.
        decision = "reject"
    else:
        # Compare against what continuing is REALISTICALLY worth, not what it
        # would be worth against an equilibrium opponent. Holding out for the
        # latter against someone who never concedes pays zero.
        threshold = p["realistic_continuation"] * 0.98
        decision = "accept" if my_gain >= threshold else "reject"
        # Last resort where inflation, not the cap, is the real deadline: past
        # that point any positive offer beats grinding the pot down to nothing.
        if (decision == "reject" and p["effective_horizon"] is not None and my_gain > 0
                and _num(state.get("round"), 1) >= p["effective_horizon"]):
            decision = "accept"

    p["offered_to_me"] = my_gain
    return {"decision": decision, "_plan": p}
