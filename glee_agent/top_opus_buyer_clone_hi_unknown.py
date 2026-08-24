"""Prospective hidden unknown-horizon slice of the observed Opus buyer policy.

The complete Opus reconstruction is deliberately partial, but its hidden
unknown-horizon buyer trajectory is unusually well observed: 20 direct games,
16 counter-emitting games, and 465 counter states support the first 43 literal
price coefficients. All 317 supported message-enabled wires used the exact
sentence copied by the underlying table; neither price nor text is a fitted
curve.
This arm copies only that trajectory for buyer types 1.0B, 1.2B, and 1.5B.
The structurally dead 0.8B buyer type is excluded rather than diluting the
experiment with a cell no individually rational policy can close.

This scope is disjoint from the running 7aidara hidden known-cap-10 buyer arm.
It uses a fresh salt because the earlier broad 7aidara clone was a different
policy and its hidden-unknown point estimate was negative.  Opus's path is not
that retry: it holds near 0.6767 of the buyer's own value before following the
43 observed coefficients, while the 7aidara treatment used four different
piecewise price/base paths.

Pre-arm reachability over the latest 20 MB of each intended host turn stream
(``1787592547..1787597591``) found 1,057 supported action states in 103 games;
all 1,057 reconstructed Opus wires differed semantically from control.  Those
counts establish reachability only, never causal value.  Bargaining is outside
the parser and no bargaining module is imported.
"""

from __future__ import annotations

import hashlib

from . import runtime_flags, top_opus_buyer_clone


FLAG = "GLEE_NEGO_TOP_OPUS_BUYER_CLONE_HI_UNKNOWN_AB"
SALT = "nego_top_opus_buyer_clone_hi_unknown_v1|"
PLAN_SOURCE = "top_opus_buyer_clone_hi_unknown"

# The known-cap-10 7aidara arm is intentionally absent: the two static scopes
# cannot overlap.  These flags can own the same hidden unknown-horizon turn, so
# a present collision makes this arm inert rather than producing a mixed policy.
CONFLICTING_BOOLEAN_FLAGS = (
    "GLEE_NEGO_TOP_BUYER_CLONE_AB",
    "GLEE_NEGO_TOP_OPUS_BUYER_CLONE_AB",
    "GLEE_NEGO_TOP_ATHENA_BUYER_CLONE_AB",
    "GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB",
    "GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB",
    "GLEE_NEGO_HIDDEN_POLICY_V1",
    "GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB",
    "GLEE_NEGO_TABLE_VCONT_PRECEDENCE_AB",
    "GLEE_NEGO_STALL_CURRENT_BREAK_AB",
    "GLEE_NEGO_CLOSE_AB",
    "GLEE_NEGO_PROBE_V1",
)
OWN_TYPES = frozenset({1.0, 1.2, 1.5})


def treatment_assignment(game_id) -> bool | None:
    """Stable candidate bit recoverable from a non-empty game id alone."""
    if not isinstance(game_id, str) or not game_id.strip():
        return None
    digest = hashlib.sha256((SALT + game_id).encode("utf-8")).digest()
    return bool(digest[-1] & 1)


def enabled() -> bool:
    """Enable only when no overlapping hidden-policy experiment is armed."""
    return (
        runtime_flags.enabled(FLAG)
        and not any(runtime_flags.enabled(flag)
                    for flag in CONFLICTING_BOOLEAN_FLAGS)
        and runtime_flags.as_float("GLEE_NEGO_HIDDEN_FLOOR", 0.0) == 0.0
    )


def eligible(game: dict) -> bool:
    """Static ITT scope: live-value hidden unknown-horizon buyer games."""
    try:
        if not top_opus_buyer_clone.eligible(game):
            return False
        state = game.get("game_state") or {}
        ctx = top_opus_buyer_clone._context(game)
        return (
            ctx is not None
            and (game.get("valid_actions") or {}).get("type") == "decision"
            and ctx.complete is False
            and ctx.horizon_known is False
            and "max_rounds" not in state
            and ctx.own_mult in OWN_TYPES
        )
    except Exception:
        return False


def owns(game: dict) -> bool:
    """Own prospective hash-candidate turns only inside the exact scope."""
    try:
        return (
            enabled()
            and treatment_assignment(game.get("game_id")) is True
            and eligible(game)
        )
    except Exception:
        return False


def action(game: dict) -> dict | None:
    """Return an observed Opus move, or ``None`` for full-control fallback."""
    if not eligible(game):
        return None
    move = top_opus_buyer_clone.identified_action(game)
    if move is None:
        return None
    result = dict(move)
    plan = dict(result.get("_plan") or {})
    plan["source"] = PLAN_SOURCE
    result["_plan"] = plan
    return result


def matches_wire(game: dict, wire: dict) -> bool:
    """Whether a submitted wire exactly matches this scoped reconstruction."""
    if not isinstance(wire, dict) or not owns(game):
        return False
    expected = action(game)
    if expected is None:
        return False
    semantic_keys = ("decision", "product_price", "message")
    return all(wire.get(key) == expected.get(key) for key in semantic_keys)
