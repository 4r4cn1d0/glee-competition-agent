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

import copy
import math

from .. import barg_offer
from .. import messages
from .. import opponents
from .. import runtime_flags

from ..actions import _num, coerce

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


def _observed_gain(state: dict, me: str, money: float):
    """The opponent's ACTUAL concession rate, as a fraction of the pot per round.

    None when there is not enough of their offer trail to estimate it, in which
    case the caller keeps its prior. Three of their offers is the minimum that
    can distinguish a trend from a single step.

    Measured across the trail rather than between the last two offers, because
    a single pair is noisy: opponents commonly jump then hold, and the pair test
    would read that jump as a rate they will sustain.
    """
    if not money:
        return None
    theirs = []
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        off = entry.get("offer") or {}
        if off.get("proposer") == me:
            continue
        val = off.get(f"{me}_gain")
        rnd = entry.get("round")
        if val is not None and rnd:
            theirs.append((int(rnd), float(val)))
    theirs = sorted(set(theirs))
    if len(theirs) < 3:
        return None
    span = theirs[-1][0] - theirs[0][0]
    if span < 2:
        return None
    return ((theirs[-1][1] - theirs[0][1]) / money) / span


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

    Returned separately from the action so the hand-written message layer and
    the game log can both see *why* the agent moved as it did.
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


def _gate(p: dict, name: str) -> None:
    """Append ``name`` to the gate trace when tracing is on (see negotiation).

    Pure instrumentation behind GLEE_TRACE_GATES, OFF by default: with the flag
    off the plan dict never carries the key and nothing reads the list, so the
    action is byte-identical either way. The list records, in firing ORDER,
    every gate that changed the pending offer/threshold/decision this turn.
    """
    g = p.get("gates_fired")
    if g is not None:
        g.append(name)


def _post_reject_offer(game: dict, cfg) -> dict:
    """Run the actual offer policy on the deterministic state after rejection.

    Bargaining has no intervening opponent move: rejecting records the live
    offer, advances the round, and makes the rejecter the next proposer. The
    projected observation follows ``sim.bargaining``'s API transition shape and
    is then sent through public ``decide`` plus wire coercion, so endgame caps,
    opponent floors, Bob pricing, profile exploitation, and future offer writers
    are shared with the next real turn rather than copied here.
    """
    projected = copy.deepcopy(game)
    state = projected.get("game_state") or {}
    live = state.get("last_offer") or {}
    me = state.get("current_player") or projected.get("your_player")
    round_no = int(_num(state.get("round"), 1))

    recorded_offer = {
        key: live.get(key)
        for key in ("player_1_gain", "player_2_gain", "message")
        if key in live
    }
    history = list(state.get("history") or [])
    history.append({
        "round": round_no,
        "proposer": live.get("proposer") or state.get("proposer"),
        "offer": recorded_offer,
        "decision": "reject",
    })
    state.update(
        phase="offer",
        current_player=me,
        proposer=me,
        round=round_no + 1,
        history=history,
    )
    projected["phase"] = "offer"
    projected["game_state"] = state
    projected["valid_actions"] = {"type": "offer", "fields": {}}
    return coerce(decide(projected, cfg), projected)


def _decide(game: dict, cfg) -> dict:
    state = game["game_state"]
    p = plan(game, cfg)
    money, mine = p["money"], p["me_is_alice"]
    if runtime_flags.enabled("GLEE_TRACE_GATES"):
        p["gates_fired"] = []

    if game["valid_actions"]["type"] == "offer":
        my_gain = p["aspiration"]
        rl = p["rounds_left"]
        if rl == 1:
            # A true ultimatum: rejecting pays them nothing, so in theory they
            # take any crumb. In practice humans and LLMs reject offers that
            # read as insulting, and a spite rejection costs the whole pot —
            # so leave a share big enough to be worth taking.
            if my_gain != money * 0.75:
                _gate(p, "ultimatum")
            my_gain = money * 0.75
        elif rl <= 2:
            # The opponent gets the last word after this. Cap the ask so the
            # offer stays acceptable, floored by what a refusal is worth.
            _g0 = my_gain
            my_gain = max(p["continuation_if_refused"], min(my_gain, money * 0.62))
            if my_gain != _g0:
                _gate(p, "lastword_cap")
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
            if my_gain > (1.0 - opp_floor) * money:
                _gate(p, "opp_floor")
            my_gain = min(my_gain, (1.0 - opp_floor) * money)
            p["opponent_floor_applied"] = opp_floor

        # --- responder-seat (Bob) offer rebuild ---------------------------
        # Bob is player_2: he answers first and proposes on even rounds, and
        # the rest of this function was written for the seat that opens. Two
        # things break in his seat specifically.
        #
        # PARITY. Disclosed games state max_rounds = 12 -- an EVEN cap -- so
        # player_2 is the last proposer and proposer_share() hands him
        # 0.77-1.00 of the pot on every even round against Alice's 0.00-0.74 on
        # every odd one. The last word is really his; it is also unbankable,
        # since collecting it means agreeing at round 12 where delta_me = 0.8
        # leaves 8.6% of face value. The blend and the two floors then crush the
        # whole oscillation into one number, and 532 of Bob's 704 logged offers
        # landed in the single bin [0.60, 0.65) whoever he was playing.
        #
        # THE VALUE OF A REFUSAL IS NOT SYMMETRIC. Measured as the realised
        # percentile after one of our offers was refused (15,812 offers over
        # 9,881 games): with delta_me = 1.0 a refusal at round 2 still returns
        # 0.66 and at round 6 returns 0.74, because waiting costs nothing; with
        # delta_me < 1.0 the same refusals return 0.28 and 0.06. A patient
        # player should ask high and can afford to be refused; a burning one is
        # choosing between closing now and collecting a fifth of the field. One
        # flat 0.61 ask cannot be right for both, and 0.61 is what we sent.
        #
        # So the ask is chosen by maximising expected PERCENTILE -- the rating's
        # own objective -- against a fitted P(accept | give, round, delta_opp,
        # their demand) and the field's payoff distribution in this exact
        # configuration cell. See glee_agent/barg_offer.py.
        #
        # SHIPPED AS A FLOOR, NOT A CONCESSION, and the asymmetry is deliberate.
        # The model wants to move Bob's ask in both directions, and only one
        # direction can be screened here:
        #  * UPWARD, where the baseline concession schedule has walked the ask
        #    below the percentile-optimal level. That is most of the undisclosed
        #    horizon: `(1 - elapsed)**2` drags Bob from 0.61 down through 0.41 by
        #    round 12, i.e. straight across the field's 0.50 atom, which is 9.6%
        #    of the whole bargaining distribution and where an extra 0.01 of pot
        #    buys +0.095 percentile against +0.025 anywhere else.
        #  * DOWNWARD, trading share for a higher chance of acceptance. That
        #    rests entirely on P(accept) rising with the give, and live it rises
        #    with the RESPONDER'S PATIENCE far more than with the give itself --
        #    at a give of 0.35-0.45 the field accepts 63.6% at delta_opp = 0.8
        #    and 6.2% at 1.0. The offline arena cannot see that: its cloned
        #    responders are fitted on (share, round) alone, delta-blind, and
        #    nearly flat across the range in question (give 0.39 -> 0.48 moves
        #    their acceptance 0.325 -> 0.404). Screened over 2,400 paired games
        #    the two halves separate cleanly -- the concession half returns
        #    -0.028 percentile [-0.049, -0.009] in the delta_me = 0.95 cell while
        #    the floor half returns +0.013 [+0.007, +0.019] across Bob's seat --
        #    so the floor ships and the concession does not. Unresolved, not
        #    refuted: the harness has no way to price it.
        #
        # Deliberately narrow beyond that. Bob's seat only (Alice's opener is a
        # different problem and already plays above the field). Never in the last
        # two rounds, where the endgame rules above own the decision and the
        # ultimatum is a real, checkable thing rather than a fitted curve. The
        # flag is a shrinkage weight, so a small value is a small step toward the
        # model rather than a cliff, and a missing or unreadable model file
        # leaves the baseline ask untouched.
        bob_w = runtime_flags.as_float("GLEE_BARG_BOB_OFFER", 0.0)
        if bob_w > 0.0 and not mine and p["rounds_left"] > 2 and money > 0:
            offers = _offers_to_me(state, game.get("your_player", "player_2"))
            best_seen = max([g for _, g in offers], default=0.0)
            latest = offers[-1][1] if offers else None
            # The search is floored at the baseline ask (so the model can only
            # raise, see above) and at the BEST share the opponent has ever
            # offered -- proposing ourselves less than something they have
            # already shown they will part with is dominated whatever any curve
            # says. The demand FEATURE takes the LATEST instead: that is the
            # number Bob is actually answering, and what the model was fitted on.
            #
            # Deliberately NOT floored by continuation_if_refused. plan() floors
            # the aspiration there, but that number is the parity oscillation
            # again -- with delta_me = 0.95 against delta_opp = 0.9 it claims a
            # refusal is worth 0.77 of the pot -- and the opponent-floor cap in
            # this function already overrides it on every live arm.
            floor_gain = max(best_seen, my_gain, 0.0)
            picked = barg_offer.best_ask(
                money=money,
                rnd=int(_num(state.get("round"), 1)),
                delta_me=p["delta_me"],
                # Under incomplete information the opponent's delta key is
                # ABSENT, and plan() substitutes an assumed middling value.
                # Hand the model the absence, not the assumption -- it fitted
                # a separate "hidden" coefficient for exactly this case.
                delta_opp=(p["delta_opp"]
                           if state.get("delta_1") is not None else None),
                their_demand=(1.0 - latest / money) if latest is not None else None,
                cell=barg_offer.cell_key(money, state.get("max_rounds"),
                                         p["horizon_known"],
                                         state.get("complete_information")),
                lo=floor_gain / money)
            if picked is not None:
                target = picked[0] * money
                w = min(max(bob_w, 0.0), 1.0)
                _g0 = my_gain
                my_gain = my_gain + w * (target - my_gain)
                my_gain = min(max(my_gain, floor_gain), money)
                p["bob_offer"] = dict(picked[1], target=round(picked[0], 4),
                                      weight=round(w, 3))
                if my_gain != _g0:
                    _gate(p, "bob_offer")

        # Opponent-conditional exploitation: when this game DISCLOSES who we are
        # playing and their fitted profile says they accept far less than the
        # generic floor gives them, tighten the offer to just above their own
        # measured threshold. This deliberately overrides the generic
        # opponent-floor above -- that floor protects us against the AVERAGE
        # field, and the whole point of a profile is that this opponent is not
        # average. max() so the exploit can only ever raise our ask, never make
        # us more generous than the baseline.
        if runtime_flags.enabled("GLEE_OPP_EXPLOIT"):
            give = opponents.barg_give_floor(game)
            if give is not None:
                if my_gain < (1.0 - give) * money:
                    _gate(p, "opp_exploit")
                my_gain = max(my_gain, (1.0 - give) * money)
                p["opp_exploit_give"] = give

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
        # Share-floor acceptance: the fleet's agreed share averages 0.476-0.494
        # in every config cell, and the percentile pays the 0.500 focal atom --
        # a 0.48 close ranks below the entire even-split pile, so discounted
        # continuation math that happily clears a 47% offer is surplus-correct
        # and rating-wrong. While enough rounds remain to counter safely,
        # refuse anything under this share of the pot. Final two rounds are
        # untouched (the opponent holds the last word there). OFF by default.
        accept_floor = runtime_flags.as_float("GLEE_BARG_ACCEPT_FLOOR", 0.0)
        if accept_floor > 0.0 and p["rounds_left"] > 2 and money > 0:
            floor_share = min(max(accept_floor, 0.0), 0.6)
            # Discount-derived floor. The flat 0.50 floor is delta-blind, and
            # the 500-game export priced that exactly: it HELPS where patience
            # is cheap (delta>0.9: +1.37 rating post-deploy) and HURTS where
            # the clock burns (delta<=0.9: value kept fell 88%->67%, closes
            # pushed from round 2.0 to 4.4; the worst cell loses 0.095 pot per
            # game held). Break-even is exact: another round is worth taking
            # only if the expected haggling gain G (~0.05 pot/round, measured
            # n=299) beats the discount loss, so the floor a patient player
            # can afford is delta*G/(1-delta), capped by the flat floor:
            # delta 0.8 -> 0.20, 0.9 -> 0.45, 0.95+ -> the 0.50 atom floor.
            gain = runtime_flags.as_float("GLEE_BARG_FLOOR_GAIN", 0.0)
            # G IS MEASURABLE, AND THE CONSTANT IS WRONG BY 40x.
            #
            # The formula above is right: another round is worth taking only if
            # the haggling gain G beats the discount loss, so a patient player
            # can afford a floor of delta*G/(1-delta). But G was hardcoded at
            # 0.05 pot/round from an old 299-game fit, and the opponent's ACTUAL
            # concession rate is observable in their own offer trail.
            #
            # Measured over 899 live games with three or more of their offers:
            # median G is +0.0012 pot/round, mean +0.0030. NOT ONE GAME IN 895
            # reached the assumed 0.05, and in 16% G is NEGATIVE -- the opponent
            # improves their own share over time, farming a clock that costs us
            # more than it costs them.
            #
            # The cost of believing 0.05 is the floor it produces: at delta 0.9
            # it demands 0.450 of the pot when the observed G justifies 0.000,
            # and at 0.95 it demands the full 0.500 against 0.020. So we hold
            # out for half the pot waiting for a concession that never arrives.
            # Two live transcripts show the endgame: one dragged to round 7 and
            # kept 371k where accepting at round 3 was worth 406k; the other
            # dragged to round 11 and kept 1,046 where the opponent's ROUND ONE
            # offer was worth 4,500 -- a 77% loss.
            #
            # This is the same insight as the stonewall override below, which
            # already fires when the opponent's number never moves. A stonewall
            # is just the special case G = 0; the general test is economic, and
            # it catches the far more common case of an opponent who concedes
            # but too slowly to outrun our discount. Both transcripts above have
            # MOVING offers, so the stonewall rule never fires on either.
            #
            # Safe when G is small: the floor collapsing toward zero does not
            # mean "accept anything". It hands the decision back to the
            # discounted-continuation test at the top of this function, which is
            # the economically correct judge -- exactly what the stonewall
            # override says it is doing when it releases the floor.
            if gain > 0.0:
                dme = p.get("delta_me")
                if dme is not None and dme < 1.0:
                    g_used = gain
                    if runtime_flags.enabled("GLEE_BARG_OBSERVED_GAIN"):
                        g_obs = _observed_gain(state, state.get("current_player") or "", money)
                        if g_obs is not None:
                            g_used = max(g_obs, 0.0)
                            p["observed_gain"] = round(g_obs, 5)
                            _gate(p, "observed_gain")
                    if dme * g_used / (1.0 - dme) < floor_share:
                        _gate(p, "floor_gain")
                    floor_share = min(floor_share, dme * g_used / (1.0 - dme))
            # Stonewall override. The floor's whole premise is that waiting
            # BUYS something; against an opponent who simply repeats their
            # number it buys nothing while our clock burns. Measured on Agent
            # 5's live games: ten grinds to round 7-22 where the opponent's
            # offer never moved (0.400 repeated for eleven rounds), each
            # costing -3.9 to -7.9 rating, and each strictly worse than
            # accepting the SAME opponent's round-1 offer -- one kept 35% of
            # nominal where round-1 acceptance kept 100%. Two flat offers is
            # the signal the negotiation stall policy already acts on; here it
            # releases the floor so the discounted-continuation test (which
            # correctly says "take it") can decide.
            # Two guards, both measured, both absent from the first version --
            # which the arena correctly rejected (-0.009 on both seeds):
            #  * RUN LENGTH. A flat PAIR is weak evidence: it breaks 58% of the
            #    time, and its modal appearance is round 3. The live grinds
            #    that motivated this rule were all runs of four or more (rounds
            #    7-22 with the number never moving). Across 6,917 logged games
            #    P(they ever improve) falls 0.37 -> 0.26 -> 0.23 as the run
            #    grows, and mean improvement is +0.33% of pot -- a dead signal.
            #  * OUR CLOCK. The counterfactual REVERSES on delta_me: with
            #    delta_me = 1.0 waiting is free and holding out was worth
            #    +7.7pp of pot (better in 92.7% of 368 logged cases), while at
            #    delta_me < 1.0 holding LOST 6.0pp (worse in 73.8% of 225).
            #    Releasing the floor for a patient player is pure loss.
            run_needed = int(runtime_flags.as_float("GLEE_BARG_STONEWALL", 0))
            dme_sw = p.get("delta_me")
            if run_needed >= 2 and dme_sw is not None and dme_sw < 1.0:
                # Count the run over HISTORY only. _offers_to_me also appends
                # last_offer, which duplicates the newest history entry when
                # the platform omits its round key -- and a duplicate cannot be
                # told from a genuinely new repeat without that key. Undercount
                # by one rather than over: releasing the floor a round early is
                # the failure the arena already priced at -0.009.
                me_sw = state.get("current_player") or ""
                vals = []
                for entry in state.get("history") or []:
                    if not isinstance(entry, dict):
                        continue
                    off = entry.get("offer") or {}
                    if not isinstance(off, dict):
                        continue
                    if (off.get("proposer") or entry.get("proposer")) == me_sw:
                        continue
                    g_ = off.get(f"{me_sw}_gain")
                    if g_ is not None:
                        vals.append(_num(g_))
                run = 1
                for i in range(len(vals) - 1, 0, -1):
                    if abs(vals[i] - vals[i - 1]) <= 0.01 * max(abs(vals[i - 1]), 1.0):
                        run += 1
                    else:
                        break
                if run >= run_needed:
                    # EXTORTION GUARD (red team, scripts/redteam.py). The
                    # release is stated as "waiting buys nothing against an
                    # opponent who repeats their number", and that premise is
                    # about the WAITING, not about the number. It says nothing
                    # about how big the number is -- so the rule as written is
                    # a switch any opponent can flip on our acceptance floor by
                    # repeating ANY offer three times, a crumb included.
                    #
                    # The evolved adversary found exactly that switch and stood
                    # on it: opening at 99% of the pot, repeating the same
                    # figure verbatim, never conceding and never accepting
                    # under ~92%. It scores 0.589 estimated percentile against
                    # this stack where the cloned field scores 0.304, and it
                    # takes us from 0.696 to 0.047. Ablating this one flag is
                    # worth +0.0092 of OUR percentile against it and -0.0003
                    # against the ordinary field -- the only flag in the whole
                    # arm with that signature.
                    #
                    # The live evidence the release was actually built on is
                    # narrower than the release: every grind in it repeated a
                    # number in the 0.40-0.50 band (Agent 5's "0.400 repeated
                    # for eleven rounds"), and across 12,000 simulated field
                    # games 92% of releases fire on an offer of 0.40-0.50 of
                    # the pot, only 8.5% below 0.35. So requiring the repeated
                    # offer to be worth something keeps every case the rule was
                    # measured on and removes the extortion corner it was never
                    # measured on. OFF by default (0.0 reproduces the old path
                    # exactly).
                    sw_min = runtime_flags.as_float("GLEE_BARG_STONEWALL_MIN", 0.0)
                    if sw_min > 0.0 and money > 0 and \
                            my_gain < min(max(sw_min, 0.0), 0.6) * money:
                        p["stonewall_extortion"] = run
                        _gate(p, "stonewall_extortion")
                    else:
                        if floor_share != 0.0:
                            _gate(p, "stonewall_release")
                        floor_share = 0.0
                        p["stonewall_release"] = run
            # Economic-stagnation release (generalises the stonewall). The
            # flat-run release above only sees an opponent whose number never
            # moves; one who crawls +0.3-0.5% of pot per round against our
            # delta 0.9-0.95 clock is economically identical and invisible to
            # it -- live, Alice at delta 0.95 watched offers crawl
            # 4,552 -> 4,797 nominal over ten rounds while their discounted
            # value fell 4,325 -> 2,728, and the floor held until we accepted
            # at round 12 for -8 rating. So project the opponent's OWN
            # concession rate through OUR discount: if no reachable round's
            # projected offer beats today's by more than epsilon in discounted
            # terms, waiting buys nothing and the floor releases, exactly as
            # it does for a flat run. Guards, all deliberate:
            #  * the extortion guard (GLEE_BARG_STONEWALL_MIN) stays -- a
            #    crawler repeating crumbs must not flip the floor either;
            #  * delta_me < 1.0 -- for a patient player waiting is free and
            #    holding out measurably pays (the stonewall's own evidence:
            #    +7.7pp of pot at delta_me = 1.0);
            #  * >= 3 DISTINCT opponent offers -- two points cannot support a
            #    slope estimate, and the rate is the MEDIAN pairwise slope
            #    over the last 3-4 distinct offers so one outlier step cannot
            #    fake or hide a trend;
            #  * the sequence collapses consecutive equal VALUES, the
            #    echo-collapse pattern from negotiation's _price_seq:
            #    _offers_to_me double-counts the newest offer via last_offer
            #    when the platform omits its round key (the trap the
            #    stonewall counter documents), and a (round, gain) dedup
            #    cannot see that duplicate -- a value collapse can, and it
            #    also stops a verbatim repeat posing as a fresh offer. The
            #    offer being decided (last_offer, not yet in history) DOES
            #    count when its value moved: it is the newest evidence of
            #    the crawl and what makes the release fire by round ~6
            #    rather than ~8.
            econ_eps = runtime_flags.as_float("GLEE_BARG_ECON_STALL", 0.0)
            dme_ec = p.get("delta_me")
            if econ_eps > 0.0 and floor_share > 0.0 and money > 0 \
                    and my_gain > 0 and dme_ec is not None and dme_ec < 1.0:
                me_ec = state.get("current_player") or ""
                seq_ec: list[tuple[int, float]] = []
                for entry in state.get("history") or []:
                    if not isinstance(entry, dict):
                        continue
                    off = entry.get("offer") or {}
                    if not isinstance(off, dict):
                        continue
                    if (off.get("proposer") or entry.get("proposer")) == me_ec:
                        continue
                    g_ = off.get(f"{me_ec}_gain")
                    if g_ is None:
                        continue
                    gv = _num(g_)
                    if seq_ec and gv == seq_ec[-1][1]:
                        continue          # echo / verbatim repeat, not distinct
                    seq_ec.append((int(_num(entry.get("round"), 0)), gv))
                last_ec = state.get("last_offer") or {}
                if last_ec.get("proposer") and last_ec["proposer"] != me_ec \
                        and last_ec.get(f"{me_ec}_gain") is not None:
                    gv = _num(last_ec[f"{me_ec}_gain"])
                    if not (seq_ec and gv == seq_ec[-1][1]):
                        seq_ec.append((int(_num(last_ec.get("round"), 0)), gv))
                if len(seq_ec) >= 3:
                    window = seq_ec[-4:]
                    slopes = sorted((g2 - g1) / (r2 - r1)
                                    for i, (r1, g1) in enumerate(window)
                                    for (r2, g2) in window[i + 1:] if r2 > r1)
                    if slopes:
                        m = len(slopes)
                        rate_ec = (slopes[m // 2] if m % 2 else
                                   0.5 * (slopes[m // 2 - 1] + slopes[m // 2]))
                        # The planning clock is SYNTHETIC in undisclosed games
                        # (rounds_left counts against the hidden 99 cap), so
                        # only a DISCLOSED cap bounds the projection; matching
                        # realistic_continuation, waiting k rounds only means
                        # anything up to rounds_left - 1.
                        horizon_ec = (max(1, min(5, p["rounds_left"] - 1))
                                      if p["horizon_known"] else 5)
                        rr = max(rate_ec, 0.0)
                        best_wait = max((my_gain + rr * k) * dme_ec ** k
                                        for k in range(1, horizon_ec + 1))
                        if best_wait <= my_gain * (1.0 + econ_eps):
                            sw_min_ec = runtime_flags.as_float(
                                "GLEE_BARG_STONEWALL_MIN", 0.0)
                            if sw_min_ec > 0.0 and \
                                    my_gain < min(max(sw_min_ec, 0.0), 0.6) * money:
                                p["econ_stall_extortion"] = round(
                                    best_wait / my_gain, 4)
                            else:
                                floor_share = 0.0
                                p["econ_stall_release"] = round(
                                    best_wait / my_gain, 4)
            floor_gain = floor_share * money
            if threshold < floor_gain:
                threshold = floor_gain
                p["accept_floor_applied"] = round(floor_share, 3)
                _gate(p, "accept_floor")
        # Opponent-conditional: against a PROFILED soft opponent our next offer
        # (asking all but their measured threshold) is very likely accepted, so
        # continuing is worth nearly (1-give) discounted one round -- far more
        # than the generic continuation estimate. Without this, the offer-side
        # exploit is theatre: deals close on THEIR ~50/50 proposal because our
        # baseline acceptance takes it first. Only ever RAISES the bar, and only
        # while rounds remain; the final-round any-positive rule stays untouched.
        if runtime_flags.enabled("GLEE_OPP_EXPLOIT") and p["rounds_left"] > 2:
            give = opponents.barg_give_floor(game)
            if give is not None:
                hold = (1.0 - give) * money * p["delta_me"]
                if min(hold, 0.95 * money) > threshold:
                    _gate(p, "opp_exploit")
                threshold = max(threshold, min(hold, 0.95 * money))
                p["opp_exploit_hold"] = threshold
        decision = "accept" if my_gain >= threshold else "reject"
        # Last resort where inflation, not the cap, is the real deadline: past
        # that point any positive offer beats grinding the pot down to nothing.
        if (decision == "reject" and p["effective_horizon"] is not None and my_gain > 0
                and _num(state.get("round"), 1) >= p["effective_horizon"]):
            decision = "accept"
            _gate(p, "inflation_accept")

    # NO-REGRESSION GUARD. In nine measured games the old decision path rejected
    # a live offer and the next outgoing policy kept no more of the pot; the
    # avoidable delay forfeited 17.36 pot-points and -44.9 rating in aggregate.
    # When armed, the code above still owns every ordinary accept condition. A
    # remaining Reject is changed only when the wire-coerced offer produced by
    # the exact next-turn policy keeps no more than the live offer plus the
    # configured share epsilon. Projection failure leaves the Reject unchanged.
    if (decision == "reject" and money > 0.0
            and p["rounds_left"] > 1
            and runtime_flags.enabled("GLEE_BARG_NO_REGRESS")):
        epsilon = runtime_flags.as_float("GLEE_BARG_NO_REGRESS_EPS", 0.0)
        if not math.isfinite(epsilon):
            epsilon = 0.0
        epsilon = min(max(epsilon, 0.0), 1.0)
        try:
            counter = _post_reject_offer(game, cfg)
            own_key = "alice_gain" if mine else "bob_gain"
            counter_gain = _num(counter.get(own_key), -1.0)
            if 0.0 <= counter_gain <= money:
                offered_share = my_gain / money
                counter_share = counter_gain / money
                p["no_regress"] = {
                    "offered_share": round(offered_share, 6),
                    "planned_counter_share": round(counter_share, 6),
                    "epsilon": epsilon,
                    "projected_round": int(_num(state.get("round"), 1)) + 1,
                }
                if counter_share <= offered_share + epsilon:
                    decision = "accept"
                    _gate(p, "no_regress")
        except Exception:
            p["no_regress"] = {"status": "projection_failed"}

    p["offered_to_me"] = my_gain
    return {"decision": decision, "_plan": p}


def decide(game: dict, cfg) -> dict:
    """Choose numeric bargaining behaviour, then attach the assigned text arm."""
    action = _decide(game, cfg)
    try:
        record = messages.attach_bargaining_arm(game, action)
        if record is not None and isinstance(action.get("_plan"), dict):
            _gate(action["_plan"], "barg_msg")
    except Exception:
        pass                         # a message is never worth risking the move
    return action
