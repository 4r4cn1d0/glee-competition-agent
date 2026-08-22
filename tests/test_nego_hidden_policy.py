"""Grid-conditioned hidden negotiation policy stays offer-only and randomized."""

from __future__ import annotations

import hashlib
import os

import pytest

from glee_agent import actions, runtime_flags
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.strategies import negotiation


def _gid(treatment: bool, *, legacy_treatment: bool | None = None) -> str:
    for i in range(10_000):
        gid = f"hidden-policy-{i}"
        bit = int(hashlib.sha256(("hidden_policy_v1|" + gid).encode()).hexdigest(), 16) & 1
        legacy = int(hashlib.sha256(("hidden_floor|" + gid).encode()).hexdigest(), 16) & 1
        if bool(bit) is treatment and (
                legacy_treatment is None or bool(legacy) is legacy_treatment):
            return gid
    raise AssertionError("could not find the requested hash assignment")


def _game(*, gid=None, role="seller", own_value=None, complete=False,
          opening=True, max_rounds=10, opponent_price=None,
          own_price_count=1):
    me = "player_1" if role == "seller" else "player_2"
    other = "player_2" if me == "player_1" else "player_1"
    if own_value is None:
        own_value = 80.0 if role == "seller" else 150.0
    state = {
        "round": 1 if opening else 5,
        "max_rounds": max_rounds,
        "horizon_known": max_rounds is not None,
        "complete_information": complete,
        "current_player": me,
        "player_1_role": "seller",
        "player_2_role": "buyer",
        f"{me}_value": own_value,
        "history": [],
        "last_offer": None,
        "messages_allowed": False,
    }
    if max_rounds is None:
        state.pop("max_rounds")
    if complete:
        state[f"{other}_value"] = 150.0 if role == "seller" else 80.0
    if not opening:
        their_counter = {
            "from_player": other,
            "price": opponent_price if opponent_price is not None else (
                90.0 if role == "seller" else 130.0),
        }
        state["history"] = [
            {
                "round": i + 1,
                "offer": {"from_player": me, "price": 140.0 + i},
                "decision": "RejectOffer",
                "counteroffer": their_counter,
                "decided_by": other,
            }
            for i in range(own_price_count)
        ]
        state["last_offer"] = {**their_counter, "round": 5}
    elif role == "buyer":
        # The buyer's first outgoing price is its counter to the seller opener.
        state["last_offer"] = {
            "from_player": other,
            "price": opponent_price if opponent_price is not None else 140.0,
            "round": 1,
        }
    return {
        "game_id": gid if gid is not None else _gid(True),
        "game_family": "negotiation",
        "your_player": me,
        "phase": "offer" if role == "seller" and opening else "decision",
        "game_state": state,
        "valid_actions": {
            "type": "offer" if role == "seller" and opening else "decision",
        },
    }


def _raw(game: dict, price: float) -> dict:
    if game["valid_actions"]["type"] == "offer":
        return {"product_price": price}
    return {"decision": "RejectOffer", "product_price": price}


@pytest.fixture(autouse=True)
def _clean_flags(monkeypatch):
    for name in list(os.environ):
        if name.startswith("GLEE_NEGO_") or name in (
                "GLEE_PROBE", "GLEE_TRACE_GATES", "GLEE_LLM_FAMILIES"):
            monkeypatch.delenv(name, raising=False)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


@pytest.mark.parametrize(
    ("role", "own_value", "expected"),
    [
        ("seller", 80.0, 139.5),
        ("seller", 100.0, 142.5),
        ("seller", 120.0, 145.5),
        ("buyer", 150.0, 90.5),
        ("buyer", 120.0, 86.0),
        ("buyer", 100.0, 83.0),
    ],
)
def test_candidate_opening_claims_85_percent_of_the_largest_possible_zone(
        monkeypatch, role, own_value, expected):
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_POLICY_V1", "1")
    game = _game(role=role, own_value=own_value, opening=True)

    action = coerce(_raw(game, 999.0 if role == "seller" else 1.0), game)

    assert action["product_price"] == expected


@pytest.mark.parametrize(
    ("role", "own_value", "expected"),
    [
        ("seller", 80.0, 95.0),
        ("seller", 100.0, 115.0),
        ("seller", 120.0, 142.5),
        ("buyer", 150.0, 127.5),
        ("buyer", 120.0, 105.0),
        ("buyer", 100.0, 85.0),
    ],
)
def test_candidate_floor_claims_75_percent_of_the_narrowest_feasible_zone(
        monkeypatch, role, own_value, expected):
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_POLICY_V1", "1")
    game = _game(
        role=role, own_value=own_value, opening=False, own_price_count=4)
    generous = 0.0 if role == "seller" else 200.0

    action = coerce(_raw(game, generous), game)

    assert action["product_price"] == expected


@pytest.mark.parametrize(
    ("role", "own_value", "raw_price", "expected"),
    [
        ("seller", 80.0, 400.0, 136.72),
        ("buyer", 150.0, 15.0, 92.81),
    ],
)
def test_later_price_cannot_jump_back_outside_the_credible_opening(
        monkeypatch, role, own_value, raw_price, expected):
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_POLICY_V1", "1")
    game = _game(role=role, own_value=own_value, opening=False)

    assert coerce(_raw(game, raw_price), game)["product_price"] == expected


@pytest.mark.parametrize(
    ("role", "own_value", "expected"),
    [
        ("seller", 80.0, [139.5, 136.72, 128.38, 114.47, 95.0]),
        ("buyer", 150.0, [90.5, 92.81, 99.75, 111.31, 127.5]),
    ],
)
def test_h10_sequence_uses_all_five_role_symmetric_price_opportunities(
        monkeypatch, role, own_value, expected):
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_POLICY_V1", "1")

    prices = []
    for prior_count in range(5):
        game = _game(
            role=role, own_value=own_value, opening=prior_count == 0,
            own_price_count=prior_count)
        prices.append(coerce(_raw(game, 0.0), game)["product_price"])

    assert prices == expected


@pytest.mark.parametrize(
    ("role", "own_value", "expected"),
    [("seller", 80.0, 107.35), ("buyer", 150.0, 117.23)],
)
def test_uncapped_linear_clock_caps_at_85_percent_before_squaring(
        monkeypatch, role, own_value, expected):
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_POLICY_V1", "1")

    prices = {
        coerce(_raw(game, 0.0), game)["product_price"]
        for prior_count in (5, 8, 20)
        for game in [_game(
            role=role, own_value=own_value, opening=False,
            max_rounds=None, own_price_count=prior_count)]
    }

    assert prices == {expected}


def test_counteroffer_echo_is_counted_as_one_prior_price():
    game = _game(opening=False, own_price_count=0)
    me, other = "player_1", "player_2"
    game["game_state"]["history"] = [
        {
            "offer": {"from_player": other, "price": 100.0},
            "counteroffer": {"from_player": me, "price": 130.0},
        },
        {
            "offer": {"from_player": me, "price": 130.0},
            "counteroffer": {"from_player": other, "price": 105.0},
        },
    ]

    assert actions._hidden_own_price_count(game["game_state"], me) == 1


@pytest.mark.parametrize(
    ("role", "own_value", "opponent_price", "raw_price", "expected"),
    [
        ("seller", 80.0, 105.0, 100.0, 110.0),
        ("seller", 80.0, 121.0, 100.0, 132.5),
        ("buyer", 150.0, 110.0, 130.0, 110.0),
        ("buyer", 150.0, 99.0, 130.0, 97.5),
    ],
)
def test_only_a_crossed_grid_bound_hardens_the_concession_boundary(
        monkeypatch, role, own_value, opponent_price, raw_price, expected):
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_POLICY_V1", "1")
    game = _game(
        role=role, own_value=own_value, opening=False,
        opponent_price=opponent_price, own_price_count=4)

    assert coerce(_raw(game, raw_price), game)["product_price"] == expected


@pytest.mark.parametrize(
    ("role", "own_value", "opponent_price", "raw_price", "expected"),
    [
        ("seller", 80.0, 90.0, 0.0, 95.0),
        ("buyer", 150.0, 130.0, 200.0, 127.5),
    ],
)
def test_static_uninformative_offer_does_not_accelerate_concession(
        monkeypatch, role, own_value, opponent_price, raw_price, expected):
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_POLICY_V1", "1")
    game = _game(
        role=role, own_value=own_value, opening=False,
        opponent_price=opponent_price, own_price_count=4)

    assert coerce(_raw(game, raw_price), game)["product_price"] == expected


@pytest.mark.parametrize(
    ("role", "own_value", "opponent_price", "raw_price"),
    [
        ("seller", 80.0, 145.0, 400.0),
        ("buyer", 150.0, 85.0, 1.0),
    ],
)
def test_counter_never_gives_back_a_better_opponent_price(
        monkeypatch, role, own_value, opponent_price, raw_price):
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_POLICY_V1", "1")
    game = _game(
        role=role, own_value=own_value, opening=False,
        opponent_price=opponent_price)

    assert coerce(_raw(game, raw_price), game)["product_price"] == opponent_price


@pytest.mark.parametrize(
    ("role", "own_value"),
    [("seller", 150.0), ("buyer", 80.0)],
)
def test_zero_percent_feasible_own_draws_remain_on_deadgame_path(
        monkeypatch, role, own_value):
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_POLICY_V1", "1")
    game = _game(role=role, own_value=own_value, opening=False)
    raw = _raw(game, 177.0)

    assert coerce(raw, game) == raw


def test_one_round_complete_info_missing_id_and_hash_control_are_inert(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_POLICY_V1", "1")
    cases = [
        _game(max_rounds=1),
        _game(complete=True),
        _game(gid=""),
        _game(gid=_gid(False)),
    ]
    for game in cases:
        raw = _raw(game, 177.0)
        assert coerce(raw, game) == raw


def test_default_off_is_byte_for_byte_inert():
    game = _game(gid=_gid(True), opening=False)
    raw = _raw(game, 177.0)
    assert coerce(raw, game) == raw


def test_new_policy_owns_hash_control_and_suppresses_legacy_floor(monkeypatch):
    gid = _gid(False, legacy_treatment=True)
    game = _game(gid=gid, opening=False)
    raw = _raw(game, 110.0)
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_POLICY_V1", "1")
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "1.40")

    assert coerce(raw, game) == raw


def test_accept_path_never_reads_the_offer_policy(monkeypatch):
    game = _game(opening=False)

    def fail_if_read(_name):
        raise AssertionError("offer-only policy read on AcceptOffer")

    monkeypatch.setattr(runtime_flags, "get", fail_if_read)
    assert coerce({"decision": "AcceptOffer"}, game) == {
        "decision": "AcceptOffer",
    }


def test_flag_does_not_change_plan_or_acceptance_inputs(monkeypatch):
    game = _game(role="buyer", opening=False)
    cfg = Config.from_env()
    before = negotiation.plan(game, cfg)
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_POLICY_V1", "1")

    assert negotiation.plan(game, cfg) == before


class _HiddenState(dict):
    def __init__(self, *args, forbidden, **kwargs):
        super().__init__(*args, **kwargs)
        self.forbidden = forbidden

    def get(self, key, default=None):
        if key == self.forbidden:
            raise AssertionError("hidden opponent value was read")
        return super().get(key, default)


@pytest.mark.parametrize("role", ["seller", "buyer"])
def test_policy_never_reads_the_hidden_opponent_value(monkeypatch, role):
    game = _game(role=role, opening=False)
    other = "player_2" if role == "seller" else "player_1"
    state = _HiddenState(game["game_state"], forbidden=f"{other}_value")
    dict.__setitem__(state, f"{other}_value", 150.0 if role == "seller" else 80.0)
    game["game_state"] = state
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_POLICY_V1", "1")

    coerce(_raw(game, 110.0), game)


def test_uncapped_game_is_eligible_and_uses_the_same_hash_assignment(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_POLICY_V1", "1")
    game = _game(max_rounds=None, opening=False)
    context = actions._hidden_policy_context(game)

    assert context is not None
    assert context["eligible"] is True
    assert context["treatment"] is True
