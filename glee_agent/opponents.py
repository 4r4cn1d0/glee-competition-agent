"""Opponent-conditional play: read the profile of who we are facing.

Half of games disclose the opponent's name, the mid-field is 78% deterministic
template bots, and 26 of the 28 opponents with enough repeat observations are
>=95% self-consistent. Their fitted profiles (models/opponent_profiles.json,
refit with scripts/profile_opponents.py) contain, among other things, the lowest
share of the pot each has ever been seen accepting at a >=70% rate. Those
thresholds span 0.17 to 0.50 -- and until this module, we offered every one of
them the same flat share.

This is the one edge an LLM opponent structurally cannot copy: it sees one game
at a time, we have seen every game we ever played against this name.

Deliberately conservative, because a wrong exploit costs a real deal:
  * a profile fires only above a per-field sample-size floor;
  * the fitted threshold must be a share the opponent was actually SEEN
    accepting (the fitter guarantees this), and we pad it rather than offer it
    exactly;
  * an unknown name, a hidden opponent, a thin profile, or a missing file all
    return None, and the caller keeps its baseline behaviour.
"""
from __future__ import annotations

import json
import os
import threading
import time

_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "models", "opponent_profiles.json")
#: Minimum labelled observations behind a bargaining threshold before we act on it.
MIN_N = 30
#: Offer this much above the fitted threshold, in pot share. The threshold is
#: the lowest ACCEPTED observation; the pad buys room for the binning.
PAD = 0.04

_LOCK = threading.Lock()
_STATE = {"checked": 0.0, "mtime": None, "profiles": None}


def _profiles() -> dict | None:
    now = time.monotonic()
    with _LOCK:
        if now - _STATE["checked"] < 10.0:
            return _STATE["profiles"]
        _STATE["checked"] = now
        try:
            mtime = os.stat(_PATH).st_mtime_ns
        except OSError:
            return _STATE["profiles"]
        if mtime == _STATE["mtime"]:
            return _STATE["profiles"]
        try:
            with open(_PATH, encoding="utf-8") as fh:
                doc = json.load(fh)
            profiles = doc.get("profiles")
        except (OSError, ValueError):
            return _STATE["profiles"]
        if isinstance(profiles, dict):
            _STATE["mtime"] = mtime
            _STATE["profiles"] = profiles
        return _STATE["profiles"]


def opponent_name(game: dict) -> str | None:
    opp = game.get("opponent")
    if isinstance(opp, dict):
        name = opp.get("name")
        if name:
            return str(name)
    return None


def barg_give_floor(game: dict) -> float | None:
    """The share of the pot this opponent needs to be offered, or None.

    None means "no basis": act exactly as if the opponent were unknown. A float
    g means: offers giving them at least g have historically been accepted at
    >=70% by this specific opponent, so the baseline generosity floor can be
    tightened to g for them.
    """
    name = opponent_name(game)
    profiles = _profiles()
    if not name or not profiles:
        return None
    barg = (profiles.get(name) or {}).get("bargaining") or {}
    thr = barg.get("accept_threshold")
    n = barg.get("n") or 0
    if thr is None or n < MIN_N:
        return None
    give = thr + PAD
    if not (0.02 <= give <= 0.5):
        return None
    return give
