"""Negotiation (bilateral trade) — private valuations, alternating prices.

Seller payoff = price - seller_value; buyer payoff = buyer_value - price. There
is no inflation here, so the only pressure is the round cap: a no-deal pays both
sides $0, and on the final round a rejection simply ends the game.

Two ideas carry the strategy:

1. **Every offer the opponent makes leaks their valuation.** A buyer never
   offers above their maximum, and a seller never offers below their minimum, so
   each incoming price is a hard bound on the zone of agreement. Their
   concessions across rounds narrow it further.
2. **Concede on a Boulware schedule** — hold near the anchor while rounds are
   cheap, then drop fast toward the reservation as the deadline arrives. Ending
   at the reservation rather than past it means the agent never signs a losing
   deal, but always signs a winning one rather than taking $0.
"""

from __future__ import annotations

import os

from ..actions import _num, is_final_round

# Exponent on the concession curve. >1 holds firm early and concedes late, which
# extracts more from an opponent who concedes linearly.
_BOULWARE = 2.0


def _bound_as_floor_enabled() -> bool:
    """Whether the opponent's revealed bound raises our anchor instead of capping it.

    OFF by default so a restart cannot change live behaviour. Deployed per-agent
    by environment variable, which makes the rollout deliberate and gives the
    controlled comparison for free.
    """
    return os.environ.get("GLEE_NEGO_BOUND_AS_FLOOR", "").strip().lower() in (
        "1", "true", "yes", "on")


def _continuation_accept_enabled() -> bool:
    """Whether to accept on continuation value rather than on our own ask.

    OFF by default, and deliberately so. A live supervisor restarts agents from
    this source, so an ungated change deploys itself at whatever moment an agent
    happens to crash, on whichever agent crashes first -- an uncontrolled A/B
    nobody started. Gating it per-agent by environment variable makes the
    rollout a deliberate act and gives us the controlled comparison for free:
    set it on one agent, leave the rest as the control.

    Evidence so far is genuinely mixed. Replaying 716 live rejections of
    profitable offers, the new rule accepts 84% of them and would have rescued
    431 outcomes against 82 forgone (5.3:1). But a simulator sweep found no
    effect -- on a grid we have since discovered draws 63.7% configurations
    where no deal is possible at all, against ~100% in the live sample, which
    discredits the null rather than confirming it.
    """
    return os.environ.get("GLEE_NEGO_CONTINUATION_ACCEPT", "").strip().lower() in (
        "1", "true", "yes", "on")


def _rounds_left(state: dict, assumed_horizon: int) -> tuple[int, bool]:
    """(rounds remaining including this one, whether the cap is real).

    An uncapped game still needs a clock. Returning the planning horizon as a
    CONSTANT froze the concession schedule — the agent asked the same opening
    price on round 1 and on round 40, never conceded, and three quarters of
    negotiations died with no deal at zero. Count down against the planning
    horizon instead, so the schedule actually advances.
    """
    if state.get("horizon_known") is False or state.get("max_rounds") is None:
        current = int(_num(state.get("round"), 1))
        return max(1, assumed_horizon - current + 1), False
    remaining = int(_num(state.get("max_rounds"), 1)) - int(_num(state.get("round"), 1)) + 1
    return max(1, remaining), True


def _opponent_bound(state: dict, i_am_seller: bool) -> float | None:
    """Tightest bound on the opponent's valuation implied by their own offers.

    A buyer offering p proves buyer_value >= p; a seller offering p proves
    seller_value <= p. Take the most informative such offer in the history.
    """
    me = state.get("current_player")
    bound: float | None = None
    entries = state.get("history") or []
    prices = []
    for entry in entries:
        offer = (entry or {}).get("offer") or {}
        if offer.get("from_player") and offer.get("from_player") != me:
            price = offer.get("price")
            if price is not None:
                prices.append(_num(price))
        counter = (entry or {}).get("counteroffer")
        if isinstance(counter, dict) and counter.get("from_player") != me:
            if counter.get("price") is not None:
                prices.append(_num(counter["price"]))
    last = state.get("last_offer") or {}
    if last.get("from_player") and last.get("from_player") != me and last.get("price") is not None:
        prices.append(_num(last["price"]))
    if not prices:
        return None
    # As seller, the buyer's *highest* bid is the strongest lower bound on their
    # value; as buyer, the seller's *lowest* ask is the strongest upper bound.
    bound = max(prices) if i_am_seller else min(prices)
    return bound


def plan(game: dict, cfg) -> dict:
    state = game["game_state"]
    me = state.get("current_player") or game["your_player"]
    role = state.get(f"{me}_role") or ("seller" if game["your_player"] == "player_1" else "buyer")
    i_am_seller = role == "seller"
    my_value = _num(state.get(f"{me}_value"), 0.0)

    rounds_left, capped = _rounds_left(state, cfg.nego_assumed_horizon)
    horizon = max(1, int(_num(state.get("max_rounds"), cfg.nego_assumed_horizon)))
    # Fraction of the negotiation elapsed, 0 at the start and 1 at the deadline.
    elapsed = 1.0 - (rounds_left - 1) / max(1, horizon)
    elapsed = min(max(elapsed, 0.0), 1.0)

    anchor = my_value * (cfg.nego_seller_anchor if i_am_seller else cfg.nego_buyer_anchor)
    if not i_am_seller:
        anchor = min(anchor, my_value)     # never open above your own maximum

    bound = _opponent_bound(state, i_am_seller)
    if bound is not None:
        if _bound_as_floor_enabled():
            # A buyer never bids above their maximum, so their best bid is a
            # FLOOR on what they will pay — evidence to raise our ambition with,
            # never a reason to lower it. The reverse for a seller's lowest ask.
            if i_am_seller:
                anchor = max(anchor, bound)
            else:
                anchor = min(anchor, bound)
        else:
            # Legacy: treated their bid as a CEILING on what is achievable. That
            # inverts the inference — it lets an opponent set our price by
            # lowballing, and measured live it collapsed a configured 4.00x
            # anchor to 1.05x our own valuation, making the anchor knobs inert.
            if i_am_seller:
                anchor = max(my_value, min(anchor, max(bound * 1.6, my_value * 1.05)))
            else:
                anchor = min(my_value, max(anchor, min(bound * 0.6, my_value * 0.95)))

    # The valuation is a HARD floor: trading through it is worse than no deal.
    floor = my_value

    # But conceding all the way TO the floor earns nothing — a deal at your own
    # valuation pays exactly zero, which is payoff-identical to walking away.
    # Live data: 55% of closed negotiations landed on exactly 0.00, and where a
    # zone of agreement existed we captured a median 3.5% of it. So the
    # concession curve stops short, keeping a slice of whatever spread we opened.
    margin = min(max(cfg.nego_min_margin, 0.0), 0.9)
    reservation = floor + (anchor - floor) * margin

    # Boulware concession from anchor toward reservation.
    concession = elapsed ** _BOULWARE
    target = anchor + (reservation - anchor) * concession

    return {
        "role": role,
        "i_am_seller": i_am_seller,
        "my_value": my_value,
        "floor": floor,
        "anchor": anchor,
        "reservation": reservation,
        "target": target,
        "rounds_left": rounds_left,
        "capped": capped,
        "elapsed": elapsed,
        "opponent_bound": bound,
    }


def _their_offers(state: dict, me: str) -> list[tuple[int, float]]:
    """Every price the opponent has named, oldest first."""
    seen: list[tuple[int, float]] = []
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        for key in ("offer", "counteroffer"):
            off = entry.get(key)
            if isinstance(off, dict) and off.get("from_player") not in (None, me):
                if off.get("price") is not None:
                    seen.append((int(_num(entry.get("round"), 0)), _num(off["price"])))
    last = state.get("last_offer") or {}
    if last.get("from_player") not in (None, me) and last.get("price") is not None:
        entry = (int(_num(last.get("round"), 0)), _num(last["price"]))
        if entry not in seen:
            seen.append(entry)
    seen.sort()
    return seen


def _surplus(price: float, p: dict) -> float:
    """What this price is worth to us. Negative means it is worse than no deal."""
    return (price - p["my_value"]) if p["i_am_seller"] else (p["my_value"] - price)


def continuation_value(state: dict, p: dict, cfg) -> tuple[float, dict]:
    """Surplus a rejection is realistically worth.

    This replaces the rule that only accepted an offer beating our own current
    ask. The proposal schedule and the acceptance threshold are different
    objects: what we would *ask* for says nothing about whether a given offer
    beats walking on. Measured over 3,439 live decision points, the old rule
    turned down 716 profitable offers, of which 66% ended worse than the offer
    refused and 61% ended at zero — the mechanism behind a no-deal rate above 50%.

    Two things bound the estimate. The opponent's own concession trend says how
    much better their next offer plausibly gets; and the chance of closing at
    all decays as rounds run out, reaching zero on the final round where a
    rejection simply ends the game.
    """
    me = state.get("current_player") or ""
    rounds_left = max(1, int(p.get("rounds_left", 1)))
    # Survival: probability we still reach a deal by continuing. Zero with one
    # round left, rising toward the base rate with room to manoeuvre.
    survival = cfg.nego_deal_odds * (1.0 - 1.0 / rounds_left)

    offers = _their_offers(state, me)
    info: dict = {"offers_seen": len(offers), "survival": survival}

    if len(offers) < 2:
        # No trend yet. The best case is that they come to our current ask.
        best = max(0.0, _surplus(p["target"], p))
        info["basis"] = "no trend; our own target as the ceiling"
    else:
        (r0, x0), (r1, x1) = offers[0], offers[-1]
        span = max(1, r1 - r0)
        # Concession is movement in the direction that helps us.
        rate = ((x1 - x0) if p["i_am_seller"] else (x0 - x1)) / span
        if rate <= 0:
            # They are not moving. Rejecting buys the same offer, later.
            best = max(0.0, _surplus(x1, p))
            info.update(basis="opponent not conceding", rate=rate)
        else:
            steps = max(1, min(4, rounds_left - 1))
            projected = [x1 + rate * k if p["i_am_seller"] else x1 - rate * k
                         for k in range(1, steps + 1)]
            best = max([0.0] + [_surplus(x, p) for x in projected])
            info.update(basis="projected from concession trend", rate=rate)
        # Never project past what our own schedule would ever ask for.
        best = min(best, max(0.0, _surplus(p["anchor"], p)))

    value = best * survival
    info["projected_surplus"] = best
    info["continuation_value"] = value
    return value, info


def _profitable(price: float, p: dict) -> bool:
    """Strictly better than no deal. Equality earns zero, which is not."""
    return price > p["my_value"] if p["i_am_seller"] else price < p["my_value"]


def decide(game: dict, cfg) -> dict:
    state = game["game_state"]
    p = plan(game, cfg)

    if game["valid_actions"]["type"] == "offer":
        return {"product_price": round(p["target"], 2), "_plan": p}

    # --- decision phase ---
    offer_price = _num((state.get("last_offer") or {}).get("price"), 0.0)
    p["offered_price"] = offer_price
    final = is_final_round(state) or p["rounds_left"] <= 1

    if final:
        # Rejecting now ends the game at $0 for both. Take any profitable deal.
        if _profitable(offer_price, p):
            return {"decision": "AcceptOffer", "_plan": p}
        return {"decision": "RejectOffer", "_plan": p}

    surplus_now = _surplus(offer_price, p)
    v_cont, evidence = continuation_value(state, p, cfg)
    p["surplus_now"] = surplus_now
    p["continuation_value"] = v_cont
    p["continuation_evidence"] = evidence
    p["continuation_accept"] = _continuation_accept_enabled()

    if p["continuation_accept"]:
        # Accept when the offer beats what rejecting is worth. NOT when it beats
        # our own current ask — those are different questions, and conflating
        # them is what threw away 716 profitable offers.
        if _profitable(offer_price, p) and surplus_now >= v_cont:
            return {"decision": "AcceptOffer", "_plan": p}
    else:
        # Legacy rule, retained as the control arm.
        good_enough = ((offer_price >= p["target"]) if p["i_am_seller"]
                       else (offer_price <= p["target"]))
        if good_enough and _profitable(offer_price, p):
            return {"decision": "AcceptOffer", "_plan": p}

    counter = p["target"]
    if _profitable(offer_price, p):
        # Their offer already pays; the counter must stay on the profitable side
        # of it so a rejection can never turn a winning deal into a no-deal.
        counter = max(offer_price, counter) if p["i_am_seller"] else min(offer_price, counter)
    return {"decision": "RejectOffer", "product_price": round(counter, 2), "_plan": p}
