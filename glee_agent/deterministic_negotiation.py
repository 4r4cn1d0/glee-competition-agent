"""Default-off deterministic negotiation policy selection.

The competition selects the account's best *complete* agent, so these flags
select complete negotiation components rather than per-game arms.  Neither
policy hashes a game id or randomizes an action.  Both retain the current
seller decision/price policy, which was the winning role in the motivating
63-game official window (+47.9 rating total); they differ in buyer coverage
and whether they include the observed leader's seller-message table.

``rank_hybrid_v1`` is the evidence-bounded portfolio alternative.  It copies
the frozen 7aidara buyer policy in every complete-information game and in
hidden cap-10 games, but keeps the current buyer in hidden single-round and
unknown-horizon games.  The terminal receiver rule in single-round games
already accepts every strictly profitable offer.  The unknown-horizon
exclusion is evidence-driven:
at the frozen 91-game full-clone checkpoint, that slice scored -0.227/game for
the clone (n=11) versus +0.093/game for control (n=15), and 10/11 clone games
walked.  Hidden cap-10 was the opposite directional signal: +1.573/game (n=15)
versus -0.236/game (n=11), followed by a clean prospective checkpoint of
+2.467/game (n=9) versus +1.100/game (n=16).  Neither interval proved the
effect, so the flag remains default OFF and the limitation belongs in handoff.

``leader_replica_v1`` reproduces the complete negotiation behavior currently
running on Test 4: the same observed buyer policy in every supported buyer
regime, the current seller decision/price policy, and the 57/57 observed
message-only seller table in its supported cells.  Test 4's first clean
post-launch interval implied an opponent-adjusted percentile of 0.568 over 52
official games; extending the same all-game window to 77 games put it at
0.549, essentially tied with champion's concurrent 0.548.  This is
observational and does not prove superiority, but it is direct evidence for
preserving the exact live profile rather than deleting one of its components
post hoc.  The older frozen buyer-only checkpoint was +1.116/game (n=44)
versus +0.247/game (n=47), with an interval crossing zero.

Both flags being on is a configuration error and deliberately selects neither
policy.  Flag-off behavior is therefore the pre-existing negotiation stack.
"""

from __future__ import annotations

import math

from . import runtime_flags, top_buyer_clone


RANK_HYBRID_FLAG = "GLEE_NEGO_RANK_HYBRID_V1"
LEADER_REPLICA_FLAG = "GLEE_NEGO_LEADER_REPLICA_V1"

RANK_HYBRID = "rank_hybrid_v1"
LEADER_REPLICA = "leader_replica_v1"

__all__ = [
    "RANK_HYBRID_FLAG",
    "LEADER_REPLICA_FLAG",
    "RANK_HYBRID",
    "LEADER_REPLICA",
    "mode",
    "buyer_action",
    "trace_action",
    "matches_wire",
    "fallback_component",
]


def mode() -> str | None:
    """Return the one selected deterministic policy, or ``None`` on/off conflict."""
    rank_hybrid = runtime_flags.enabled(RANK_HYBRID_FLAG)
    leader_replica = runtime_flags.enabled(LEADER_REPLICA_FLAG)
    if rank_hybrid == leader_replica:
        return None
    return RANK_HYBRID if rank_hybrid else LEADER_REPLICA


def _finite_number(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    parsed = float(value)
    return parsed if math.isfinite(parsed) else None


def _supported_public_cell(game: dict) -> tuple[dict, str] | None:
    """Validate the official information/horizon grid without inventing defaults."""
    if not top_buyer_clone.eligible(game):
        return None
    state = game.get("game_state")
    if not isinstance(state, dict):
        return None
    complete = state.get("complete_information")
    known = state.get("horizon_known")
    if not isinstance(complete, bool) or not isinstance(known, bool):
        return None
    if known:
        cap = _finite_number(state.get("max_rounds"))
        if cap is None or not cap.is_integer() or int(cap) not in (1, 10):
            return None
        horizon = f"cap{int(cap)}"
    else:
        if state.get("max_rounds") is not None:
            return None
        horizon = "unknown"
    return state, ("complete" if complete else "hidden") + "/" + horizon


def _uses_leader_buyer(game: dict, selected: str) -> bool:
    parsed = _supported_public_cell(game)
    if parsed is None:
        return False
    _state, cell = parsed
    if selected == LEADER_REPLICA:
        return True
    if selected != RANK_HYBRID:
        return False
    # Complete information is always feasible and exposes the exact zone.  In
    # hidden cap-10, the copied path screens the four-point support by moving
    # from an 85%-of-wide-zone claim toward an 85%-of-marginal-zone claim.
    # Hidden cap-1 already has the exact any-positive terminal rule; hidden
    # unknown retains control because the broad replica's eight-price walk was
    # the only coherent negative horizon slice (10 walks in 11 candidates).
    return cell.startswith("complete/") or cell == "hidden/cap10"


def buyer_action(game: dict, selected: str | None = None) -> dict | None:
    """Return the deterministic leader buyer move in cells owned by ``selected``."""
    selected = selected or mode()
    if selected not in (RANK_HYBRID, LEADER_REPLICA):
        return None
    if not _uses_leader_buyer(game, selected):
        return None
    try:
        return top_buyer_clone.action(game)
    except Exception:
        return None


def trace_action(action: dict, selected: str) -> dict:
    """Label a copied buyer action without changing its public wire."""
    result = dict(action)
    plan = dict(result.get("_plan") or {})
    evidence_source = plan.get("source")
    if evidence_source is not None:
        plan["evidence_source"] = evidence_source
    plan["source"] = selected
    plan["component"] = "observed_leader_buyer"
    result["_plan"] = plan
    return result


def matches_wire(game: dict, wire: dict) -> bool:
    """Whether a public wire is owned by the currently selected whole policy."""
    if not isinstance(wire, dict):
        return False
    expected = buyer_action(game)
    if not isinstance(expected, dict):
        return False
    return all(
        wire.get(key) == expected.get(key)
        for key in ("decision", "product_price", "message")
    )


def fallback_component(game: dict) -> str:
    """Describe the deterministic policy branch that keeps the current stack."""
    state = game.get("game_state") or {}
    me = state.get("current_player") or game.get("your_player")
    if state.get(f"{me}_role") == "seller":
        return "current_seller"
    if state.get("complete_information") is False:
        if state.get("horizon_known") is False:
            return "current_hidden_unknown_buyer"
        if _finite_number(state.get("max_rounds")) == 1.0:
            return "current_hidden_terminal_buyer"
    return "current_fallback"
