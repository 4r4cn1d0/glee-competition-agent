"""Default-off, seller-only 7aidara negotiation message overlay.

The helper in this module is deliberately downstream of the control policy: it
receives an already-computed action and can change only the free-text message
and adjacent private trace metadata.  It never chooses a decision or a price,
and it is not imported by bargaining.

Direct wire evidence is narrow but exact: 57/57 observed message-enabled
seller wires followed this table across 14 source games.  The supported public
cells have 22.846% prospective structural reach.  This is message-channel-only
evidence; it does not identify a better price, acceptance rule, or walk policy.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Iterable

from . import runtime_flags


FLAG = "GLEE_NEGO_TOP_SELLER_MESSAGE_CLONE_AB"
SALT = "nego_top_seller_message_clone_v1|"
PLAN_TRACE = "top_seller_message_clone"
GATE = "top_seller_message_clone"

FIRST_PRICE_MESSAGE = (
    "That is my price for this one. I would rather close now than trade "
    "rounds -- tell me if it works."
)
EARLY_COUNTER_MESSAGE = "Below my line, but here is a number I can actually sign."
LATE_COUNTER_MESSAGE = "I have moved as far as this is worth to me. Let us close here."

SUPPORTED_CELLS = frozenset({
    "hidden_cap1",
    "hidden_cap10",
    "hidden_unknown",
    "complete_cap10",
    "complete_unknown",
})

_OFF_VALUES = frozenset({"", "0", "off", "false", "no", "none"})

__all__ = [
    "FLAG",
    "SALT",
    "PLAN_TRACE",
    "GATE",
    "FIRST_PRICE_MESSAGE",
    "EARLY_COUNTER_MESSAGE",
    "LATE_COUNTER_MESSAGE",
    "SUPPORTED_CELLS",
    "treatment_assignment",
    "message_arms_active",
    "negotiation_llm_active",
    "enabled",
    "evidence_cell",
    "prior_seller_price_count",
    "eligible",
    "owns",
    "message_for_price_count",
    "wire_fingerprint",
    "non_message_fingerprint",
    "fingerprint_audit",
    "audit_message_only",
    "apply_deterministic",
    "apply_clone",
    "attach",
]


def _finite_number(value) -> float | None:
    """Accept finite JSON numbers only; booleans and numeric strings are not wires."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    parsed = float(value)
    return parsed if math.isfinite(parsed) else None


def treatment_assignment(game_id) -> bool | None:
    """Return the stable SHA-256 low-bit arm, or ``None`` for malformed IDs."""
    if not isinstance(game_id, str) or not game_id.strip():
        return None
    digest = hashlib.sha256((SALT + game_id).encode("utf-8")).digest()
    return bool(digest[-1] & 1)


def _active_flag_value(value) -> bool:
    if value is None:
        return False
    if not isinstance(value, str):
        return True
    return value.strip().lower() not in _OFF_VALUES


def message_arms_active(raw_value: str | None = None) -> bool:
    """Whether the existing negotiation message experiment owns the channel."""
    if raw_value is None:
        try:
            raw_value = runtime_flags.get("GLEE_NEGO_MSG_ARMS")
        except Exception:
            return True
    return _active_flag_value(raw_value)


def _family_set(value: str | Iterable[str] | None) -> set[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return {part.strip().lower() for part in value.split(",") if part.strip()}
    try:
        families = {str(part).strip().lower() for part in value if str(part).strip()}
    except (TypeError, ValueError):
        return None
    return families


def negotiation_llm_active(
    llm_mode: str | None = None,
    llm_families: str | Iterable[str] | None = None,
) -> bool:
    """Fail closed when negotiation text or full actions are routed to an LLM."""
    try:
        if llm_mode is None:
            llm_mode = runtime_flags.get("GLEE_LLM_MODE") or "messages"
        if llm_families is None:
            llm_families = runtime_flags.get("GLEE_LLM_FAMILIES") or "persuasion"
    except Exception:
        return True
    if not isinstance(llm_mode, str):
        return True
    mode = llm_mode.strip().lower()
    families = _family_set(llm_families)
    if families is None:
        return True
    return mode in {"messages", "full"} and "negotiation" in families


def enabled(
    *,
    llm_mode: str | None = None,
    llm_families: str | Iterable[str] | None = None,
    msg_arms_value: str | None = None,
) -> bool:
    """The arm is live only while no other negotiation message owner is active."""
    try:
        return (
            runtime_flags.enabled(FLAG)
            and not message_arms_active(msg_arms_value)
            and not negotiation_llm_active(llm_mode, llm_families)
        )
    except Exception:
        return False


def _seller(game: dict) -> tuple[dict, str] | None:
    if not isinstance(game, dict) or game.get("game_family") != "negotiation":
        return None
    if treatment_assignment(game.get("game_id")) is None:
        return None
    state = game.get("game_state")
    if not isinstance(state, dict):
        return None
    if state.get("game_family") not in (None, "negotiation"):
        return None
    me_from_game = game.get("your_player")
    me_from_state = state.get("current_player")
    if me_from_game in ("player_1", "player_2"):
        me = me_from_game
        if (me_from_state in ("player_1", "player_2")
                and me_from_state != me):
            return None
    elif me_from_state in ("player_1", "player_2"):
        me = me_from_state
    else:
        return None
    if state.get(f"{me}_role") != "seller":
        return None
    return state, me


def evidence_cell(game: dict) -> str | None:
    """Return the exact supported public cell; complete cap-1 is unsupported."""
    parsed = _seller(game)
    if parsed is None:
        return None
    state, _ = parsed
    complete = state.get("complete_information")
    known = state.get("horizon_known")
    if complete not in (True, False) or known not in (True, False):
        return None
    prefix = "complete" if complete else "hidden"
    if known is False:
        if state.get("max_rounds") is not None:
            return None
        cell = f"{prefix}_unknown"
        return cell if cell in SUPPORTED_CELLS else None
    cap = _finite_number(state.get("max_rounds"))
    if cap is None or not cap.is_integer():
        return None
    cell = f"{prefix}_cap{int(cap)}"
    return cell if cell in SUPPORTED_CELLS else None


def prior_seller_price_count(game: dict) -> int | None:
    """Count our prior finite ``history[*].offer`` wires, never counter echoes.

    The protocol records a counteroffer again as the next round's ``offer``.
    Counting only offer objects therefore counts each transmitted seller price
    once, while inspecting ``counteroffer`` too would double-count those wires.
    """
    parsed = _seller(game)
    if parsed is None:
        return None
    state, me = parsed
    history = state.get("history")
    if history is None:
        history = []
    if not isinstance(history, (list, tuple)):
        return None
    count = 0
    for entry in history:
        if not isinstance(entry, dict):
            return None
        offer = entry.get("offer")
        if offer is None:
            continue
        if not isinstance(offer, dict):
            return None
        if offer.get("from_player") != me:
            continue
        if _finite_number(offer.get("price")) is None:
            return None
        count += 1
    return count


def _carries_supported_seller_price(game: dict, action: dict) -> bool:
    if not isinstance(action, dict) or _finite_number(action.get("product_price")) is None:
        return False
    action_type = (game.get("valid_actions") or {}).get("type")
    if action_type == "offer":
        return "decision" not in action
    if action_type == "decision":
        return action.get("decision") == "RejectOffer"
    return False


def eligible(game: dict, action: dict) -> bool:
    """Whether a control action lies in the observed seller-message support."""
    try:
        parsed = _seller(game)
        if parsed is None:
            return False
        state, _ = parsed
        return (
            state.get("messages_allowed") is True
            and evidence_cell(game) is not None
            and prior_seller_price_count(game) is not None
            and _carries_supported_seller_price(game, action)
            and ("_plan" not in action or isinstance(action.get("_plan"), dict))
        )
    except Exception:
        return False


def owns(
    game: dict,
    action: dict,
    *,
    llm_mode: str | None = None,
    llm_families: str | Iterable[str] | None = None,
    msg_arms_value: str | None = None,
) -> bool:
    """Whether this turn is an enabled, eligible hash candidate."""
    try:
        return (
            enabled(
                llm_mode=llm_mode,
                llm_families=llm_families,
                msg_arms_value=msg_arms_value,
            )
            and treatment_assignment(game.get("game_id")) is True
            and eligible(game, action)
        )
    except Exception:
        return False


def message_for_price_count(count: int) -> str | None:
    """The literal 7aidara message table; ten or more prices are unsupported."""
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        return None
    if count == 0:
        return FIRST_PRICE_MESSAGE
    if count <= 3:
        return EARLY_COUNTER_MESSAGE
    if count <= 9:
        return LATE_COUNTER_MESSAGE
    return None


def _canonical_fingerprint(payload) -> str:
    try:
        blob = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError):
        blob = json.dumps(
            ["<unserializable>", type(payload).__name__, repr(payload)],
            separators=(",", ":"),
            ensure_ascii=False,
        )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _public_wire(action) -> object:
    if not isinstance(action, dict):
        return ["<non-dict>", type(action).__name__, repr(action)]
    return {key: value for key, value in action.items()
            if not str(key).startswith("_")}


def wire_fingerprint(action) -> str:
    """SHA-256 of the complete submitted wire, excluding private ``_`` metadata."""
    return _canonical_fingerprint(_public_wire(action))


def non_message_fingerprint(action) -> str:
    """SHA-256 of every submitted field except the free-text message."""
    wire = _public_wire(action)
    if isinstance(wire, dict):
        wire = {key: value for key, value in wire.items() if key != "message"}
    return _canonical_fingerprint(wire)


def fingerprint_audit(before, after) -> dict[str, object]:
    """Return independent full-wire and protected non-message fingerprints."""
    before_wire = wire_fingerprint(before)
    after_wire = wire_fingerprint(after)
    before_non_message = non_message_fingerprint(before)
    after_non_message = non_message_fingerprint(after)
    return {
        "wire_before": before_wire,
        "wire_after": after_wire,
        "wire_changed": before_wire != after_wire,
        "non_message_before": before_non_message,
        "non_message_after": after_non_message,
        "non_message_unchanged": before_non_message == after_non_message,
    }


def audit_message_only(before, after, expected_message: str | None = None) -> bool:
    """Whether public wire changes are confined to the expected message field."""
    if not isinstance(before, dict) or not isinstance(after, dict):
        return False
    if non_message_fingerprint(before) != non_message_fingerprint(after):
        return False
    if expected_message is not None and after.get("message") != expected_message:
        return False
    before_public = _public_wire(before)
    after_public = _public_wire(after)
    if not isinstance(before_public, dict) or not isinstance(after_public, dict):
        return False
    before_without = dict(before_public)
    after_without = dict(after_public)
    before_without.pop("message", None)
    after_without.pop("message", None)
    return before_without == after_without


def _traced_copy(
    action: dict,
    message: str,
    game: dict,
    count: int,
    *,
    arm: str = "candidate",
) -> dict | None:
    existing_plan = action.get("_plan")
    if existing_plan is not None and not isinstance(existing_plan, dict):
        return None
    plan = dict(existing_plan or {})
    gates = plan.get("gates_fired")
    if gates is None:
        copied_gates: list = []
    elif isinstance(gates, list):
        copied_gates = list(gates)
    else:
        return None
    if PLAN_TRACE in plan:
        return None
    copied_gates.append(GATE)
    plan["gates_fired"] = copied_gates
    plan[PLAN_TRACE] = {
        "arm": arm,
        "cell": evidence_cell(game),
        "prior_seller_price_count": count,
        "message_sha256": _canonical_fingerprint(message),
        "non_message_sha256": non_message_fingerprint(action),
    }

    result = dict(action)
    result["message"] = message
    result["_plan"] = plan
    if not audit_message_only(action, result, message):
        return None
    return result


def apply_deterministic(game: dict, action: dict) -> dict:
    """Attach the exact seller table after a whole-policy flag is selected.

    Unlike :func:`apply_clone`, this path has no runtime flag and no hash arm:
    its caller already resolved the mutually exclusive default-off deterministic
    policy flags.  It still changes only the message field and returns the
    original action for buyers, unsupported public cells, non-price decisions,
    or the unsupported tail.
    """
    try:
        if not eligible(game, action):
            return action
        count = prior_seller_price_count(game)
        if count is None:
            return action
        message = message_for_price_count(count)
        if message is None:
            return action
        changed = _traced_copy(
            action,
            message,
            game,
            count,
            arm="leader_replica",
        )
        return changed if changed is not None else action
    except Exception:
        return action


def apply_clone(
    game: dict,
    action: dict,
    *,
    armed: bool,
    msg_arms_armed: bool = False,
    llm_mode: str = "off",
    llm_families: str | Iterable[str] = (),
) -> dict:
    """Pure integration helper: overlay a candidate message or return ``action``.

    All ownership inputs are explicit, so this function does not read runtime
    configuration.  It is suitable immediately after the control action has
    been computed.  Ineligible states, hash controls, conflicts, unsupported
    price counts, and already-identical messages return the exact same object.
    """
    if not isinstance(action, dict) or not armed or msg_arms_armed:
        return action
    if negotiation_llm_active(llm_mode, llm_families):
        return action
    if not eligible(game, action):
        return action
    if treatment_assignment(game.get("game_id")) is not True:
        return action
    count = prior_seller_price_count(game)
    if count is None:
        return action
    message = message_for_price_count(count)
    if message is None or action.get("message") == message:
        return action
    changed = _traced_copy(action, message, game, count)
    return changed if changed is not None else action


def attach(
    game: dict,
    action: dict,
    *,
    llm_mode: str | None = None,
    llm_families: str | Iterable[str] | None = None,
) -> dict:
    """Runtime wrapper around :func:`apply_clone`; never mutates ``action``."""
    try:
        raw_msg_arms = runtime_flags.get("GLEE_NEGO_MSG_ARMS")
        mode = llm_mode
        families = llm_families
        if mode is None:
            mode = runtime_flags.get("GLEE_LLM_MODE") or "messages"
        if families is None:
            families = runtime_flags.get("GLEE_LLM_FAMILIES") or "persuasion"
        return apply_clone(
            game,
            action,
            armed=runtime_flags.enabled(FLAG),
            msg_arms_armed=message_arms_active(raw_msg_arms),
            llm_mode=mode,
            llm_families=families,
        )
    except Exception:
        return action
