from bisect import bisect_left, bisect_right

import pytest

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
