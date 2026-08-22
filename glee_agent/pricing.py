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

import bisect
import json
import math
import os
import threading
import time

from . import runtime_flags

_MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "models", "negotiation_acceptance_v5.json")
_CDF_PATH = os.path.join(os.path.dirname(_MODEL_PATH), "percentile_cdf_v3.json")
_BASES = (100.0, 1e4, 1e6)
_MULTS = (0.8, 1.0, 1.2, 1.5)
#: Trust no bin thinner than this; a 3-observation acceptance estimate is noise.
_MIN_BIN_N = 20
#: Conditional responder-type bins are sparse; this is the existing v5 fallback
#: contract used by posterior_final_ask before it substitutes the pooled rate.
_MIN_TYPE_BIN_N = 8
#: A 30-sample empirical CDF still has worst-case pointwise SE about 0.091;
#: below it, a single result moves rank by more than 3.3 percentile points.
_MIN_CDF_N = 30

_LOCK = threading.Lock()
_STATE = {"checked": 0.0, "mtime": None, "curves": None}
_CDF_STATE = {"checked": 0.0, "mtime": None, "cells": None}


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
# Rank-optimal pricing for a real terminal offer.
# ---------------------------------------------------------------------------

def _cdf_cells() -> dict | None:
    """Load the exact-cell payoff samples without importing simulator code."""
    now = time.monotonic()
    with _LOCK:
        if now - _CDF_STATE["checked"] < 10.0:
            return _CDF_STATE["cells"]
        _CDF_STATE["checked"] = now
        try:
            mtime = os.stat(_CDF_PATH).st_mtime_ns
        except OSError:
            return _CDF_STATE["cells"]       # keep last good; never flip live
        if mtime == _CDF_STATE["mtime"]:
            return _CDF_STATE["cells"]
        try:
            with open(_CDF_PATH, encoding="utf-8") as fh:
                cells = json.load(fh).get("cells")
        except (OSError, ValueError):
            return _CDF_STATE["cells"]
        if isinstance(cells, dict):
            _CDF_STATE.update(mtime=mtime, cells=cells)
        return _CDF_STATE["cells"]


def _midrank(samples: list[float], payoff_over_b: float) -> float:
    """Empirical CDF using the competition proxy's half-credit-for-ties rule."""
    lo = bisect.bisect_left(samples, payoff_over_b - 1e-9)
    hi = bisect.bisect_right(samples, payoff_over_b + 1e-9)
    return (lo + hi) / 2.0 / len(samples)


def _nego_cdf_key(base: float, my_value: float, role: str, state: dict) -> str:
    """Mirror scripts/fit_percentile.py's negotiation cell key exactly."""
    return "|".join(str(x) for x in (
        "negotiation", base, round(my_value / base, 2), role,
        state.get("max_rounds"), bool(state.get("horizon_known")),
        bool(state.get("complete_information"))))


def rank_terminal_price(my_value: float, i_am_seller: bool, state: dict,
                        opponent_value: float | None = None) -> dict:
    """Price a take-it-or-leave-it offer for expected payoff percentile.

    The bounded grid is the midpoint of every adequately observed pooled
    ``seller_final`` or ``buyer_final`` acceptance bin. Acceptance v5 estimates
    no within-bin slope, so a finer price grid would manufacture precision and
    extrapolating beyond those bins would manufacture coverage.

    In hidden games A(P) is the uniform mixture over the four responder-value
    curves, with the pooled rate substituted wherever a type bin has fewer than
    eight observations. Uniform is the structural hidden-type prior; deliberately
    do not reweight it with the selected v2 posterior. When the responder value is
    visible, use that type's curve with the same pooled fallback.

    This is still a fitted proxy, not an identified structural result. The CDF
    contains some of OUR OWN games. FINDINGS shows persuasion percentile
    calibration is coarse; negotiation cells are better populated, but that does
    not make them ground truth. Both the v2 posterior and v5 hidden-type labels are
    learned mainly from agreements (scripts/fit_posterior.py's label path), so
    those labels are selected-on-close even though we refuse v2's selected weights.
    """
    base = infer_base(my_value)
    if base is None:
        return {"status": "fallback", "reason": "unknown_base"}

    role = "seller" if i_am_seller else "buyer"
    cell_key = _nego_cdf_key(base, my_value, role, state)
    cells = _cdf_cells()
    raw_samples = cells.get(cell_key) if isinstance(cells, dict) else None
    if not isinstance(raw_samples, list) or not raw_samples:
        return {"status": "fallback", "reason": "unknown_cdf_cell",
                "cell": cell_key}
    try:
        samples = sorted(float(x) for x in raw_samples if math.isfinite(float(x)))
    except (TypeError, ValueError):
        return {"status": "fallback", "reason": "invalid_cdf_cell",
                "cell": cell_key}
    if len(samples) < _MIN_CDF_N:
        return {"status": "fallback", "reason": "thin_cdf_cell",
                "cell": cell_key, "cdf_n": len(samples)}

    curves = _curves()
    if not isinstance(curves, dict):
        return {"status": "fallback", "reason": "acceptance_curve_unavailable",
                "cell": cell_key, "cdf_n": len(samples)}
    rows = curves.get(f"{role}_final")
    if not isinstance(rows, list):
        return {"status": "fallback", "reason": "acceptance_curve_unavailable",
                "cell": cell_key, "cdf_n": len(samples)}

    my_over_b = my_value / base
    complete_information = bool(state.get("complete_information"))
    opponent_over_b = None
    if complete_information:
        try:
            opponent_over_b = float(opponent_value) / base
        except (TypeError, ValueError):
            return {"status": "fallback", "reason": "unknown_responder_type",
                    "cell": cell_key, "cdf_n": len(samples)}
    known_mult = None
    if complete_information:
        if not math.isfinite(opponent_over_b):
            return {"status": "fallback", "reason": "unknown_responder_type",
                    "cell": cell_key, "cdf_n": len(samples)}
        for mult in _MULTS:
            if abs(opponent_over_b - mult) <= 1e-6:
                known_mult = mult
                break
        if known_mult is None:
            return {"status": "fallback", "reason": "unknown_responder_type",
                    "cell": cell_key, "cdf_n": len(samples)}
    acceptance_basis = ("known_responder_type" if known_mult is not None
                        else "uniform_hidden_types")
    f_zero = _midrank(samples, 0.0)
    candidates = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            lo, hi = float(row["lo"]), float(row["hi"])
            n = int(row.get("n", 0))
            p_accept = float(row["p_accept"])
        except (KeyError, TypeError, ValueError):
            continue
        if (n < _MIN_BIN_N or not all(math.isfinite(x) for x in (lo, hi, p_accept))
                or lo < 0.0 or hi <= lo or not 0.0 <= p_accept <= 1.0):
            continue
        type_mults = (known_mult,) if known_mult is not None else _MULTS
        type_rates = []
        for mult in type_mults:
            rate = None
            type_rows = curves.get(f"{role}|m{mult}_final") or []
            for type_row in type_rows:
                if not isinstance(type_row, dict):
                    continue
                try:
                    same_bin = (float(type_row["lo"]) == lo
                                and float(type_row["hi"]) == hi)
                    type_n = int(type_row.get("n", 0))
                    type_rate = float(type_row["p_accept"])
                except (KeyError, TypeError, ValueError):
                    continue
                if (same_bin and type_n >= _MIN_TYPE_BIN_N
                        and math.isfinite(type_rate) and 0.0 <= type_rate <= 1.0):
                    rate = type_rate
                    break
            type_rates.append(p_accept if rate is None else rate)
        p_accept = sum(type_rates) / len(type_rates)
        if p_accept <= 0.0:
            continue
        price_over_b = (lo + hi) / 2.0
        payoff_over_b = ((price_over_b - my_over_b) if i_am_seller
                         else (my_over_b - price_over_b))
        if payoff_over_b <= 0.0:
            continue                         # never trade through our own value
        if opponent_over_b is not None:
            if i_am_seller and price_over_b >= opponent_over_b:
                continue                     # visible buyer gets no positive gain
            if not i_am_seller and price_over_b <= opponent_over_b:
                continue                     # visible seller gets no positive gain
        f_payoff = _midrank(samples, payoff_over_b)
        expected_rank = (p_accept * f_payoff
                         + (1.0 - p_accept) * f_zero)
        candidates.append({
            "price": price_over_b * base,
            "p_accept": p_accept,
            "acceptance_n": n,
            "expected_money_over_b": p_accept * payoff_over_b,
            "expected_rank": expected_rank,
        })

    if not candidates:
        return {"status": "fallback", "reason": "no_acceptance_coverage",
                "cell": cell_key, "cdf_n": len(samples)}

    # Rank ties go to the higher-acceptance action. Money ties go to the action
    # with the higher rank, so neither comparator is needlessly rejection-prone.
    generosity = (lambda x: -x["price"]) if i_am_seller else (lambda x: x["price"])
    rank_best = max(candidates,
                    key=lambda x: (x["expected_rank"], x["p_accept"],
                                   generosity(x)))
    money_best = max(candidates,
                     key=lambda x: (x["expected_money_over_b"],
                                    x["expected_rank"], x["p_accept"],
                                    generosity(x)))
    return {
        "status": "applied",
        "reason": "max_expected_rank",
        "cell": cell_key,
        "acceptance_basis": acceptance_basis,
        "chosen_price": rank_best["price"],
        "money_optimal_price": money_best["price"],
        "chosen_acceptance": rank_best["p_accept"],
        "money_acceptance": money_best["p_accept"],
        "chosen_expected_rank": rank_best["expected_rank"],
        "money_expected_rank": money_best["expected_rank"],
        "cdf_at_zero": f_zero,
        "cdf_n": len(samples),
        "grid_points": len(candidates),
    }


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
