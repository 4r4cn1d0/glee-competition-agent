"""Full-configuration official negotiation seed CDF."""

from __future__ import annotations

import json

import pytest

from sim import official_negotiation_seed as seed


def _state(*, seat="player_1", own=80.0, complete=False, messages=False,
           horizon=10):
    state = {
        "horizon_known": horizon != 99,
        "complete_information": complete,
        "messages_allowed": messages,
        f"{seat}_value": own,
    }
    if horizon != 99:
        state["max_rounds"] = horizon
    return state


def test_checked_in_artifact_has_the_complete_official_grid():
    document = json.loads(seed.MODEL_PATH.read_text(encoding="utf-8"))
    assert document["_schema"] == "glee.negotiation_seed_cdf/full-v1"
    assert document["_games"] == 32_403
    assert document["_role_samples"] == 64_806
    assert len(document["cells"]) == 1_152
    assert {len(samples) for samples in document["cells"].values()} == {
        53, 54, 55, 56, 57, 58,
    }


def test_exact_score_requires_both_values_in_hidden_information():
    state = _state(seat="player_2", own=120.0)
    assert seed.percentile(state, "player_2", 0.0) is None

    scores = seed.hidden_prior_percentiles(state, "player_2", 0.0)
    assert scores == pytest.approx([
        0.1315789474, 0.4107142857, 0.4561403509, 0.5446428571,
    ])
    assert len(set(round(score, 8) for score in scores)) == 4, \
        "pooling counterpart values would erase the official scoring cells"


def test_known_full_cell_score_is_monotone_in_payoff():
    state = _state(seat="player_1", own=80.0, complete=True, messages=True)
    state["player_2_value"] = 150.0
    scores = [seed.percentile(state, "player_1", payoff)
              for payoff in (0.0, 10.0, 30.0, 69.99)]
    assert all(score is not None for score in scores)
    assert scores == sorted(scores)


@pytest.mark.parametrize("scale", [100.0, 10_000.0, 1_000_000.0])
@pytest.mark.parametrize("messages", [False, True])
def test_scale_and_message_axes_are_literal_configuration_keys(scale, messages):
    state = _state(seat="player_2", own=1.2 * scale, complete=True,
                   messages=messages, horizon=1)
    state["player_1_value"] = 0.8 * scale
    assert seed.percentile(state, "player_2", 0.1 * scale) is not None


def test_unknown_horizon_maps_to_the_official_99_round_seed_cell():
    state = _state(seat="player_1", own=100.0, complete=True, horizon=99)
    state["player_2_value"] = 120.0
    assert seed.percentile(state, "player_1", 10.0) is not None
