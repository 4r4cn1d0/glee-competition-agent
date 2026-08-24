"""Exact full-configuration percentiles from the official negotiation seed.

Unlike ``sim.percentile``, this module never pools over a hidden counterpart
value.  ``percentile`` therefore returns ``None`` unless both valuations are
known.  ``hidden_prior_percentiles`` exposes the four prior possibilities for
diagnostics, but callers must not treat their mean as an observed official
score after conditioning on an outcome or late-game exposure.
"""

from __future__ import annotations

import bisect
import json
import math
from pathlib import Path

from glee_agent.pricing import infer_base

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / \
    "negotiation_seed_cdf_full.json"
VALUE_MULTS = (0.8, 1.0, 1.2, 1.5)
_cells = None


def _load() -> dict:
    global _cells
    if _cells is None:
        try:
            document = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
            if document.get("_schema") != "glee.negotiation_seed_cdf/full-v1":
                return {}
            _cells = document.get("cells") or {}
        except (OSError, ValueError):
            _cells = {}
    return _cells


def _snap(value: float, base: float) -> float | None:
    ratio = value / base
    return next((mult for mult in VALUE_MULTS
                 if abs(ratio - mult) <= 1e-6), None)


def _key(state: dict, seat: str, seller_value: float,
         buyer_value: float) -> tuple[str, float] | None:
    if seat not in ("player_1", "player_2"):
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
        try:
            horizon = int(float(state.get("max_rounds")))
        except (TypeError, ValueError):
            return None
    else:
        horizon = 99
    if horizon not in (1, 10, 99):
        return None
    role = "seller" if seat == "player_1" else "buyer"
    key = "|".join(str(value) for value in (
        "negotiation-seed", horizon,
        state.get("complete_information") is True,
        state.get("messages_allowed") is True,
        int(base), f"{seller_mult:.1f}", f"{buyer_mult:.1f}", role,
    ))
    return key, base


def percentile(state: dict, seat: str, payoff: float, *,
               seller_value: float | None = None,
               buyer_value: float | None = None) -> float | None:
    """Official-seed midrank for a known full negotiation configuration."""
    if not isinstance(payoff, (int, float)) or not math.isfinite(float(payoff)):
        return None
    if seller_value is None:
        seller_value = state.get("player_1_value")
    if buyer_value is None:
        buyer_value = state.get("player_2_value")
    if not isinstance(seller_value, (int, float)) \
            or not isinstance(buyer_value, (int, float)):
        return None
    keyed = _key(state, seat, float(seller_value), float(buyer_value))
    if keyed is None:
        return None
    key, base = keyed
    samples = _load().get(key)
    if not samples:
        return None
    normalized = float(payoff) / base
    lo = bisect.bisect_left(samples, normalized - 1e-9)
    hi = bisect.bisect_right(samples, normalized + 1e-9)
    return (lo + hi) / 2 / len(samples)


def hidden_prior_percentiles(state: dict, seat: str,
                             payoff: float) -> list[float]:
    """Four latent-value scores under the ex-ante uniform grid, when available."""
    if seat not in ("player_1", "player_2"):
        return []
    own = state.get(f"{seat}_value")
    if not isinstance(own, (int, float)):
        return []
    base = infer_base(own)
    if base is None:
        return []
    values = []
    for counterpart_mult in VALUE_MULTS:
        seller = own if seat == "player_1" else counterpart_mult * base
        buyer = counterpart_mult * base if seat == "player_1" else own
        score = percentile(state, seat, payoff, seller_value=seller,
                           buyer_value=buyer)
        if score is not None:
            values.append(score)
    return values
