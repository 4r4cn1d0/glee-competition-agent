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

from . import pricing, runtime_flags

MAX_MESSAGE_LEN = 2000

# Hidden negotiation values are the public four-point research grid.  The live
# 22-cell joint support is a repository reconstruction, not an organizer-published
# fact, so the policy that uses it stays inside a default-off randomized arm.
_HIDDEN_VALUE_MULTS = (0.8, 1.0, 1.2, 1.5)
_HIDDEN_POLICY_OPEN_CLAIM = 0.85
_HIDDEN_POLICY_FLOOR_CLAIM = 0.75
_HIDDEN_POLICY_SALT = "hidden_policy_v1|"
_HIDDEN_POLICY_BOULWARE = 2.0
_HIDDEN_POLICY_UNCAPPED_STEPS = 5
_HIDDEN_POLICY_UNCAPPED_PROGRESS_CAP = 0.85

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


def _hidden_floor_treatment(game: dict) -> tuple[float, float, bool] | None:
    """Return (floor multiple, base, whether we sell) for a treatment game.

    Only an explicit hidden-information marker is eligible.  The base is
    recovered from our own visible value; no opponent value is consulted.
    Invalid settings, off-grid values, missing ids, and hash-control games keep
    the existing outgoing price.
    """
    state = game.get("game_state") or {}
    if state.get("complete_information") is not False:
        return None

    floor = runtime_flags.as_float("GLEE_NEGO_HIDDEN_FLOOR", 0.0)
    if not math.isfinite(floor) or floor <= 0.0 or floor > 2.0:
        return None

    gid = str(game.get("game_id") or "")
    if not gid:
        return None
    bit = int(hashlib.sha256(("hidden_floor|" + gid).encode()).hexdigest(), 16) & 1
    if not bit:
        return None

    me = game.get("your_player") or state.get("current_player")
    role = state.get(f"{me}_role")
    if role not in ("seller", "buyer"):
        return None
    my_value = _num(state.get(f"{me}_value"), math.nan)
    if not math.isfinite(my_value):
        return None
    base = pricing.infer_base(my_value)
    if base is None:
        return None
    return floor, base, role == "seller"


def _hidden_policy_context(game: dict) -> dict | None:
    """Return the armed hidden-policy assignment, including hash controls.

    ``None`` means the new policy is off or the information regime is outside
    its scope.  An armed but ineligible context is returned as ``eligible=False``
    so this policy owns the hidden price path and cannot be mixed with the older
    flat HIDDEN_FLOOR arm if both flags are set accidentally.
    """
    state = game.get("game_state") or {}
    if state.get("complete_information") is not False:
        return None
    if not runtime_flags.enabled("GLEE_NEGO_HIDDEN_POLICY_V1"):
        return None

    context = {"eligible": False}
    gid = str(game.get("game_id") or "")
    me = game.get("your_player") or state.get("current_player")
    role = state.get(f"{me}_role")
    my_value = _num(state.get(f"{me}_value"), math.nan)
    base = pricing.infer_base(my_value) if math.isfinite(my_value) else None
    if not gid or role not in ("seller", "buyer") or base is None:
        return context

    own_mult = next(
        (m for m in _HIDDEN_VALUE_MULTS
         if abs(my_value / base - m) <= 1e-6),
        None,
    )
    if own_mult is None:
        return context

    # A one-round offer is a terminal posted-price problem, not an opening that
    # can screen types over a concession path.  Seller 1.5B and buyer 0.8B have
    # no strictly positive-ZOPA type under the reconstructed grid; DEADGAME_V1
    # already owns those cells.
    max_rounds = state.get("max_rounds")
    if max_rounds is not None and _num(max_rounds, math.nan) == 1.0:
        return context
    feasible = [
        m for m in _HIDDEN_VALUE_MULTS
        if (m > own_mult + 1e-9 if role == "seller"
            else m < own_mult - 1e-9)
    ]
    if not feasible:
        return context

    bit = int(hashlib.sha256((_HIDDEN_POLICY_SALT + gid).encode()).hexdigest(), 16) & 1
    return {
        "eligible": True,
        "treatment": bool(bit),
        "base": base,
        "my_value": my_value,
        "own_mult": own_mult,
        "feasible": tuple(feasible),
        "i_am_seller": role == "seller",
    }


def _hidden_opponent_prices(state: dict, me: str) -> list[float]:
    """Finite prices named by the opponent, without reading their hidden value."""
    prices: list[float] = []
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        for key in ("offer", "counteroffer"):
            offer = entry.get(key)
            if (isinstance(offer, dict)
                    and offer.get("from_player") not in (None, me)):
                price = _num(offer.get("price"), math.nan)
                if math.isfinite(price):
                    prices.append(price)
    last = state.get("last_offer") or {}
    if (isinstance(last, dict)
            and last.get("from_player") not in (None, me)):
        price = _num(last.get("price"), math.nan)
        if math.isfinite(price):
            prices.append(price)
    return prices


def _hidden_own_price_count(state: dict, me: str) -> int:
    """Number of our prior price utterances, collapsing the record echo."""
    prices: list[float] = []
    previous_key = None
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        for key in ("offer", "counteroffer"):
            offer = entry.get(key)
            if (not isinstance(offer, dict) or offer.get("from_player") != me
                    or offer.get("price") is None):
                continue
            price = _num(offer["price"], math.nan)
            if not math.isfinite(price):
                continue
            if (key == "offer" and previous_key == "counteroffer"
                    and prices and price == prices[-1]):
                previous_key = key
                continue
            prices.append(price)
            previous_key = key
    return len(prices)


def _hidden_policy_progress(state: dict, me: str, i_am_seller: bool) -> float:
    """Squared concession progress for this outgoing price opportunity."""
    index = _hidden_own_price_count(state, me)
    max_rounds = state.get("max_rounds")
    if max_rounds is None:
        linear = min(
            index / _HIDDEN_POLICY_UNCAPPED_STEPS,
            _HIDDEN_POLICY_UNCAPPED_PROGRESS_CAP,
        )
    else:
        horizon = max(1, int(_num(max_rounds, 1.0)))
        opportunities = ((horizon + 1) // 2 if i_am_seller else horizon // 2)
        linear = (index / (opportunities - 1)
                  if opportunities > 1 else 0.0)
        linear = min(max(linear, 0.0), 1.0)
    return linear ** _HIDDEN_POLICY_BOULWARE


def _hidden_policy_prices(game: dict, context: dict) -> tuple[float, float, float]:
    """Return scheduled price, credible opening, and current floor/cap.

    The opening claims 85% of the largest support-compatible zone.  The
    concession boundary claims 75% of the smallest still-compatible positive
    zone.  Opponent prices can only harden that boundary when they cross a grid
    point that a rational type could not cross; concession speed is never read.
    A squared path runs over this interval by our outgoing-offer index, rather
    than clipping the old 4x/0.15x curve whose scale is seat-asymmetric.
    """
    state = game.get("game_state") or {}
    me = game.get("your_player") or state.get("current_player")
    base = context["base"]
    my_value = context["my_value"]
    feasible = context["feasible"]
    i_am_seller = context["i_am_seller"]

    extreme = max(feasible) if i_am_seller else min(feasible)
    extreme_value = extreme * base
    opening = (my_value + _HIDDEN_POLICY_OPEN_CLAIM * (extreme_value - my_value)
               if i_am_seller else
               my_value - _HIDDEN_POLICY_OPEN_CLAIM * (my_value - extreme_value))

    # The nearest positive-ZOPA type sets the prior boundary.  A best opponent
    # bid/ask supplies a one-sided rational bound: buyer bid <= buyer value;
    # seller ask >= seller cost.  Out-of-support prices are preserved as offers
    # below, but do not manufacture a type inference outside the known grid.
    compatible = min(feasible) if i_am_seller else max(feasible)
    opponent_prices = _hidden_opponent_prices(state, me)
    best = ((max(opponent_prices) if i_am_seller else min(opponent_prices))
            if opponent_prices else None)
    if best is not None:
        bound = best / base
        if i_am_seller and bound <= max(_HIDDEN_VALUE_MULTS) + 1e-9:
            possible = [m for m in feasible if m + 1e-9 >= bound]
            if possible:
                compatible = max(compatible, min(possible))
        elif not i_am_seller and bound >= min(_HIDDEN_VALUE_MULTS) - 1e-9:
            possible = [m for m in feasible if m <= bound + 1e-9]
            if possible:
                compatible = min(compatible, max(possible))

    compatible_value = compatible * base
    boundary = (
        my_value + _HIDDEN_POLICY_FLOOR_CLAIM * (compatible_value - my_value)
        if i_am_seller else
        my_value - _HIDDEN_POLICY_FLOOR_CLAIM * (my_value - compatible_value)
    )

    # Never counter with a price worse for us than one the opponent already
    # named.  This changes the ambitious end of the interval, not its floor.
    if best is not None:
        opening = max(opening, best) if i_am_seller else min(opening, best)
    progress = _hidden_policy_progress(state, me, i_am_seller)
    scheduled = opening + (boundary - opening) * progress
    if best is not None:
        scheduled = max(scheduled, best) if i_am_seller else min(scheduled, best)
    return scheduled, opening, boundary


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
    """Apply flagged information-regime postconditions to an outgoing price."""
    if "product_price" not in action:
        return
    state = game.get("game_state") or {}

    # HIDDEN POLICY V1 A/B.  In 319 selected hidden no-deals our opening demand
    # was 3.97x our own limit versus 1.54x for opponents, yet both paths ended at
    # 1.17x/1.13x.  In 3,104 hidden closes our median reconstructed-zone share
    # was 0.520 while top-rated agents were near 0.75, and the field's recent
    # claimed share reached 0.830.  Candidate games therefore replace every
    # multi-round outgoing price with a squared Boulware path from an on-support
    # 0.85 opening to a 0.75 boundary for the narrowest feasible grid type.
    # Capped progress is indexed by our actual price opportunities, so both seats
    # reach the boundary on their last H=10 price opportunity.  In an uncapped
    # game the linear clock caps at 0.85, so the squared path concedes at most
    # 72.25% of the opening-to-boundary distance because there is no real deadline.
    # Opponent prices can harden the boundary only by crossing a rational
    # grid-value bound; their concession rate is not used.
    #
    # This runs after strategy/LLM choice and only when product_price exists, so
    # AcceptOffer/RejectOffer selection and every acceptance input are unchanged.
    # The 0.85/0.75 values are unproved and are tested only through the independent
    # `hidden_policy_v1|` game hash.  When the new flag is armed it owns both hash
    # arms and suppresses the older flat HIDDEN_FLOOR path, preventing a mixed
    # control if both flags are set accidentally.
    policy = _hidden_policy_context(game)
    if policy is not None:
        if policy.get("eligible") and policy.get("treatment"):
            price, opening, boundary = _hidden_policy_prices(game, policy)
            price = max(0.0, round(price, 2))
            # Reapply both literal wire bounds after cent rounding.
            if policy["i_am_seller"]:
                price = max(min(price, opening), boundary)
            else:
                price = min(max(price, opening), boundary)
            action["product_price"] = price
        return

    # HIDDEN-INFORMATION FLOOR A/B.  Over 30h our seller path moved from 2.624B
    # in rounds 1-3 to 1.375B at round 10+, while counterparty buyer bids moved
    # 1.630B to 1.449B; our buyer path moved 0.251B to 0.979B while counterparty
    # seller asks moved 0.729B to 0.826B.  In assigned treatment games this final
    # wire postcondition keeps seller prices at or above floor*B and buyer prices
    # at or below (2-floor)*B.  The buyer expression is the additive reflection
    # around B: floor=1.15 protects the same 0.15B distance on each side (seller
    # >=1.15B, buyer <=0.85B).
    # It runs only after a product_price exists, so AcceptOffer/RejectOffer choice
    # and every acceptance input are unchanged.  Complete-information games take
    # the separate OPEN_CLAIM/CLAIM_FLOOR path below, and B comes only from our
    # visible value through pricing.infer_base.
    hidden = _hidden_floor_treatment(game)
    if hidden is not None:
        floor, base, i_am_seller = hidden
        protected = (floor * base if i_am_seller else (2.0 - floor) * base)
        price = _num(action["product_price"])
        price = max(price, protected) if i_am_seller else min(price, protected)
        price = max(0.0, round(price, 2))
        # Reapply after cent rounding so the literal wire price cannot cross a
        # fractional configured boundary in the conceding direction.
        price = max(price, protected) if i_am_seller else min(price, protected)
        action["product_price"] = price
        return

    # Hidden/control games have no visible ZOPA.  Return on the information
    # marker before `_complete_negotiation_zopa` can inspect an opponent value.
    if state.get("complete_information") is not True:
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
