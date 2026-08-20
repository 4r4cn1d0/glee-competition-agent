"""Curve-driven pricing: choose the ask from a fitted acceptance curve.

The strategy's constants (anchor multiples, margin fractions) were each measured
against one failure and shipped as the smallest safe change; this module is what
they were scaffolding for. The ask that maximises value depends on the
configuration -- most sharply on our own value multiplier, which a constant
cannot express. Fitted on 741 take-it-or-leave-it responses: a seller worth
0.8xB should ask ~1.4xB (P(accept) 35%, fat margin), while a seller worth 1.5xB
asking the old constant 1.36x its value would demand 2.04xB -- above the hard
cliff at 1.5xB where acceptance is 0/283, a guaranteed no-deal.

Curves live in models/negotiation_acceptance_v5.json (refit any time with
scripts/fit_acceptance.py; this module re-reads on mtime change). The axis is
price/B, where B is the configuration base, recoverable at decision time from
our own valuation because values are multiplier x B with multipliers in
{0.8, 1.0, 1.2, 1.5} and bases {100, 1e4, 1e6}.

The objective is P(accept | ask) x margin^gamma. gamma is live-tunable
(GLEE_NEGO_MARGIN_WEIGHT): 1.0 maximises expected payoff; lower values tilt
toward close frequency, which is the direction the percentile scoring pays --
51% of negotiation outcomes are exactly $0 and any positive close beats that
entire pile in its configuration.
"""
from __future__ import annotations

import json
import os
import threading
import time

from . import runtime_flags

_MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "models", "negotiation_acceptance_v5.json")
_BASES = (100.0, 1e4, 1e6)
_MULTS = (0.8, 1.0, 1.2, 1.5)
#: Trust no bin thinner than this; a 3-observation acceptance estimate is noise.
_MIN_BIN_N = 20

_LOCK = threading.Lock()
_STATE = {"checked": 0.0, "mtime": None, "curves": None}


def infer_base(value: float) -> float | None:
    """The configuration's base B, from our own valuation. None if off-grid."""
    if not value:
        return None
    for m in _MULTS:
        b = value / m
        for base in _BASES:
            if abs(b - base) <= base * 1e-6:
                return base
    return None


def _curves() -> dict | None:
    now = time.monotonic()
    with _LOCK:
        if now - _STATE["checked"] < 10.0:
            return _STATE["curves"]
        _STATE["checked"] = now
        try:
            mtime = os.stat(_MODEL_PATH).st_mtime_ns
        except OSError:
            return _STATE["curves"]         # keep last good; never flip live
        if mtime == _STATE["mtime"]:
            return _STATE["curves"]
        try:
            with open(_MODEL_PATH, encoding="utf-8") as fh:
                doc = json.load(fh)
            curves = doc.get("curves")
        except (OSError, ValueError):
            return _STATE["curves"]
        if isinstance(curves, dict):
            _STATE["mtime"] = mtime
            _STATE["curves"] = curves
        return _STATE["curves"]


def seller_final_ask(my_value: float) -> float | None:
    """The curve-optimal take-it-or-leave-it ask for a seller, or None.

    None means "no basis to price": the base is off-grid, the curve is missing,
    or no adequately-observed bin offers a profitable ask. The caller falls back
    to its existing constant-margin path, so this module can only ever replace a
    constant with a measurement, never with a guess.
    """
    base = infer_base(my_value)
    curves = _curves()
    if base is None or not curves:
        return None
    rows = curves.get("seller_final") or []
    gamma = runtime_flags.as_float("GLEE_NEGO_MARGIN_WEIGHT", 0.5)
    gamma = min(max(gamma, 0.05), 2.0)
    best_score, best_ask = 0.0, None
    for row in rows:
        if row.get("n", 0) < _MIN_BIN_N:
            continue
        p = row.get("p_accept") or 0.0
        if p <= 0.0:
            continue
        ask = (row["lo"] + row["hi"]) / 2.0 * base
        margin = ask - my_value
        if margin <= 0:
            continue
        score = p * (margin / base) ** gamma
        if score > best_score:
            best_score, best_ask = score, ask
    return best_ask
