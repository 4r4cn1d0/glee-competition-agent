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
