"""Default-off deterministic negotiation policy selection.

The competition selects the account's best *complete* agent, so these flags
select complete negotiation components rather than per-game arms.  None hashes
a game id or randomizes an action.  The first three retain the current seller
decision/price policy, which was the winning role in the motivating 63-game
official window (+47.9 rating total); V2 changes only support-inconsistent
seller prices and preserves the seller decision.  They otherwise differ in
buyer coverage and whether they include the observed leader's seller-message
table.

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

``agent5_default_v1`` is the single deterministic policy assembled for Agent 5.
It gives the first-principles component hard precedence in its three designed
cells, then uses the leader-replica buyer policy everywhere else it has public
support, and names the current seller stack as its explicit fallback in seller
cells where no replacement has been identified.  The dispatcher selects this
mode before the legacy randomized message bank; direct first-principles and
leader-buyer wires are also exempt from all downstream price postconditions.
This makes the ownership boundary executable rather than relying on a launch
configuration to keep conflicting rules quiet.

``agent5_default_v2`` preserves that complete matrix and fixes two support-level
holes disclosed by live failures and the official four-value generator.  In a
hidden unknown-horizon seller game it replaces only outgoing prices that could
sit above every possible buyer value, while retaining the current decision
rule (the earlier accept-all-profitable alternative measured negative).  At a
hidden cap-10 buyer terminal with no tighter seller-offer bound, it bids one
cent above the greatest feasible seller type.  Bound inference still has first
precedence.  Both additions are deterministic and use no outcome-conditioned
continuation model.

More than one whole-policy flag being on is a configuration error and
deliberately selects none. Flag-off behavior is the pre-existing negotiation
stack.
"""

from __future__ import annotations

import math

from . import (first_principles, nego_hidden_terminal_inference,
               nego_support_v2, runtime_flags, top_buyer_clone)


RANK_HYBRID_FLAG = "GLEE_NEGO_RANK_HYBRID_V1"
LEADER_REPLICA_FLAG = "GLEE_NEGO_LEADER_REPLICA_V1"
AGENT5_DEFAULT_FLAG = "GLEE_NEGO_AGENT5_DEFAULT_V1"
AGENT5_DEFAULT_V2_FLAG = "GLEE_NEGO_AGENT5_DEFAULT_V2"

RANK_HYBRID = "rank_hybrid_v1"
LEADER_REPLICA = "leader_replica_v1"
AGENT5_DEFAULT = "agent5_default_v1"
AGENT5_DEFAULT_GATE = "agent5_default_v1"
AGENT5_DEFAULT_V2 = "agent5_default_v2"
AGENT5_DEFAULT_V2_GATE = "agent5_default_v2"

WHOLE_POLICY_FLAGS = (
    RANK_HYBRID_FLAG,
    LEADER_REPLICA_FLAG,
    AGENT5_DEFAULT_FLAG,
    AGENT5_DEFAULT_V2_FLAG,
)
_AGENT5_POLICIES = (AGENT5_DEFAULT, AGENT5_DEFAULT_V2)

__all__ = [
    "RANK_HYBRID_FLAG",
    "LEADER_REPLICA_FLAG",
    "AGENT5_DEFAULT_FLAG",
    "AGENT5_DEFAULT_V2_FLAG",
    "RANK_HYBRID",
    "LEADER_REPLICA",
    "AGENT5_DEFAULT",
    "AGENT5_DEFAULT_GATE",
    "AGENT5_DEFAULT_V2",
    "AGENT5_DEFAULT_V2_GATE",
    "WHOLE_POLICY_FLAGS",
    "mode",
    "buyer_action",
    "direct_action",
    "trace_action",
    "matches_wire",
    "fallback_component",
]


def mode() -> str | None:
    """Return exactly one selected deterministic policy, else fail closed."""
    selected = [
        policy
        for flag, policy in (
            (RANK_HYBRID_FLAG, RANK_HYBRID),
            (LEADER_REPLICA_FLAG, LEADER_REPLICA),
            (AGENT5_DEFAULT_FLAG, AGENT5_DEFAULT),
            (AGENT5_DEFAULT_V2_FLAG, AGENT5_DEFAULT_V2),
        )
        if runtime_flags.enabled(flag)
    ]
    if len(selected) != 1:
        return None
    return selected[0]


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
    if selected in (LEADER_REPLICA, *_AGENT5_POLICIES):
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
    if selected not in (RANK_HYBRID, LEADER_REPLICA, *_AGENT5_POLICIES):
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
    gate = _agent5_gate(selected)
    if gate is not None and runtime_flags.enabled("GLEE_TRACE_GATES"):
        gates = list(plan.get("gates_fired") or [])
        if gate not in gates:
            gates.append(gate)
        plan["gates_fired"] = gates
    result["_plan"] = plan
    return result


def direct_action(game: dict, selected: str | None = None) -> dict | None:
    """Return a move owned outright by the selected whole policy.

    Agent 5's first-principles cells are checked before the copied buyer policy;
    this is the hard precedence guarantee requested by the operator.  A direct
    action never enters the legacy planner or randomized message attachment.
    """
    selected = selected or mode()
    if selected in _AGENT5_POLICIES and first_principles.deterministic_eligible(game):
        action = first_principles.action(game)
        if action is None:
            return None
        result = dict(action)
        plan = dict(result.get("_plan") or {})
        plan["source"] = selected
        plan["component"] = "first_principles"
        gate = _agent5_gate(selected)
        if gate is not None and runtime_flags.enabled("GLEE_TRACE_GATES"):
            gates = list(plan.get("gates_fired") or [])
            if gate not in gates:
                gates.append(gate)
            plan["gates_fired"] = gates
        result["_plan"] = plan
        return result
    if selected in _AGENT5_POLICIES:
        action = nego_hidden_terminal_inference.action(game)
        if action is not None:
            result = dict(action)
            plan = dict(result.get("_plan") or {})
            plan["source"] = selected
            plan["component"] = nego_hidden_terminal_inference.COMPONENT
            gate = _agent5_gate(selected)
            if gate is not None and runtime_flags.enabled("GLEE_TRACE_GATES"):
                gates = list(plan.get("gates_fired") or [])
                if gate not in gates:
                    gates.append(gate)
                plan["gates_fired"] = gates
            result["_plan"] = plan
            return result
    if selected == AGENT5_DEFAULT_V2:
        action = nego_support_v2.terminal_buyer_action(game)
        if action is not None:
            result = dict(action)
            plan = dict(result.get("_plan") or {})
            plan["source"] = selected
            plan["component"] = nego_support_v2.TERMINAL_BUYER_COMPONENT
            if runtime_flags.enabled("GLEE_TRACE_GATES"):
                gates = list(plan.get("gates_fired") or [])
                if AGENT5_DEFAULT_V2_GATE not in gates:
                    gates.append(AGENT5_DEFAULT_V2_GATE)
                plan["gates_fired"] = gates
            result["_plan"] = plan
            return result
    action = buyer_action(game, selected)
    return trace_action(action, selected) if action is not None else None


def matches_wire(game: dict, wire: dict) -> bool:
    """Whether a public wire is owned by the currently selected whole policy."""
    if not isinstance(wire, dict):
        return False
    selected = mode()
    if (selected == AGENT5_DEFAULT_V2
            and nego_support_v2.matches_hidden_unknown_seller_wire(game, wire)):
        return True
    expected = direct_action(game, selected)
    if not isinstance(expected, dict):
        return False
    return all(
        wire.get(key) == expected.get(key)
        for key in ("decision", "product_price", "message")
    )


def _agent5_gate(selected: str) -> str | None:
    if selected == AGENT5_DEFAULT:
        return AGENT5_DEFAULT_GATE
    if selected == AGENT5_DEFAULT_V2:
        return AGENT5_DEFAULT_V2_GATE
    return None


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
