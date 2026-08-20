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


# ---------------------------------------------------------------------------
# Posterior-conditional pricing for hidden-information games.
# ---------------------------------------------------------------------------

_POST_PATH = os.path.join(os.path.dirname(_MODEL_PATH),
                          "negotiation_value_posterior_v2.json")
_POST_STATE = {"checked": 0.0, "mtime": None, "doc": None}
_POST_EDGES = [0.0, 0.7, 0.9, 1.05, 1.2, 1.4, 1.6, 1.9, 2.3, 3.0, 99.0]


def _posterior_doc():
    now = time.monotonic()
    with _LOCK:
        if now - _POST_STATE["checked"] < 10.0:
            return _POST_STATE["doc"]
        _POST_STATE["checked"] = now
        try:
            mtime = os.stat(_POST_PATH).st_mtime_ns
        except OSError:
            return _POST_STATE["doc"]
        if mtime == _POST_STATE["mtime"]:
            return _POST_STATE["doc"]
        try:
            with open(_POST_PATH, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            return _POST_STATE["doc"]
        if isinstance(doc, dict) and doc.get("table") is not None:
            _POST_STATE["mtime"] = mtime
            _POST_STATE["doc"] = doc
        return _POST_STATE["doc"]


def posterior_mults(their_role: str, their_first_over_B: float | None):
    """[(mult, p), ...] over the opponent's value multiplier.

    Conditioned on their first offer when we have both the observation and a
    fitted cell (n>=15); the fitted marginal otherwise. None when the model is
    missing entirely -- callers must then behave as if this module didn't exist.
    """
    doc = _posterior_doc()
    if not doc:
        return None
    mults = [float(m) for m in doc["mults"]]
    dist = [float(doc["marginal"][str(m)]) for m in mults]
    if their_first_over_B is not None and their_role:
        for lo, hi in zip(_POST_EDGES, _POST_EDGES[1:]):
            if lo <= their_first_over_B < hi:
                cell = doc["table"].get(f"{their_role}|{lo}-{hi}")
                if cell:
                    dist = cell["p"]
                break
    return list(zip(mults, dist))


def _seat_mult_curve(seat: str, mult: float, pos: str):
    curves = _curves()
    if not curves:
        return None
    return curves.get(f"{seat}|m{mult}_{pos}")


def posterior_final_ask(my_value: float, their_role: str,
                        their_first_over_B: float | None,
                        i_am_seller: bool) -> float | None:
    """Final-offer price from posterior-mixed BEHAVIOURAL acceptance curves.

    v1 of this idea priced 'a hair inside the rational step' and the arena
    rejected it on both seeds: the field does not accept near-threshold prices
    at rational rates, and a static step-ask closes less than the concession
    walk it replaced. This version scores candidate prices against the fitted
    per-multiplier acceptance curves -- what opponents of each hidden value
    ACTUALLY accepted -- mixed by the posterior, and only ever prices the final
    offer, where a rejection has no continuation to damage.
    """
    base = infer_base(my_value)
    post = posterior_mults(their_role, their_first_over_B)
    if base is None or not post:
        return None
    my_seat = "seller" if i_am_seller else "buyer"
    pooled = (_curves() or {}).get(f"{my_seat}_final") or []
    pooled_p = {(r["lo"], r["hi"]): r.get("p_accept", 0.0) for r in pooled
                if r.get("n", 0) >= _MIN_BIN_N}
    gamma = runtime_flags.as_float("GLEE_NEGO_MARGIN_WEIGHT", 0.5)
    gamma = min(max(gamma, 0.05), 2.0)
    best_score, best_ask = 0.0, None
    for (lo, hi), pool_acc in pooled_p.items():
        mid = (lo + hi) / 2.0 * base
        margin = (mid - my_value) if i_am_seller else (my_value - mid)
        if margin <= 0:
            continue
        mix = 0.0
        for mult, pm in post:
            rows = _seat_mult_curve(my_seat, mult, "final")
            a = None
            if rows:
                for r in rows:
                    if r["lo"] == lo and r["hi"] == hi and r.get("n", 0) >= 8:
                        a = r.get("p_accept", 0.0)
                        break
            if a is None:
                a = pool_acc            # thin cell: fall back to the pooled rate
            mix += pm * a
        score = mix * (margin / base) ** gamma
        if score > best_score:
            best_score, best_ask = score, mid
    return best_ask


def posterior_cap(my_value: float, their_role: str,
                  their_first_over_B: float | None,
                  i_am_seller: bool) -> float | None:
    """The most aggressive MID-ROUND price the posterior still considers live.

    Mid-round pricing stays with the concession walk (replacing it measured
    worse); the posterior's mid-game job is only to stop the walk from
    stonewalling in a region the opponent's value cannot reach -- e.g. a seller
    holding at 1.4xB against a buyer whose first offer marked them 91% a
    0.8-value. Cap = one step inside the highest multiplier with meaningful
    posterior mass.
    """
    base = infer_base(my_value)
    post = posterior_mults(their_role, their_first_over_B)
    if base is None or not post:
        return None
    live = [m for m, pm in post if pm >= 0.05]
    if not live:
        return None
    return (max(live) * base * 0.97) if i_am_seller else (min(live) * base * 1.03)


# ---------------------------------------------------------------------------
# Stall response: where to park against a stonewalling opponent.
# ---------------------------------------------------------------------------

_STALL_PATH = os.path.join(os.path.dirname(_MODEL_PATH), "stall_response_v1.json")
_STALL_STATE = {"checked": 0.0, "mtime": None, "doc": None}


def _stall_doc():
    now = time.monotonic()
    with _LOCK:
        if now - _STALL_STATE["checked"] < 10.0:
            return _STALL_STATE["doc"]
        _STALL_STATE["checked"] = now
        try:
            mtime = os.stat(_STALL_PATH).st_mtime_ns
        except OSError:
            return _STALL_STATE["doc"]
        if mtime == _STALL_STATE["mtime"]:
            return _STALL_STATE["doc"]
        try:
            with open(_STALL_PATH, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            return _STALL_STATE["doc"]
        if isinstance(doc, dict) and "seller" in doc:
            _STALL_STATE.update(mtime=mtime, doc=doc)
        return _STALL_STATE["doc"]


def stall_park(my_value: float, i_am_seller: bool) -> float | None:
    """The best PROFITABLE price to hold against a stonewalling opponent.

    Fitted on 1,644 stalled games: stallers stall their OFFERS, not their
    acceptance -- 53% of stalled closes were them taking our price -- and their
    acceptance has sweet spots strictly BETWEEN the value-grid points (a price
    at a staller's own value gives them zero surplus; 0.1B inside it gives them
    a reason). Stalled sellers take bids of 1.3-1.4B at 17-18% per offer while
    grid-point bids run 0.1-2% -- and our normal pricing concentrates exactly on
    the dead grid points. Parking = repeating the sweet-spot price; at ~5-18%
    per offer, ten held rounds compound to 40%+ cumulative acceptance.

    None when no profitable bin with n>=50 exists (e.g. a 1.5xB seller):
    caller falls back to freezing.
    """
    base = infer_base(my_value)
    doc = _stall_doc()
    if base is None or not doc:
        return None
    seat = "seller" if i_am_seller else "buyer"
    gamma = runtime_flags.as_float("GLEE_NEGO_MARGIN_WEIGHT", 0.5)
    gamma = min(max(gamma, 0.05), 2.0)
    best, best_price = 0.0, None
    for pb, cell in (doc.get(seat) or {}).items():
        if cell.get("n", 0) < 50 or not cell.get("p"):
            continue
        # a bin whose probability rests on 1-2 accepts is a tail artifact (a
        # single irrational buyer at 3.5xB once outscored every real sweet spot
        # on margin alone); demand >=3 observed accepts and a sane price range
        if cell["p"] * cell["n"] < 3 or float(pb) > 2.0:
            continue
        price = float(pb) * base
        margin = (price - my_value) if i_am_seller else (my_value - price)
        if margin <= 0:
            continue
        score = cell["p"] * (margin / base) ** gamma
        if score > best:
            best, best_price = score, price
    return best_price
