"""Live per-agent flag overlay, re-read from arms.json while the agent runs.

Every strategy gate reads ``os.environ`` at *decision* time rather than at
import, which means a flag can change mid-process if something changes what the
gate reads. The supervisor plants the arm in the environment at launch, so until
now a flag change could only land by restarting the agent -- and a restart is
expensive: SIGINT abandons the 6-9 games an agent holds at any moment, each
scored at the 5th percentile, and three abandoned games in a row earn a 30-minute
queue ban. So "deploy a strategy" cost real placement.

This module removes that cost. The gates consult arms.json first and fall back to
the environment, so ``fleet.py set <probe> FLAG=1`` reaches a running agent within
POLL_SECONDS with no restart, no abandoned games, and no ban risk. At launch the
two agree by construction (the supervisor seeds env from the same file), so
adding the overlay changes nothing until someone deliberately edits arms.json.

Deliberately conservative:
  * An agent with no ``GLEE_PROBE`` (e.g. one adopted from before this existed,
    or a local one-off run) gets no overlay at all and behaves exactly as before.
  * An unreadable or half-written arms.json keeps the last good values rather
    than silently reverting a live agent to defaults. Writers use os.replace, so
    a torn read should not happen, but a strategy must never flip because of a
    filesystem hiccup.
  * A probe absent from arms.json falls through to the environment instead of
    resolving to "no flags" -- removing an entry is not a way to disarm an agent.
"""
from __future__ import annotations

import json
import os
import threading
import time

#: Re-stat at most this often. The file is tiny, but a gate is consulted several
#: times per decision across concurrent games; statting each time is pure waste.
POLL_SECONDS = 3.0

_ARMS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "arms.json")
_LOCK = threading.Lock()
_STATE = {"checked": 0.0, "mtime": None, "arms": None}


def _load() -> dict | None:
    """Current arms.json contents, or None if it has never been read cleanly."""
    now = time.monotonic()
    with _LOCK:
        if now - _STATE["checked"] < POLL_SECONDS:
            return _STATE["arms"]
        _STATE["checked"] = now
        try:
            mtime = os.stat(_ARMS_PATH).st_mtime_ns
        except OSError:
            return _STATE["arms"]          # keep last good; never revert live
        if mtime == _STATE["mtime"]:
            return _STATE["arms"]
        try:
            with open(_ARMS_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            return _STATE["arms"]          # torn or malformed; keep last good
        if not isinstance(data, dict):
            return _STATE["arms"]
        _STATE["mtime"] = mtime
        _STATE["arms"] = data
        return data


def get(name: str) -> str | None:
    """Value of ``name`` for this agent: arms.json first, then the environment."""
    probe = os.environ.get("GLEE_PROBE", "").strip()
    if probe:
        arms = _load()
        if isinstance(arms, dict):
            arm = arms.get(probe)
            if isinstance(arm, dict) and name in arm:
                return str(arm[name])
    return os.environ.get(name)


def enabled(name: str) -> bool:
    return (get(name) or "").strip().lower() in ("1", "true", "yes", "on")


def as_float(name: str, default: float) -> float:
    try:
        return float(get(name))          # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
