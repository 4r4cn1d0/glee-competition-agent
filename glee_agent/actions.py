"""Client-side validation and repair of actions.

The SDK does not retry a rejected move: it logs a warning, burns one of the five
per-game attempts, and leaves the turn clock running. So every action is repaired
into a legal shape *here*, before it reaches the wire.

``coerce`` is total — it always returns something the server will accept, falling
back to a conservative legal move rather than raising.
"""

from __future__ import annotations

import hashlib
import logging
import math

from . import runtime_flags

MAX_MESSAGE_LEN = 2000

BARGAINING_DECISIONS = {"accept", "reject", "walkaway"}
NEGOTIATION_DECISIONS = {"AcceptOffer", "RejectOffer", "WalkAway"}
YES_NO = {"yes", "no"}

logger = logging.getLogger("glee.actions")


class InvalidAction(Exception):
    """Raised internally when an action cannot be repaired; never escapes."""


def _num(value, default: float = 0.0) -> float:
    """Coerce anything model- or heuristic-shaped into a finite float."""
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(float(value)) else default
    if isinstance(value, str):
        cleaned = value.strip().replace("$", "").replace(",", "").replace("%", "")
        try:
            parsed = float(cleaned)
        except ValueError:
            return default
        return parsed if math.isfinite(parsed) else default
    return default


def _clean_message(action: dict, state: dict) -> None:
    """Trim an over-long message, and drop it entirely when the game forbids one.

    A message over 2,000 chars is an invalid move and costs an attempt.
    """
    msg = action.get("message")
    if msg is None:
        return
    if state.get("messages_allowed") is False:
        action.pop("message", None)
        return
    if not isinstance(msg, str):
        action.pop("message", None)
        return
    msg = msg.strip()
    if not msg:
        action.pop("message", None)
    elif len(msg) > MAX_MESSAGE_LEN:
        action["message"] = msg[: MAX_MESSAGE_LEN - 1].rstrip()
    else:
        action["message"] = msg


def _complete_negotiation_zopa(game: dict) -> tuple[float, float, bool] | None:
    """Return (seller cost, buyer value, whether we sell) when both are visible."""
    state = game.get("game_state") or {}
    if state.get("complete_information") is not True:
        return None

    seller = next((p for p in ("player_1", "player_2")
                   if state.get(f"{p}_role") == "seller"), None)
    buyer = next((p for p in ("player_1", "player_2")
                  if state.get(f"{p}_role") == "buyer"), None)
    if seller is None or buyer is None:
        return None

    seller_value = _num(state.get(f"{seller}_value"), math.nan)
    buyer_value = _num(state.get(f"{buyer}_value"), math.nan)
    if not math.isfinite(seller_value) or not math.isfinite(buyer_value):
        return None
    if buyer_value <= seller_value:
        return None

    me = state.get("current_player") or game.get("your_player")
    if me not in (seller, buyer):
        return None
    return seller_value, buyer_value, me == seller


def _open_claim_treatment(game: dict) -> tuple[float, float] | None:
    """Return (opening claim, claim floor) for an assigned treatment game.

    Hidden-information games return before either opponent role or value can be
    read.  Each non-finite or non-positive float is independently inert; when
    both are inert, or the game hashes to control, the existing price is kept.
    """
    state = game.get("game_state") or {}
    if state.get("complete_information") is not True:
        return None

    opening = runtime_flags.as_float("GLEE_NEGO_OPEN_CLAIM", 0.0)
    floor = runtime_flags.as_float("GLEE_NEGO_CLAIM_FLOOR", 0.0)
    opening = opening if math.isfinite(opening) and opening > 0.0 else 0.0
    floor = floor if math.isfinite(floor) and floor > 0.0 else 0.0
    if opening == 0.0 and floor == 0.0:
        return None

    gid = str(game.get("game_id") or "")
    if not gid:
        return None
    bit = int(hashlib.sha256(("open_claim|" + gid).encode()).hexdigest(), 16) & 1
    return (opening, floor) if bit else None


def _is_negotiation_opening(game: dict) -> bool:
    """Whether this is our first outgoing price in the game's visible record."""
    state = game.get("game_state") or {}
    me = state.get("current_player") or game.get("your_player")
    if me not in ("player_1", "player_2"):
        return False
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        for key in ("offer", "counteroffer"):
            prior = entry.get(key) or {}
            if isinstance(prior, dict) and prior.get("from_player") == me:
                return False
    last = state.get("last_offer") or {}
    if isinstance(last, dict) and last.get("from_player") == me:
        return False
    return True


def _apply_negotiation_price_guards(action: dict, game: dict) -> None:
    """Apply flagged complete-information postconditions to an outgoing price."""
    if "product_price" not in action:
        return
    # Hidden games have no visible ZOPA.  Return on the information marker before
    # `_complete_negotiation_zopa` can inspect either opponent role or value.
    if (game.get("game_state") or {}).get("complete_information") is not True:
        return
    zopa = _complete_negotiation_zopa(game)
    if zopa is None:
        return

    seller_value, buyer_value, i_am_seller = zopa
    span = buyer_value - seller_value
    price = _num(action["product_price"])
    ult_bounds = None

    # When ULT_FLOOR is positive, every complete-information one-round proposal
    # is placed inside [ULT_FLOOR, ULT_CAP] as our share of the visible span.
    # At 0.72 this moves the measured <45% cluster (n=154, percentile .484) into
    # the 70-85% band (245/245 closed, percentile .787). The 0.85 default is read
    # only inside this default-off gate: 85-100% is unmeasured and >=100% closed
    # 0/69.
    ult_floor = runtime_flags.as_float("GLEE_NEGO_ULT_FLOOR", 0.0)
    one_round_offer = ((game.get("valid_actions") or {}).get("type") == "offer"
                       and _num((game.get("game_state") or {}).get("max_rounds"), 0.0)
                       == 1.0)
    if math.isfinite(ult_floor) and ult_floor > 0.0 and one_round_offer:
        ult_cap = runtime_flags.as_float("GLEE_NEGO_ULT_CAP", 0.85)
        if not math.isfinite(ult_cap):
            ult_cap = 0.85
        ult_cap = min(max(ult_cap, 0.0), 1.0)
        ult_floor = min(max(ult_floor, 0.0), ult_cap)
        share = ((price - seller_value) / span if i_am_seller
                 else (buyer_value - price) / span)
        share = min(max(share, ult_floor), ult_cap)
        price = (seller_value + share * span if i_am_seller
                 else buyer_value - share * span)
        ult_bounds = (ult_floor, ult_cap)

    price = max(0.0, round(price, 2))
    # Rounding can move a fractional-boundary ask back outside the configured
    # share interval, so the interval is re-applied to the literal wire number.
    if ult_bounds is not None:
        ult_floor, ult_cap = ult_bounds
        share = ((price - seller_value) / span if i_am_seller
                 else (buyer_value - price) / span)
        if share < ult_floor:
            price = (seller_value + ult_floor * span if i_am_seller
                     else buyer_value - ult_floor * span)
        elif share > ult_cap:
            price = (seller_value + ult_cap * span if i_am_seller
                     else buyer_value - ult_cap * span)

    # COMPLETE-INFORMATION OPEN-CLAIM A/B.  Against seven ranked opponents, the
    # agents above 2195 opened at 0.92-1.05 of visible ZOPA and ended at 0.82-0.93;
    # our corresponding levels were 0.681 and 0.581.  Across 1,612 complete-info
    # games the field median moved 0.900 -> 0.657 and 58% conceded over 0.05, so
    # treatment games set each seat's first outgoing price to OPEN_CLAIM
    # and keep every later outgoing offer at or above CLAIM_FLOOR.  Both knobs use
    # the same per-game `open_claim|` hash; control games keep the prior wire price.
    # This postcondition runs after strategy/LLM decisions and only sees an emitted
    # product_price, so it cannot change an accept/reject threshold.  Any affected
    # price is clamped into the visible ZOPA; this prevents the guaranteed zero
    # seen with the measured 84.2% impossible-offer rate on one agent.
    claim = _open_claim_treatment(game)
    if claim is not None:
        opening_claim, claim_floor = claim
        affected = False
        if opening_claim > 0.0 and _is_negotiation_opening(game):
            price = (seller_value + opening_claim * span if i_am_seller
                     else buyer_value - opening_claim * span)
            affected = True

        floor_price = None
        if claim_floor > 0.0:
            floor_price = (seller_value + claim_floor * span if i_am_seller
                           else buyer_value - claim_floor * span)
            price = (max(price, floor_price) if i_am_seller
                     else min(price, floor_price))
            affected = True

        if affected:
            price = max(0.0, round(price, 2))
            # Reapply a fractional floor after cent rounding so the literal wire
            # number never gives us less than the requested share.
            if floor_price is not None:
                price = (max(price, floor_price) if i_am_seller
                         else min(price, floor_price))
            price = min(max(price, seller_value), buyer_value)

    # This is the final numeric postcondition in coerce(), after cent rounding.
    # With the clamp armed, the seller never submits above the visible buyer value
    # and the buyer never submits below the visible seller cost. It repairs the
    # 727/2,800 measured complete-info games containing an impossible offer;
    # hidden games returned above before either bound is read, so their probing
    # prices are unchanged.
    if runtime_flags.enabled("GLEE_NEGO_ZOPA_CLAMP"):
        price = min(price, buyer_value) if i_am_seller else max(price, seller_value)

    action["product_price"] = price


def _split_exactly(my_gain: float, money: float) -> tuple[float, float]:
    """Return (my_gain, other_gain) summing to ``money`` under float arithmetic.

    The server requires the two gains to sum to ``money_to_divide`` exactly, so
    the partner share is *derived* rather than rounded independently. Integer
    pots stay integral, which sidesteps float representation entirely.
    """
    my_gain = min(max(my_gain, 0.0), money)
    if float(money).is_integer():
        mine = float(round(my_gain))
        mine = min(max(mine, 0.0), money)
        return mine, float(money) - mine
    mine = round(my_gain, 2)
    other = round(money - mine, 2)
    if mine + other != money:          # residual from the rounding
        other = money - mine
    return mine, other


def coerce(action, game: dict) -> dict:
    """Repair ``action`` into a legal move for the game's current phase."""
    state = game.get("game_state") or {}
    family = game.get("game_family")
    action_type = (game.get("valid_actions") or {}).get("type")

    if not isinstance(action, dict):
        logger.warning("Non-dict action %r; using safe fallback", action)
        out = safe_action(game)
    else:
        action = dict(action)
        try:
            if action_type == "offer" and family == "bargaining":
                out = _coerce_bargaining_offer(action, game)
            elif action_type == "offer" and family == "negotiation":
                out = _coerce_negotiation_offer(action, state)
            elif action_type == "decision" and family == "bargaining":
                out = _coerce_bargaining_decision(action)
            elif action_type == "decision" and family == "negotiation":
                out = _coerce_negotiation_decision(action, state)
            elif action_type in ("seller_recommendation", "buyer_decision"):
                out = _coerce_yes_no(action)
            elif action_type == "seller_message":
                out = _coerce_seller_message(action)
            else:
                logger.warning("Unknown action type %r; using safe fallback", action_type)
                out = safe_action(game)
        except InvalidAction as exc:
            logger.warning("Could not repair action %r (%s); using safe fallback", action, exc)
            out = safe_action(game)

    if family == "negotiation":
        try:
            _apply_negotiation_price_guards(out, game)
        except Exception:
            # A failed live flag read or malformed guard input falls back to our
            # own valuation, which is a legal visible-ZOPA boundary, rather than
            # escaping the dispatcher and submitting nothing.
            logger.exception("Negotiation price guard failed; using safe fallback")
            out = safe_action(game)
            if (game.get("valid_actions") or {}).get("type") == "offer":
                me = state.get("current_player") or game.get("your_player") or ""
                own_value = _num(state.get(f"{me}_value"), math.nan)
                if math.isfinite(own_value):
                    # Sub-cent prices are legal; keeping the exact valuation
                    # prevents fallback rounding from crossing a narrow ZOPA.
                    out["product_price"] = max(0.0, own_value)
    _clean_message(out, state)
    return out


def _coerce_bargaining_offer(action: dict, game: dict) -> dict:
    state = game.get("game_state") or {}
    money = _num(state.get("money_to_divide"), 0.0)
    if money <= 0:
        raise InvalidAction("money_to_divide missing")

    me_is_alice = game.get("your_player") == "player_1"
    # Accept either naming; a model given the state often echoes player_N keys.
    alice = action.get("alice_gain", action.get("player_1_gain"))
    bob = action.get("bob_gain", action.get("player_2_gain"))

    if alice is None and bob is None:
        raise InvalidAction("no gains proposed")
    if alice is None:
        alice = money - _num(bob)
    if bob is None:
        bob = money - _num(alice)

    my_gain = _num(alice) if me_is_alice else _num(bob)
    mine, theirs = _split_exactly(my_gain, money)
    out = {"alice_gain": mine if me_is_alice else theirs,
           "bob_gain": theirs if me_is_alice else mine}
    if "message" in action:
        out["message"] = action["message"]
    return out


def _coerce_negotiation_offer(action: dict, state: dict) -> dict:
    price = action.get("product_price", action.get("price"))
    if price is None:
        raise InvalidAction("no price proposed")
    out = {"product_price": max(0.0, round(_num(price), 2))}
    if "message" in action:
        out["message"] = action["message"]
    return out


def _coerce_bargaining_decision(action: dict) -> dict:
    raw = str(action.get("decision", "")).strip().lower().replace(" ", "").replace("_", "")
    alias = {"acceptoffer": "accept", "rejectoffer": "reject", "walkaway": "walkaway",
             "yes": "accept", "no": "reject", "quit": "walkaway"}
    decision = raw if raw in BARGAINING_DECISIONS else alias.get(raw, "")
    if not decision:
        raise InvalidAction(f"unrecognised decision {action.get('decision')!r}")
    out = {"decision": decision}
    if "message" in action:
        out["message"] = action["message"]
    return out


def _coerce_negotiation_decision(action: dict, state: dict) -> dict:
    raw = str(action.get("decision", "")).strip().lower().replace(" ", "").replace("_", "")
    alias = {"accept": "AcceptOffer", "acceptoffer": "AcceptOffer", "yes": "AcceptOffer",
             "reject": "RejectOffer", "rejectoffer": "RejectOffer", "no": "RejectOffer",
             "counter": "RejectOffer", "counteroffer": "RejectOffer",
             "walkaway": "WalkAway", "walk": "WalkAway", "quit": "WalkAway"}
    decision = alias.get(raw, "")
    if not decision:
        raise InvalidAction(f"unrecognised decision {action.get('decision')!r}")

    out: dict = {"decision": decision}
    if decision == "RejectOffer" and not is_final_round(state):
        # Off the final round a rejection must carry a counteroffer; without one
        # the move is invalid. Fall back to repeating our own valuation.
        price = action.get("product_price", action.get("price"))
        if price is None:
            me = state.get("current_player", "")
            price = state.get(f"{me}_value")
        if price is None:
            raise InvalidAction("rejection without a counteroffer")
        out["product_price"] = max(0.0, round(_num(price), 2))
    if "message" in action:
        out["message"] = action["message"]
    return out


def _coerce_yes_no(action: dict) -> dict:
    raw = str(action.get("decision", action.get("buy", ""))).strip().lower()
    alias = {"yes": "yes", "y": "yes", "true": "yes", "buy": "yes", "recommend": "yes",
             "accept": "yes", "no": "no", "n": "no", "false": "no", "pass": "no",
             "decline": "no", "reject": "no"}
    decision = alias.get(raw, "")
    if not decision:
        raise InvalidAction(f"unrecognised decision {action.get('decision')!r}")
    return {"decision": decision}


def _coerce_seller_message(action: dict) -> dict:
    msg = action.get("message")
    if not isinstance(msg, str) or not msg.strip():
        raise InvalidAction("empty seller message")
    return {"message": msg}


def is_final_round(state: dict) -> bool:
    """True when this is the last round of a capped game (no counteroffer exists)."""
    max_rounds = state.get("max_rounds")
    if max_rounds is None:
        return False           # uncapped game: there is always a next round
    return _num(state.get("round"), 1) >= _num(max_rounds, 1)


def safe_action(game: dict) -> dict:
    """A guaranteed-legal conservative move for the current phase.

    Used whenever a strategy fails, an LLM reply is unusable, or an action
    cannot be repaired. Every branch is a move the server accepts; burning one
    move on a mediocre-but-legal action beats burning the 120s turn clock.
    """
    state = game.get("game_state") or {}
    family = game.get("game_family")
    action_type = (game.get("valid_actions") or {}).get("type")

    if action_type == "offer":
        if family == "bargaining":
            money = _num(state.get("money_to_divide"), 0.0)
            mine, theirs = _split_exactly(money / 2, money)
            me_is_alice = game.get("your_player") == "player_1"
            return {"alice_gain": mine if me_is_alice else theirs,
                    "bob_gain": theirs if me_is_alice else mine}
        me = state.get("current_player", game.get("your_player", ""))
        return {"product_price": max(0.0, round(_num(state.get(f"{me}_value"), 1.0), 2))}

    if action_type == "seller_message":
        return {"message": "I recommend this product."}
    if action_type in ("seller_recommendation", "buyer_decision"):
        return {"decision": "yes"}

    # A decision phase. Accepting is the safe default: a no-deal pays $0, which
    # scores at the bottom of the percentile scale.
    if family == "bargaining":
        return {"decision": "accept"}
    return {"decision": "AcceptOffer"}
