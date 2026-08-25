import json
import math
from bisect import bisect_left, bisect_right
from pathlib import Path

import pytest

from scripts import fit_percentile
from scripts.fit_percentile import _cap_cell_distribution


def _midrank(values, payoff):
    return (
        bisect_left(values, payoff) + bisect_right(values, payoff)
    ) / (2.0 * len(values))


def test_cell_cap_keeps_small_cells_exact_and_sorted():
    values = [0.7, 0.0, 0.4, 0.4]

    assert _cap_cell_distribution(values, limit=10) == [0.0, 0.4, 0.4, 0.7]


def test_cell_cap_samples_the_whole_distribution_instead_of_the_top_tail():
    values = [0.0] * 2_500 + [index / 10_000 for index in range(2_500, 10_000)]

    capped = _cap_cell_distribution(values, limit=2_000)

    assert len(capped) == 2_000
    assert capped == sorted(capped)
    assert capped[0] == values[0]
    assert capped[-1] == values[-1]
    assert 490 <= capped.count(0.0) <= 510
    assert abs(_midrank(capped, 0.48) - _midrank(values, 0.48)) <= 0.001


def test_cell_cap_is_deterministic_and_rejects_invalid_limits():
    values = list(reversed(range(10_000)))

    first = _cap_cell_distribution(values, limit=2_000)
    second = _cap_cell_distribution(values, limit=2_000)

    assert first == second
    assert len(set(first)) == 2_000
    with pytest.raises(ValueError, match="positive"):
        _cap_cell_distribution(values, limit=0)


def test_fit_can_write_a_candidate_without_replacing_the_default(monkeypatch, tmp_path):
    candidate = tmp_path / "candidate.json"
    finals = [
        {
            "game_family": "bargaining",
            "your_player": "player_1",
            "game_state": {
                "money_to_divide": 100,
                "max_rounds": 12,
                "horizon_known": True,
                "complete_information": True,
            },
            "result": {"player_1_payoff": 0, "player_2_payoff": 100},
        }
        for _ in range(25)
    ]
    monkeypatch.setattr(fit_percentile, "_iter_finals", lambda: iter(finals))

    assert fit_percentile.fit(str(candidate)) == 0

    doc = json.loads(candidate.read_text())
    samples = doc["cells"]["bargaining|100|12|True|True"]
    assert samples.count(0.0) == 25
    assert samples.count(1.0) == 25


def test_checked_in_artifact_retains_full_capped_distributions():
    """Fail if a stale top-tail refit is checked in again.

    Commit 1f757c7 replaced a fixed fitter's artifact with an older direct
    refit: every saturated bargaining cell lost its zero atom and began near
    0.47.  Metadata alone cannot detect a stale blob, so validate both the cap
    method and the empirical tail invariant exhibited by all 12 current
    bargaining cells.
    """
    artifact = Path(fit_percentile.OUT)
    doc = json.loads(artifact.read_text(encoding="utf-8"))
    cap = doc.get("_cell_cap") or {}

    assert cap == {
        "max_samples": fit_percentile.MAX_PER_CELL,
        "method": "evenly_spaced_order_statistics",
    }
    assert doc.get("_schema") == "glee.percentile_cdf/v3"

    cells = doc.get("cells") or {}
    assert cells
    for values in cells.values():
        assert 0 < len(values) <= fit_percentile.MAX_PER_CELL
        assert all(isinstance(value, (int, float)) and math.isfinite(value)
                   for value in values)
        assert values == sorted(values)

    bargaining = [
        values for key, values in cells.items()
        if key.startswith("bargaining|")
    ]
    assert len(bargaining) == 12
    assert all(len(values) == fit_percentile.MAX_PER_CELL
               for values in bargaining)
    assert all(values[0] == 0.0 and 0.0 in values for values in bargaining)
