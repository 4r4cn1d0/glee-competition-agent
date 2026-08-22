"""Regression coverage for the fitted negotiation opponent clone."""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from glee_agent import runtime_flags
from sim import field_data

FLAG = "GLEE_SIM_NEGO_RESP_V2"


class HighDraw:
    """Choose the nonaccept branch except at effectively certain acceptance."""

    def random(self):
        return 0.999999

    def choice(self, values):
        return values[0]


class LowDraw(HighDraw):
    def random(self):
        return 0.0


@pytest.fixture(autouse=True)
def _clean_sim_flag(monkeypatch):
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    monkeypatch.delenv(FLAG, raising=False)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield


def _decision_game(*, price=118.0, round_no=1, max_rounds=6):
    return {
        "game_family": "negotiation",
        "your_player": "player_2",
        "valid_actions": {"type": "decision"},
        "game_state": {
            "round": round_no,
            "max_rounds": max_rounds,
            "complete_information": True,
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "player_1_value": 80.0,
            "player_2_value": 120.0,
            "last_offer": {"price": price, "from_player": "player_1"},
        },
    }


def _clone_table():
    return {
        "nego_resp": {},
        "nego_resp_v2": {
            "s|0.4|buyer|1|continuing": {"accept": 3, "counter": 1},
            "s|0.8|buyer|1|continuing": {"accept": 1, "counter": 3},
        },
        "nego_counter": {"buyer|1": [1.0]},
        "nego_counter_v2": {"buyer|1": [1.0]},
    }


def test_v2_does_not_grant_an_unseen_greedy_ask(monkeypatch):
    """A profitable ask outside observed greedy support is not auto-accepted."""
    table = _clone_table()
    game = _decision_game()
    assert field_data._share_bin((118.0 - 80.0) / (120.0 - 80.0)) == 0.96

    # Pin compatibility: the default path still reaches the legacy
    # profitable-price fallback and grants this unobserved ask.
    legacy = field_data.Clone("test", table, table, HighDraw())(deepcopy(game))
    assert legacy["decision"] == "AcceptOffer"

    monkeypatch.setenv(FLAG, "1")
    repaired = field_data.Clone("test", table, table, HighDraw())(deepcopy(game))
    assert repaired["decision"] == "RejectOffer"


def test_v2_final_rejection_does_not_send_an_invalid_counter(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    table = _clone_table()
    action = field_data.Clone("test", table, table, HighDraw())(
        _decision_game(round_no=1, max_rounds=1))
    assert action == {"decision": "RejectOffer"}


def test_visible_proposer_share_has_one_greed_direction_for_both_roles():
    seller_ask = field_data._proposer_share(118.0, "seller", 80.0, 120.0)
    buyer_bid = field_data._proposer_share(82.0, "buyer", 120.0, 80.0)
    assert seller_ask == pytest.approx(0.95)
    assert buyer_bid == pytest.approx(0.95)


def test_v2_keeps_terminal_and_continuing_response_curves_separate(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    table = {
        "nego_resp_v2": {
            "s|0.48|buyer|1|continuing": {"counter": 100},
            "s|0.48|buyer|1|final": {"accept": 100},
        },
        "nego_counter_v2": {"buyer|1": [1.0]},
    }
    clone = lambda: field_data.Clone("field", table, table, LowDraw())
    assert clone()(_decision_game(price=100.0, max_rounds=6))["decision"] \
        == "RejectOffer"
    assert clone()(_decision_game(price=100.0, max_rounds=1))["decision"] \
        == "AcceptOffer"


@pytest.mark.parametrize(
    ("me", "role", "my_value", "price", "key"),
    (
        ("player_2", "buyer", 120.0, 114.9, "p|1.1|buyer|1|continuing"),
        ("player_1", "seller", 80.0, 85.1, "p|0.9|seller|1|continuing"),
    ),
)
def test_hidden_price_lookup_uses_the_same_bin_as_fit(
        monkeypatch, me, role, my_value, price, key):
    monkeypatch.setenv(FLAG, "1")
    other = "player_2" if me == "player_1" else "player_1"
    table = {
        "nego_resp_v2": {key: {"accept": 10}},
        "nego_counter_v2": {f"{role}|1": [1.0]},
    }
    game = {
        "game_family": "negotiation",
        "your_player": me,
        "valid_actions": {"type": "decision"},
        "game_state": {
            "round": 1,
            "max_rounds": 6,
            "complete_information": False,
            f"{me}_role": role,
            f"{me}_value": my_value,
            f"{other}_role": "seller" if role == "buyer" else "buyer",
            "last_offer": {"price": price, "from_player": other},
        },
    }
    action = field_data.Clone("field", table, table, LowDraw())(game)
    assert action["decision"] == "AcceptOffer"


def test_sparse_personal_cell_cannot_override_the_pooled_curve(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    personal = {
        "nego_resp_v2": {"s|0.48|buyer|1|continuing": {"accept": 1}},
        "nego_counter_v2": {"buyer|1": [1.0]},
    }
    pooled = {
        "nego_resp_v2": {"s|0.48|buyer|1|continuing": {"counter": 100}},
        "nego_counter_v2": {"buyer|1": [1.0]},
    }
    action = field_data.Clone("thin", personal, pooled, LowDraw())(
        _decision_game(price=100.0))
    assert action["decision"] == "RejectOffer"


@pytest.mark.parametrize(
    ("role", "my_value", "generous_price", "greedy_price"),
    (
        ("buyer", 120.0, 80.0, 100.0),
        ("seller", 80.0, 100.0, 80.0),
    ),
)
def test_hidden_price_curve_has_the_right_greed_direction_for_both_seats(
        monkeypatch, role, my_value, generous_price, greedy_price):
    monkeypatch.setenv(FLAG, "1")
    table = {
        "nego_resp_v2": {
            f"p|0.8|{role}|1|continuing": ({"accept": 100} if role == "buyer"
                                            else {"counter": 100}),
            f"p|1.0|{role}|1|continuing": ({"counter": 100} if role == "buyer"
                                            else {"accept": 100}),
        },
        "nego_counter_v2": {f"{role}|1": [1.0]},
    }
    me = "player_2" if role == "buyer" else "player_1"
    other = "player_1" if me == "player_2" else "player_2"

    def play(price):
        game = {
            "game_family": "negotiation",
            "your_player": me,
            "valid_actions": {"type": "decision"},
            "game_state": {
                "round": 1,
                "max_rounds": 6,
                "complete_information": False,
                f"{me}_role": role,
                f"{me}_value": my_value,
                f"{other}_role": "seller" if role == "buyer" else "buyer",
                "last_offer": {"price": price, "from_player": other},
            },
        }
        return field_data.Clone("field", table, table, LowDraw())(game)["decision"]

    assert play(generous_price) == "AcceptOffer"
    assert play(greedy_price) == "RejectOffer"


@pytest.mark.parametrize(
    ("me", "role", "my_value", "price", "key", "counter"),
    (
        ("player_2", "buyer", 80.0, 100.0,
         "p|1.0|buyer|1|continuing", 0.7),
        ("player_1", "seller", 150.0, 130.0,
         "p|1.3|seller|1|continuing", 1.6),
    ),
)
def test_hidden_pooled_curve_cannot_accept_a_losing_trade(
        monkeypatch, me, role, my_value, price, key, counter):
    monkeypatch.setenv(FLAG, "1")
    other = "player_2" if me == "player_1" else "player_1"
    table = {
        "nego_resp_v2": {key: {"accept": 100}},
        "nego_counter_v2": {f"{role}|1": [counter]},
    }
    game = {
        "game_family": "negotiation",
        "your_player": me,
        "valid_actions": {"type": "decision"},
        "game_state": {
            "round": 1,
            "max_rounds": 6,
            "complete_information": False,
            f"{me}_role": role,
            f"{me}_value": my_value,
            f"{other}_role": "seller" if role == "buyer" else "buyer",
            "last_offer": {"price": price, "from_player": other},
        },
    }
    action = field_data.Clone("field", table, table, LowDraw())(game)
    assert action["decision"] == "RejectOffer"


def test_monotone_curve_pools_violations_and_extrapolates_conservatively():
    violating = {
        0.4: {"accept": 1, "counter": 3},
        0.8: {"accept": 3, "counter": 1},
    }
    assert field_data._monotone_response(violating, 0.4)[0] == pytest.approx(0.5)
    assert field_data._monotone_response(violating, 0.8)[0] == pytest.approx(0.5)

    decreasing = {
        0.4: {"accept": 3, "counter": 1},
        0.8: {"accept": 1, "counter": 3},
    }
    assert field_data._monotone_response(decreasing, 0.1)[0] == pytest.approx(0.75)
    assert field_data._monotone_response(decreasing, 0.6)[0] == pytest.approx(0.25)
    assert field_data._monotone_response(decreasing, 0.9) == (0.0, None)


def test_counter_quantiles_do_not_overweight_singleton_extremes():
    values = list(range(1000)) + [1_000_000]
    sampled = field_data._even_order_stats(values, limit=10)
    assert len(sampled) == 10
    assert sampled == sorted(sampled)
    assert sampled[-1] < 1_000_000


@pytest.mark.parametrize(
    ("me", "role", "my_value", "samples", "expected"),
    (
        ("player_2", "buyer", 80.0, [0.9, 0.7], 70.0),
        ("player_1", "seller", 150.0, [1.2, 1.6], 160.0),
    ),
)
def test_v2_counter_never_crosses_the_clones_reservation_value(
        monkeypatch, me, role, my_value, samples, expected):
    monkeypatch.setenv(FLAG, "1")
    table = {"nego_counter_v2": {f"{role}|1": samples}}
    other = "player_2" if me == "player_1" else "player_1"
    game = {
        "game_family": "negotiation",
        "your_player": me,
        "valid_actions": {"type": "offer"},
        "game_state": {
            "round": 1,
            "complete_information": False,
            f"{me}_role": role,
            f"{me}_value": my_value,
            f"{other}_role": "seller" if role == "buyer" else "buyer",
            "last_offer": None,
        },
    }
    action = field_data.Clone("field", table, table, LowDraw())(game)
    assert action["product_price"] == expected


def test_sparse_personal_counter_uses_the_pooled_distribution(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    personal = {"nego_counter_v2": {"buyer|1": [0.5]}}
    pooled = {"nego_counter_v2": {"buyer|1": [0.7] * field_data.MIN_CLONE_OBS}}
    game = {
        "game_family": "negotiation",
        "your_player": "player_2",
        "valid_actions": {"type": "offer"},
        "game_state": {
            "round": 1,
            "complete_information": False,
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "player_2_value": 80.0,
            "last_offer": None,
        },
    }
    action = field_data.Clone("thin", personal, pooled, LowDraw())(game)
    assert action["product_price"] == 70.0


def test_tracked_model_contains_fitted_v2_tables():
    with open(field_data.OUT, encoding="utf-8") as fh:
        doc = json.load(fh)
    assert doc["_nego_resp_schema"] == "share-price-terminal/v2"
    pooled = doc["clones"]["__field__"]
    assert pooled["nego_resp_v2"]
    assert pooled["nego_counter_v2"]
    assert all(len(key.split("|")) == 5 for key in pooled["nego_resp_v2"])
    endings = {key.rsplit("|", 1)[-1] for key in pooled["nego_resp_v2"]}
    assert endings == {"continuing", "final"}


def test_fit_separates_visible_share_from_hidden_price_without_value_keys(monkeypatch):
    complete = {
        "game_family": "negotiation",
        "your_player": "player_1",
        "opponent": {},
        "game_state": {
            "player_1_value": 80.0,
            "player_2_value": 120.0,
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "complete_information": True,
            "history": [{
                "round": 1,
                "offer": {"price": 100.0, "from_player": "player_1"},
                "decision": "reject",
            }],
        },
    }
    hidden_closed = {
        "game_family": "negotiation",
        "your_player": "player_1",
        "opponent": {},
        "result": {
            "outcome": "agreement",
            "agreed_price": 110.0,
            "player_2_payoff": 10.0,
        },
        "game_state": {
            "player_1_value": 80.0,
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "complete_information": False,
            "history": [{
                "round": 1,
                "offer": {"price": 110.0, "from_player": "player_1"},
                "decision": "accept",
            }],
        },
    }
    monkeypatch.setattr(field_data, "_iter_finals",
                        lambda: iter((complete, hidden_closed)))

    table = field_data.fit()["clones"]["__field__"]
    assert set(table["nego_resp_v2"]) == {
        "s|0.48|buyer|1|continuing",
        "p|1.1|buyer|1|continuing",
    }
    # The legacy table proves the hidden responder multiplier was recoverable
    # from this agreement, while V2 deliberately has no value-conditioned key.
    assert "1.1|m1.2|buyer|1" in table["nego_resp"]
    assert all("|m" not in key for key in table["nego_resp_v2"])
