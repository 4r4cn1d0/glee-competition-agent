"""The first-principles negotiation policy, derived in .ai/NEGO_FIRST_PRINCIPLES.md.

This module exists to answer one question unambiguously: **which component owns
the outgoing price?**  When :func:`owns` returns True for a game, this module
owns it end to end.  ``negotiation._decide`` returns our action directly without
consulting ``plan()``, and ``actions._apply_negotiation_price_guards`` returns
before any hidden-floor, open-claim or ultimatum postcondition can rewrite it.
Nothing layers on top.  That is deliberate: our cap-10 buyer path previously
priced 46.4% of its round-10 bids below the seller's cost and had them rejected
0/71, while the 82 feasible ones were accepted 82/82 — the hold-out was sound and
a downstream rewriter was the whole defect.

Three facts from 17,361 logged games drive everything here.

1. Values are always ``base * scale`` for ``base`` in {80,100,120,150}, both
   seats on the same scale.  Twelve possible values, ever.
2. Turn order never varies: odd rounds are player_1, even rounds are player_2
   (229,848 offers, no exceptions).  So the final offer belongs to the seller in
   a one-round game and to the buyer in a ten-round game.
3. At a genuine terminal node under complete information the opponent accepts
   any positive share and rejects every non-positive one — 892/892 and 0/159.

Together those make the two complete-information dictator cells deterministic:
whoever offers last takes the zone by leaving the other seat one cent.

Under hidden information the buyer's value is uniform over the same four points,
so P(accept) is fixed by the grid and no schedule can improve on picking the
right grid point.  Because the field's payoff distribution in those cells has a
~70% atom at exactly zero, closing at all is worth +0.369 percentile while
winning the entire rest of the zone is worth +0.09.  We therefore ask the
*lowest* profitable grid point, which is not the money-maximising ask.
"""

from __future__ import annotations

import hashlib
import math

from . import runtime_flags

GRID = (80.0, 100.0, 120.0, 150.0)
SCALES = (1.0, 100.0, 10000.0)

#: Crumb left to the opponent at a terminal node.  Owns exactly one decision:
#: staying strictly above zero after the server's cent rounding.  Acceptance is
#: deterministic for any positive share, so there is nothing to buy by leaving
#: more than this.
EPS = 0.01

#: Share at which we take an early offer rather than wait for our own terminal
#: turn.  Owns exactly one decision.  Set to 1 - 0.0057, the measured
#: walk-away rate in cap-10 complete-information games.
HOLD_ACCEPT = 0.994

#: Ask in a cell where our own value is the top of the grid, so no zone can
#: exist.  Both outcomes pay $0, so this free-rolls the ~1.7% of opponents who
#: accept a loss-making price.  Owns exactly one decision.
DEAD_CELL_ASK = 200.0


def _num(x, default=math.nan) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v if math.isfinite(v) else default


def scale_of(value: float) -> float | None:
    """The grid scale this value belongs to, or None if it is off-grid."""
    for s in SCALES:
        for b in GRID:
            if abs(value - b * s) <= max(1e-6, 1e-9 * b * s):
                return s
    return None


def enabled() -> bool:
    return runtime_flags.enabled("GLEE_NEGO_FIRST_PRINCIPLES")


def in_treatment(game: dict) -> bool:
    """Within-agent arm assignment by game id.

    Both arms therefore meet the same opponents in the same hour, which is the
    only way we can read an effect: between-agent splits confounded rotation
    phase, opponent pool and hour of day, and placebo-treating an untouched
    agent produced a -0.12 'effect'.
    """
    # Exploit mode. The 50/50 split exists to MEASURE the policy; once measured,
    # halving its exposure only halves the gain. Test 4 keeps the split and stays
    # the measurement arm; the agent that actually carries our leaderboard row
    # runs it on every eligible game.
    if runtime_flags.enabled("GLEE_NEGO_FP_ALWAYS"):
        return True
    gid = str(game.get("game_id") or "")
    if not gid:
        return False
    return bool(int(hashlib.sha256(("nego_fp|" + gid).encode()).hexdigest(), 16) & 1)


def _seat(game: dict):
    state = game.get("game_state") or {}
    me = state.get("current_player") or game.get("your_player")
    if me not in ("player_1", "player_2"):
        return None
    them = "player_2" if me == "player_1" else "player_1"
    return me, them, state


def cell(game: dict):
    """Return (horizon, complete, i_am_seller, my_value, their_value) or None."""
    seat = _seat(game)
    if seat is None:
        return None
    me, them, state = seat
    role = state.get(f"{me}_role")
    if role not in ("seller", "buyer"):
        return None
    my_value = _num(state.get(f"{me}_value"))
    if not math.isfinite(my_value):
        return None
    complete = state.get("complete_information") is True
    their_value = _num(state.get(f"{them}_value")) if complete else math.nan
    if complete and not math.isfinite(their_value):
        return None
    if state.get("horizon_known") is True:
        mr = _num(state.get("max_rounds"))
        horizon = "single" if mr == 1.0 else ("cap10" if mr == 10.0 else None)
    else:
        horizon = "unknown"
    return horizon, complete, role == "seller", my_value, their_value


#: The cells this policy is designed for.  Everything else falls through to the
#: existing stack untouched -- 18 of 24 cells are not yet designed and saying so
#: is cheaper than pretending otherwise.
DESIGNED = {
    ("single", True, True),    # one round, complete info, seller  -- we offer last
    ("cap10", True, False),    # ten rounds, complete info, buyer  -- we offer last
    ("single", False, True),   # one round, hidden info, seller    -- grid ask
}


def owns(game: dict) -> bool:
    """True when this module, and nothing downstream, sets the price."""
    try:
        if game.get("game_family") != "negotiation":
            return False
        if not enabled() or not in_treatment(game):
            return False
        c = cell(game)
        if c is None:
            return False
        horizon, complete, i_am_seller, my_value, _ = c
        if (horizon, complete, i_am_seller) not in DESIGNED:
            return False
        return scale_of(my_value) is not None
    except Exception:
        return False


def _grid_ask(my_value: float) -> float:
    """Lowest grid point strictly above our cost, minus a cent.

    Rank-optimal, not money-optimal.  At cost 80 the money-maximising ask is 120
    (EV $20.0 against $15.0) but the rank-maximising ask is 100, worth +0.103
    percentile, because P(close) moves us across a 70% atom at zero and the size
    of the win barely moves us at all.  Verified identical at all three scales,
    so this never conditions on scale.
    """
    s = scale_of(my_value)
    base = my_value / s
    above = [b for b in GRID if b > base + 1e-9]
    if not above:
        return DEAD_CELL_ASK * s
    return min(above) * s - EPS


def _reject_with_counter(state: dict, i_am_seller: bool, my_value: float,
                         their_value: float) -> dict:
    """Reject, carrying our own counteroffer.

    Off the final round the server requires a rejection to name a counteroffer.
    If we omit it, ``actions._coerce_negotiation_decision`` supplies one -- and
    its fallback is OUR OWN VALUATION, which is the worst legal number on the
    board: it hands the counterparty the entire zone and leaves us exactly $0.
    A bare ``{"decision": "RejectOffer"}`` from this module therefore silently
    surrenders the very games the hold-out exists to win, so the price is named
    here or not at all.
    """
    out = {"decision": "RejectOffer"}
    rnd = _num(state.get("round"), 0.0)
    mr = _num(state.get("max_rounds"), math.inf)
    if state.get("horizon_known") is True and rnd >= mr:
        return out                      # final round: no counteroffer exists
    if math.isfinite(their_value):
        # Complete information: counter at our own terminal price. If they take
        # it early we capture the zone a round sooner, which is strictly better
        # than waiting; if they refuse we simply repeat it at the terminal node.
        span = abs(their_value - my_value)
        if span > 2 * EPS:
            price = (their_value - EPS) if i_am_seller else (their_value + EPS)
        else:
            price = (my_value + their_value) / 2.0
    else:
        price = _grid_ask(my_value) if i_am_seller else _grid_bid(my_value)
    out["product_price"] = round(price, 2)
    return out


def _grid_bid(my_value: float) -> float:
    """Highest grid point strictly below our value, plus a cent -- the buyer's
    mirror of :func:`_grid_ask`. Rank-optimal for the same reason: it maximises
    P(close) subject to leaving us a positive payoff."""
    s = scale_of(my_value)
    base = my_value / s
    below = [b for b in GRID if b < base - 1e-9]
    if not below:
        return max(0.0, my_value / 2.0)
    return max(below) * s + EPS


def action(game: dict) -> dict | None:
    """The move.  Returns None only if something is malformed, never a bad price."""
    c = cell(game)
    if c is None:
        return None
    horizon, complete, i_am_seller, my_value, their_value = c
    state = game.get("game_state") or {}
    phase = (game.get("valid_actions") or {}).get("type")

    if phase == "offer":
        if not complete:
            return {"product_price": round(_grid_ask(my_value), 2)}
        # Complete information: we own the terminal node, so take the zone and
        # leave one cent.  Priced off the opponent's visible value directly --
        # never off a share, a schedule or an estimate.
        seller_v = my_value if i_am_seller else their_value
        buyer_v = their_value if i_am_seller else my_value
        if buyer_v - seller_v <= 2 * EPS:      # degenerate zone: split it
            price = (seller_v + buyer_v) / 2.0
        elif i_am_seller:
            price = buyer_v - EPS
        else:
            price = seller_v + EPS
        return {"product_price": round(price, 2)}

    if phase == "decision":
        offered = _num((state.get("last_offer") or {}).get("price"))
        if not math.isfinite(offered):
            return {"decision": "RejectOffer"}
        gain = (offered - my_value) if i_am_seller else (my_value - offered)
        rnd = _num(state.get("round"), 0.0)
        mr = _num(state.get("max_rounds"), math.inf)
        final = state.get("horizon_known") is True and rnd >= mr
        if final:
            # Rejecting ends the game at $0.  Any positive cent beats that.
            return {"decision": "AcceptOffer" if gain > 0 else "RejectOffer"}
        if complete:
            span = abs(their_value - my_value)
            share = (gain / span) if span > 0 else 0.0
            # We hold out for our own terminal turn unless this already gives us
            # essentially the whole zone; the wait costs only the 0.57% chance
            # the opponent walks.
            if share >= HOLD_ACCEPT:
                return {"decision": "AcceptOffer"}
            return _reject_with_counter(state, i_am_seller, my_value, their_value)
        if gain > 0:
            return {"decision": "AcceptOffer"}
        return _reject_with_counter(state, i_am_seller, my_value, their_value)

    return None
