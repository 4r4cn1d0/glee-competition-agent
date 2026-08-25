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

import math

from .. import (deterministic_negotiation, first_principles, nego_arms, pricing,
                runtime_flags, top_buyer_clone, top_buyer_clone_hi_cap10,
                top_opus_buyer_clone,
                top_opus_buyer_clone_hi_unknown,
                top_seller_message_clone)
from .. import table_policy

from ..actions import _num, coerce, is_final_round

# Exponent on the concession curve. >1 holds firm early and concedes late, which
# extracts more from an opponent who concedes linearly.
_BOULWARE = 2.0

# Default-off deterministic safety hypothesis for the complete-information,
# explicitly unknown-horizon cell.  The round/cycle constants were selected
# post hoc and therefore must not be activated as if they were causal results.
COMPLETE_UNKNOWN_LATE_STASIS_FLAG = (
    "GLEE_NEGO_COMPLETE_UNKNOWN_LATE_STASIS_V1"
)
COMPLETE_UNKNOWN_LATE_STASIS_MIN_ROUND = 75
COMPLETE_UNKNOWN_LATE_STASIS_CYCLES = 10

# The measured cohort used the exact current stack.  Refuse a mixed/randomized
# policy so a future activation cannot silently become a renamed version of an
# older arm or an unanalysed factorial treatment.
_COMPLETE_UNKNOWN_LATE_STASIS_CONFLICTS = (
    "GLEE_NEGO_CLOSE_AB",
    "GLEE_NEGO_FIRST_PRINCIPLES",
    "GLEE_NEGO_FP_ALWAYS",
    "GLEE_NEGO_HIDDEN_FLOOR",
    "GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB",
    "GLEE_NEGO_HIDDEN_POLICY_V1",
    "GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB",
    "GLEE_NEGO_HI_CAP10_BUYER_CURVE_AB",
    "GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB",
    "GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB",
    "GLEE_NEGO_PROBE_V1",
    "GLEE_NEGO_MSG_ARMS",
    "GLEE_NEGO_RANK_PRICE_AB",
    "GLEE_NEGO_RECIP_DAMP",
    "GLEE_NEGO_SPLIT_CANDIDATE",
    "GLEE_NEGO_STALL_CURRENT_BREAK_AB",
    "GLEE_NEGO_SURPLUS_PROBE",
    "GLEE_NEGO_TABLE_VCONT_PRECEDENCE_AB",
    "GLEE_NEGO_TOP_ATHENA_BUYER_CLONE_AB",
    "GLEE_NEGO_TOP_BUYER_CLONE_AB",
    "GLEE_NEGO_TOP_BUYER_CLONE_HI_CAP10_AB",
    "GLEE_NEGO_TOP_OPUS_BUYER_CLONE_AB",
    "GLEE_NEGO_TOP_OPUS_BUYER_CLONE_HI_UNKNOWN_AB",
    "GLEE_NEGO_TOP_SELLER_MESSAGE_CLONE_AB",
    "GLEE_NEGO_UNCAPPED_AB",
    "GLEE_NEGO_ZOPA_AB",
    "GLEE_NEGO_ZOPA_CLAMP",
)


def _split_candidate_enabled() -> bool:
    """Whether to propose split-the-difference when it dominates our schedule.

    Field evidence across used cars, insurance, housing and eBay (Keniston,
    Larsen, Li, Prescott, Silveira & Yu, Intl. Economic Review 65(4), 2024)
    finds offers at the midpoint of the two most recent prices are accepted
    disproportionately often — a focal point a smooth concession curve can
    never land on. Only the DOMINANT case is taken: the midpoint must be at
    least as good for us as our own scheduled target, so this can raise
    acceptance but never concede a cent beyond schedule. OFF by default.
    """
    return runtime_flags.enabled("GLEE_NEGO_SPLIT_CANDIDATE")


def _our_last_price(state: dict, me: str) -> float | None:
    """The price we most recently put on the table, if any."""
    last = None
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        for key in ("offer", "counteroffer"):
            off = entry.get(key)
            if isinstance(off, dict) and off.get("from_player") == me:
                if off.get("price") is not None:
                    last = _num(off["price"])
    return last


def _maybe_split(state: dict, p: dict, price: float) -> float:
    """Take the midpoint of the two most recent prices when it dominates."""
    if not _split_candidate_enabled():
        return price
    me = state.get("current_player") or ""
    ours = _our_last_price(state, me)
    theirs = (state.get("last_offer") or {}).get("price")
    if ours is None or theirs is None:
        return price
    split = (ours + _num(theirs)) / 2.0
    # Dominant case only: the focal midpoint must be no worse for us than the
    # scheduled price, and still strictly profitable.
    if _surplus(split, p) <= 0:
        return price
    if p["i_am_seller"] and split >= price:
        return split
    if not p["i_am_seller"] and split <= price:
        return split
    return price


def _horizon_v2_enabled() -> bool:
    """Whether to use the corrected horizon / ZOPA / margin logic.

    OFF by default. These three changes are unflagged code by nature — they
    would apply to every agent on its next restart, including the controls, and
    three agents are currently mid-ban and will restart automatically. One of
    them is also known-imperfect: it clamps the target to the EDGE of the zone
    of agreement, leaving the opponent zero surplus, which the measured 0.39
    acceptance cliff says gets rejected. Gating keeps the controls clean and
    stops a ban lifting into an untested policy.
    """
    return runtime_flags.enabled("GLEE_NEGO_HORIZON_V2")


def other_player(me: str) -> str:
    return "player_2" if me == "player_1" else "player_1"


def _trace_enabled() -> bool:
    """Whether plan()/decide() record ``plan["gates_fired"]``.

    Pure instrumentation, OFF by default. Each gate already leaves its own
    fingerprint boolean; this unifies them into one ordered list — the firing
    ORDER is what debugging gate-override bugs needs (which gate set the target
    last, which one it overrode). With the flag off the plan dict is
    byte-identical to before this existed: the key is never present, and no
    gate reads the list, so it can never change an action either way.
    """
    return runtime_flags.enabled("GLEE_TRACE_GATES")


def _gate(p: dict, name: str) -> None:
    """Record that ``name`` changed the pending target/decision this turn."""
    g = p.get("gates_fired")
    if g is not None:
        g.append(name)


def _bound_as_floor_enabled() -> bool:
    """Whether the opponent's revealed bound raises our anchor instead of capping it.

    OFF by default so a restart cannot change live behaviour. Deployed per-agent
    by environment variable, which makes the rollout deliberate and gives the
    controlled comparison for free.
    """
    return runtime_flags.enabled("GLEE_NEGO_BOUND_AS_FLOOR")


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
    return runtime_flags.enabled("GLEE_NEGO_CONTINUATION_ACCEPT")


def _their_stall_price(state: dict, me: str):
    """The opponent's price if their last 3+ offers moved <=1% of scale, else None.

    Measured on 6,540 deduped games (workflow nego-regime-evidence, verified):
    44% of uncapped and 19% of capped multi-round games feature a stalling
    opponent; we kept conceding into stalls ~74% of the time, 70% of stalled
    games die at 0/0, and in uncapped stalls the concessions earn nothing.
    """
    other = "player_2" if me == "player_1" else "player_1"
    theirs = [float((r.get("offer") or {}).get("price"))
              for r in state.get("history") or []
              if (r.get("offer") or {}).get("from_player") == other
              and (r.get("offer") or {}).get("price") is not None]
    if len(theirs) < 3:
        return None
    recent = theirs[-3:]
    scale = max(abs(x) for x in recent) or 1.0
    if max(recent) - min(recent) <= 0.01 * scale:
        return recent[-1]
    return None


STALL_CURRENT_BREAK_SALT = "nego_stall_current_break_v1|"

# The validated competition support is {0.8, 1.0, 1.2, 1.5} * B.  Therefore
# our own type identifies the smallest strictly-positive feasible ZOPA even
# though it does not identify the opponent's type.  Forty percent is deliberately
# conservative relative to the 0.610 shoulder in our completed-deal distribution:
# in the current five-slot corpus, 1,473 nonfinal hidden offers that the policy
# accepted paid less than this bound (1,243 through continuation/stall after the
# table said "below", plus 230 direct table accepts).  Of 479 locally recovered
# finals, 474 captured strictly under 40% of the realised surplus; the other five
# were two exact-boundary float artefacts and three irrational negative-payoff
# opponent offers.  The causal value of HOLDING is not identified by those
# selected agreements, so the behavior remains a per-game randomized arm.
HIDDEN_MIN_SHARE_VETO_SALT = "nego_hidden_min_share_veto_v1|"
HIDDEN_MIN_SHARE_VETO_FRACTION = 0.40

# TABLE currently returns before the state-dependent continuation comparator.
# In the latest 100,000 Test 3 turns, 76 first-eligible games (about 25.5 per
# 1,000 negotiation games) had three distinct improving opponent prices, a
# direct TABLE acceptance outside the support-minimum veto, and an existing
# continuation value above the offered surplus.  Completed outcomes cannot tell
# us whether one more counter is worth risking the guaranteed deal, so this is
# a per-game randomized precedence test rather than a fitted policy change.
TABLE_VCONT_PRECEDENCE_SALT = "nego_table_vcont_precedence_v1|"
TABLE_VCONT_REQUIRED_FINAL_OPTION = 0.60


def stall_current_break_assignment(game_id) -> bool | None:
    """Stable treatment bit for the current-offer stale-stall experiment."""
    gid = str(game_id or "")
    if not gid:
        return None
    import hashlib as _hashlib
    return bool(
        int(_hashlib.sha256((STALL_CURRENT_BREAK_SALT + gid).encode()).hexdigest(), 16)
        & 1
    )


def hidden_min_share_veto_assignment(game_id) -> bool | None:
    """Stable treatment bit for the support-aware hidden acceptance veto."""
    gid = str(game_id or "")
    if not gid:
        return None
    import hashlib as _hashlib
    return bool(int(_hashlib.sha256(
        (HIDDEN_MIN_SHARE_VETO_SALT + gid).encode()).hexdigest(), 16) & 1)


def table_vcont_precedence_assignment(game_id) -> bool | None:
    """Stable treatment bit for the TABLE-versus-continuation experiment."""
    gid = str(game_id or "")
    if not gid:
        return None
    import hashlib as _hashlib
    return bool(int(_hashlib.sha256(
        (TABLE_VCONT_PRECEDENCE_SALT + gid).encode()).hexdigest(), 16) & 1)


def hidden_min_positive_zone(my_value: float, i_am_seller: bool) -> dict | None:
    """Return the smallest positive hidden ZOPA allowed by validated support.

    The value support is discrete.  A seller at .8B or 1.0B can first trade
    with the next type .2B away; a seller at 1.2B needs the 1.5B buyer (.3B).
    Buyer types mirror that map.  Extreme seller-1.5/buyer-.8 cells have no
    positive ZOPA and are already owned by DEADGAME_V1, so they return None.
    """
    try:
        value = float(my_value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    base = pricing.infer_base(value)
    if base is None:
        return None
    multiplier = value / base
    if i_am_seller:
        support_gap = ((0.8, 0.2), (1.0, 0.2), (1.2, 0.3))
    else:
        support_gap = ((1.0, 0.2), (1.2, 0.2), (1.5, 0.3))
    gap = next((candidate for own, candidate in support_gap
                if abs(multiplier - own) <= 1e-6), None)
    if gap is None:
        return None
    return {
        "base": base,
        "own_multiplier": round(multiplier, 1),
        "min_positive_zone": gap * base,
    }


def hidden_min_share_signal(state: dict, seat: str,
                            fraction: float = HIDDEN_MIN_SHARE_VETO_FRACTION
                            ) -> dict | None:
    """Pre-action signal for a profitable offer below the support-aware floor."""
    if seat not in ("player_1", "player_2"):
        return None
    if state.get("complete_information") is not False:
        return None
    # Keep the shared production/reader predicate honest on its own.  The
    # candidate never overrules the dominant real-final action: accept every
    # strictly profitable terminal offer because rejection is certainly zero.
    if is_final_round(state):
        return None
    if (state.get("current_player") or seat) != seat:
        return None
    role = state.get(f"{seat}_role")
    if role not in ("seller", "buyer"):
        return None
    own_value = state.get(f"{seat}_value")
    support = hidden_min_positive_zone(own_value, role == "seller")
    if support is None:
        return None
    try:
        offer = float((state.get("last_offer") or {}).get("price"))
        own_value = float(own_value)
        fraction = float(fraction)
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(value) for value in (offer, own_value, fraction)):
        return None
    surplus = offer - own_value if role == "seller" else own_value - offer
    floor = fraction * support["min_positive_zone"]
    # Exclude exact-boundary offers despite binary-float multiplication (8.00
    # must not become "< 40% of 20" because .4*.2*100 is 8.000000000000002).
    tolerance = max(support["base"] * 1e-9, 1e-9)
    if surplus <= 0.0 or surplus + tolerance >= floor:
        return None
    return {
        **support,
        "role": role,
        "own_value": own_value,
        "offer_price": offer,
        "surplus": surplus,
        "veto_fraction": fraction,
        "veto_floor": floor,
        # Conditional on a positive-ZOPA latent cell, the actual ZOPA is at
        # least this minimum, so actual capture is no larger than this ratio.
        # A legal but irrational loss-making opponent offer can violate that
        # premise; its causal frequency is intentionally left to the A/B.
        "positive_zone_share_upper": surplus / support["min_positive_zone"],
    }


def _hidden_min_share_veto_enabled() -> bool:
    """Whether the randomized veto can safely compose with the current stack."""
    if not runtime_flags.enabled("GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB"):
        return False
    # This experiment changes an acceptance decision made by this exact stack.
    # Closing it when any owner changes is safer than silently estimating a
    # mixture of policies under one hash salt.
    if not (_horizon_v2_enabled() and _continuation_accept_enabled()
            and runtime_flags.enabled("GLEE_NEGO_TABLE")):
        return False
    conflicts = (
        "GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB",
        "GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB",
        "GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB",
        "GLEE_NEGO_HIDDEN_POLICY_V1",
        "GLEE_NEGO_HIDDEN_FLOOR",
        "GLEE_NEGO_STALL_CURRENT_BREAK_AB",
        "GLEE_NEGO_TABLE_VCONT_PRECEDENCE_AB",
        "GLEE_NEGO_RANK_PRICE_AB",
        "GLEE_NEGO_CLOSE_AB",
        "GLEE_NEGO_UNCAPPED_AB",
        "GLEE_NEGO_SURPLUS_PROBE",
    )
    return not any(runtime_flags.enabled(name) for name in conflicts)


def _maybe_hidden_min_share_veto(state: dict, p: dict, offer_price: float,
                                 control_acceptor: str) -> dict | None:
    """Replace one provably-low-share control acceptance in the candidate arm.

    Call only at a branch that is otherwise about to return AcceptOffer.  That
    makes first eligibility independent of treatment and keeps hash controls
    exactly on the current policy.  The candidate uses the existing profitable-
    side counter construction; no concession schedule or price parameter is
    bundled into the accept/reject experiment.
    """
    if not _hidden_min_share_veto_enabled():
        return None
    seat = state.get("current_player")
    signal = hidden_min_share_signal(state, seat)
    if signal is None:
        return None
    treatment = hidden_min_share_veto_assignment(p.get("game_id"))
    if treatment is None:
        return None
    metadata = {
        **signal,
        "eligible": True,
        "arm": "candidate" if treatment else "control",
        "control_acceptor": control_acceptor,
    }
    p["hidden_min_share_veto"] = metadata
    if not treatment:
        return None

    _gate(p, "hidden_min_share_veto")
    counter = p["target"]
    if _profitable(offer_price, p):
        counter = (max(offer_price, counter) if p["i_am_seller"]
                   else min(offer_price, counter))
    before_split = counter
    counter = _maybe_split(state, p, counter)
    if counter != before_split:
        _gate(p, "split")
    counter = _enforce_span_invariant(p, counter)
    metadata["counter_price"] = round(counter, 2)
    return {"decision": "RejectOffer", "product_price": round(counter, 2),
            "_plan": p}


def _table_vcont_precedence_enabled() -> bool:
    """Whether the randomized TABLE-precedence test owns this exact stack."""
    if not runtime_flags.enabled("GLEE_NEGO_TABLE_VCONT_PRECEDENCE_AB"):
        return False
    # Freeze the accept stack whose ordering is under test.  In particular,
    # STALL_POLICY must remain on because the cohort excludes states that would
    # immediately accept through that next branch; FINAL_OPTION=0.60 freezes the
    # earlier option-value owner.  Any overlapping behavioral arm fails closed.
    if not (_horizon_v2_enabled() and _continuation_accept_enabled()
            and runtime_flags.enabled("GLEE_NEGO_TABLE")
            and runtime_flags.enabled("GLEE_NEGO_STALL_POLICY")):
        return False
    if abs(runtime_flags.as_float("GLEE_NEGO_FINAL_OPTION", 0.0)
           - TABLE_VCONT_REQUIRED_FINAL_OPTION) > 1e-9:
        return False
    conflicts = (
        "GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB",
        "GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB",
        "GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB",
        "GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB",
        "GLEE_NEGO_HIDDEN_POLICY_V1",
        "GLEE_NEGO_HIDDEN_FLOOR",
        "GLEE_NEGO_STALL_CURRENT_BREAK_AB",
        "GLEE_NEGO_FIRST_PRINCIPLES",
        "GLEE_NEGO_FP_ALWAYS",
        "GLEE_NEGO_RANK_PRICE_AB",
        "GLEE_NEGO_CLOSE_AB",
        "GLEE_NEGO_UNCAPPED_AB",
        "GLEE_NEGO_SURPLUS_PROBE",
    )
    return not any(runtime_flags.enabled(name) for name in conflicts)


def table_vcont_precedence_signal(
    state: dict, p: dict, offer_price: float, surplus_now: float,
    continuation: float, evidence: dict, table_threshold: float,
) -> dict | None:
    """Pre-action signal for a TABLE accept contradicted by observed momentum.

    The continuation model is not identified when it extrapolates from our own
    unplayed target.  This signal therefore requires three distinct, echo-
    collapsed opponent prices and a positive measured concession trend.  It
    also excludes support-minimum lowballs (owned by a separate experiment) and
    states the next STALL branch would accept anyway.
    """
    seat = state.get("current_player")
    if seat not in ("player_1", "player_2"):
        return None
    if state.get("complete_information") is not False or is_final_round(state):
        return None
    if p.get("their_value") is not None or int(p.get("rounds_left", 1)) <= 1:
        return None
    if not _profitable(offer_price, p):
        return None
    values = (offer_price, surplus_now, continuation, table_threshold)
    if not all(isinstance(value, (int, float)) and math.isfinite(float(value))
               for value in values):
        return None
    tolerance = max(abs(float(p.get("my_value", 0.0))) * 1e-9, 1e-9)
    if surplus_now + tolerance < table_threshold:
        return None
    if continuation <= surplus_now + tolerance:
        return None
    if not isinstance(evidence, dict):
        return None
    if (evidence.get("basis") != "projected from concession trend"
            or _num(evidence.get("rate"), 0.0) <= 0.0):
        return None
    if hidden_min_share_signal(state, seat) is not None:
        return None

    offers = _their_offers(state, seat)
    scale = max([abs(price) for _, price in offers] + [abs(offer_price), 1.0])
    distinct: list[float] = []
    for _, price in offers:
        if all(abs(price - prior) > scale * 1e-9 for prior in distinct):
            distinct.append(price)
    if len(distinct) < 3 or abs(distinct[-1] - offer_price) > scale * 1e-9:
        return None

    stall_price = _their_stall_price(state, seat)
    if (stall_price is not None
            and abs(offer_price - stall_price)
            <= 0.01 * max(abs(stall_price), 1.0)):
        return None
    return {
        "role": p.get("role"),
        "offer_price": offer_price,
        "surplus_now": surplus_now,
        "table_threshold": table_threshold,
        "continuation_value": continuation,
        "continuation_rate": _num(evidence.get("rate"), 0.0),
        "distinct_opponent_prices": len(distinct),
    }


def _maybe_table_vcont_precedence(
    state: dict, p: dict, offer_price: float, surplus_now: float,
    continuation: float, evidence: dict, table_threshold: float,
) -> bool:
    """Return True only when the candidate arm suppresses a direct TABLE accept."""
    if not _table_vcont_precedence_enabled():
        return False
    signal = table_vcont_precedence_signal(
        state, p, offer_price, surplus_now, continuation, evidence,
        table_threshold)
    if signal is None:
        return False
    treatment = table_vcont_precedence_assignment(p.get("game_id"))
    if treatment is None:
        return False
    p["table_vcont_precedence"] = {
        **signal,
        "eligible": True,
        "arm": "candidate" if treatment else "control",
    }
    if not treatment:
        return False
    _gate(p, "table_vcont_precedence")
    p["table_accept_vetoed"] = True
    return True


def _current_concession_break(state: dict, me: str,
                              stall_price: float) -> float | None:
    """Return a current opponent price that invalidates the historical stall.

    ``_their_stall_price`` deliberately remains unchanged because dead-game
    walking and stall acceptance use its completed-history definition.  This
    helper is only for the offer-target writer: the standing ``last_offer`` is
    one opponent action newer than that history and can show that the apparent
    stall has already ended.
    """
    if me not in ("player_1", "player_2"):
        return None
    other = "player_2" if me == "player_1" else "player_1"
    last = state.get("last_offer") or {}
    if not isinstance(last, dict) or last.get("from_player") != other:
        return None
    try:
        current = float(last.get("price"))
        stale = float(stall_price)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(current) or not math.isfinite(stale):
        return None
    scale = max(abs(stale), abs(current), 1.0)
    gap = 0.01 * scale
    role = state.get(f"{me}_role")
    if role == "seller" and current > stale + gap:
        return current
    if role == "buyer" and current < stale - gap:
        return current
    return None


def _target_improves_for_role(state: dict, me: str, candidate: float,
                              control: float) -> bool:
    """Whether ``candidate`` asks strictly more for us than ``control``."""
    try:
        candidate = float(candidate)
        control = float(control)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(candidate) or not math.isfinite(control):
        return False
    tolerance = 1e-12 * max(abs(candidate), abs(control), 1.0)
    role = state.get(f"{me}_role")
    if role == "seller":
        return candidate > control + tolerance
    if role == "buyer":
        return candidate < control - tolerance
    return False


def _stall_current_break_enabled() -> bool:
    """Whether the isolated stale-stall treatment is safe to consult.

    The candidate changes a target, so it is offer-only only while the deployed
    continuation-value acceptor owns decisions.  The listed price probes can
    alter whether a later stale state is reached (or overwrite its counter), so
    refusing a mixed stack prevents an accidental, unanalyzed factorial.
    """
    if not runtime_flags.enabled("GLEE_NEGO_STALL_CURRENT_BREAK_AB"):
        return False
    if not _continuation_accept_enabled():
        return False
    conflicts = (
        "GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB",
        "GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB",
        "GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB",
        "GLEE_NEGO_HIDDEN_POLICY_V1",
        "GLEE_NEGO_HIDDEN_FLOOR",
        "GLEE_NEGO_FIRST_PRINCIPLES",
        "GLEE_NEGO_FP_ALWAYS",
    )
    return not any(runtime_flags.enabled(name) for name in conflicts)


def _rounds_left(state: dict, assumed_horizon: int) -> tuple[int, bool]:
    """(rounds remaining including this one, whether the cap is real).

    An uncapped game still needs a clock. Returning the planning horizon as a
    CONSTANT froze the concession schedule — the agent asked the same opening
    price on round 1 and on round 40, never conceded, and three quarters of
    negotiations died with no deal at zero. Count down against the planning
    horizon instead, so the schedule actually advances.
    """
    if state.get("horizon_known") is False or state.get("max_rounds") is None:
        # An uncapped game has NO known final round. Counting down against the
        # planning horizon and then treating the result as a deadline was a bug
        # of mine: from round 10 onward rounds_left hit 1, decide() read that as
        # the final round, and we accepted any offer with positive surplus. An
        # opponent only had to stall to round 10 to get our floor. The planning
        # clock still paces concession; it must never declare the game over.
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


def _zopa_share(gid, default: float) -> float:
    """The share of the visible zone we LEAVE the opponent, A/B-aware.

    Normally this is just GLEE_NEGO_ZOPA_SHARE. But this parameter is the one
    lever measured large enough to matter for negotiation (+0.0121 in the arena)
    AND the one the arena cannot be trusted on: sim/field_data.py bins nego
    responses on _price_bin (0.1 of base) when the move is often smaller than one
    bin, consults a survivorship-selected value-keyed table first, and falls back
    at field_data.py:343 to "profitable -> AcceptOffer", which GRANTS any greedy
    ask it has never seen. So it has to be settled on live play instead.

    GLEE_NEGO_ZOPA_AB=<value> runs that experiment: each GAME is assigned by a
    hash of its id to control (`default`) or to the candidate <value>. Assignment
    is per GAME, not per turn, so a game is never half in each arm, and it is a
    pure function of the game id, so scripts/live_percentile.py can recover the
    arm afterwards without us logging anything that could drift.

    Deliberately unlike the surplus probe this replaces: that one assigned inside
    plan() before the offer/decision branch and overwrote p["target"], which
    negotiation.py:1046 also compares against INCOMING offers -- so the treatment
    leaked into our accept threshold and the experiment could not identify
    anything. Here the assignment changes only this one parameter, at every site
    that reads it, exactly as shipping the flag would.
    """
    ab = runtime_flags.as_float("GLEE_NEGO_ZOPA_AB", 0.0)
    if ab <= 0.0:
        return runtime_flags.as_float("GLEE_NEGO_ZOPA_SHARE", default)
    gid = str(gid or "")
    if not gid:
        return runtime_flags.as_float("GLEE_NEGO_ZOPA_SHARE", default)
    import hashlib as _h
    bit = int(_h.sha256(("zopa_ab|" + gid).encode()).hexdigest(), 16) & 1
    return ab if bit else default


#: The historical clamp on the uncapped planning clock. ENDGAME_V3 failure 2 was
#: real -- letting elapsed reach 1.0 in a game with no deadline bid our full value
#: by round 12 and paid a stonewaller everything -- so this floor stays.
_UNCAPPED_FLOOR = 0.85


def _uncapped_ceiling(gid) -> float:
    """How far the planning clock may advance when no real deadline exists.

    WHY THIS IS NOT JUST THE CLAMP. Pinning elapsed at 0.85 does not slow the
    concession walk, it STOPS it: concession = 0.85**2 = 0.7225 from the round the
    planning horizon expires (round ~11 at the default horizon of 10) until the
    game dies, so target never moves again. Measured over 1,988 uncapped games
    with at least eight of our own offers, 84.5% contain a run of five or more
    byte-identical prices, the median longest run is 38, and the runs begin at a
    median round of 11 -- exactly where the horizon expires. The games that reach
    21+ rounds close 5.4% of the time and score 0.3667, against 87.4% and 0.6023
    for uncapped games that settle by round 10. In every complete-information
    game of that grinding cohort (93 of 93) a zone of agreement existed, and our
    own frozen price sat INSIDE it in 91.4% of them: a deal was available, we were
    already asking a price the opponent could profitably take, and neither side
    moved again.

    So the walk must keep approaching without ever arriving. Returning a ceiling
    above the floor lets the caller advance elapsed asymptotically toward it,
    which preserves failure 2's guarantee (we never bid our full value, because
    the ceiling is capped strictly below 1.0) while restoring the movement that
    actually closes deals.

    Assignment mirrors _zopa_share exactly: GLEE_NEGO_UNCAPPED_AB holds the
    treatment ceiling and splits games 50/50 on a hash of the game id, so both
    arms run inside ONE agent and the comparison cannot be confounded by which
    slot, which opponent pool, or which hour the game was played in. Unset, or
    at or below the floor, the whole mechanism is inert and behaviour is
    byte-identical to the clamp it replaces.

    READ THIS BEFORE ARMING. A six-way adversarial review measured, on 44,000
    logged late uncapped turns, that this walk owns our price on only 11.6%
    (Test 4) to 22.5% of them: GLEE_NEGO_STALL_POLICY's park branch writes
    62.4-69.2%, the span veto 5.5-20.5% and DEADGAME_V1 2.6-4.4%, and all three
    overwrite `target` AFTER the concession line. The byte-identical price runs
    this was built to break are stall_park re-emitting the previous price, not a
    frozen clock. Worse, 0 of 7,961 schedule-owned late uncapped turns are
    complete-information, so the evidence that motivated it -- 93 of 93 grinding
    games having a visible ZOPA -- comes from a population where this is inert.
    And the protection is inverted: the ENDGAME_V3 interior bound at :476 is
    gated on `zopa_lo is not None` and _enforce_span_invariant returns early on a
    falsy zopa, so in hidden games, which is where 100% of the reachable turns
    live, the only floor is reservation = value + margin*(anchor - value), about
    1.06x value as seller. At ceiling 0.97 that hands back roughly half the
    surplus the clamp exists to preserve. Measured effect across three
    independent routes: -0.027 to +0.0007 percentile. DO NOT ARM without new
    evidence; the lever that actually writes these prices is stall_park.
    """
    plain = runtime_flags.as_float("GLEE_NEGO_UNCAPPED_CEILING", _UNCAPPED_FLOOR)
    ab = runtime_flags.as_float("GLEE_NEGO_UNCAPPED_AB", 0.0)
    # A non-finite flag must fail CLOSED. min/max propagate NaN and every NaN
    # comparison is False, so an unguarded 'nan' in arms.json would skip the
    # inert branch, carry NaN through target, and reach actions.coerce -- which
    # sanitises it into a $0.00 offer. Fail-open on a typo is not acceptable.
    if not math.isfinite(plain):
        plain = _UNCAPPED_FLOOR
    if not math.isfinite(ab) or ab <= 0.0:
        return plain
    gid = str(gid or "")
    if not gid:
        return plain
    import hashlib as _h
    bit = int(_h.sha256(("uncapped_ab|" + gid).encode()).hexdigest(), 16) & 1
    return ab if bit else plain


def _rank_price_arm(gid) -> bool | None:
    """Per-game treatment bit for terminal rank pricing, or None when OFF.

    The salt is deliberately independent of ``zopa_ab|``: that greedy-price
    experiment is live, and sharing its bit would confound the two arms. A pure
    game-id hash makes assignment stable across every turn and lets
    scripts/live_percentile.py recover it after the game without mutable logs.
    """
    if not runtime_flags.enabled("GLEE_NEGO_RANK_PRICE_AB"):
        return None
    gid = str(gid or "")
    if not gid:
        return None
    import hashlib as _h
    return bool(int(_h.sha256(("rank_price_ab|" + gid).encode()).hexdigest(), 16) & 1)


def _close_harder(game: dict, i_am_seller: bool, my_value, complete: bool) -> bool:
    """Is this a hidden game we should be PUSHING to close, and is it in the arm?

    Codex's decomposition of the remaining negotiation prize (deal rates in
    .ai/FINDINGS.md against the grid's feasibility ceiling):
        complete-info games we fail to close   0.02236 of all games = 28%
        HIDDEN-info games we fail to close     0.05745 of all games = 72%
    So nearly three quarters of what is left is hidden-information closure, and
    almost all of THAT sits in two cells. By our own factor, hidden info:
        0.8  we close 64.5% against a 75% ceiling   gap 10.5pp
        1.0  we close 41.4% against a 50% ceiling   gap  8.6pp
        1.2  we close 23.3% against a 25% ceiling   gap  1.7pp
        1.5  we close  2.6% against a  0% ceiling   (harvest, not closure)

    The point is that we ALREADY KNOW which cell we are in at round one. Our own
    value is observed, the factor grid is {0.8,1.0,1.2,1.5}, and in hidden games
    the two factors are drawn independently and uniformly -- so our own factor
    alone fixes P(a deal exists): 75/50/25/0%. Today we play every hidden game
    identically and spend the same caution on a game that is 75% likely to be
    winnable as on one that is provably dead.

    This marks the games worth pushing: hidden information, and our own draw on
    the favourable side (seller at or below 1.0x base, buyer at or above 1.2x).
    Assignment is per GAME by a hash of its id, the same scheme as
    GLEE_NEGO_ZOPA_AB, so scripts/live_percentile.py can recover the arm without
    anything being logged that could drift.
    """
    ab = runtime_flags.as_float("GLEE_NEGO_CLOSE_AB", 0.0)
    if ab <= 0.0 or complete or my_value is None:
        return False
    base = pricing.infer_base(my_value)
    if not base:
        return False
    ratio = my_value / base
    favourable = (ratio <= 1.0 + 1e-9) if i_am_seller else (ratio >= 1.2 - 1e-9)
    if not favourable:
        return False
    gid = str((game or {}).get("game_id") or "")
    if not gid:
        return False
    import hashlib as _h
    return bool(int(_h.sha256(("close_ab|" + gid).encode()).hexdigest(), 16) & 1)


def plan(game: dict, cfg) -> dict:
    state = game["game_state"]
    me = state.get("current_player") or game["your_player"]
    role = state.get(f"{me}_role") or ("seller" if game["your_player"] == "player_1" else "buyer")
    i_am_seller = role == "seller"
    my_value = _num(state.get(f"{me}_value"), 0.0)

    # Under complete information the server hands us BOTH valuations. Ignoring
    # that ran the same blind anchor-and-concede as when we know nothing, in
    # roughly half of all games. With both values the zone of agreement is
    # exact: no search, no posterior, no model.
    other = other_player(me)
    their_value = None
    if _horizon_v2_enabled() and state.get(f"{other}_value") is not None:
        their_value = _num(state.get(f"{other}_value"), 0.0)
    zopa_lo = zopa_hi = None
    if their_value is not None:
        seller_v = my_value if i_am_seller else their_value
        buyer_v = their_value if i_am_seller else my_value
        if buyer_v > seller_v:
            zopa_lo, zopa_hi = seller_v, buyer_v

    rounds_left, capped = _rounds_left(state, cfg.nego_assumed_horizon)
    horizon = max(1, int(_num(state.get("max_rounds"), cfg.nego_assumed_horizon)))
    # Fraction of the negotiation elapsed, 0 at the start and 1 at the deadline.
    elapsed = 1.0 - (rounds_left - 1) / max(1, horizon)
    elapsed = min(max(elapsed, 0.0), 1.0)
    if (not capped and elapsed > _UNCAPPED_FLOOR
            and runtime_flags.enabled("GLEE_NEGO_ENDGAME_V3")):
        # No real deadline exists; the planning clock paces concession but must
        # never finish it (failure 2 above -- full-value bids by round 12 of an
        # uncapped game, exactly when a stonewaller profits from waiting).
        ceiling = min(max(_uncapped_ceiling(game.get("game_id")),
                          _UNCAPPED_FLOOR), 0.99)
        if ceiling <= _UNCAPPED_FLOOR:
            elapsed = _UNCAPPED_FLOOR
        else:
            # Hyperbolic approach, never arrival: at `half` rounds past the
            # horizon we are halfway from the floor to the ceiling, and the 0.99
            # cap above means concession tops out at 0.9801 at the default
            # exponent -- the walk closes on the reservation without reaching it.
            # Monotone in round, and exactly _UNCAPPED_FLOOR at the horizon, so
            # the schedule is continuous rather than jumping at the boundary.
            # NO SAFETY NET BELOW THIS. An earlier version of this comment
            # claimed the ENDGAME_V3 interior bound floors the reservation at
            # nego_zopa_share of the span. That is false wherever this code can
            # actually reach: :476 gates the bound on `zopa_lo is not None` and
            # _enforce_span_invariant returns early on a falsy zopa, and every
            # turn this walk owns is hidden-information. The floor here is only
            # reservation itself. See _uncapped_ceiling for the measurements.
            half = runtime_flags.as_float("GLEE_NEGO_UNCAPPED_HALFLIFE", 10.0)
            half = max(half if math.isfinite(half) else 10.0, 1e-9)
            extra = max(0.0, _num(state.get("round"), 1) - horizon)
            elapsed = _UNCAPPED_FLOOR + (ceiling - _UNCAPPED_FLOOR) * (extra / (extra + half))

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
    # Live-tunable, and the single most percentile-sensitive number in this
    # family. 51% of negotiation outcomes field-wide are exactly $0, and scoring
    # is percentile-per-config: ANY positive close beats that whole pile. Live
    # comparison on the same configs (single-round seller seat): the field asks
    # 1.24x its value and closes 42.7%; margin 0.12 under a 4.0x anchor made us
    # ask 1.36x and close 33.7% -- more money per close, fewer closes, and the
    # scoring pays frequency. This margin sets the concession ENDPOINT (and, via
    # elapsed=1, the whole ask in a single-round game), so lowering it trades
    # margin for close rate, which is the direction the percentile pays.
    margin = runtime_flags.as_float("GLEE_NEGO_MIN_MARGIN", cfg.nego_min_margin)
    margin = min(max(margin, 0.0), 0.9)
    # The margin used to be a fraction of the ANCHOR SPREAD, so a theatrical 4x
    # opening produced a terminal reservation of 1.36x our own value — outside
    # the zone of agreement in three of the six strict-ZOPA type pairs, i.e. a
    # guaranteed no-deal. Scale it to the surplus that actually exists instead.
    if zopa_lo is not None:
        span = zopa_hi - zopa_lo
        reservation = (floor + span * margin) if i_am_seller else (floor - span * margin)
    else:
        reservation = floor + (anchor - floor) * margin

    # Endgame v3 -- three measured failures, one gate (games cited in commit):
    # 1. With a VISIBLE zone of agreement the walk's endpoint was our own value
    #    (value -/+ span*margin ~ value at margin 0.02), so a stonewalling bot
    #    collected our entire surplus: game 120a6b39, buyer value 10,000 vs a
    #    seller at 8,000, closed at 10,000 for payoff 0, 4th percentile. The
    #    interior share must bound the ENDPOINT, not just early offers.
    # 2. In UNCAPPED games the planning clock still ran elapsed to 1.0 by round
    #    ~12, full capitulation with no deadline anywhere. Cap elapsed short of
    #    1 when no real deadline exists: the walk approaches, never surrenders.
    # 3. A 1.5xB seller has no rational deal, but 39% of the field's payoffs in
    #    that cell are POSITIVE (median +0.35xB): irrational buyers pay above
    #    value. Reservation 1.5B*(1+2*margin) at margin 0.02 asked 1.54B --
    #    below the harvest zone. Floor the no-rational-deal seller's ask at
    #    1.15x value; the ask costs nothing (the alternative was 0 anyway).
    if runtime_flags.enabled("GLEE_NEGO_ENDGAME_V3"):
        share_iv = _zopa_share(game.get("game_id"), cfg.nego_zopa_share)
        share_iv = min(max(share_iv, 0.0), 0.5)
        if zopa_lo is not None:
            span_iv = zopa_hi - zopa_lo
            if i_am_seller:
                reservation = max(reservation, zopa_lo + share_iv * span_iv)
            else:
                reservation = min(reservation, zopa_hi - share_iv * span_iv)
        elif i_am_seller:
            pb = pricing.infer_base(my_value)
            if pb and my_value >= 1.5 * pb - 1e-9:
                reservation = max(reservation, 1.15 * my_value)

    # Boulware concession from anchor toward reservation.
    # Live-tunable. The fitted field concedes at k~1.18 (n=71 paths); our 2.0
    # holds-then-collapses where the field glides, which reads as stonewalling to
    # opponents pacing us against their own curve (our measured k was 2.04).
    boulware = runtime_flags.as_float("GLEE_NEGO_BOULWARE", _BOULWARE)
    # Push to close where a deal is probably THERE. Faster concession measured
    # WORSE when applied unconditionally (-0.0166/-0.0182), but that test spent
    # the concession everywhere, including the 62.5% of hidden cells with no
    # possible trade, where conceding buys nothing and can only cost price. Here
    # it is spent only where our own draw says a deal is 50-75% likely.
    if _close_harder(game, i_am_seller, my_value, bool(state.get("complete_information"))):
        boulware = runtime_flags.as_float("GLEE_NEGO_CLOSE_AB", boulware)
        p_close = True
    else:
        p_close = False
    concession = elapsed ** min(max(boulware, 0.5), 4.0)
    target = anchor + (reservation - anchor) * concession

    # Propose INSIDE the zone of agreement we can see — never at its boundary.
    # The boundary hands the opponent exactly zero surplus, which the measured
    # acceptance cliff says gets rejected: technically inside the ZOPA,
    # economically a no-deal. Leave them at least nego_zopa_share of the span.
    if zopa_lo is not None:
        span = zopa_hi - zopa_lo
        share = _zopa_share(game.get("game_id"), cfg.nego_zopa_share)
        give = min(max(share, 0.0), 0.5) * span
        if i_am_seller:
            target = min(max(target, zopa_lo), zopa_hi - give)
        else:
            target = min(max(target, zopa_lo + give), zopa_hi)

    # Ultimatum pricing. When the horizon really ends after this offer and we
    # can SEE the zone, rejection pays the opponent exactly zero, so the whole
    # span above their indifference is ours to claim -- yet the concession walk
    # arrives at elapsed=1.0 on its interior reservation and hands over 61% of
    # it. Measured live: 1-round complete-info seller games ask 0.390 of the
    # span in EVERY configuration ([80,100], [80,120], [80,150], [100,150]),
    # for -5.6 to -6.4 rating apiece; the field pays +6.5 for a 50% split of
    # the same span. bargaining.py already encodes this asymmetry for its own
    # ultimatum ("rejecting pays them nothing, so leave a share big enough to
    # be worth taking" -> it claims 0.75); this is the negotiation counterpart.
    # Deliberately not a full claim: an insulted opponent rejecting costs the
    # whole deal, so the share is a live knob, not 1.0. OFF by default.
    _tr: list | None = [] if _trace_enabled() else None
    ult = runtime_flags.as_float("GLEE_NEGO_ULTIMATUM_SHARE", 0.0)
    ultimatum = False
    if (ult > 0.0 and zopa_lo is not None and capped and rounds_left <= 1
            and state.get(f"{other}_value") is not None):
        span_u = zopa_hi - zopa_lo
        if span_u > 0:
            take = min(max(ult, 0.0), 0.95)
            _t0 = target
            target = (zopa_lo + take * span_u) if i_am_seller \
                else (zopa_hi - take * span_u)
            ultimatum = True
            if _tr is not None and target != _t0:
                _tr.append("ultimatum")

    # SURPLUS-SHARE RESPONSE PROBE. A randomised controlled experiment, not a
    # policy: in complete-information games the zone is fully visible, so our
    # ask can be expressed as a share x of the available surplus rather than as
    # a multiple of our own value. The probe draws x from a grid and records
    # what the opponent does next, which is the ONLY way to learn the causal
    # frontier P(accept | x).
    #
    # Why an experiment and not a target: observational data says closes at
    # 60-65% of span earn +4.68 rating while ours land at 49.4% -- but that
    # statistic conditions on a DEAL HAVING HAPPENED and is therefore blind to
    # the rejections a greedier ask would cause. The same survivorship trap
    # made one-round asks at 0.90/0.95 look optimal from accepted prices, and
    # the arena then measured them clearly worse. Randomising x and observing
    # the immediate response is what breaks the conditioning.
    #
    # Assignment is seeded on the game id so a replay reproduces it exactly,
    # and stratified by seat and round-block so the arms stay balanced across
    # cells. OFF by default; costs nothing outside complete-info offer turns.
    probe_arm = None
    if (runtime_flags.enabled("GLEE_NEGO_SURPLUS_PROBE")
            and zopa_lo is not None and state.get(f"{other}_value") is not None
            and not ultimatum):
        span_p = zopa_hi - zopa_lo
        if span_p > 0:
            import hashlib as _h
            grid = (0.50, 0.55, 0.60, 0.65, 0.70, 0.75)
            _rn = int(_num(state.get("round"), 1))
            rb = 0 if _rn <= 2 else (1 if _rn <= 5 else 2)
            stratum = f"{'s' if i_am_seller else 'b'}|{rb}|{int(capped)}"
            key = f"{game.get('game_id')}|{stratum}"
            idx = int(_h.sha256(key.encode()).hexdigest(), 16) % len(grid)
            x = grid[idx]
            _t0 = target
            target = (zopa_lo + x * span_p) if i_am_seller \
                else (zopa_hi - x * span_p)
            probe_arm = {"x": x, "stratum": stratum, "span": span_p,
                         "prev_target": _t0}
            if _tr is not None and target != _t0:
                _tr.append("surplus_probe")

    # Final-offer pricing from the fitted acceptance curve, where the constants
    # were blindest: a hidden-information game at our last offer opportunity.
    # The right ask depends on our own value multiplier -- a 0.8xB seller should
    # ask ~1.15-1.4xB while a 1.5xB seller has NO profitable ask at all (the
    # curve's acceptance is 0/283 above 1.5xB) -- which no constant margin can
    # express: margin 0.12 asked 1.36x our value regardless, demanding an
    # impossible 2.04xB from a 1.5xB seller. Gated, and None falls back to the
    # constant path, so the curve can only replace a constant with a measurement.
    # Posterior-conditional pricing: in a hidden-information game the opponent's
    # value is one of four grid points and their FIRST OFFER leaks which -- a
    # seller opening at 0.9-1.05xB is a 0.8-value seller 91% of the time (n=174),
    # a buyer opening at 1.2-1.4xB holds the 1.5 value 87% of the time (n=97).
    # grid_ask prices just inside the posterior-likely step instead of walking a
    # blind concession curve. Applies to EVERY offer round in a hidden game, both
    # seats; the pooled final-round curve below stays as the fallback when this
    # gate is off or the model is missing.
    # Freeze-probe classifier (clean-room panel): our third offer REPEATS our
    # second -- a designed experiment. An opponent who keeps conceding into a
    # flat offer is paced by their own clock, not by reciprocity, so meeting
    # them halfway pays twice for concessions their clock delivers free: once
    # classified time-driven, hold our current price until the endgame
    # machinery (final-ask curves, any-positive) takes over at 85% elapsed.
    # Stones are already the stall policy's job; reciprocators get the normal
    # schedule back. Probe skipped in short capped games where an offer is
    # too scarce to spend on an experiment. OFF by default.
    probe_hold = False
    time_driven = False
    if runtime_flags.enabled("GLEE_NEGO_PROBE_V1") and (not capped or rounds_left >= 6):
        _pbase = pricing.infer_base(my_value)
        _ours_seq = _price_seq(state, me, True)
        _theirs_seq = _price_seq(state, me, False)
        if len(_ours_seq) == 2:
            if _tr is not None and target != _ours_seq[-1]:
                _tr.append("probe_hold")
            target = _ours_seq[-1]
            probe_hold = True
        elif (len(_ours_seq) >= 3 and _pbase
              and abs(_ours_seq[2] - _ours_seq[1]) <= 1e-6 * max(abs(_ours_seq[1]), 1.0)
              and len(_theirs_seq) >= 2):
            # echo-collapsed, each side's k-th distinct price answers the
            # other's k-th offer, so their move ACROSS our flat pair is the
            # last delta in their sequence
            _mv = (_theirs_seq[-1] - _theirs_seq[-2]) if i_am_seller \
                else (_theirs_seq[-2] - _theirs_seq[-1])
            if _mv >= 0.01 * _pbase:
                time_driven = True
        # Release the hold to the endgame machinery only when a REAL deadline
        # approaches. Uncapped games have none -- the planning clock reaching
        # 0.85 is our own fiction, and conceding on it against an opponent
        # whose clock is delivering concessions for free is the exact mistake
        # the classifier exists to stop.
        if time_driven and ((not capped) or elapsed < 0.85):
            _ol = _our_last_price(state, me)
            if _ol is not None:
                _t0 = target
                target = max(target, _ol) if i_am_seller else min(target, _ol)
                if _tr is not None and target != _t0:
                    _tr.append("time_driven")

    # Learned-table OFFER policy (glee_agent/table_policy.py). NOTE: the first
    # attempt to wire this aborted before writing and only the acceptance half
    # shipped -- an evolver run then optimised ask parameters that were never
    # consulted. Verified through decide() this time.
    table_fired = False
    if (state.get(f"{other}_value") is None
            and runtime_flags.enabled("GLEE_NEGO_TABLE")):
        t_ask = table_policy.offer(my_value, i_am_seller, elapsed)
        if t_ask is not None:
            if _tr is not None and target != t_ask:
                _tr.append("table")
            target = t_ask
            table_fired = True

    # Stall policy, offer side (verified measurement in _their_stall_price's
    # docstring): freeze against an unprofitable stall -- further concession is
    # what makes stonewalling pay; converge onto a profitable one -- each extra
    # round is 70%-no-deal territory.
    stall_current_break = None
    if runtime_flags.enabled("GLEE_NEGO_STALL_POLICY"):
        _sp = _their_stall_price(state, me)
        if _sp is not None:
            _t0 = target
            _control_target = target
            if (_sp > my_value) if i_am_seller else (_sp < my_value):
                _control_target = _sp
            else:
                # v2: stallers stall their OFFERS, not their acceptance (53% of
                # stalled closes were them taking our price). Park at the
                # fitted profitable sweet spot; freeze only when none exists.
                _park = pricing.stall_park(my_value, i_am_seller)
                if _park is not None:
                    _control_target = _park
                else:
                    _prev = [float((r.get("offer") or {}).get("price"))
                             for r in state.get("history") or []
                             if (r.get("offer") or {}).get("from_player") == me
                             and (r.get("offer") or {}).get("price") is not None]
                    if _prev:
                        _control_target = _prev[-1]

            _current = _current_concession_break(state, me, _sp)
            _safe_direction = _target_improves_for_role(
                state, me, _t0, _control_target)
            _enabled = _current is not None and _stall_current_break_enabled()
            _assigned = (stall_current_break_assignment(game.get("game_id"))
                         if _enabled and _safe_direction else None)
            if _enabled and not _safe_direction:
                # Record why a raw favorable-current shadow did not enter the
                # experiment. Suppressing the writer when the ordinary target
                # is less favorable than stall control would test extra
                # concession, not stale-state correction; exact-stack replay
                # found real wrong-direction actions before this guard.
                stall_current_break = {
                    "eligible": False,
                    "stale_price": _sp,
                    "current_price": _current,
                    "pre_stall_target": _t0,
                    "control_target": _control_target,
                }
            if _assigned is not None:
                # Live evidence over the last 20k turns per slot found 52-120
                # favorable current breaks and 35-107 changed counters; a real
                # seller-.8 example had historical 0/0/0, current 440,779.69,
                # yet the stale park rewrote ~1,400,527 to 900,000.  Suppress
                # only this one target writer in the treatment arm.  The old
                # park was accepted in that example, so stronger holding is a
                # randomized hypothesis, not a direct bug-fix deployment.
                stall_current_break = {
                    "eligible": True,
                    "arm": "candidate" if _assigned else "control",
                    "stale_price": _sp,
                    "current_price": _current,
                    "pre_stall_target": _t0,
                    "control_target": _control_target,
                }
            if _assigned is True:
                # Leave ``target`` at the pre-stall schedule.  Dead-game,
                # posterior and terminal writers below remain free to own the
                # final counter exactly as in control.
                if _tr is not None and target != _control_target:
                    _tr.append("stall_current_break")
            else:
                target = _control_target
                if _tr is not None and target != _t0:
                    _tr.append("stall_park")

    # Dead-game play (clean-room panel, all four frames): when the opponent's
    # own offers PROVE no profitable close plausibly exists, the 0 atom is our
    # floor either way -- rejection can never cost rank. So fish: hold a small
    # decaying premium above our own value, where any acceptance by an
    # irrational opponent converts a structurally-zero game into a top-decile
    # outcome, at provably zero downside. Detection is deliberately strict --
    # their best price still unprofitable to us by a 2%-of-B margin after at
    # least four of their offers.
    deadgame = False
    if runtime_flags.enabled("GLEE_NEGO_DEADGAME_V1") and not table_fired:
        _pb = pricing.infer_base(my_value)
        # Own-draw gate first: only the structurally dominated draws (1.5xB
        # seller, 0.8xB buyer -- measured zero-rates 97-100%), where the
        # normal schedule closes essentially nothing to displace. The first
        # arena run skipped this gate and misfired on winnable games: a weak
        # opponent bound read "probably dead" and the ladder dumped closeable
        # asks to near-value (-0.010/-0.007 pct, both seeds, closes UP 2pp at
        # ruined prices).
        _dominated = _pb is not None and (
            (my_value >= 1.5 * _pb - 1e-9) if i_am_seller
            else (my_value <= 0.8 * _pb + 1e-9))
        # How many of THEIR offers must land before we start fishing. The
        # strictness was aimed at the detection half of the gate -- reading
        # "probably dead" off a weak bound and dumping closeable asks. But the
        # own-draw gate above already establishes deadness by ARITHMETIC, not
        # inference: at 1.5xB seller / 0.8xB buyer the opposite seat's value
        # cannot reach ours, so no bound can rescue the cell and no evidence
        # threshold is protecting anything. Waiting for four of their offers
        # costs the whole early game in a 10-round cap, and in the 16% of games
        # drawn at max_rounds=1 a fourth offer never arrives at all, so fishing
        # never starts. Live-tunable; defaults to the measured 4.
        _minoff = int(runtime_flags.as_float("GLEE_NEGO_DEADGAME_MINOFF", 4.0))
        if _dominated and bound is not None \
                and len(_their_offers(state, me)) >= max(_minoff, 0):
            _margin = 0.02 * _pb
            _unprof = (bound < my_value + _margin) if i_am_seller \
                else (bound > my_value - _margin)
            if _unprof:
                deadgame = True
                _prem = _pb * max(0.10 * (1.0 - elapsed), 0.02)
                _t0 = target
                target = (my_value + _prem) if i_am_seller else (my_value - _prem)
                if _tr is not None and target != _t0:
                    _tr.append("deadgame")
    # (recorded in the returned plan below; decide() walks away on it late in
    # uncapped games once the opponent has also stalled)

    # Reciprocal-concession damping. The Boulware walk is paced by the CLOCK
    # alone, so it keeps conceding even while the opponent is closing the gap
    # from their side -- paying twice for the same convergence. The percentile
    # decomposition put half of negotiation's drag on wide-surplus cells where
    # our closes rank ~51st among the field's, and the paired transcripts show
    # the shape exactly: schedule-priced closes bleed rating, anchor-and-hold
    # closes land at the field's q75. While their counters are walking toward
    # us at >= RECIP_DAMP of the remaining gap per step, we repeat our last
    # price instead of meeting them; the schedule resumes the moment they
    # stall (which the stall policy above already prices) or the endgame
    # nears. OFF by default.
    recip_damped = False
    _damp = runtime_flags.as_float("GLEE_NEGO_RECIP_DAMP", 0.0)
    if _damp > 0 and not table_fired and rounds_left > 1:
        _ours_last = _our_last_price(state, me)
        # Opponent price sequence with the ECHO collapsed: a counteroffer is
        # recorded again as the next round's opening offer at the identical
        # price -- one utterance, two rows. Comparing a price to its own echo
        # reads every mover as a staller (measured: 0 damp firings in 2,858
        # arena games while buyers walked 9,750->10,528->10,917). A genuine
        # staller still shows as repeated COUNTERS, which the collapse keeps.
        _seq: list[float] = []
        _prev_key = None
        for _entry in state.get("history") or []:
            if not isinstance(_entry, dict):
                continue
            for _k in ("offer", "counteroffer"):
                _off = _entry.get(_k)
                if (isinstance(_off, dict) and _off.get("from_player")
                        not in (None, me) and _off.get("price") is not None):
                    _pr = _num(_off["price"])
                    if (_k == "offer" and _prev_key == "counteroffer"
                            and _seq and _pr == _seq[-1]):
                        _prev_key = _k
                        continue               # echo of the same utterance
                    _seq.append(_pr)
                    _prev_key = _k
        if _ours_last is not None and len(_seq) >= 2:
            _a, _b = _seq[-2], _seq[-1]
            _move = (_b - _a) if i_am_seller else (_a - _b)
            _gap = abs(_ours_last - _b)
            if _gap > 1e-9 and _move >= _damp * _gap:
                _t0 = target
                target = max(target, _ours_last) if i_am_seller \
                    else min(target, _ours_last)
                recip_damped = True
                if _tr is not None and target != _t0:
                    _tr.append("recip_damp")

    posterior_fired = table_fired
    if (not table_fired and state.get(f"{other}_value") is None
            and runtime_flags.enabled("GLEE_NEGO_POSTERIOR")):
        first_over_b = None
        pb = pricing.infer_base(my_value)
        if pb:
            for _rnd in state.get("history") or []:
                _off = _rnd.get("offer") or {}
                if _off.get("from_player") == other and _off.get("price") is not None:
                    first_over_b = _off["price"] / pb
                    break
        if capped and rounds_left <= 1:
            p_ask = pricing.posterior_final_ask(my_value, state.get(f"{other}_role"),
                                                first_over_b, i_am_seller)
            if p_ask is not None:
                if _tr is not None and target != p_ask:
                    _tr.append("posterior")
                target = p_ask
                posterior_fired = True
        elif runtime_flags.enabled("GLEE_NEGO_POSTERIOR_CAP"):
            p_cap = pricing.posterior_cap(my_value, state.get(f"{other}_role"),
                                          first_over_b, i_am_seller)
            if p_cap is not None:
                capped_target = min(target, p_cap) if i_am_seller else max(target, p_cap)
                # the cap must never push the walk through our own floor
                if (capped_target > my_value) if i_am_seller else (capped_target < my_value):
                    if _tr is not None and target != capped_target:
                        _tr.append("posterior_cap")
                    target = capped_target

    # NOTE the visibility test reads the STATE, not plan's their_value: that
    # local is (pre-existing) gated behind GLEE_NEGO_HORIZON_V2, so without V2 it
    # is None even when the opponent's valuation is right there in the state.
    # Conditioning on it would have silently extended curve pricing to
    # complete-information games.
    if (not posterior_fired and i_am_seller
            and state.get(f"{other}_value") is None and capped
            and rounds_left <= 1
            and runtime_flags.enabled("GLEE_NEGO_CURVE_PRICING")):
        curve_ask = pricing.seller_final_ask(my_value)
        if curve_ask is not None and curve_ask > my_value:
            if _tr is not None and target != curve_ask:
                _tr.append("curve_final")
            target = curve_ask

    # TERMINAL RANK PRICING is the final writer on an outgoing REAL-final offer.
    # The measured hidden-state proxy moved seller asks DOWN by as much as 0.275B
    # and buyer offers UP, buying acceptance; examples gained +0.111 expected rank
    # over the money argmax. Each armed GAME hashes to control or treatment, and
    # only an offer turn may move target, so the arm cannot leak into accept/reject
    # thresholds as the invalid surplus probe did. Treatment searches v5's covered
    # final-bin midpoints and maximises A(P)F(payoff)+(1-A(P))F(0); missing/thin
    # inputs leave every preceding path, including the 0.80 ultimatum, untouched.
    # This remains a proxy: the CDF includes our own games, and v2/v5 hidden-type
    # labels are agreement-selected. We keep the structural uniform hidden prior
    # instead of v2's selected weights, but the four v5 component curves are fitted.
    rank_price = None
    rank_arm = _rank_price_arm(game.get("game_id"))
    if (rank_arm is not None and game.get("valid_actions", {}).get("type") == "offer"
            and capped and rounds_left <= 1):
        previous_target = target
        if not rank_arm:
            rank_price = {"arm": "control", "status": "control",
                          "reason": "hash_control",
                          "previous_target": round(previous_target, 2)}
        else:
            visible_value = state.get(f"{other}_value")
            try:
                rank_price = pricing.rank_terminal_price(
                    my_value, i_am_seller, state, visible_value)
            except Exception:
                # A model artifact must never turn a legal terminal offer into a
                # strategy exception and therefore a timeout/no-submission.
                rank_price = {"status": "fallback", "reason": "pricing_error"}
            rank_price = {"arm": "candidate", **rank_price,
                          "previous_target": round(previous_target, 2)}
            for _k in ("chosen_price", "money_optimal_price"):
                if _k in rank_price:
                    rank_price[_k] = round(rank_price[_k], 2)
            for _k in ("chosen_acceptance", "money_acceptance",
                       "chosen_expected_rank", "money_expected_rank",
                       "cdf_at_zero"):
                if _k in rank_price:
                    rank_price[_k] = round(rank_price[_k], 6)
            if rank_price.get("status") == "applied":
                target = rank_price["chosen_price"]
                if _tr is not None and target != previous_target:
                    _tr.append("rank_price")

    out = {
        "close_push": p_close,
        # Carried so _final_option_value() can resolve the SAME A/B arm this
        # game was assigned; without it that site silently stayed on the control
        # value and the two arms disagreed inside one game.
        "game_id": game.get("game_id"),
        "role": role,
        "i_am_seller": i_am_seller,
        "my_value": my_value,
        "their_value": their_value,
        "zopa": (zopa_lo, zopa_hi) if zopa_lo is not None else None,
        "floor": floor,
        "anchor": anchor,
        "reservation": reservation,
        "target": target,
        "rounds_left": rounds_left,
        "capped": capped,
        "elapsed": elapsed,
        "opponent_bound": bound,
        "recip_damped": recip_damped,
        "deadgame": deadgame,
        "probe_hold": probe_hold,
        "time_driven": time_driven,
        "ultimatum": ultimatum,
        "surplus_probe": probe_arm,
    }
    if rank_price is not None:
        out["rank_price"] = rank_price
    if stall_current_break is not None:
        stall_current_break["final_target"] = target
        out["stall_current_break"] = stall_current_break
    if _tr is not None:
        out["gates_fired"] = _tr
    return out


def _price_seq(state: dict, me: str, of_mine: bool) -> list[float]:
    """One side's distinct price sequence, with the record echo collapsed.

    A counteroffer is re-recorded as the next round's opening offer at the
    identical price; comparing a price to its own echo reads every mover as
    a staller (the recip-damp postmortem). Used by the probe classifier for
    both sides of the table.
    """
    seq: list[float] = []
    prev_key = None
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        for k in ("offer", "counteroffer"):
            off = entry.get(k)
            if not isinstance(off, dict) or off.get("price") is None:
                continue
            if (off.get("from_player") == me) != of_mine:
                continue
            pr = _num(off["price"])
            if k == "offer" and prev_key == "counteroffer" and seq and pr == seq[-1]:
                prev_key = k
                continue
            seq.append(pr)
            prev_key = k
    return seq


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


def _span_invariant_share() -> float:
    """Share of the visible ZOPA span the invariant protects. 0 = off."""
    share = runtime_flags.as_float("GLEE_NEGO_SPAN_INVARIANT", 0.0)
    if share <= 0:
        return 0.0
    return min(share, 0.95)


def _real_final(p: dict) -> bool:
    """True only when a REAL cap ends the game after this decision.

    Never the planning clock: rounds_left is SYNTHETIC in uncapped games
    (p["capped"] is False there no matter how far the clock has run down).
    """
    return bool(p["capped"]) and p["rounds_left"] <= 1


def _enforce_span_invariant(p: dict, price: float) -> float:
    """Span protection as a final-action INVARIANT on every outgoing price.

    Two leaks this closes, both measured live on 2026-08-21 (Agent 5):

    1. The acceptance veto's clock condition used rounds_left — the SYNTHETIC
       planning clock in uncapped games — so it expired mid-game: uncapped
       complete-info game, visible ZOPA [8000, 12000], we accepted 11,760 as
       the buyer for 6% of the span, -6.8 rating (game dcc290cd). The veto's
       clock is fixed at its call site; this function is the same rule for
       prices WE name.
    2. Outgoing counters were never span-protected — after vetoing their
       sub-floor offer we could counter at our own sub-floor walk price and
       they accept it: a complete-info seller countered at 8% of a 300,000
       span, -5.8 rating.

    Applied as the LAST price transform before every return carrying
    product_price (offer path and both counter paths), after _maybe_split.
    Seller: max() only — it lifts a too-cheap price to zopa_lo + share*span
    and NEVER caps a richer ask (ultimatum's 0.80 claim passes untouched).
    Buyer mirrored: min() against zopa_hi - share*span. Skipped when no
    visible ZOPA, span <= 0, or on a REAL final round (capped and
    rounds_left <= 1 — never the planning clock), where any-profitable
    endgame pricing owns the number. OFF by default.
    """
    share = _span_invariant_share()
    if share <= 0:
        return price
    zopa = p.get("zopa")
    if not zopa:
        return price
    zlo, zhi = zopa
    span = zhi - zlo
    if span <= 0:
        return price
    if _real_final(p):
        return price
    if p["i_am_seller"]:
        protected = zlo + share * span
        if price < protected:
            p["span_invariant_applied"] = round(protected, 2)
            return protected
    else:
        protected = zhi - share * span
        if price > protected:
            p["span_invariant_applied"] = round(protected, 2)
            return protected
    return price


def _finite_wire_number(value) -> float | None:
    """Parse one already-public numeric wire without inventing a default."""
    if isinstance(value, dict):
        value = value.get("price")
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _flag_is_nonzero(name: str) -> bool:
    """Treat numeric arms as active even when their value is not literal 1."""
    raw = runtime_flags.get(name)
    if raw is None:
        return False
    try:
        parsed = float(raw)
        # A non-finite knob is malformed, not safely equivalent to OFF.  Fail
        # the exact-stack pin closed instead of letting NaN evade ``> 0``.
        return not math.isfinite(parsed) or abs(parsed) > 0.0
    except (TypeError, ValueError):
        # Only explicit false spellings are safely inactive.  A typo or other
        # malformed text must not let an overlapping treatment evade the pin.
        return str(raw).strip().lower() not in ("", "false", "no", "off")


def _complete_unknown_late_stasis_stack_ok() -> bool:
    """Pin the guard to the exact deterministic stack measured on 25 Aug."""
    required = (
        "GLEE_NEGO_BOUND_AS_FLOOR",
        "GLEE_NEGO_CONTINUATION_ACCEPT",
        "GLEE_NEGO_CURVE_PRICING",
        "GLEE_NEGO_DEADGAME_V1",
        "GLEE_NEGO_ENDGAME_V3",
        "GLEE_NEGO_HORIZON_V2",
        "GLEE_NEGO_OPEN_CLAIM_ALWAYS",
        "GLEE_NEGO_POSTERIOR",
        "GLEE_NEGO_STALL_POLICY",
        "GLEE_NEGO_TABLE",
    )
    if not all(runtime_flags.enabled(name) for name in required):
        return False
    pinned = (
        ("GLEE_NEGO_ACCEPT_SPAN", 0.48),
        ("GLEE_NEGO_CLAIM_FLOOR", 0.80),
        ("GLEE_NEGO_FINAL_OPTION", 0.60),
        ("GLEE_NEGO_OPEN_CLAIM", 0.95),
        ("GLEE_NEGO_SPAN_INVARIANT", 0.40),
    )
    for name, expected in pinned:
        actual = runtime_flags.as_float(name, math.nan)
        if not math.isfinite(actual) or abs(actual - expected) > 1e-12:
            return False
    # ``deterministic_negotiation.mode`` deliberately maps both whole-policy
    # selectors ON to the legacy stack.  That ambiguity is unacceptable for an
    # evidence-pinned guard, though either one selector or neither is valid.
    if (runtime_flags.enabled(deterministic_negotiation.RANK_HYBRID_FLAG)
            and runtime_flags.enabled(
                deterministic_negotiation.LEADER_REPLICA_FLAG)):
        return False
    return not any(_flag_is_nonzero(name)
                   for name in _COMPLETE_UNKNOWN_LATE_STASIS_CONFLICTS)


def _counter_wire_number(entry: dict, expected_from: str,
                         entry_round: int) -> float | None:
    """Parse a recorded counter, requiring provenance when schema provides it."""
    raw = entry.get("counteroffer")
    if isinstance(raw, dict):
        if raw.get("from_player") != expected_from:
            return None
        counter_round = raw.get("round")
        if counter_round is not None:
            parsed_round = _finite_wire_number(counter_round)
            if parsed_round != float(entry_round):
                return None
    return _finite_wire_number(raw)


def _optional_record_round_matches(record: dict, expected: int) -> bool:
    """Accept canonical history records without a nested round; verify if present."""
    if "round" not in record:
        return True
    return _finite_wire_number(record.get("round")) == float(expected)


def _exact_mutual_stasis_cycles(state: dict, action: dict,
                                me: str) -> tuple[int, float | None, float | None]:
    """Count fully completed, consecutive two-way cycles before this turn.

    Each cycle must contain both record rows: opponent offers P, we reject and
    counter C; our echoed C is then rejected by the opponent, who counters P.
    The current unplayed counter is never counted as evidence.  This prevents a
    provisional action or a missing bridge row from manufacturing ten cycles.
    """
    other = other_player(me)
    current_round_number = _finite_wire_number(state.get("round"))
    current_offer = state.get("last_offer")
    current_counter = _finite_wire_number(action.get("product_price"))
    if (current_round_number is None or not current_round_number.is_integer()
            or current_counter is None or not isinstance(current_offer, dict)
            or current_offer.get("from_player") != other):
        return 0, None, current_counter
    current_round = int(current_round_number)
    offer_round = _finite_wire_number(current_offer.get("round"))
    offer_price = _finite_wire_number(current_offer.get("price"))
    if (offer_round != float(current_round) or offer_price is None):
        return 0, offer_price, current_counter

    by_round: dict[int, dict] = {}
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        round_number = _finite_wire_number(entry.get("round"))
        if round_number is None or not round_number.is_integer():
            continue
        parsed_round = int(round_number)
        if parsed_round in by_round:
            return 0, offer_price, current_counter
        by_round[parsed_round] = entry

    cycles = 0
    for offset in range(1, COMPLETE_UNKNOWN_LATE_STASIS_CYCLES + 1):
        own_round = current_round - 2 * offset
        bridge_round = own_round + 1
        entry = by_round.get(own_round)
        bridge = by_round.get(bridge_round)
        if not isinstance(entry, dict) or not isinstance(bridge, dict):
            break
        historical_offer = entry.get("offer")
        bridge_offer = bridge.get("offer")
        if (not isinstance(historical_offer, dict)
                or historical_offer.get("from_player") != other
                or not _optional_record_round_matches(
                    historical_offer, own_round)
                or entry.get("decided_by") != me
                or entry.get("decision") != "RejectOffer"
                or _finite_wire_number(historical_offer.get("price"))
                != offer_price
                or _counter_wire_number(entry, me, own_round)
                != current_counter
                or not isinstance(bridge_offer, dict)
                or bridge_offer.get("from_player") != me
                or not _optional_record_round_matches(
                    bridge_offer, bridge_round)
                or _finite_wire_number(bridge_offer.get("price"))
                != current_counter
                or bridge.get("decided_by") != other
                or bridge.get("decision") != "RejectOffer"
                or _counter_wire_number(bridge, other, bridge_round)
                != offer_price):
            break
        cycles += 1
    return cycles, offer_price, current_counter


def _maybe_complete_unknown_late_stasis(game: dict, action: dict) -> dict:
    """Accept only a very late, exactly static, mutually feasible live offer.

    This is deliberately NOT the measured-negative hidden unknown-horizon
    accept-all-profitable rule (-.06628 exposed exact percentile, n=375), nor a
    generic "accept after repeats" rename: repeat-3 and repeat-10 fences were
    also negative (-.28173 and -.04804 exact percentile).  In the complete-info
    unknown-horizon all-outcome audit, the post-hoc round>=75 / ten exact mutual
    cycles fence reached 17/17 terminal no-deals and 0/44 agreements.  Its 61
    terminal games implied +.03062 exact percentile, but one of five unresolved
    Agent 5 games also reached and makes the adverse percentile bound -.01553.
    Therefore the implementation is default OFF and research-only: activation
    requires a separately precommitted prospective challenger window.

    When armed, the function runs after every policy component has produced its
    public baseline action.  It can change only that baseline RejectOffer to
    AcceptOffer; offers, counters, earlier rounds, hidden games, known horizons,
    and any changing trajectory remain byte-identical.
    """
    if (not runtime_flags.enabled(COMPLETE_UNKNOWN_LATE_STASIS_FLAG)
            or not isinstance(action, dict)
            or not _complete_unknown_late_stasis_stack_ok()):
        return action

    state = game.get("game_state")
    if (not isinstance(state, dict)
            or game.get("game_family") != "negotiation"
            or (game.get("phase") or state.get("phase")) != "decision"
            or (game.get("valid_actions") or {}).get("type") != "decision"
            or state.get("complete_information") is not True
            or state.get("horizon_known") is not False
            or state.get("max_rounds") is not None):
        return action
    me = state.get("current_player")
    if (me not in ("player_1", "player_2")
            or game.get("your_player") != me):
        return action
    other = other_player(me)
    role = state.get(f"{me}_role")
    expected_other_role = "buyer" if role == "seller" else "seller"
    if (role not in ("seller", "buyer")
            or state.get(f"{other}_role") != expected_other_role):
        return action
    own_value = _finite_wire_number(state.get(f"{me}_value"))
    other_value = _finite_wire_number(state.get(f"{other}_value"))
    round_number = _finite_wire_number(state.get("round"))
    if (own_value is None or other_value is None or round_number is None
            or not round_number.is_integer()
            or int(round_number) < COMPLETE_UNKNOWN_LATE_STASIS_MIN_ROUND):
        return action

    seller_value = own_value if role == "seller" else other_value
    buyer_value = other_value if role == "seller" else own_value
    if buyer_value <= seller_value:
        return action
    # Strategy actions are not the submitted wire.  OPEN_CLAIM and CLAIM_FLOOR
    # can rewrite a RejectOffer counter in ``actions.coerce``; compare history
    # with that final counter so the guard proves reachability on the real stack.
    public_baseline = {
        key: value for key, value in action.items()
        if not str(key).startswith("_")
    }
    try:
        projected = coerce(public_baseline, game)
    except Exception:
        return action
    if projected.get("decision") != "RejectOffer":
        return action
    cycles, offer_price, counter_price = _exact_mutual_stasis_cycles(
        state, projected, me)
    if offer_price is None or counter_price is None:
        return action
    if not seller_value <= offer_price <= buyer_value:
        return action
    profitable = offer_price > own_value if role == "seller" \
        else offer_price < own_value
    if not profitable:
        return action

    result = dict(action)
    plan_data = dict(result.get("_plan") or {})
    eligible = cycles >= COMPLETE_UNKNOWN_LATE_STASIS_CYCLES
    plan_data["complete_unknown_late_stasis_v1"] = {
        "eligible": eligible,
        "round": int(round_number),
        "cycles": cycles,
        "offer_price": offer_price,
        "counter_price": counter_price,
        "mode": "deterministic",
    }
    if eligible:
        if _trace_enabled():
            plan_data.setdefault("gates_fired", [])
        _gate(plan_data, "complete_unknown_late_stasis_v1")
        result = {"decision": "AcceptOffer"}
    result["_plan"] = plan_data
    return result


def decide(game: dict, cfg) -> dict:
    """Choose a default-off deterministic component or the existing stack.

    The deterministic policies are mutually exclusive runtime flags, never
    game-hash arms.  While one is selected, the legacy randomized message bank
    is deliberately bypassed so a complete policy cannot silently become a
    mixed treatment.  Flag-off behavior retains the original attachment path.
    """
    # The exact last-mover component must precede the broader deterministic
    # buyer replicas.  Otherwise a selected replica returns before _decide()
    # and silently shadows the cent-leaving terminal price.  This override is
    # itself deterministic and owns only first_principles.DESIGNED cells.
    if first_principles.deterministic_owns(game):
        action = first_principles.action(game)
        if action is not None:
            plan = {
                "source": first_principles.DETERMINISTIC_GATE,
                "component": "first_principles",
            }
            if runtime_flags.enabled("GLEE_TRACE_GATES"):
                plan["gates_fired"] = [first_principles.DETERMINISTIC_GATE]
            action["_plan"] = plan
        else:
            action = _decide(game, cfg)
    else:
        selected = deterministic_negotiation.mode()
        if selected is not None:
            action = _deterministic_policy_decide(game, cfg, selected)
        else:
            action = _decide(game, cfg)
            try:
                if nego_arms.enabled():
                    nego_arms.attach(game, action)
            except Exception:
                pass              # a message is never worth risking the move
    return _maybe_complete_unknown_late_stasis(game, action)


def _deterministic_policy_decide(game: dict, cfg, selected: str) -> dict:
    """Execute one complete role/information/horizon policy matrix."""
    direct = deterministic_negotiation.direct_action(game, selected)
    if direct is not None:
        return direct

    # Sellers retain the measured winning decision/price stack.  The full
    # replica additionally applies the exact message-only seller table from
    # Test 4's live profile (implied percentile 0.568 over its first 52 clean
    # games and 0.549 after 77).  The rank hybrid keeps current seller text and
    # current hidden-cap1/unknown buyer behavior.
    action = _decide(game, cfg)
    if selected == deterministic_negotiation.LEADER_REPLICA:
        return top_seller_message_clone.apply_deterministic(game, action)
    if selected == deterministic_negotiation.AGENT5_DEFAULT:
        action = top_seller_message_clone.apply_deterministic(
            game, action, arm=selected)
    plan = dict(action.get("_plan") or {})
    plan["deterministic_policy"] = selected
    plan["component"] = deterministic_negotiation.fallback_component(game)
    if (selected == deterministic_negotiation.AGENT5_DEFAULT
            and runtime_flags.enabled("GLEE_TRACE_GATES")):
        gates = list(plan.get("gates_fired") or [])
        if deterministic_negotiation.AGENT5_DEFAULT_GATE not in gates:
            gates.append(deterministic_negotiation.AGENT5_DEFAULT_GATE)
        plan["gates_fired"] = gates
    action = dict(action)
    action["_plan"] = plan
    return action


def _decide(game: dict, cfg) -> dict:
    # The broad clone's only coherent positive cell at its fixed official
    # checkpoint was hidden-information cap-10 buyers (+1.81 rating/game and a
    # lower no-deal rate, candidate n=15/control n=11).  Because that slice was
    # selected post hoc, this independent salt re-tests it prospectively and
    # owns the complete move only in that exact cell.
    if top_buyer_clone_hi_cap10.owns(game):
        scoped_clone_action = top_buyer_clone_hi_cap10.action(game)
        if scoped_clone_action is not None:
            return scoped_clone_action

    # Opus's first 43 hidden unknown-horizon buyer coefficients are direct
    # observed wires.  In a recent pre-arm window this exact slice reached 103
    # games / 1,057 changed states on the four intended hosts.  It is statically
    # disjoint from the live known-cap-10 clone above; unsupported late branches
    # deliberately fall through to the complete current stack.
    if top_opus_buyer_clone_hi_unknown.owns(game):
        scoped_opus_action = top_opus_buyer_clone_hi_unknown.action(game)
        if scoped_opus_action is not None:
            return scoped_opus_action

    # The observed-leader buyer clone is a full-policy treatment: both its
    # prices and accept/reject boundary must move together or the experiment
    # would repeat the single-flag/two-mechanism failure.  Candidate games are
    # therefore returned before the layered planner; hash controls fall through
    # to the complete current stack.
    if top_buyer_clone.owns(game):
        clone_action = top_buyer_clone.action(game)
        if clone_action is not None:
            return clone_action

    # The second direct-leader reconstruction is intentionally partial.  It
    # owns only point-identified Opus buyer wires and decisions; every
    # unidentified late branch executes the complete current control policy.
    # Its module also fails closed while the 7aidara clone is armed, preventing
    # a game from entering two imitation experiments.
    if top_opus_buyer_clone.owns(game):
        opus_action = top_opus_buyer_clone.action(game)
        if opus_action is not None:
            return opus_action

    # The first-principles policy owns its cells outright: it is consulted before
    # plan() so no concession schedule, stall detector or span invariant can see
    # -- let alone rewrite -- the price it returns.  actions.py yields to it too.
    # Cells it does not claim fall through untouched.
    if first_principles.owns(game):
        fp_action = first_principles.action(game)
        if fp_action is not None:
            fp_action["_plan"] = {"source": "first_principles"}
            return fp_action

    state = game["game_state"]
    p = plan(game, cfg)

    if game["valid_actions"]["type"] == "offer":
        # Rank pricing is already the argmax over every supported terminal price.
        # A later split transform could greedify a seller ask (or lowball a buyer
        # offer) and silently submit a different price than the plan records.
        rank_applied = (p.get("rank_price") or {}).get("status") == "applied"
        price = p["target"] if rank_applied else _maybe_split(state, p, p["target"])
        p["split_taken"] = price != p["target"]
        if p["split_taken"]:
            _gate(p, "split")
        price = _enforce_span_invariant(p, price)
        return {"product_price": round(price, 2), "_plan": p}

    # --- decision phase ---
    offer_price = _num((state.get("last_offer") or {}).get("price"), 0.0)
    p["offered_price"] = offer_price
    # Only a REAL cap ends the game. p["capped"] is False for uncapped games no
    # matter how far the planning clock has run down.
    if _horizon_v2_enabled():
        # Only a REAL cap ends the game.
        final = is_final_round(state) or (p["capped"] and p["rounds_left"] <= 1)
    else:
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

    # Dead-game walk-away: proven-unprofitable opponent bound + confirmed
    # stall + late uncapped game = the 99-round grind from the transcript
    # export. Walking banks the same 0 the grind ends in, frees the queue
    # slot ~25 rounds sooner, and (unlike a timeout at the 5th percentile)
    # costs nothing. Capped games never walk -- the final-round any-positive
    # rule above may still convert them.
    if (p.get("deadgame") and not p["capped"] and p["elapsed"] >= 0.6
            and not _profitable(offer_price, p)
            and _their_stall_price(state, state.get("current_player") or "") is not None):
        _gate(p, "deadgame_walk")
        return {"decision": "WalkAway", "_plan": p}

    # Span-floor acceptance veto. The 500-game transcript export scored 77
    # complete-info closes below 40% of the visible ZOPA span at -5.07 rating
    # EACH (closes at >=55% averaged +4.52), and 53 of them were our own
    # AcceptOffer with rounds to spare: continuation value underestimates what
    # holding is worth, so "beats continuation" accepts lowballs the field
    # prices at ~half the span. While the ZOPA is visible and >=2 rounds
    # remain, refuse anything below this share of the span and counter on the
    # profitable side instead. Final-round any-positive stays untouched above.
    # OFF by default.
    # Clock condition: rounds_left is the SYNTHETIC planning clock in uncapped
    # games, so `rounds_left >= 2` let the veto EXPIRE mid-game with no real
    # deadline anywhere (the 11,760 accept above). Under the span invariant the
    # veto stands whenever this is not a REAL final round; the invariant share
    # also acts as an acceptance floor of its own, so the protection cannot be
    # disarmed by omitting GLEE_NEGO_ACCEPT_SPAN. With the invariant off, the
    # legacy condition is kept bit-for-bit.
    _span_floor = runtime_flags.as_float("GLEE_NEGO_ACCEPT_SPAN", 0.0)
    _inv_share = _span_invariant_share()
    if _inv_share > 0:
        _veto_floor = max(_span_floor, _inv_share)
        _veto_live = not _real_final(p)
    else:
        _veto_floor = _span_floor
        _veto_live = p["rounds_left"] >= 2
    if _veto_floor > 0 and p.get("zopa") and _veto_live:
        _zlo, _zhi = p["zopa"]
        _span = _zhi - _zlo
        if _span > 0:
            _share = ((offer_price - _zlo) / _span) if p["i_am_seller"] \
                else ((_zhi - offer_price) / _span)
            p["span_share"] = round(_share, 3)
            if _share < _veto_floor:
                p["span_veto"] = True
                _gate(p, "span_veto")
                counter = p["target"]
                if _profitable(offer_price, p):
                    counter = max(offer_price, counter) if p["i_am_seller"] \
                        else min(offer_price, counter)
                _c0 = counter
                counter = _maybe_split(state, p, counter)
                if counter != _c0:
                    _gate(p, "split")
                counter = _enforce_span_invariant(p, counter)
                return {"decision": "RejectOffer",
                        "product_price": round(counter, 2), "_plan": p}

    # FINAL-PROPOSER OPTION VALUE. Rejecting is not merely "wait and see what
    # they offer next" -- in a capped game with an even number of remaining
    # turns, rejecting hands US the last take-it-or-leave-it price, and there
    # is no discounting in negotiation to erode it. The coarse table threshold
    # cannot represent that option: measured live, a 1.5xB buyer accepted
    # 1.375xB in round 9 of 10 for 17.8% of a 0.7xB surplus (-7.1 rating)
    # because the offer cleared an absolute end-phase threshold of 0.118xB by
    # 0.006 -- while rejecting would have made it the round-10 proposer.
    # When we own the final proposal, compare against what that proposal is
    # worth (its expected acceptance times its surplus) rather than against a
    # constant. OFF by default.
    final_opt = runtime_flags.as_float("GLEE_NEGO_FINAL_OPTION", 0.0)
    own_final = False
    if final_opt > 0.0 and p.get("capped") and p["rounds_left"] >= 2:
        # turns alternate; we propose next, so an EVEN number of remaining
        # turns means the last one is ours
        own_final = (int(p["rounds_left"]) % 2) == 0
        if own_final:
            _fb = _final_option_value(state, p, final_opt)
            if _fb is not None:
                p["final_option_value"] = _fb
                if surplus_now < _fb:
                    p["final_option_hold"] = True
                    _gate(p, "final_option")
                    counter = p["target"]
                    if _profitable(offer_price, p):
                        counter = max(offer_price, counter) if p["i_am_seller"] \
                            else min(offer_price, counter)
                    counter = _maybe_split(state, p, counter)
                    counter = _enforce_span_invariant(p, counter)
                    return {"decision": "RejectOffer",
                            "product_price": round(counter, 2), "_plan": p}

    # Learned-table acceptance: in hidden games the evolved threshold decides
    # mid-game acceptance when present; final-round any-positive stays above.
    # NOTE the table's ask maps are EMPTY in models/nego_policy_v1.json (0
    # seller cells, 0 buyer cells, verified by sha256 f20c8620), so
    # table_policy.offer() has always returned None -- this gate is the whole
    # of what GLEE_NEGO_TABLE does. Its four absolute thresholds ignore the
    # available surplus, so the same 0.118xB bar is 59% of a 0.2xB surplus and
    # 17% of a 0.7xB one, and its phase buckets step from 0.330xB to 0.076xB
    # between rounds 4 and 5 of ten -- an artificial surrender point.
    if (p.get("their_value") is None
            and runtime_flags.enabled("GLEE_NEGO_TABLE")):
        t_thr = table_policy.accept_threshold(
            p["my_value"], p["i_am_seller"], p.get("elapsed", 0.5))
        if t_thr is not None:
            if _profitable(offer_price, p) and surplus_now >= t_thr:
                # The table may only ACCEPT once nothing better is available:
                # with the final proposal in hand it is not allowed to close
                # under the option value computed above.
                if not (own_final and p.get("final_option_value") is not None
                        and surplus_now < p["final_option_value"]):
                    hold_for_vcont = _maybe_table_vcont_precedence(
                        state, p, offer_price, surplus_now, v_cont, evidence,
                        t_thr)
                    if not hold_for_vcont:
                        veto = _maybe_hidden_min_share_veto(
                            state, p, offer_price, "table_accept")
                        if veto is not None:
                            return veto
                        _gate(p, "table_accept")
                        return {"decision": "AcceptOffer", "_plan": p}
                if not p.get("table_accept_vetoed"):
                    # Preserve the legacy diagnostic for earlier owners (for
                    # example FINAL_OPTION) that made TABLE fall through even
                    # after its numeric threshold cleared.
                    p["table_accept_below"] = True
            else:
                # Below threshold: fall through to counter via the offer path.
                # A candidate precedence veto also falls through, but it passed
                # the threshold and is recorded separately above rather than
                # contaminating this diagnostic.
                p["table_accept_below"] = True

    if runtime_flags.enabled("GLEE_NEGO_STALL_POLICY"):
        _sp = _their_stall_price(state, state.get("current_player") or "")
        if (_sp is not None and _profitable(offer_price, p)
                and abs(offer_price - _sp) <= 0.01 * max(abs(_sp), 1.0)):
            veto = _maybe_hidden_min_share_veto(
                state, p, offer_price, "stall_accept")
            if veto is not None:
                return veto
            _gate(p, "stall_accept")
            return {"decision": "AcceptOffer", "_plan": p}

    if p["continuation_accept"]:
        # Accept when the offer beats what rejecting is worth. NOT when it beats
        # our own current ask — those are different questions, and conflating
        # them is what threw away 716 profitable offers.
        if _profitable(offer_price, p) and surplus_now >= v_cont:
            veto = _maybe_hidden_min_share_veto(
                state, p, offer_price, "continuation_accept")
            if veto is not None:
                return veto
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
    _c0 = counter
    counter = _maybe_split(state, p, counter)
    if counter != _c0:
        _gate(p, "split")
    counter = _enforce_span_invariant(p, counter)
    precedence = p.get("table_vcont_precedence")
    if isinstance(precedence, dict) and precedence.get("arm") == "candidate":
        precedence["counter_price"] = round(counter, 2)
    return {"decision": "RejectOffer", "product_price": round(counter, 2), "_plan": p}


def _final_option_value(state: dict, p: dict, weight: float) -> float | None:
    """What our own final take-it-or-leave-it proposal is worth, in surplus.

    Rejecting an offer when we own the last proposal is not a gamble on their
    next concession -- it buys the right to name the closing price. That right
    is worth P(they accept our final ask) x (our surplus at that ask), and the
    acceptance side is exactly what models/negotiation_acceptance_v5.json
    measures. `weight` shrinks the estimate (a live-tunable haircut, since a
    rejected final offer pays zero and the curve is a field average, not this
    opponent). None when we cannot price it -- caller keeps its baseline.

    Complete information: they accept anything leaving them a sliver, so the
    ask is the zopa bound less the usual give, and acceptance is near-certain.
    Hidden information: use the fitted final-round curve via pricing.
    """
    my_value = p["my_value"]
    i_am_seller = p["i_am_seller"]
    zopa = p.get("zopa")
    if zopa is not None:
        lo, hi = zopa
        span = hi - lo
        if span <= 0:
            return None
        share = _zopa_share(p.get("game_id"), 0.2)
        give = min(max(share, 0.0), 0.5) * span
        ask = (hi - give) if i_am_seller else (lo + give)
        surplus = (ask - my_value) if i_am_seller else (my_value - ask)
        # a final offer inside the visible zone that still pays them `give`
        # is accepted by anything rational; haircut carries the doubt
        return max(surplus, 0.0) * min(max(weight, 0.0), 1.0)
    # Hidden information: score candidate final prices against the fitted
    # final-round acceptance curve for our seat and keep the best expected
    # surplus. The seller path has a dedicated helper; the buyer path reads the
    # same pooled curve directly (models/negotiation_acceptance_v5.json carries
    # buyer_final as well as seller_final), which is what the live failure
    # needed -- a 1.5xB BUYER in round 9 of 10 had no way to price its own
    # round-10 offer, so the option value came back None and the coarse table
    # closed the game at 17.8% of the surplus.
    base = pricing.infer_base(my_value)
    if base is None:
        return None
    if i_am_seller:
        ask = pricing.seller_final_ask(my_value)
        if ask is None:
            return None
        surplus = ask - my_value
    else:
        rows = (pricing._curves() or {}).get("buyer_final") or []
        best = 0.0
        for row in rows:
            if row.get("n", 0) < 20:
                continue
            pa = row.get("p_accept") or 0.0
            if pa <= 0.0:
                continue
            price = (row["lo"] + row["hi"]) / 2.0 * base
            s = my_value - price
            if s <= 0:
                continue
            best = max(best, pa * s)
        if best <= 0.0:
            return None
        # `best` already carries P(accept); return it as an expected surplus
        return best * min(max(weight, 0.0), 1.0)
    if surplus <= 0:
        return None
    return surplus * min(max(weight, 0.0), 1.0)
