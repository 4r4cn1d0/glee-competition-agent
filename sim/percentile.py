"""Score a simulated payoff as a percentile of the observed field distribution.

Loads models/percentile_cdf_v3.json (refit with scripts/fit_percentile.py).
percentile() returns the mid-rank of the payoff within its configuration cell,
or None when the cell is unknown -- callers must treat None as "no opinion",
never as zero.
"""
from __future__ import annotations

import bisect
import json
import os

_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "models", "percentile_cdf_v3.json")
_cells = None


def _load():
    global _cells
    if _cells is None:
        try:
            with open(_PATH, encoding="utf-8") as fh:
                _cells = json.load(fh)["cells"]
        except (OSError, ValueError, KeyError):
            _cells = {}
    return _cells


def percentile(family: str, params: dict, seat: str, payoff: float):
    cells = _load()
    if family == "bargaining":
        money = params.get("money_to_divide")
        if not money:
            return None
        key = "|".join(str(x) for x in (
            "bargaining", money, params.get("max_rounds"),
            bool(params.get("horizon_known")), bool(params.get("complete_information"))))
        norm = payoff / money
    elif family == "negotiation":
        my_value = params.get(f"{seat}_value")
        if not my_value:
            return None
        from sim.field_data import infer_base
        base = infer_base(my_value)
        if base is None:
            return None
        key = "|".join(str(x) for x in (
            "negotiation", base, round(my_value / base, 2), params.get("max_rounds"),
            bool(params.get("horizon_known")), bool(params.get("complete_information"))))
        norm = payoff / base
    else:
        return None
    samples = cells.get(key)
    if not samples:
        return None
    lo = bisect.bisect_left(samples, norm - 1e-9)
    hi = bisect.bisect_right(samples, norm + 1e-9)
    return (lo + hi) / 2 / len(samples)
