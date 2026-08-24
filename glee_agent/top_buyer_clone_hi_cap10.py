"""Prospective hidden-information, cap-10 slice of the leader buyer clone.

The earlier full buyer-clone experiment was randomized over every negotiation
buyer cell.  At its fixed 91-game official checkpoint it was not promotable:
candidate minus control was +0.87 rating/game, but the interval crossed zero,
one host was negative, and no-deals rose 6.1 percentage points.  The one
mechanically coherent cell with both higher rating and fewer no-deals was the
hidden-information, known 10-round buyer cell: +1.81 rating/game (candidate
n=15, control n=11), with no-deals 46.7% versus 54.5%.

That cell was found after examining the broad experiment, so those numbers are
motivation rather than proof.  This module gives it a new per-game hash salt
and a default-off flag for a clean prospective test.  Candidate games execute
the already-frozen literal 7aidara buyer paths; controls execute the entire
current stack.  Seller, complete-information, unknown-horizon, single-round,
and bargaining games are never eligible.
"""

from __future__ import annotations

import hashlib
import math

from . import runtime_flags, top_buyer_clone


FLAG = "GLEE_NEGO_TOP_BUYER_CLONE_HI_CAP10_AB"
SALT = "nego_top_buyer_clone_hi_cap10_v1|"
PLAN_SOURCE = "top_buyer_clone_hi_cap10"
CONFLICTING_FLAGS = (
    "GLEE_NEGO_TOP_BUYER_CLONE_AB",
    "GLEE_NEGO_TOP_OPUS_BUYER_CLONE_AB",
    "GLEE_NEGO_TOP_ATHENA_BUYER_CLONE_AB",
)


def treatment_assignment(game_id) -> bool | None:
    """Stable candidate bit recoverable from a non-empty game id alone."""
    if not isinstance(game_id, str) or not game_id.strip():
        return None
    digest = hashlib.sha256((SALT + game_id).encode("utf-8")).digest()
    return bool(digest[-1] & 1)


def enabled() -> bool:
    """Remain inert unless this is the only direct-leader arm enabled."""
    return (runtime_flags.enabled(FLAG)
            and not any(runtime_flags.enabled(flag)
                        for flag in CONFLICTING_FLAGS))


def _is_exact_cap10(value) -> bool:
    if isinstance(value, bool):
        return False
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(parsed) and parsed == 10.0


def eligible(game: dict) -> bool:
    """Static scope: well-formed hidden buyer decisions in known cap-10 games."""
    if not top_buyer_clone.eligible(game):
        return False
    state = game.get("game_state") or {}
    return (state.get("complete_information") is False
            and state.get("horizon_known") is True
            and _is_exact_cap10(state.get("max_rounds")))


def owns(game: dict) -> bool:
    """True only for prospective candidate games while the scoped arm is live."""
    try:
        return (enabled() and eligible(game)
                and treatment_assignment(game.get("game_id")) is True)
    except Exception:
        return False


def action(game: dict) -> dict | None:
    """Return the frozen leader action, relabelled for trace auditing."""
    if not eligible(game):
        return None
    move = top_buyer_clone.action(game)
    if move is None:
        return None
    plan = dict(move.get("_plan") or {})
    plan["source"] = PLAN_SOURCE
    move["_plan"] = plan
    return move
