"""Cooperative fleet-stop limit for live agents.

The supervisor cannot safely signal a busy agent: live processes normally hold
6-9 scored games, and interrupting the SDK loop strands those games until their
turn clocks expire.  ``fleet.py bank`` therefore writes the physical slot to
``control.json.drain_now`` while also disabling relaunch.  This object makes
that atomic request look like the SDK's ordinary ``max_time`` limit, so the SDK
itself stops queueing, leaves all queues, plays every in-flight game to
completion, and only then returns.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from glee_sdk import GleeClient


logger = logging.getLogger("glee.run")

DEFAULT_CONTROL_PATH = Path(__file__).resolve().parent.parent / "control.json"


class CooperativeStopLimit:
    """Combine a numeric SDK time limit with a live per-slot stop request.

    GLEE SDK 0.0.5 checks its limit as ``elapsed >= max_time`` on every poll.
    Python falls back from ``float.__ge__`` to this object's ``__le__`` method,
    allowing a stop request to enter the SDK's existing lossless drain path.

    Control reads retain the last complete value.  ``fleet.py`` writes the file
    atomically, but retaining last-good state also prevents a transient read or
    parse failure from cancelling a stop already observed.  Once either limit
    fires it is latched for the rest of the process.
    """

    def __init__(
        self,
        seconds: float | None,
        *,
        physical_slot: str | None,
        control_path: str | Path = DEFAULT_CONTROL_PATH,
    ) -> None:
        self.seconds = seconds
        self.physical_slot = (physical_slot or "").strip()
        self.control_path = Path(control_path)
        self._last_good_requests: frozenset[str] = frozenset()
        self._latched = False
        self.reason: str | None = None

    @property
    def latched(self) -> bool:
        return self._latched

    def _requested_slots(self) -> frozenset[str]:
        try:
            with self.control_path.open(encoding="utf-8") as handle:
                data: Any = json.load(handle)
            if not isinstance(data, dict):
                raise ValueError("control root must be an object")
            raw = data.get("drain_now") or []
            if not isinstance(raw, list) or not all(isinstance(x, str) for x in raw):
                raise ValueError("drain_now must be a list of slot names")
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            logger.warning(
                "Could not read fleet stop control %s (%s); retaining last good state.",
                self.control_path,
                exc,
            )
            return self._last_good_requests

        self._last_good_requests = frozenset(raw)
        return self._last_good_requests

    def control_stop_requested(self) -> bool:
        """Return and latch whether this physical slot has a bank request."""
        if self._latched:
            return True
        if self.physical_slot and self.physical_slot in self._requested_slots():
            self._latched = True
            self.reason = "fleet_control"
            logger.info(
                "Fleet stop requested for physical slot %s; entering the SDK's "
                "lossless in-flight drain.",
                self.physical_slot,
            )
            return True
        return False

    def should_stop(self, elapsed: float) -> bool:
        """Return true once the configured time or live control limit fires."""
        if self._latched:
            return True
        if self.seconds is not None and elapsed >= self.seconds:
            self._latched = True
            self.reason = "max_time"
            return True
        return self.control_stop_requested()

    def __le__(self, elapsed: object) -> bool:
        """Support the SDK's ``elapsed >= limit`` comparison contract."""
        if not isinstance(elapsed, (int, float)):
            return NotImplemented
        return self.should_stop(float(elapsed))


class CooperativeGleeClient(GleeClient):
    """Fence queue calls as soon as a bank request becomes visible.

    The SDK checks its stop limit before each top-up, but a request can land
    while the preceding ``stats()`` call is in flight.  Rechecking immediately
    before every queue call closes that race: the client leaves all queues once
    and refuses the top-up, while the next run-loop comparison enters the SDK's
    normal in-flight drain.
    """

    def __init__(self, *args, stop_limit: CooperativeStopLimit, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.stop_limit = stop_limit
        self._bank_queue_fenced = False

    def queue(self, game_family: str) -> dict:
        if not self.stop_limit.control_stop_requested():
            return super().queue(game_family)
        if not self._bank_queue_fenced:
            self._bank_queue_fenced = True
            try:
                super().leave_queue()
            except Exception as exc:
                # The SDK's limit transition retries this best-effort leave on
                # the next poll.  The important invariant here is no new queue.
                logger.warning("Could not leave queues while fencing bank: %s", exc)
        return {"status": "draining", "game_family": game_family}
