"""Expected-percentile offer choice for the bargaining seat that answers.

Bob (player_2) responds first and proposes on even rounds. Until this module his
ask came from ``proposer_share()``, the exact alternating-offers recursion, whose
value swings with round parity -- and in Bob's seat the swing is structural, not
incidental. Disclosed games state max_rounds = 12, an EVEN cap, so player_2 is
the last proposer: the recursion hands Bob 0.77-1.00 of the pot on every even
round and Alice 0.00-0.74 on every odd one. That last word is genuinely his and
genuinely worthless -- banking it means agreeing at round 12, where delta_me =
0.8 leaves 8.6% of face value. The blend and the two floors then flatten the
whole oscillation into one number, and 532 of Bob's 704 logged offers landed in
the single bin [0.60, 0.65) regardless of who he was playing.

What decides whether an offer closes, over the 15,812 offers we have made in
9,881 logged bargaining games, is the responder's patience. At a give of
0.35-0.45 of the pot: delta_opp = 0.8 accepts 63.6% (n=761), 0.9 accepts 31.0%,
0.95 accepts 15.5%, 1.0 accepts 6.2% (n=926). Our equilibrium claim appears
nowhere in that.

And the rating is a percentile of the DISCOUNTED payoff inside the configuration
cell, so the value of a rejection is not symmetric between seats or clocks. Also
measured, as the realised percentile after one of our offers was refused:

    our delta = 1.0 (waiting is free)   round 2 -> 0.66,  round 6 -> 0.74
    our delta < 1.0 (the clock burns)   round 2 -> 0.28,  round 6 -> 0.06

A patient player loses almost nothing to a refusal and should ask high; a
burning one is choosing between closing now and collecting a fifth of the field.
The same 0.61 ask cannot be right for both.

So the ask is chosen by maximising expected percentile directly:

    argmax_a  P(accept | 1-a, round, delta_opp, their demand) * F(a * delta_me^(r-1))
              + (1 - P(accept | ...)) * V_cont(round, clock)

where F is the field's own payoff distribution in this configuration cell -- the
object the rating is taken against, whose 9.6% atom at exactly half the pot is
why crossing it pays +0.095 percentile per 0.01 of pot against +0.025 elsewhere.
All three come from models/barg_bob_offer_v1.json (scripts/fit_barg_bob_offer.py).

The caller ships this as a FLOOR on the ask, not as a concession rule, and
passes `lo` = the baseline ask to enforce that. The reason is a limit of the
offline screen rather than of the model: the arena's cloned responders are
fitted on (share, round) alone and are blind to their own delta, so the half of
this optimisation that trades share for acceptance -- the half that rests on the
63.6%-vs-6.2% patience gap above -- cannot be priced there, and screening it
returned -0.028 percentile [-0.049, -0.009] in the delta_me = 0.95 cell. Treat
that as unmeasured, not as refuted. See the call site in strategies/bargaining.py.

Returns None -- and the caller keeps its baseline ask -- whenever the file is
missing, the cell is unmodelled, the pot is degenerate, or no reachable offer
beats simply playing on. A missing model must never change how the agent plays.
"""
from __future__ import annotations

import bisect
import json
import math
import os
import threading
import time

_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "models", "barg_bob_offer_v1.json")

#: Ask grid, in pot share. 1% steps: finer than the field's own 4% response bins
#: and finer than the CDF knots, so a finer grid would only chase quantisation.
_GRID_LO, _GRID_HI, _GRID_STEP = 0.20, 0.95, 0.01

#: How much expected percentile the best ask must beat "just keep playing" by
#: before we act on it. Without this the optimiser has a degenerate corner: once
#: our clock has burned far enough that NO closable offer beats V_cont -- round
#: 8 at delta_me = 0.8 leaves 21% of face value, so even the whole pot scores
#: below the field's median -- every ask scores V_cont, the argmax is noise, and
#: tie-breaking upward picks the top of the grid, i.e. a guaranteed no-deal. In
#: that state the model has no opinion and must say so; the baseline concession
#: schedule, which the sweep already priced, keeps the seat.
_MIN_EDGE = 0.005

_LOCK = threading.Lock()
_STATE = {"checked": 0.0, "mtime": None, "doc": None}


def _doc() -> dict | None:
    """The fitted model, re-read when the file changes; None if unreadable.

    Same discipline as runtime_flags: a torn or missing read keeps the last good
    document rather than silently reverting a running agent to no model.
    """
    now = time.monotonic()
    with _LOCK:
        if now - _STATE["checked"] < 10.0:
            return _STATE["doc"]
        _STATE["checked"] = now
        try:
            mtime = os.stat(_PATH).st_mtime_ns
        except OSError:
            return _STATE["doc"]
        if mtime == _STATE["mtime"]:
            return _STATE["doc"]
        try:
            with open(_PATH, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            return _STATE["doc"]
        if not isinstance(doc, dict) or not doc.get("accept"):
            return _STATE["doc"]
        _STATE["mtime"] = mtime
        _STATE["doc"] = doc
        return doc


def cell_key(money, max_rounds, horizon_known, complete_information) -> str:
    return "|".join(str(x) for x in (money, max_rounds,
                                     bool(horizon_known), bool(complete_information)))


def _p_accept(doc, give, rnd, dop, their_demand) -> float:
    a = doc["accept"]
    cliff = a.get("cliff", 0.39)
    x = [1.0,
         give,
         1.0 if give >= cliff else 0.0,
         0.0 if dop is None else (float(dop) - 0.9) * 10.0,
         1.0 if (dop is not None and float(dop) >= 1.0) else 0.0,
         1.0 if dop is None else 0.0,
         1.0 if rnd >= 4 else 0.0,
         1.0 if rnd <= 1 else 0.0,
         0.5 if their_demand is None else float(their_demand)]
    z = sum(c * xi for c, xi in zip(a["coef"], x))
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))


def _cdf(doc, key):
    """Sorted payoff/money knots for this rating cell, or the pooled fallback."""
    knots = (doc.get("cdf") or {}).get(key)
    if knots:
        return knots
    return doc.get("cdf_pooled") or None


def _percentile(knots, x) -> float:
    lo = bisect.bisect_left(knots, x - 1e-9)
    hi = bisect.bisect_right(knots, x + 1e-9)
    return (lo + hi) / 2.0 / len(knots)


def _vcont(doc, rnd, delta_me) -> float:
    clock = "patient" if (delta_me is None or delta_me >= 1.0) else "burning"
    table = doc.get("vcont") or {}
    for r in range(min(int(rnd), 6), 0, -1):
        hit = table.get(f"{r}|{clock}")
        if hit is not None:
            return float(hit)
    return float(doc.get("vcont_default", 0.42))


def best_ask(money, rnd, delta_me, delta_opp, their_demand, cell,
             lo=None, hi=None):
    """Our pot share maximising expected percentile, or None if unmodelled.

    `their_demand` is the share the opponent kept in their most recent offer --
    the demand Bob is answering, and the strongest single predictor of whether
    they will take ours after `give`. `lo`/`hi` clamp the grid to whatever the
    caller's own floors already guarantee.

    Returns (ask_share, diagnostics).
    """
    doc = _doc()
    if not doc or not money or money <= 0:
        return None
    knots = _cdf(doc, cell)
    if not knots:
        return None
    rnd = max(1, int(rnd))
    d = 1.0 if delta_me is None else max(0.0, min(1.0, float(delta_me)))
    mult = d ** (rnd - 1)
    v = _vcont(doc, rnd, delta_me)

    lo_ = _GRID_LO if lo is None else max(_GRID_LO, float(lo))
    hi_ = _GRID_HI if hi is None else min(_GRID_HI, float(hi))
    if hi_ < lo_:
        return None

    best, best_ev = None, -1.0
    n = int(round((hi_ - lo_) / _GRID_STEP))
    for i in range(n + 1):
        a = round(lo_ + i * _GRID_STEP, 4)
        p = _p_accept(doc, 1.0 - a, rnd, delta_opp, their_demand)
        ev = p * _percentile(knots, a * mult) + (1.0 - p) * v
        # Ties go to the LARGER ask: the percentile map is a step function, so
        # long flats are common and conceding across one buys nothing.
        if ev >= best_ev - 1e-9:
            best = (a, ev, p)
        best_ev = max(best_ev, ev)
    if best is None or best[1] <= v + _MIN_EDGE:
        return None
    return best[0], {"ev_percentile": round(best[1], 4),
                     "p_accept": round(best[2], 4),
                     "v_cont": round(v, 4),
                     "discount_mult": round(mult, 4)}
