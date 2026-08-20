"""A learned negotiation policy: the decision table IS the model.

Everything before this evolved dials on a hand-written strategy; this makes the
strategy itself the learned object. For hidden-information negotiation -- the
71% of the family where the remaining rating lives -- the offer and the
acceptance threshold come from a table keyed by (seat, own value multiplier,
game phase), and the table is fitted by evolutionary search against the cloned
field on the estimated-percentile objective (scripts/evolve_table.py).

Genome layout (models/nego_policy_v1.json or GLEE_NEGO_TABLE_PATH):
  ask[seat][mult][phase]    -> our offer as a multiple of the base B
  accept[seat][phase]       -> minimum surplus/B required to accept mid-game

Guard rails are NOT evolved: offers are floored at strict profitability, the
final round of a capped game accepts any positive surplus (rejecting pays 0),
and any lookup failure returns None so the caller keeps the hand-written path.
Gated by GLEE_NEGO_TABLE.
"""
from __future__ import annotations

import json
import os
import threading
import time

from . import pricing

PHASES = ("open", "early", "late", "end")     # elapsed quartiles
MULTS = ("0.8", "1.0", "1.2", "1.5")

_LOCK = threading.Lock()
_STATE = {"checked": 0.0, "mtime": None, "path": None, "doc": None}


def _phase(elapsed: float) -> int:
    """Index into the phase axis. The genome stores phase LISTS in PHASES
    order; the first build indexed them with the phase NAME and every lookup
    fell to the except-clause -- an evolver run where nothing evolves."""
    return min(int(elapsed * 4), 3)


def _doc():
    path = os.environ.get("GLEE_NEGO_TABLE_PATH") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "models", "nego_policy_v1.json")
    now = time.monotonic()
    with _LOCK:
        if path == _STATE["path"] and now - _STATE["checked"] < 5.0:
            return _STATE["doc"]
        _STATE["checked"] = now
        try:
            mtime = os.stat(path).st_mtime_ns
        except OSError:
            if path != _STATE["path"]:
                _STATE["path"], _STATE["doc"], _STATE["mtime"] = path, None, None
            return _STATE["doc"]
        if path == _STATE["path"] and mtime == _STATE["mtime"]:
            return _STATE["doc"]
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            return _STATE["doc"]
        if isinstance(doc, dict) and "ask" in doc and "accept" in doc:
            _STATE.update(path=path, mtime=mtime, doc=doc)
        return _STATE["doc"]


def offer(my_value: float, i_am_seller: bool, elapsed: float) -> float | None:
    doc = _doc()
    base = pricing.infer_base(my_value)
    if not doc or base is None:
        return None
    seat = "seller" if i_am_seller else "buyer"
    mult = f"{my_value / base:.1f}"
    try:
        ask = float(doc["ask"][seat][mult][_phase(elapsed)]) * base
    except (KeyError, TypeError, ValueError):
        return None
    # never evolved through: strict profitability
    floor = my_value * (1.02 if i_am_seller else 0.98)
    return max(ask, floor) if i_am_seller else min(ask, floor)


def accept_threshold(my_value: float, i_am_seller: bool, elapsed: float) -> float | None:
    """Minimum acceptable surplus, in absolute currency. None -> no opinion."""
    doc = _doc()
    base = pricing.infer_base(my_value)
    if not doc or base is None:
        return None
    seat = "seller" if i_am_seller else "buyer"
    try:
        return float(doc["accept"][seat][_phase(elapsed)]) * base
    except (KeyError, TypeError, ValueError):
        return None
