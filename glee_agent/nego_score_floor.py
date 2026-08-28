"""Official-seed payoff floors for complete-information negotiation cells.

The live scorer compares a payoff with the same full configuration and role.
This helper deliberately refuses hidden-information states: averaging over an
unobserved counterpart value would not reproduce the scoring cell.  The model
is the checked-in official GLEE seed, not a continuation model and not a claim
that the evolving live field has the same empirical CDF forever.
"""

from __future__ import annotations

import bisect
import json
import math
from pathlib import Path

from .pricing import infer_base


MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "negotiation_seed_cdf_full.json"
)
MODEL_SCHEMA = "glee.negotiation_seed_cdf/full-v1"
VALUE_MULTS = (0.8, 1.0, 1.2, 1.5)

_cells: dict | None = None


def _load_cells() -> dict:
    """Load the immutable seed model once; malformed artifacts fail closed."""
    global _cells
    if _cells is None:
        try:
            document = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
            if document.get("_schema") != MODEL_SCHEMA:
                _cells = {}
            else:
                cells = document.get("cells")
                _cells = cells if isinstance(cells, dict) else {}
        except (OSError, ValueError):
            _cells = {}
    return _cells


def _snap(value: float, base: float) -> float | None:
    ratio = value / base
    return next(
        (mult for mult in VALUE_MULTS if abs(ratio - mult) <= 1e-6),
        None,
    )


def _samples(
    state: dict,
    seat: str,
    seller_value: float,
    buyer_value: float,
) -> tuple[list[float], float] | None:
    """Return one exact official-seed cell and its monetary base."""
    if (
        seat not in ("player_1", "player_2")
        or state.get("complete_information") is not True
        or not isinstance(state.get("messages_allowed"), bool)
        or not math.isfinite(seller_value)
        or not math.isfinite(buyer_value)
        or seller_value <= 0.0
        or buyer_value <= seller_value
    ):
        return None

    own_value = seller_value if seat == "player_1" else buyer_value
    base = infer_base(own_value)
    if base is None:
        return None
    seller_mult = _snap(seller_value, base)
    buyer_mult = _snap(buyer_value, base)
    if seller_mult is None or buyer_mult is None:
        return None

    if state.get("horizon_known") is True:
        raw_horizon = state.get("max_rounds")
        if isinstance(raw_horizon, bool):
            return None
        try:
            horizon_number = float(raw_horizon)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(horizon_number) or not horizon_number.is_integer():
            return None
        horizon = int(horizon_number)
    elif state.get("horizon_known") is False and state.get("max_rounds") is None:
        # The official corpus records the nominally unknown horizon as 99.
        horizon = 99
    else:
        return None
    if horizon not in (1, 10, 99):
        return None

    role = "seller" if seat == "player_1" else "buyer"
    key = "|".join(
        str(value)
        for value in (
            "negotiation-seed",
            horizon,
            True,
            state["messages_allowed"],
            int(base),
            f"{seller_mult:.1f}",
            f"{buyer_mult:.1f}",
            role,
        )
    )
    samples = _load_cells().get(key)
    if not isinstance(samples, list) or not samples:
        return None
    if not all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        for value in samples
    ):
        return None
    if any(float(left) > float(right)
           for left, right in zip(samples, samples[1:])):
        return None
    return samples, float(base)


def _midrank(samples: list[float], normalized_payoff: float) -> float:
    lo = bisect.bisect_left(samples, normalized_payoff - 1e-9)
    hi = bisect.bisect_right(samples, normalized_payoff + 1e-9)
    return (lo + hi) / 2.0 / len(samples)


def cent_payoff_floor(
    state: dict,
    seat: str,
    seller_value: float,
    buyer_value: float,
    target_percentile: float,
    max_payoff: float,
) -> tuple[float, float, int] | None:
    """Smallest cent payoff whose exact seed midrank reaches ``target``.

    The returned tuple is ``(payoff, achieved_percentile, cell_sample_size)``.
    A binary search over legal cent amounts is exact because empirical midrank
    is monotone.  If the target cannot be reached while leaving the other side
    at least one cent, the caller keeps its existing policy.
    """
    if (
        isinstance(target_percentile, bool)
        or not isinstance(target_percentile, (int, float))
        or not math.isfinite(float(target_percentile))
        or not 0.5 < float(target_percentile) < 1.0
        or isinstance(max_payoff, bool)
        or not isinstance(max_payoff, (int, float))
        or not math.isfinite(float(max_payoff))
    ):
        return None
    resolved = _samples(state, seat, seller_value, buyer_value)
    if resolved is None:
        return None
    samples, base = resolved
    max_cents = int(math.floor((float(max_payoff) + 1e-9) * 100.0))
    if max_cents < 1:
        return None

    target = float(target_percentile)

    def percentile(cents: int) -> float:
        return _midrank(samples, (cents / 100.0) / base)

    if percentile(max_cents) + 1e-12 < target:
        return None
    low, high = 1, max_cents
    while low < high:
        middle = (low + high) // 2
        if percentile(middle) + 1e-12 >= target:
            high = middle
        else:
            low = middle + 1
    achieved = percentile(low)
    return low / 100.0, achieved, len(samples)
