"""Grounded message templates — the language channel without an LLM.

The channel is open in about a third of bargaining and negotiation turns and in
half of all persuasion turns, where in text mode the message IS the entire move.
Live data shows opponents using it well: they cite discount asymmetry, claim
reservation prices, and spend a round declining to recommend in order to buy
credibility for later ones.

We were sending two fixed strings. These templates are the floor: they say
something true and specific drawn from the solver's own reasoning, which is what
makes a message move an opponent rather than decorate an offer. When an LLM
provider key is configured, llm.write_message supersedes this — but a failed or
slow provider call falls back here rather than to nothing.

Nothing here changes a single number. The move is already decided; this only
chooses how to say it.
"""

from __future__ import annotations

import random

from .actions import _num


def _pick(rng: random.Random, options: list[str]) -> str:
    """Vary the phrasing so a repeat opponent cannot key on a fixed string."""
    return rng.choice(options)


def bargaining_message(game: dict, action: dict, plan: dict | None,
                       rng: random.Random) -> str | None:
    state = game.get("game_state") or {}
    if not plan:
        return None
    money = _num(state.get("money_to_divide"), 0.0)
    me_is_alice = game.get("your_player") == "player_1"
    mine = _num(action.get("alice_gain" if me_is_alice else "bob_gain"), 0.0)
    theirs = money - mine
    delta_me = plan.get("delta_me", 1.0)
    delta_opp = plan.get("delta_opp", 1.0)
    rounds_left = plan.get("rounds_left")
    share = (mine / money) if money else 0.5

    parts = []
    # Lead with the split, stated plainly — vagueness invites a counteroffer.
    parts.append(_pick(rng, [
        f"You take {theirs:,.0f} of {money:,.0f}.",
        f"My proposal leaves you {theirs:,.0f}.",
        f"{theirs:,.0f} to you, {mine:,.0f} to me.",
    ]))

    # The strongest true argument available, in order of force. Conceding hard
    # and claiming leverage in the same breath reads as bluster, so the
    # leverage lines are gated on actually holding some.
    holding_ground = share >= 0.45
    knows_their_delta = state.get("complete_information") is True
    if rounds_left is not None and rounds_left <= 1:
        parts.append(_pick(rng, [
            "This is the last round — if you reject, we both take nothing.",
            "There is no round after this one. Rejecting pays us both zero.",
        ]))
    elif knows_their_delta and holding_ground and delta_opp < delta_me - 0.01:
        parts.append(_pick(rng, [
            "Delay costs you more per round than it costs me, so waiting shrinks "
            "your side of this faster than mine.",
            "Your value decays faster than mine here. Time is not on your side.",
        ]))
    elif delta_me < 1.0 or delta_opp < 1.0:
        parts.append(_pick(rng, [
            "Every round we spend costs us both real value — settling now beats a "
            "marginally better split later.",
            "Inflation takes a bite out of this each round. Closing now is worth "
            "more than haggling.",
        ]))
    if rounds_left is not None and 1 < rounds_left <= 3:
        parts.append(f"We have {int(rounds_left)} rounds left before this pays nothing.")

    evidence = plan.get("opponent_evidence") or {}
    if evidence.get("basis", "").startswith("opponent not conceding") and holding_ground:
        parts.append(_pick(rng, [
            "You have not moved in several rounds. I am willing to close, but not "
            "to keep trading the same offer until it is worthless.",
            "Neither of us gains by repeating ourselves into a zero.",
        ]))
    elif share >= 0.6 and knows_their_delta:
        parts.append("I have priced this off the discount rates, not off a "
                     "fairness norm.")
    elif not holding_ground:
        # We are conceding. Say so as a closing move rather than posturing.
        parts.append(_pick(rng, [
            "That is a serious move toward you. I would like to close here.",
            "I have come a long way to you on this. Let us finish it.",
        ]))
    return " ".join(parts)[:1800]


def negotiation_message(game: dict, action: dict, plan: dict | None,
                        rng: random.Random) -> str | None:
    if not plan:
        return None
    price = _num(action.get("product_price"), 0.0)
    seller = plan.get("i_am_seller")
    reservation = plan.get("reservation", 0.0)
    rounds_left = plan.get("rounds_left")
    decision = action.get("decision")

    if decision == "AcceptOffer":
        return _pick(rng, ["Agreed — done at that price.", "That works. Closing here."])

    parts = []
    if price:
        parts.append(_pick(rng, [
            f"{price:,.2f}.",
            f"I can do {price:,.2f}.",
            f"My number is {price:,.2f}.",
        ]))
    # Near the reservation the strongest honest claim is that there is no room.
    close_to_limit = (abs(price - reservation) / reservation < 0.10) if reservation else False
    if close_to_limit:
        parts.append(_pick(rng, [
            "That is effectively my limit — below it I am better off with no deal.",
            "There is no meaningful room left on my side of this.",
        ]))
    elif seller:
        parts.append(_pick(rng, [
            "I would rather trade than not, but not at any number.",
            "Priced to close, not to start a haggle.",
        ]))
    else:
        parts.append(_pick(rng, [
            "That leaves you a clear gain over walking away.",
            "This is a real offer, and it beats no deal for both of us.",
        ]))
    # Deadline talk only when the deadline is REAL. In uncapped games
    # rounds_left is the synthetic planning clock, and the transcript export
    # showed "nearly out of rounds" repeated from round 11 to round 99 of a
    # hidden-horizon game -- a claim any patient opponent can falsify by
    # simply waiting, which converts the message from leverage into a leak.
    if (rounds_left is not None and rounds_left <= 2
            and plan.get("capped", False)):
        parts.append("We are nearly out of rounds, and no deal pays us both zero.")
    return " ".join(parts)[:1800]


def persuasion_message(game: dict, action: dict, plan: dict | None,
                       rng: random.Random) -> str | None:
    """Text mode: the message IS the move, so it must carry the recommendation.

    A seller's only asset is credibility across rounds, so an honest round is
    said plainly — that is what makes the recommending rounds worth anything.
    """
    if not plan:
        return None
    recommend = plan.get("recommend", True)
    round_no = int(_num(plan.get("round"), 1))
    total = int(_num(plan.get("total_rounds"), 1))
    reason = str(plan.get("reason", ""))
    # Whether THIS recommendation is truthful. A promise of candour made while
    # pushing a known-low unit is falsifiable the moment the buyer purchases,
    # and a broken promise costs more credibility than saying nothing.
    truthful = plan.get("quality_is_high", None)

    if not recommend:
        # Declining to sell is the credibility purchase. Say so explicitly.
        return _pick(rng, [
            "Not this one. It is below the standard I want to put my name to — "
            "wait for the next.",
            "I would pass on this unit. I would rather tell you that than sell it "
            "to you and lose your trust for the rest of these rounds.",
            "Honestly, this one is weak. Skip it.",
        ])

    parts = [_pick(rng, [
        "This one is worth taking.",
        "Strong unit this round — I would buy it.",
        "This is one of the better ones.",
    ])]
    if truthful and (reason.startswith("building reputation") or round_no <= 2):
        parts.append("I will tell you plainly when a unit is not worth it, so you "
                     "can judge me by the ones I do recommend.")
    elif truthful is False:
        # Pushing a weak unit: stay generic. No verifiable claim to be caught on.
        parts.append(_pick(rng, [
            "Priced the same as every other round, so the call is yours.",
            "Same price as always — take it or leave it on your own read.",
        ]))
    elif round_no >= max(2, total - 1):
        parts.append("We are near the end and my record this game is what it is — "
                     "check it against how I have called these.")
    else:
        parts.append(_pick(rng, [
            "You can check that against the calls I have made so far.",
            "My record on these is the reason to take this one seriously.",
        ]))
    return " ".join(parts)[:1800]


# --------------------------------------------------------------------------
# NEGOTIATION MESSAGE ARMS — the randomised bank behind GLEE_NEGO_MSG_ARMS.
#
# ``negotiation_message`` above is the single un-randomised template: it picks
# the strongest available line and sends it, which is fine for playing and
# useless for measuring, because every offer gets the treatment its own state
# selected. The arms below hold the NUMBER fixed and vary only the argument, so
# the difference between two arms is attributable to the words.
#
# Four slots, assembled in this order:
#
#     [FRAME] + [CLAIM] + [REQUEST]  (+ FILLER to reach the length band)
#
# FRAME, REQUEST and FILLER are drawn from pools shared by every messaged arm,
# from one rng seeded per turn (not per arm), so length is matched by
# construction and the only systematic difference between N1 and a treatment is
# the CLAIM. The claim itself is chosen DETERMINISTICALLY — first available in
# an ordered ladder, no rng — so "which arms are eligible here" and "what this
# arm would say here" are the same question, and the randomiser can drop an arm
# that would go quiet before it spends a block slot on it.
#
# Truth discipline, inherited from experiments/framing.py and from the
# persuasion post-mortem that produced it:
#   * every claim tagged ``fact`` is arithmetic over public objects — a price
#     the opponent themselves named, a price we ourselves named, a valuation the
#     server disclosed to both sides, or a rule of the game;
#   * the one claim tagged ``bluff`` (N3's mandate language) is an unverifiable
#     statement about our OWN position, legal under the rules, and it is gated
#     to states where our own schedule is not about to contradict it next round;
#   * no arm ever makes a falsifiable promise about our own future moves, and
#     no arm reveals our private valuation.
# --------------------------------------------------------------------------

#: Bump when a pool or a claim precondition changes; it feeds the arm-set
#: version, so a mid-flight edit shows up in the analysis instead of pooling
#: silently with data collected under the old grammar.
NEGO_ARM_GRAMMAR_VERSION = "nego-msg-grammar-1"

#: Realised length band. The floor is what makes N1 a length-matched control
#: rather than a terser one; the ceiling is an eighth of the server's 2,000.
NEGO_ARM_LEN_LO, NEGO_ARM_LEN_HI = 180, 320

NEGO_ARM_SEMANTICS = {
    "N0": "silent — no message attached, though the channel is open. This is "
          "exactly what the fleet does today, so it is the control that makes "
          "the whole experiment a measurement of the channel itself.",
    "N1": "neutral, length-matched — states the price and hands the turn back. "
          "Text with no argument in it; the reference for every contrast.",
    "N2": "precise anchor — the price to the cent, plus a concrete derivation "
          "over public numbers (their bid, our previous ask, the disclosed "
          "band). A round number reads as an opening gesture; a worked one "
          "reads as a constraint.",
    "N3": "mandate freeze — this is the limit of my mandate, and the "
          "alternative is no deal, which pays us both zero. Unverifiable about "
          "our own side, so gated to states where our own schedule will not "
          "refute it next round.",
}

NEGO_ARMS = ("N0", "N1", "N2", "N3")


def _fmt(x: float) -> str:
    return f"{x:,.2f}"


def _nego_prices(state: dict, me: str) -> tuple[list[float], list[float]]:
    """(prices we named, prices they named), oldest first.

    Local to this module on purpose: importing the negotiation strategy here
    would make the message bank a dependency of the decision core rather than
    the other way round.
    """
    ours: list[float] = []
    theirs: list[float] = []
    entries = list(state.get("history") or [])
    last = state.get("last_offer")
    if isinstance(last, dict):
        entries = entries + [{"offer": last}]
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for key in ("offer", "counteroffer"):
            offer = entry.get(key)
            if not isinstance(offer, dict) or offer.get("price") is None:
                continue
            price = _num(offer["price"])
            bucket = ours if offer.get("from_player") == me else theirs
            if not bucket or bucket[-1] != price:
                bucket.append(price)          # collapse the record echo
    return ours, theirs


def _nego_arm_facts(game: dict, action: dict, plan: dict) -> dict | None:
    """Everything a claim may read, computed once. Numbers in, no numbers out."""
    price = action.get("product_price")
    if price is None:
        return None
    price = _num(price, -1.0)
    if price < 0:
        return None
    state = game.get("game_state") or {}
    me = state.get("current_player") or game.get("your_player") or "player_1"
    ours, theirs = _nego_prices(state, me)
    if ours and abs(ours[-1] - price) < 0.005:
        ours = ours[:-1]                      # this very offer, already recorded
    zopa = plan.get("zopa")
    return {
        "price": price,
        "i_am_seller": bool(plan.get("i_am_seller")),
        "round": int(_num(state.get("round"), 1)),
        "rounds_left": int(_num(plan.get("rounds_left"), 1)),
        "capped": bool(plan.get("capped")),
        "reservation": _num(plan.get("reservation"), 0.0),
        "our_prev": ours[-1] if ours else None,
        "their_last": theirs[-1] if theirs else None,
        "zopa": zopa if isinstance(zopa, (tuple, list)) and len(zopa) == 2 else None,
        # Any of these means the concession schedule is frozen for now, so
        # "this is where I stop" is not about to be refuted by our own next move.
        "frozen": bool(plan.get("ultimatum") or plan.get("deadgame")
                       or plan.get("probe_hold") or plan.get("recip_damped")
                       or plan.get("time_driven") or plan.get("span_veto")),
    }


def _n2_claim(f: dict) -> dict | None:
    """PRECISE. Ordered ladder; the first that fires wins. Always fires.

    The claims refer back to the price rather than restating it: the FRAME slot
    already names it to the cent in every arm, so re-quoting it here would put
    the number twice in the treatment arms and once in the control — a length
    and salience difference that is not the treatment.
    """
    price, seller = f["price"], f["i_am_seller"]
    their = f["their_last"]
    if their is not None:
        gap = (price - their) if seller else (their - price)
        if gap >= 0.01:
            return {"claim_id": "n2_gap_vs_their_bid", "claim_kind": "fact",
                    "text": (f"That is {_fmt(gap)} "
                             f"{'above' if seller else 'below'} the {_fmt(their)} "
                             f"you named, and that gap is the whole of what is "
                             f"still open between us.")}
    prev = f["our_prev"]
    if prev is not None and abs(prev - price) >= 0.01:
        step = abs(prev - price)
        return {"claim_id": "n2_step_from_our_last", "claim_kind": "fact",
                "text": (f"That is {_fmt(step)} "
                         f"{'down from' if (prev > price) else 'up from'} the "
                         f"{_fmt(prev)} I named before — a worked step, not a "
                         f"round number chosen to look like one.")}
    if f["zopa"]:
        lo, hi = _num(f["zopa"][0]), _num(f["zopa"][1])
        span = hi - lo
        if span > 0 and lo - 0.01 <= price <= hi + 0.01:
            share = (price - lo) / span
            return {"claim_id": "n2_zopa_share", "claim_kind": "fact",
                    "text": (f"That sits {share * 100:.1f}% of the way across the "
                             f"{_fmt(span)} between our two disclosed valuations, "
                             f"which is exactly where the number comes from.")}
    return {"claim_id": "n2_exact", "claim_kind": "fact",
            "text": ("That figure is exact to the cent: it is worked out from "
                     "what this trade is worth to me and how many rounds are "
                     "left in it, not rounded off into an opening position.")}


def _n3_claim(f: dict) -> dict | None:
    """MANDATE FREEZE. Defined only where our own schedule will not refute it.

    The mandate sentence is a bluff — unverifiable, about our own side, legal.
    The sentence beside it is a fact: a no-deal pays both sides zero. What the
    gate buys is that nothing WE do next round contradicts the bluff, which is
    the failure mode that makes a bluff cost more than silence.
    """
    if f["capped"] and f["rounds_left"] <= 1:
        return {"claim_id": "n3_terminal", "claim_kind": "bluff",
                "text": ("There is no round after this one: if that does not "
                         "close, we both book zero. It is also the limit of my "
                         "mandate, so it is the whole decision in front of you.")}
    reservation = f["reservation"]
    if reservation and abs(f["price"] - reservation) <= 0.10 * abs(reservation):
        return {"claim_id": "n3_at_limit", "claim_kind": "bluff",
                "text": ("That is the limit of my mandate on this one. The "
                         "alternative is no deal, and no deal pays us both "
                         "exactly zero.")}
    if f["frozen"]:
        return {"claim_id": "n3_frozen", "claim_kind": "bluff",
                "text": ("I have taken this as far as my mandate allows, and "
                         "that is where it stops. If we do not close, we both "
                         "take zero out of it.")}
    return None


_NEGO_ARM_CLAIMS = {"N2": _n2_claim, "N3": _n3_claim}


def negotiation_arm_claim(arm: str, game: dict, action: dict,
                          plan: dict | None) -> dict | None:
    """The claim ``arm`` would make here, or ``None`` when it has none.

    Deterministic: no rng, so the randomiser can ask this question before it
    draws. N0 and N1 carry no claim by definition and are not asked.
    """
    try:
        builder = _NEGO_ARM_CLAIMS.get(arm)
        if builder is None or not isinstance(plan, dict):
            return None
        facts = _nego_arm_facts(game, action, plan)
        if facts is None:
            return None
        return builder(facts)
    except Exception:
        return None


def _nego_arm_frames(f: dict) -> list[str]:
    p = _fmt(f["price"])
    return [f"{p}.", f"My number is {p}.", f"I can do {p}.",
            f"Round {f['round']}: {p}.", f"The price I am naming is {p}."]


def _nego_arm_requests(arm: str) -> list[str]:
    if arm == "N1":
        return ["It is your call.", "Over to you.", "Your move.",
                "Respond as you see fit.", "The decision is yours."]
    return ["Accept and we are done.", "Take it and this closes here.",
            "Say yes and neither of us spends another round on it.",
            "Close it here.", "Accept, and we both book this now."]


def _nego_arm_fillers(f: dict) -> list[str]:
    """Argument-free, true, on-topic padding, shared across every messaged arm."""
    return [
        f"This is round {f['round']}.",
        f"The price named is {_fmt(f['price'])}.",
        f"I am the {'seller' if f['i_am_seller'] else 'buyer'} here.",
        "No conditions are attached to the price.",
        "That is the number as submitted.",
        "One price, one product, nothing else in the package.",
        "The offer stands exactly as written.",
        "Nothing else is bundled with it.",
        "That is the whole of my proposal for this round.",
    ]


def _fit(rng: random.Random, options: list[str], budget: int) -> str:
    """A random option that fits the budget; the shortest one if none does.

    Choosing to fit rather than choosing then trimming is what keeps the claim
    inviolable: a trimmer can amputate the qualifier that made a sentence true.
    """
    pool = [o for o in options if o]
    if not pool:
        return ""
    order = list(pool)
    rng.shuffle(order)
    for option in order:
        if len(option) <= budget:
            return option
    return min(pool, key=len)


def _assemble_nego_arm(frames: list[str], claim: str, requests: list[str],
                       fillers: list[str], rng: random.Random) -> str:
    """Fill the slots around the claim, then pad toward the band floor.

    Priority is fixed and arm-independent. The CLAIM is the treatment and is
    never shortened or dropped. The REQUEST is a slot every arm fills, so
    dropping it for some arms would make slot presence itself correlate with the
    arm. The FRAME comes third; filler is added last and only to reach LEN_LO.
    """
    def join(parts):
        return " ".join(p.strip() for p in parts if p and p.strip())

    claim = (claim or "").strip()
    min_frame = min((len(x) for x in frames if x), default=0)
    request = _fit(rng, requests, max(0, NEGO_ARM_LEN_HI - len(claim) - min_frame - 2))
    frame = _fit(rng, frames, max(0, NEGO_ARM_LEN_HI - len(claim) - len(request) - 2))
    parts = [frame, claim, request]
    if len(join(parts)) > NEGO_ARM_LEN_HI:
        # Keep the shortest frame rather than dropping it: the claims refer back
        # to "that", and a claim with no frame in front of it has no referent.
        parts = [min((x for x in frames if x), key=len, default=""), claim]
    text = join(parts)

    pool = [x for x in fillers if x]
    rng.shuffle(pool)
    for filler in pool:
        if len(text) >= NEGO_ARM_LEN_LO:
            break
        candidate = f"{text} {filler}"
        if len(candidate) <= NEGO_ARM_LEN_HI:
            text = candidate
    return text.strip()


def negotiation_arm_message(arm: str, game: dict, action: dict,
                            plan: dict | None,
                            rng: random.Random | None = None) -> dict:
    """The message for one arm, with its provenance. Never raises.

    Returns ``{"text": str|None, "claim_id", "claim_kind", "reason", ...}``.
    ``text is None`` means this arm sends nothing here — which is a result for
    N0 and a "do not assign me" for a treatment arm, and must never be
    back-filled from ``negotiation_message`` above: that would destroy the
    silent control and mix the un-randomised template into a treatment cell.
    """
    out = {"arm": arm, "grammar_version": NEGO_ARM_GRAMMAR_VERSION,
           "text": None, "claim_id": None, "claim_kind": None, "reason": None}
    try:
        if arm not in NEGO_ARMS:
            out["reason"] = "unknown-arm"
            return out
        if arm == "N0":
            out["reason"] = "silent-arm"
            return out
        if not isinstance(plan, dict) or not isinstance(action, dict):
            out["reason"] = "no-plan"
            return out
        facts = _nego_arm_facts(game, action, plan)
        if facts is None:
            out["reason"] = "facts-unavailable"
            return out
        claim = None
        if arm != "N1":
            claim = negotiation_arm_claim(arm, game, action, plan)
            if claim is None:
                out["reason"] = "no-true-claim-available"
                return out
        if rng is None:
            state = game.get("game_state") or {}
            rng = random.Random(f"nego-msg:{game.get('game_id')}:{state.get('round')}")
        text = _assemble_nego_arm(_nego_arm_frames(facts),
                                  claim["text"] if claim else "",
                                  _nego_arm_requests(arm),
                                  _nego_arm_fillers(facts), rng)
        if not text:
            out["reason"] = "empty"
            return out
        out.update(text=text, reason="ok",
                   claim_id=claim["claim_id"] if claim else None,
                   claim_kind=claim["claim_kind"] if claim else None)
        return out
    except Exception:
        out["text"] = None
        out["reason"] = "exception"
        return out


BUILDERS = {
    "bargaining": bargaining_message,
    "negotiation": negotiation_message,
    "persuasion": persuasion_message,
}


def compose(game: dict, action: dict, plan: dict | None,
            rng: random.Random) -> str | None:
    builder = BUILDERS.get(game.get("game_family"))
    if builder is None:
        return None
    try:
        return builder(game, action, plan, rng)
    except Exception:
        return None          # a message is never worth risking the move over
