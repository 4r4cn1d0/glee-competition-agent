"""Every baseline policy, driven through every phase of all three families.

Two properties are under test, and they matter for different reasons.

**Legality.** A policy that returns an illegal action burns one of the game's
five attempts; a policy that raises submits nothing at all and the game dies on
the turn clock. Either one silently corrupts every tournament result the policy
appears in — and unlike the live agent, nobody is watching a simulated match. So
each policy is driven through the same synthetic state grid ``scripts/selftest``
uses on the real agent, and every returned action is checked against the move
formats in docs/reference/glee-docs.md.

**Fidelity of the reference.** ``docs_baseline`` is the archetype the field is
actually seeded with, so it is checked the strongest way available: against the
published agent itself, imported from docs/reference/example_simple_agent.py and
run on the same states. Any drift is a test failure rather than a slow
mis-tuning.

The remaining tests pin the behaviour that gives each archetype its name — a
"hardliner" that quietly concedes teaches the wrong lesson just as effectively
as one that crashes.

Runs under pytest, and standalone (``python tests/test_sim_opponents.py``) so it
still works in an environment without it.
"""

from __future__ import annotations

import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from glee_agent.actions import MAX_MESSAGE_LEN, coerce  # noqa: E402
from scripts.selftest import (  # noqa: E402
    bargaining_games,
    malformed_games,
    negotiation_games,
    persuasion_games,
)
from sim.opponents import OPPONENTS, RandomValid, _is_recommendation, get  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED = ("docs_baseline", "hardliner", "conceder", "tit_for_tat", "random_valid",
            "honest_seller", "greedy_seller", "trust_tracking_buyer")


def _reference_strategy():
    """The published example agent, loaded straight from the docs directory."""
    path = os.path.join(REPO_ROOT, "docs", "reference", "example_simple_agent.py")
    spec = importlib.util.spec_from_file_location("glee_reference_agent", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.strategy


def _well_formed_games():
    for source in (bargaining_games, negotiation_games, persuasion_games):
        yield from source()


def assert_legal(game, action, who):
    """Check one action against the move formats the server accepts."""
    family = game.get("game_family")
    action_type = (game.get("valid_actions") or {}).get("type")
    state = game.get("game_state") or {}
    tag = f"{who} {family}/{action_type}/r{state.get('round')}"

    assert isinstance(action, dict) and action, f"{tag}: empty action"

    message = action.get("message")
    if message is not None:
        assert isinstance(message, str) and 0 < len(message) <= MAX_MESSAGE_LEN, \
            f"{tag}: bad message length"
        assert state.get("messages_allowed") is not False, \
            f"{tag}: message sent when messages are not allowed"

    if action_type == "offer" and family == "bargaining":
        assert {"alice_gain", "bob_gain"} <= set(action), f"{tag}: missing gain keys"
        total = action["alice_gain"] + action["bob_gain"]
        assert total == state["money_to_divide"], \
            f"{tag}: gains sum to {total!r}, need {state['money_to_divide']!r}"
        assert min(action["alice_gain"], action["bob_gain"]) >= 0, f"{tag}: negative gain"

    elif action_type == "offer" and family == "negotiation":
        assert "product_price" in action, f"{tag}: missing product_price"
        assert action["product_price"] >= 0, f"{tag}: negative price"

    elif action_type == "decision" and family == "bargaining":
        assert action.get("decision") in ("accept", "reject", "walkaway"), \
            f"{tag}: bad decision {action.get('decision')!r}"

    elif action_type == "decision" and family == "negotiation":
        assert action.get("decision") in ("AcceptOffer", "RejectOffer", "WalkAway"), \
            f"{tag}: bad decision {action.get('decision')!r}"
        final = state.get("max_rounds") is not None and state["round"] >= state["max_rounds"]
        if action.get("decision") == "RejectOffer" and not final:
            assert "product_price" in action, f"{tag}: rejection without counteroffer"

    elif action_type in ("seller_recommendation", "buyer_decision"):
        assert action.get("decision") in ("yes", "no"), \
            f"{tag}: bad decision {action.get('decision')!r}"

    elif action_type == "seller_message":
        assert action.get("message"), f"{tag}: empty seller message"


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------

def test_registry_exposes_every_archetype():
    missing = [name for name in REQUIRED if name not in OPPONENTS]
    assert not missing, f"missing archetypes: {missing}"
    for name, policy in OPPONENTS.items():
        assert callable(policy), f"{name} is not callable"
        assert get(name) is policy


def test_get_rejects_an_unknown_name():
    try:
        get("no_such_opponent")
    except ValueError as exc:
        assert "no_such_opponent" in str(exc)
        assert "docs_baseline" in str(exc), "the error should list what is available"
    else:
        raise AssertionError("get() accepted an unknown opponent name")


# --------------------------------------------------------------------------
# Legality across every phase of every family
# --------------------------------------------------------------------------

def test_every_policy_returns_a_legal_action_everywhere():
    states = list(_well_formed_games())
    assert len(states) > 1000, "the state grid collapsed; the sweep would prove nothing"
    for name, policy in OPPONENTS.items():
        for game in states:
            assert_legal(game, policy(game), name)


def test_every_policy_survives_malformed_states():
    """States the server should never send. Nothing may escape as an exception."""
    for name, policy in OPPONENTS.items():
        for game in malformed_games():
            action = policy(game)
            assert isinstance(action, dict) and action, \
                f"{name}: no fallback action for {game.get('game_family')!r}"
        # Not even for something that is not a game dict at all.
        for junk in (None, [], "offer", 7):
            assert isinstance(policy(junk), dict)


def test_policies_are_deterministic_apart_from_the_noise_floor():
    """One instance plays both seats of many matches, so it must not carry state."""
    for name, policy in OPPONENTS.items():
        if name == "random_valid":
            continue
        for game in list(_well_formed_games())[::37]:
            assert policy(game) == policy(game), f"{name} is not a pure function of the game"


# --------------------------------------------------------------------------
# docs_baseline fidelity
# --------------------------------------------------------------------------

def test_docs_baseline_reproduces_the_published_agent():
    reference = _reference_strategy()
    baseline = get("docs_baseline")
    compared = 0
    for game in _well_formed_games():
        expected = coerce(reference(game), game)
        assert baseline(game) == expected, (
            f"docs_baseline diverges from the reference agent on "
            f"{game['game_family']}/{game['valid_actions']['type']}: "
            f"{baseline(game)} != {expected}")
        compared += 1
    assert compared > 1000, "nothing was actually compared"


def test_docs_baseline_thresholds():
    """The three numbers the reference agent is defined by, checked directly."""
    baseline = get("docs_baseline")

    # 50/50 offers, and accept at exactly 40% but not a cent below.
    offer = baseline(_bargaining(money=1000, action_type="offer"))
    assert offer["alice_gain"] == 500 and offer["bob_gain"] == 500

    at = baseline(_bargaining(money=1000, action_type="decision", my_gain=400))
    below = baseline(_bargaining(money=1000, action_type="decision", my_gain=399))
    assert at["decision"] == "accept" and below["decision"] == "reject"

    # Fixed anchor multiples off your own valuation.
    seller = baseline(_negotiation(role="seller", my_value=40, action_type="offer"))
    buyer = baseline(_negotiation(role="buyer", my_value=90, action_type="offer"))
    assert seller["product_price"] == 60.0 and buyer["product_price"] == 63.0

    # Buy when the prior expected value beats the price, and always recommend.
    assert baseline(_persuasion("buyer_decision", p=0.5, v=100, u=0, price=40))["decision"] == "yes"
    assert baseline(_persuasion("buyer_decision", p=0.5, v=100, u=0, price=60))["decision"] == "no"
    assert baseline(_persuasion("seller_recommendation", quality="low"))["decision"] == "yes"


# --------------------------------------------------------------------------
# Archetype behaviour
# --------------------------------------------------------------------------

def test_hardliner_holds_where_the_conceder_folds():
    game = _bargaining(money=1000, action_type="offer", round_no=1, max_rounds=6)
    hard = get("hardliner")(game)["alice_gain"]
    base = get("docs_baseline")(game)["alice_gain"]
    soft = get("conceder")(game)["alice_gain"]
    assert hard > base >= soft, f"concession order broken: {hard} / {base} / {soft}"

    # An even split mid-game: the hardliner will not take it, the conceder will.
    even = _bargaining(money=1000, action_type="decision", my_gain=500, round_no=2, max_rounds=6)
    assert get("hardliner")(even)["decision"] == "reject"
    assert get("conceder")(even)["decision"] == "accept"


def test_hardliner_walks_the_deadline_to_the_edge():
    """It refuses a poor offer all game, then takes it in the final round."""
    early = _bargaining(money=1000, action_type="decision", my_gain=100,
                        round_no=1, max_rounds=4)
    last = _bargaining(money=1000, action_type="decision", my_gain=100,
                       round_no=4, max_rounds=4)
    assert get("hardliner")(early)["decision"] == "reject"
    assert get("hardliner")(last)["decision"] == "accept"


def test_deadline_policies_still_fold_in_an_uncapped_game():
    """No round limit means no deadline to walk to.

    Two policies that only concede at a deadline would run an uncapped game
    forever, so both fold once the assumed horizon is spent. A simulated match
    that never terminates is worse than any tuning error it could have exposed.
    """
    for name in ("hardliner", "tit_for_tat"):
        early = _bargaining(money=1000, action_type="decision", my_gain=50,
                            round_no=1, max_rounds=None)
        late = _bargaining(money=1000, action_type="decision", my_gain=50,
                           round_no=14, max_rounds=None)
        assert get(name)(early)["decision"] == "reject", name
        assert get(name)(late)["decision"] == "accept", name

    # Negotiation, same story: a thin profit beats an endless standoff.
    late = _negotiation(role="seller", my_value=40, action_type="decision",
                        price=45, round_no=14, max_rounds=None)
    assert get("hardliner")(late)["decision"] == "AcceptOffer"
    assert get("tit_for_tat")(late)["decision"] == "AcceptOffer"


def test_conceder_takes_any_profitable_trade_and_the_hardliner_does_not():
    # Seller with value 40 offered 45: a real profit, but a thin one.
    game = _negotiation(role="seller", my_value=40, action_type="decision",
                        price=45, round_no=1, max_rounds=6)
    assert get("conceder")(game)["decision"] == "AcceptOffer"
    assert get("hardliner")(game)["decision"] == "RejectOffer"
    # ... and in the final round even the hardliner takes the profit over $0.
    final = _negotiation(role="seller", my_value=40, action_type="decision",
                         price=45, round_no=6, max_rounds=6)
    assert get("hardliner")(final)["decision"] == "AcceptOffer"


def test_conceder_never_signs_a_losing_deal():
    game = _negotiation(role="buyer", my_value=40, action_type="decision",
                        price=90, round_no=8, max_rounds=8)
    assert get("conceder")(game)["decision"] == "RejectOffer"


def test_tit_for_tat_mirrors_the_opponents_concession():
    tft = get("tit_for_tat")

    # Opponent stands still across two offers: so does tit-for-tat, on its anchor.
    still = _bargaining(money=1000, action_type="offer", round_no=3, max_rounds=8,
                        opponent_gains_to_me=(100, 100))
    assert tft(still)["alice_gain"] == 750

    # Opponent concedes 20% of the pot: tit-for-tat concedes exactly 20%.
    moved = _bargaining(money=1000, action_type="offer", round_no=3, max_rounds=8,
                        opponent_gains_to_me=(100, 300))
    assert tft(moved)["alice_gain"] == 550


def test_tit_for_tat_mirrors_price_concessions():
    tft = get("tit_for_tat")
    # Buyer with value 100 facing a seller who came down from 200 to 170.
    game = _negotiation(role="buyer", my_value=100, action_type="offer",
                        round_no=3, max_rounds=8, opponent_prices=(200, 170))
    assert tft(game)["product_price"] == 90.0        # anchor 60, plus the 30 conceded

    firm = _negotiation(role="buyer", my_value=100, action_type="offer",
                        round_no=3, max_rounds=8, opponent_prices=(200, 200))
    assert tft(firm)["product_price"] == 60.0


def test_random_valid_covers_the_whole_choice_set():
    policy = RandomValid(seed=11)
    decision = _bargaining(money=100, action_type="decision", my_gain=50,
                           round_no=1, max_rounds=9)
    seen = {policy(decision)["decision"] for _ in range(200)}
    assert seen == {"accept", "reject", "walkaway"}

    buy = _persuasion("buyer_decision", p=0.5, v=100, u=0, price=50)
    assert {policy(buy)["decision"] for _ in range(200)} == {"yes", "no"}

    offers = {policy(_bargaining(money=1000, action_type="offer"))["alice_gain"]
              for _ in range(50)}
    assert len(offers) > 20, "the split draw is not actually random"


def test_random_valid_is_reproducible_from_its_seed():
    game = _bargaining(money=1000, action_type="offer")
    first = [RandomValid(seed=3)(game) for _ in range(5)]
    second = [RandomValid(seed=3)(game) for _ in range(5)]
    assert first == second
    assert [RandomValid(seed=4)(game) for _ in range(5)] != first


def test_honest_seller_tracks_quality_in_both_modes():
    honest = get("honest_seller")
    assert honest(_persuasion("seller_recommendation", quality="high"))["decision"] == "yes"
    assert honest(_persuasion("seller_recommendation", quality="low"))["decision"] == "no"

    high = honest(_persuasion("seller_message", quality="high"))["message"]
    low = honest(_persuasion("seller_message", quality="low"))["message"]
    assert high != low
    # The text has to be readable as what it is, or a trust-tracking buyer
    # cannot score it and the archetype means nothing.
    assert _is_recommendation(high) and not _is_recommendation(low)


def test_greedy_seller_recommends_everything():
    greedy = get("greedy_seller")
    for quality in ("high", "low"):
        assert greedy(_persuasion("seller_recommendation", quality=quality))["decision"] == "yes"
        assert _is_recommendation(
            greedy(_persuasion("seller_message", quality=quality))["message"])


def test_trust_tracking_buyer_learns_from_what_it_saw():
    buyer = get("trust_tracking_buyer")
    honest_history = [{"round": r, "seller_message": "yes", "buyer_decision": "yes",
                       "bought": True, "quality": "high"} for r in (1, 2, 3)]
    lying_history = [dict(entry, quality="low") for entry in honest_history]

    # Price above the prior expected value: the reference agent passes here.
    dear = dict(p=0.5, v=100, u=0, price=60)
    assert get("docs_baseline")(_persuasion("buyer_decision", **dear))["decision"] == "no"
    assert buyer(_persuasion("buyer_decision", history=honest_history, **dear))["decision"] == "yes"

    # Price below it: the reference agent buys, but not after three lies.
    cheap = dict(p=0.5, v=100, u=0, price=30)
    assert get("docs_baseline")(_persuasion("buyer_decision", **cheap))["decision"] == "yes"
    assert buyer(_persuasion("buyer_decision", history=lying_history, **cheap))["decision"] == "no"

    # With nothing observed it can only price the prior, like the reference.
    assert buyer(_persuasion("buyer_decision", **cheap))["decision"] == "yes"
    assert buyer(_persuasion("buyer_decision", **dear))["decision"] == "no"


def test_trust_tracking_buyer_ignores_rounds_it_could_not_see():
    """Quality is revealed only on rounds the buyer bought; the rest is noise."""
    buyer = get("trust_tracking_buyer")
    unseen = [{"round": r, "seller_message": "yes", "buyer_decision": "no",
               "bought": False} for r in (1, 2, 3)]
    dear = dict(p=0.5, v=100, u=0, price=60)
    assert buyer(_persuasion("buyer_decision", history=unseen, **dear))["decision"] == "no"


def test_tit_for_tat_punishes_a_seller_that_lied():
    tft = get("tit_for_tat")
    cheap = dict(p=0.5, v=100, u=0, price=30)
    honest = [{"round": 1, "seller_message": "yes", "buyer_decision": "yes",
               "bought": True, "quality": "high"}]
    lied = [{"round": 1, "seller_message": "yes", "buyer_decision": "yes",
             "bought": True, "quality": "low"}]
    # Trusting: it buys because a high-quality unit would cover the price.
    assert tft(_persuasion("buyer_decision", history=honest, **cheap))["decision"] == "yes"
    # Burned: it falls back to the prior, which at this price still clears...
    assert tft(_persuasion("buyer_decision", history=lied, **cheap))["decision"] == "yes"
    # ... and no longer does once the price sits above the prior value.
    dear = dict(p=0.5, v=100, u=0, price=60)
    assert tft(_persuasion("buyer_decision", history=honest, **dear))["decision"] == "yes"
    assert tft(_persuasion("buyer_decision", history=lied, **dear))["decision"] == "no"


# --------------------------------------------------------------------------
# Focused state builders. The sweep above uses scripts/selftest's grid; these
# are for pinning one number at a time.
# --------------------------------------------------------------------------

def _bargaining(money=1000, action_type="offer", my_gain=None, round_no=1,
                max_rounds=5, opponent_gains_to_me=()):
    me, them = "player_1", "player_2"
    state = {
        "phase": action_type, "current_player": me, "round": round_no,
        "money_to_divide": money, "horizon_known": max_rounds is not None,
        "delta_1": 0.9, "delta_2": 0.9, "messages_allowed": True,
        "complete_information": True, "last_offer": None, "history": [],
    }
    if max_rounds is not None:
        state["max_rounds"] = max_rounds
    for index, gain in enumerate(opponent_gains_to_me):
        state["history"].append({
            "round": index + 1, "proposer": them,
            "offer": {f"{me}_gain": gain, f"{them}_gain": money - gain,
                      "proposer": them, "round": index + 1},
            "decision": "reject",
        })
    if my_gain is not None:
        state["proposer"] = them
        state["last_offer"] = {f"{me}_gain": my_gain, f"{them}_gain": money - my_gain,
                               "message": "take it", "proposer": them, "round": round_no}
    elif opponent_gains_to_me:
        state["proposer"] = me
    return {"game_id": "t", "game_family": "bargaining", "your_player": me,
            "phase": action_type, "opponent": {"type": "hidden", "name": None},
            "game_state": state, "prompt": "",
            "valid_actions": {"type": action_type, "fields": {}}}


def _negotiation(role="seller", my_value=40, action_type="offer", price=None,
                 round_no=1, max_rounds=5, opponent_prices=()):
    me = "player_1" if role == "seller" else "player_2"
    them = "player_2" if role == "seller" else "player_1"
    state = {
        "phase": action_type, "current_player": me, "round": round_no,
        "player_1_role": "seller", "player_2_role": "buyer",
        f"{me}_value": my_value, "horizon_known": max_rounds is not None,
        "messages_allowed": True, "complete_information": False,
        "last_offer": None, "history": [],
    }
    if max_rounds is not None:
        state["max_rounds"] = max_rounds
    for index, offered in enumerate(opponent_prices):
        state["history"].append({
            "round": index + 1,
            "offer": {"price": offered, "message": "", "from_player": them},
            "decision": "RejectOffer", "decided_by": me,
        })
    if price is not None:
        state["last_offer"] = {"price": price, "message": "final",
                               "from_player": them, "round": round_no}
    return {"game_id": "t", "game_family": "negotiation", "your_player": me,
            "phase": action_type, "opponent": {"type": "hidden", "name": None},
            "game_state": state, "prompt": "",
            "valid_actions": {"type": action_type, "fields": {}}}


def _persuasion(action_type, p=0.5, v=100, u=0, price=50, quality="high",
                history=None, round_no=1, total_rounds=5):
    seller = action_type in ("seller_message", "seller_recommendation")
    state = {
        "phase": action_type, "current_player": "player_1" if seller else "player_2",
        "product_price": price, "p": p, "round": round_no,
        "total_rounds": total_rounds, "is_seller_know_cv": True,
        "seller_message_type": "text" if action_type == "seller_message" else "binary",
        "seller_total_payoff": 0, "buyer_total_payoff": 0,
        "history": list(history or []),
    }
    if seller:
        state["current_quality"] = quality
        state["v"], state["u"] = v, u
    else:
        state["v"], state["u"] = v, u
        state["seller_message"] = "yes"
    return {"game_id": "t", "game_family": "persuasion",
            "your_player": "player_1" if seller else "player_2",
            "phase": action_type, "opponent": {"type": "hidden", "name": None},
            "game_state": state, "prompt": "",
            "valid_actions": {"type": action_type, "fields": {}}}


def _run_standalone():
    """Run every test without pytest, for environments that lack it."""
    import logging
    import traceback

    logging.disable(logging.CRITICAL)      # the malformed cases log tracebacks by design
    tests = [(name, obj) for name, obj in sorted(globals().items())
             if name.startswith("test_") and callable(obj)]
    failures = []
    for name, test in tests:
        try:
            test()
            print(f"  PASS {name}")
        except Exception:
            failures.append(name)
            print(f"  FAIL {name}\n{traceback.format_exc()}")
    print(f"\n{len(tests) - len(failures)} passed, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
