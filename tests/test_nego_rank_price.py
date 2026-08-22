"""Terminal negotiation pricing against the actual percentile objective."""

from __future__ import annotations

import hashlib
import os

import pytest

from glee_agent import pricing, runtime_flags
from glee_agent.config import Config
from glee_agent.strategies import negotiation


def _gid(treatment: bool) -> str:
    """Find a game id with the independently recoverable production arm bit."""
    for i in range(100):
        gid = f"rank-price-{i}"
        bit = int(hashlib.sha256(("rank_price_ab|" + gid).encode()).hexdigest(), 16) & 1
        if bool(bit) is treatment:
            return gid
    raise AssertionError("no arm id found")


def _game(*, role="seller", complete=True, own_value=None,
          other_value=None, rnd=1, max_rounds=1, horizon_known=True,
          gid=None):
    seller = role == "seller"
    me, other = ("player_1", "player_2") if seller else ("player_2", "player_1")
    own_value = own_value if own_value is not None else (80.0 if seller else 150.0)
    other_value = other_value if other_value is not None else (150.0 if seller else 80.0)
    state = {
        "round": rnd,
        "max_rounds": max_rounds,
        "horizon_known": horizon_known,
        "complete_information": complete,
        "current_player": me,
        f"{me}_role": role,
        f"{me}_value": own_value,
        f"{other}_role": "buyer" if seller else "seller",
        "history": [],
    }
    if complete:
        state[f"{other}_value"] = other_value
    return {
        "game_id": gid or _gid(True),
        "game_family": "negotiation",
        "your_player": me,
        "phase": "offer",
        "game_state": state,
        "valid_actions": {"type": "offer"},
    }


@pytest.fixture(autouse=True)
def _clean_flags(monkeypatch):
    for name in list(os.environ):
        if name.startswith("GLEE_NEGO_") or name in ("GLEE_PROBE", "GLEE_TRACE_GATES"):
            monkeypatch.delenv(name, raising=False)
    # Reproduce the live terminal control while keeping the new arm default-off.
    monkeypatch.setenv("GLEE_NEGO_HORIZON_V2", "1")
    monkeypatch.setenv("GLEE_NEGO_ULTIMATUM_SHARE", "0.80")
    monkeypatch.setenv("GLEE_TRACE_GATES", "1")
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _install_seller_models(monkeypatch, *, complete=True, max_rounds=1,
                           samples=None, curves=None):
    # 74 zeros make F(0)=0.37 under midrank. The remaining atoms give the two
    # candidate payoffs different ranks: F(0.35)=0.94 and F(0.475)=1.00.
    samples = ([0.0] * 74 + [0.2] * 20 + [0.4] * 6) if samples is None else samples
    curves = curves if curves is not None else {
        "seller_final": [
            {"lo": 1.1, "hi": 1.2, "n": 100, "p_accept": 0.70},
            {"lo": 1.2, "hi": 1.35, "n": 100, "p_accept": 0.60},
        ]
    }
    key = (f"negotiation|100.0|0.8|seller|{max_rounds}|True|{complete}")
    monkeypatch.setattr(pricing, "_cdf_cells", lambda: {key: samples})
    monkeypatch.setattr(pricing, "_curves", lambda: curves)


def test_treatment_lowers_final_seller_ask_when_zero_atom_is_large(monkeypatch):
    """The submitted action, not merely a helper, replaces the 0.80 ultimatum."""
    _install_seller_models(monkeypatch)
    game = _game(gid=_gid(True))
    cfg = Config.from_env()

    off = negotiation.decide(game, cfg)
    assert off["product_price"] == 136.0  # 80 + 0.80 * (150 - 80)
    assert "rank_price" not in off["_plan"]

    monkeypatch.setenv("GLEE_NEGO_RANK_PRICE_AB", "1")
    armed = negotiation.decide(game, cfg)
    info = armed["_plan"]["rank_price"]

    assert armed["product_price"] == 115.0 < off["product_price"]
    assert armed["product_price"] == info["chosen_price"]
    assert info["money_optimal_price"] == 127.5
    # These exact values exercise the nonzero rejection term, not merely its
    # diagnostic: .70*.94 + .30*.37 versus .60*1.00 + .40*.37.
    assert info["chosen_expected_rank"] == pytest.approx(0.769)
    assert info["money_expected_rank"] == pytest.approx(0.748)
    assert info["cdf_at_zero"] == pytest.approx(0.37)
    assert info["cdf_n"] == 100
    assert armed["_plan"]["gates_fired"][-2:] == ["ultimatum", "rank_price"]


def test_hidden_price_uses_uniform_type_mix_not_the_pooled_rate(monkeypatch):
    samples = [0.0] * 74 + [0.2] * 26
    key = "negotiation|100.0|0.8|seller|1|True|False"
    rows = [
        {"lo": 1.1, "hi": 1.2, "n": 100, "p_accept": 0.10},
        {"lo": 1.2, "hi": 1.35, "n": 100, "p_accept": 0.90},
    ]
    curves = {"seller_final": rows}
    # The pooled rates point the opposite way. Distinct type rates make the
    # arithmetic 25/25/25/25 mixture observable instead of letting any single
    # component masquerade as the uniform structural prior.
    rates = {
        0.8: (0.90, 0.30),
        1.0: (0.80, 0.50),
        1.2: (0.60, 0.70),
        1.5: (0.50, 0.90),
    }
    for mult, (lower_rate, upper_rate) in rates.items():
        curves[f"seller|m{mult}_final"] = [
            {"lo": 1.1, "hi": 1.2, "n": 8, "p_accept": lower_rate},
            {"lo": 1.2, "hi": 1.35, "n": 8, "p_accept": upper_rate},
        ]
    monkeypatch.setattr(pricing, "_cdf_cells", lambda: {key: samples})
    monkeypatch.setattr(pricing, "_curves", lambda: curves)

    info = pricing.rank_terminal_price(
        80.0, True, _game(complete=False)["game_state"])
    assert info["acceptance_basis"] == "uniform_hidden_types"
    assert info["chosen_acceptance"] == pytest.approx(0.70)
    assert info["money_acceptance"] == pytest.approx(0.60)
    assert info["chosen_price"] == pytest.approx(115.0)

    assert info["money_optimal_price"] == pytest.approx(127.5)


def test_complete_information_uses_the_observed_responder_curve(monkeypatch):
    samples = [0.0] * 74 + [0.2] * 26
    key = "negotiation|100.0|0.8|seller|1|True|True"
    rows = [
        {"lo": 1.1, "hi": 1.2, "n": 100, "p_accept": 0.10},
        {"lo": 1.2, "hi": 1.35, "n": 100, "p_accept": 0.90},
    ]
    curves = {
        "seller_final": rows,
        "seller|m1.5_final": [
            {"lo": 1.1, "hi": 1.2, "n": 8, "p_accept": 0.70},
            {"lo": 1.2, "hi": 1.35, "n": 8, "p_accept": 0.60},
        ],
    }
    monkeypatch.setattr(pricing, "_cdf_cells", lambda: {key: samples})
    monkeypatch.setattr(pricing, "_curves", lambda: curves)

    state = _game(complete=True, other_value=150.0)["game_state"]
    info = pricing.rank_terminal_price(80.0, True, state, 150.0)
    assert info["acceptance_basis"] == "known_responder_type"
    assert info["chosen_acceptance"] == pytest.approx(0.70)
    assert info["money_acceptance"] == pytest.approx(0.60)
    assert info["chosen_price"] == pytest.approx(115.0)

    malformed = pricing.rank_terminal_price(80.0, True, state, "not-a-value")
    assert malformed["status"] == "fallback"
    assert malformed["reason"] == "unknown_responder_type"


def test_flag_off_and_control_hash_keep_the_old_ultimatum(monkeypatch):
    _install_seller_models(monkeypatch)
    cfg = Config.from_env()
    off = negotiation.decide(_game(gid=_gid(True)), cfg)
    assert off["product_price"] == 136.0

    monkeypatch.setenv("GLEE_NEGO_RANK_PRICE_AB", "1")
    control = negotiation.decide(_game(gid=_gid(False)), cfg)
    assert control["product_price"] == 136.0
    assert control["_plan"]["rank_price"]["status"] == "control"
    assert control["_plan"]["rank_price"]["reason"] == "hash_control"


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        ("unknown", "unknown_cdf_cell"),
        ("thin", "thin_cdf_cell"),
        ("uncovered", "no_acceptance_coverage"),
    ],
)
def test_untrusted_model_falls_back_to_the_ultimatum(monkeypatch, case, reason):
    key = "negotiation|100.0|0.8|seller|1|True|True"
    samples = [0.0] * 74 + [0.2] * 26
    cells = {} if case == "unknown" else {key: samples[:29] if case == "thin" else samples}
    curves = {"seller_final": [
        {"lo": 1.1, "hi": 1.2, "n": 19 if case == "uncovered" else 100,
         "p_accept": 0.7},
    ]}
    monkeypatch.setattr(pricing, "_cdf_cells", lambda: cells)
    monkeypatch.setattr(pricing, "_curves", lambda: curves)
    monkeypatch.setenv("GLEE_NEGO_RANK_PRICE_AB", "1")

    action = negotiation.decide(_game(gid=_gid(True)), Config.from_env())
    assert action["product_price"] == 136.0
    assert action["_plan"]["rank_price"]["status"] == "fallback"
    assert action["_plan"]["rank_price"]["reason"] == reason


def test_rank_pricing_requires_a_real_final_offer(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_RANK_PRICE_AB", "1")

    def should_not_run(*_args, **_kwargs):
        raise AssertionError("rank pricing ran outside a real final offer")

    monkeypatch.setattr(pricing, "rank_terminal_price", should_not_run)
    cfg = Config.from_env()
    midgame = _game(rnd=9, max_rounds=10, gid=_gid(True))
    uncapped = _game(rnd=99, max_rounds=None, horizon_known=False, gid=_gid(True))
    final_decision = _game(gid=_gid(True))
    final_decision["phase"] = "decision"
    final_decision["valid_actions"] = {"type": "decision"}
    final_decision["game_state"]["last_offer"] = {
        "from_player": "player_2", "price": 90.0,
    }
    for game in (midgame, uncapped, final_decision):
        action = negotiation.decide(game, cfg)
        assert "rank_price" not in action["_plan"]


def test_rank_price_is_last_writer_in_a_hidden_terminal_state(monkeypatch):
    _install_seller_models(monkeypatch, complete=False, max_rounds=10)
    monkeypatch.setenv("GLEE_NEGO_RANK_PRICE_AB", "1")
    monkeypatch.setenv("GLEE_NEGO_POSTERIOR", "1")
    monkeypatch.setenv("GLEE_NEGO_SPLIT_CANDIDATE", "1")
    monkeypatch.setattr(pricing, "posterior_final_ask", lambda *_args: 127.5)
    game = _game(complete=False, rnd=10, max_rounds=10, gid=_gid(True))
    state = game["game_state"]
    me = game["your_player"]
    state["history"] = [{"offer": {"from_player": me, "price": 150.0}}]
    state["last_offer"] = {"price": 130.0}

    action = negotiation.decide(game, Config.from_env())
    assert action["product_price"] == 115.0
    assert action["_plan"]["rank_price"]["previous_target"] == 127.5
    assert action["_plan"]["gates_fired"][-2:] == ["posterior", "rank_price"]
    # Without the explicit bypass, the downstream split transform would replace
    # the recorded argmax with midpoint (150 + 130) / 2 = 140.
    assert action["_plan"]["split_taken"] is False


def test_buyer_objective_uses_value_minus_price_and_offers_more(monkeypatch):
    samples = [0.0] * 74 + [0.4] * 26
    key = "negotiation|100.0|1.5|buyer|1|True|True"
    monkeypatch.setattr(pricing, "_cdf_cells", lambda: {key: samples})
    monkeypatch.setattr(pricing, "_curves", lambda: {"buyer_final": [
        {"lo": 0.8, "hi": 0.9, "n": 100, "p_accept": 0.60},
        {"lo": 1.0, "hi": 1.1, "n": 100, "p_accept": 0.80},
    ]})
    monkeypatch.setenv("GLEE_NEGO_RANK_PRICE_AB", "1")
    game = _game(role="buyer", gid=_gid(True))

    action = negotiation.decide(game, Config.from_env())
    info = action["_plan"]["rank_price"]
    assert action["product_price"] == 105.0
    assert info["money_optimal_price"] == 85.0
    assert info["chosen_expected_rank"] > info["money_expected_rank"]
