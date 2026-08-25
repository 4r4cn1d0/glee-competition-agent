"""Default-off, buyer-only reconstruction of directly observed Athena wires.

This module is intentionally standalone: it is not imported by negotiation
dispatch.  A future caller may use :func:`action`; ``None`` means execute the
unchanged control policy.  No bargaining code is imported or made eligible.

Evidence boundary
-----------------

The local direct corpus contains 21 games in which opponent label ``Athena``
was the buyer (5 complete-information, 16 hidden-information), with 157
observable response decisions: 152 rejects, four accepts, and one walk.  The
148 transmitted counter wires comprise 21 complete-information wires and 127
hidden-information wires.

The active table below copies only public states whose action and exact wire
are point observations: 21 counters from four complete-information histories,
plus four single-round accepts.  It does not fit a curve, normalize by scale,
weaken an equality into a threshold, or manufacture an unobserved message.

Hidden multi-round wires are deliberately evidence-only.  Athena's private
buyer value is absent from those public transcripts, so the observed .800B,
.808B, and .82195...B counter families cannot be assigned to our visible
private type without an inferred selector.  The one walk has the same defect.
Those states, incomplete histories, and every off-table branch fail closed.

Three hidden single-round buyer values are different: agreement price plus the
recorded Athena payoff algebraically recovers the private value after the game.
Their table rows are marked ``agreement_payoff_inference`` rather than public
complete-information observations.  The clone conditions only on values that
would be visible to itself as buyer; it never conditions on the hidden seller
value recovered from our side of the transcript.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math

from . import pricing, runtime_flags


FLAG = "GLEE_NEGO_TOP_ATHENA_BUYER_CLONE_AB"
CONFLICTING_FLAGS = (
    "GLEE_NEGO_TOP_BUYER_CLONE_AB",
    "GLEE_NEGO_TOP_OPUS_BUYER_CLONE_AB",
)
SALT = "nego_top_athena_buyer_clone_v1|"
PLAN_SOURCE = "top_athena_buyer_clone"

BUYER_MESSAGE_TEMPLATE = (
    "I can pay {price:,.2f}. That is the most it is worth on my side. "
    "Past that I am paying for the privilege of buying, which I will not do."
)

CORPUS_COUNTS = {
    "athena_buyer_games": 21,
    "complete_games": 5,
    "hidden_games": 16,
    "response_decisions": 157,
    "rejects": 152,
    "accepts": 4,
    "walks": 1,
    "counter_wires": 148,
    "complete_counter_wires": 21,
    "hidden_counter_wires": 127,
    "counter_wires_with_exact_generic_message": 35,
    "counter_wires_without_message": 113,
}

# Evidence-only corpus facts.  No active branch reads these families: hidden
# multi-round private types and the public state selecting a family are not
# point identified, and accepted-deal-only inference would add survivorship.
HIDDEN_MULTIROUND_UNIDENTIFIED_COUNTER_FAMILIES = (
    "0.800B family",
    "0.808B family",
    "0.82195...B family",
)
IDENTIFIED_GAPS = (
    "hidden multi-round private-type-to-counter-family selector",
    "hidden multi-round accept/reject threshold",
    "hidden walk private type and threshold",
    "complete-information states outside four literal histories",
    "player_1 buyer role symmetry; all Athena buyer observations were player_2",
    "offer-side behavior, because Athena was observed here as responder",
    "response messages on the four accepted agreements",
)


@dataclass(frozen=True)
class CounterTrace:
    """One literal complete-information public history and Athena wire path."""

    source_game_id: str
    source_log: str
    base: float
    buyer_value: float
    seller_value: float
    horizon_known: bool
    max_rounds: int | None
    messages_allowed: bool
    seller_prices: tuple[float, ...]
    seller_messages: tuple[str, ...]
    buyer_prices: tuple[float, ...]


@dataclass(frozen=True)
class AcceptTrace:
    """One exact single-round incoming state ending in Athena acceptance."""

    source_game_id: str
    source_log: str
    complete: bool
    base: float
    buyer_value: float
    seller_value: float | None
    messages_allowed: bool
    incoming_price: float
    incoming_message: str
    type_basis: str


# Exact observations from our seller-side turn streams.  Reconstructing the
# corresponding Athena decision input merely reverses the protocol echo: each
# odd seller offer was followed by the listed RejectOffer + buyer counter.
COMPLETE_COUNTER_TRACES = (
    CounterTrace(
        source_game_id="4fff8cbc-c5ba-40d8-b827-fe553766419b",
        source_log="logs/champion/turns.jsonl",
        base=10_000.0,
        buyer_value=15_000.0,
        seller_value=10_000.0,
        horizon_known=True,
        max_rounds=10,
        messages_allowed=True,
        seller_prices=(21_894.40, 15_999.68, 15_343.25, 14_271.53, 12_949.06),
        seller_messages=(
            "My number is 21,894.40. Priced to close, not to start a haggle.",
            "My number is 15,999.68. Priced to close, not to start a haggle.",
            "15,343.25. Priced to close, not to start a haggle.",
            "14,271.53. Priced to close, not to start a haggle.",
            "I can do 12,949.06. I would rather trade than not, but not at any number.",
        ),
        buyer_prices=(10_136.61, 10_136.79, 10_157.65, 10_469.69, 12_500.00),
    ),
    CounterTrace(
        source_game_id="19e883e8-1207-4674-9fb4-0644ae825b3c",
        source_log="logs/champion/turns.jsonl",
        base=10_000.0,
        buyer_value=15_000.0,
        seller_value=10_000.0,
        horizon_known=False,
        max_rounds=None,
        messages_allowed=True,
        seller_prices=(13_050.00, 13_050.00, 13_050.00, 13_050.00,
                       12_000.00, 12_000.00, 13_050.00),
        seller_messages=("", "", "", "", "", "", ""),
        buyer_prices=(10_247.81, 10_248.08, 10_256.64, 10_316.08,
                      10_539.16, 11_145.70, 12_500.00),
    ),
    CounterTrace(
        source_game_id="66969917-1abf-484a-8d66-9a38a44f14c2",
        source_log="logs/conceder/turns.jsonl",
        base=1_000_000.0,
        buyer_value=1_000_000.0,
        seller_value=800_000.0,
        horizon_known=True,
        max_rounds=10,
        messages_allowed=True,
        seller_prices=(980_000.00, 980_000.00, 980_000.00, 980_000.00),
        seller_messages=("", "", "", ""),
        buyer_prices=(807_124.22, 807_142.88, 808_440.53, 822_998.22),
    ),
    CounterTrace(
        source_game_id="7af52c95-a8bc-422e-a5b5-bddfe1edfe83",
        source_log="logs/randomized/turns.jsonl",
        base=10_000.0,
        buyer_value=15_000.0,
        seller_value=12_000.0,
        horizon_known=True,
        max_rounds=10,
        messages_allowed=False,
        seller_prices=(14_850.00, 14_400.00, 14_400.00, 14_400.00, 14_400.00),
        seller_messages=("", "", "", "", ""),
        buyer_prices=(12_044.25, 12_046.56, 12_102.27, 12_426.41, 12_120.00),
    ),
)

# Exact outcomes, but not all value labels have the same epistemic status.
# The complete row's values were public.  In each hidden row, Athena's buyer
# value is inferred ex post as agreed_price + player_2_payoff; it was private to
# Athena during the direct game but would be known to this buyer clone at use.
SINGLE_ROUND_ACCEPT_TRACES = (
    AcceptTrace(
        source_game_id="023fb45f-eab7-46ec-93d0-737a4b56b1b0",
        source_log="logs/champion/games/023fb45f-eab7-46ec-93d0-737a4b56b1b0.json",
        complete=True,
        base=100.0,
        buyer_value=150.0,
        seller_value=120.0,
        messages_allowed=False,
        incoming_price=144.0,
        incoming_message="",
        type_basis="public_complete_information",
    ),
    AcceptTrace(
        source_game_id="614ce0b5-d077-475e-aee4-7314ad09dd0b",
        source_log="logs/randomized/games/614ce0b5-d077-475e-aee4-7314ad09dd0b.json",
        complete=False,
        base=100.0,
        buyer_value=120.0,  # 95 agreement + 25 recorded Athena payoff.
        seller_value=None,
        messages_allowed=False,
        incoming_price=95.0,
        incoming_message="",
        type_basis="agreement_payoff_inference",
    ),
    AcceptTrace(
        source_game_id="85ed7d2a-c40c-4b8b-a452-2efe674a8018",
        source_log="logs/champion/games/85ed7d2a-c40c-4b8b-a452-2efe674a8018.json",
        complete=False,
        base=1_000_000.0,
        buyer_value=1_500_000.0,  # 1.275M agreement + .225M payoff.
        seller_value=None,
        messages_allowed=True,
        incoming_price=1_275_000.0,
        incoming_message="",
        type_basis="agreement_payoff_inference",
    ),
    AcceptTrace(
        source_game_id="313900de-579d-4811-b0fa-a9b02bb79dc7",
        source_log="logs/composite/games/313900de-579d-4811-b0fa-a9b02bb79dc7.json",
        complete=False,
        base=10_000.0,
        buyer_value=15_000.0,  # 12,750 agreement + 2,250 payoff.
        seller_value=None,
        messages_allowed=False,
        incoming_price=12_750.0,
        incoming_message="",
        type_basis="agreement_payoff_inference",
    ),
)


@dataclass(frozen=True)
class _Context:
    game_id: str
    state: dict
    me: str
    other: str
    complete: bool
    horizon_known: bool
    max_rounds: int | None
    round_no: int
    messages_allowed: bool
    own_value: float
    other_value: float | None
    base: float
    incoming_price: float
    incoming_message: str
    history: list


def _number(value) -> float | None:
    """Parse only finite JSON numbers; booleans and numeric strings fail."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    parsed = float(value)
    return parsed if math.isfinite(parsed) else None


def _positive_int(value) -> int | None:
    parsed = _number(value)
    if parsed is None or parsed < 1.0 or not parsed.is_integer():
        return None
    return int(parsed)


def _message(value) -> str | None:
    # The SDK normalizes a missing message and an explicitly empty wire to the
    # same no-message public state.  Non-string payloads remain malformed.
    if value is None:
        return ""
    return value if isinstance(value, str) else None


def _same_price(value, expected: float) -> bool:
    parsed = _number(value)
    return parsed is not None and abs(parsed - expected) <= 1e-7


def treatment_assignment(game_id) -> bool | None:
    """Return a stable candidate bit recoverable from a game id alone."""
    if not isinstance(game_id, str) or not game_id.strip():
        return None
    digest = hashlib.sha256((SALT + game_id).encode("utf-8")).digest()
    return bool(digest[-1] & 1)


def enabled() -> bool:
    """Remain inert when either existing direct-leader clone is armed."""
    return (runtime_flags.enabled(FLAG)
            and not any(runtime_flags.enabled(flag)
                        for flag in CONFLICTING_FLAGS))


def _context(game: dict) -> _Context | None:
    """Parse a strict negotiation buyer decision without inventing defaults."""
    if not isinstance(game, dict) or game.get("game_family") != "negotiation":
        return None
    game_id = game.get("game_id")
    if treatment_assignment(game_id) is None:
        return None
    state = game.get("game_state")
    valid = game.get("valid_actions")
    if not isinstance(state, dict) or not isinstance(valid, dict):
        return None
    if state.get("game_family") not in (None, "negotiation"):
        return None
    if valid.get("type") != "decision":
        return None

    me = state.get("current_player")
    if me not in ("player_1", "player_2") or game.get("your_player") != me:
        return None
    # Every direct Athena-buyer observation was the player_2 responder.  Role
    # symmetry is plausible but unobserved, so a player_1 buyer must use control.
    if me != "player_2":
        return None
    other = "player_2" if me == "player_1" else "player_1"
    if state.get(f"{me}_role") != "buyer":
        return None
    if state.get(f"{other}_role") != "seller":
        return None

    complete = state.get("complete_information")
    horizon_known = state.get("horizon_known")
    messages_allowed = state.get("messages_allowed")
    if (not isinstance(complete, bool) or not isinstance(horizon_known, bool)
            or not isinstance(messages_allowed, bool)):
        return None

    round_no = _positive_int(state.get("round"))
    if round_no is None or round_no % 2 != 1:
        return None
    max_rounds = None
    if horizon_known:
        max_rounds = _positive_int(state.get("max_rounds"))
        if max_rounds is None or round_no > max_rounds:
            return None
    elif state.get("max_rounds") is not None:
        # Unknown-horizon source states did not expose a cap.
        return None

    own_value = _number(state.get(f"{me}_value"))
    if own_value is None or own_value <= 0.0:
        return None
    base = pricing.infer_base(own_value)
    if base is None:
        return None

    other_value = None
    if complete:
        other_value = _number(state.get(f"{other}_value"))
        if (other_value is None or other_value <= 0.0
                or pricing.infer_base(other_value) != base):
            return None
    elif state.get(f"{other}_value") is not None:
        # Never use a leaked seller value to select a hidden-information row.
        return None

    history = state.get("history")
    if not isinstance(history, list) or any(
            not isinstance(entry, dict) for entry in history):
        return None
    offer = state.get("last_offer")
    if not isinstance(offer, dict) or offer.get("from_player") != other:
        return None
    if _positive_int(offer.get("round")) != round_no:
        return None
    incoming_price = _number(offer.get("price"))
    incoming_message = _message(offer.get("message"))
    if (incoming_price is None or incoming_price < 0.0
            or incoming_message is None):
        return None

    return _Context(
        game_id=game_id,
        state=state,
        me=me,
        other=other,
        complete=complete,
        horizon_known=horizon_known,
        max_rounds=max_rounds,
        round_no=round_no,
        messages_allowed=messages_allowed,
        own_value=own_value,
        other_value=other_value,
        base=base,
        incoming_price=incoming_price,
        incoming_message=incoming_message,
        history=history,
    )


def _buyer_message(price: float, allowed: bool) -> str:
    return BUYER_MESSAGE_TEMPLATE.format(price=price) if allowed else ""


def _offer_matches(entry: dict, *, price: float, message: str,
                   player: str, round_no: int) -> bool:
    offer = entry.get("offer")
    if not isinstance(offer, dict):
        return False
    return (
        offer.get("from_player") == player
        and _positive_int(offer.get("round")) == round_no
        and _same_price(offer.get("price"), price)
        and _message(offer.get("message")) == message
    )


def _history_matches(trace: CounterTrace, ctx: _Context, step: int) -> bool:
    """Match every prior public price/message/decision, with no extra rows."""
    if len(ctx.history) != 2 * step:
        return False
    for index in range(step):
        seller_round = 2 * index + 1
        buyer_round = seller_round + 1
        seller_entry = ctx.history[2 * index]
        buyer_entry = ctx.history[2 * index + 1]

        if not _offer_matches(
                seller_entry,
                price=trace.seller_prices[index],
                message=trace.seller_messages[index],
                player=ctx.other,
                round_no=seller_round):
            return False
        if (seller_entry.get("decision") != "RejectOffer"
                or seller_entry.get("decided_by") != ctx.me
                or not _same_price(seller_entry.get("counteroffer"),
                                   trace.buyer_prices[index])):
            return False

        if not _offer_matches(
                buyer_entry,
                price=trace.buyer_prices[index],
                message=_buyer_message(trace.buyer_prices[index],
                                       trace.messages_allowed),
                player=ctx.me,
                round_no=buyer_round):
            return False
        if (buyer_entry.get("decision") != "RejectOffer"
                or buyer_entry.get("decided_by") != ctx.other
                or not _same_price(buyer_entry.get("counteroffer"),
                                   trace.seller_prices[index + 1])):
            return False
    return True


def _matching_counter(ctx: _Context) -> tuple[CounterTrace, int] | None:
    if not ctx.complete:
        return None
    step = (ctx.round_no - 1) // 2
    matches = []
    for trace in COMPLETE_COUNTER_TRACES:
        if step >= len(trace.buyer_prices):
            continue
        if not (
            _same_price(ctx.base, trace.base)
            and _same_price(ctx.own_value, trace.buyer_value)
            and _same_price(ctx.other_value, trace.seller_value)
            and ctx.horizon_known == trace.horizon_known
            and ctx.max_rounds == trace.max_rounds
            and ctx.messages_allowed == trace.messages_allowed
            and _same_price(ctx.incoming_price, trace.seller_prices[step])
            and ctx.incoming_message == trace.seller_messages[step]
            and _history_matches(trace, ctx, step)
        ):
            continue
        matches.append(trace)
    # Ambiguous duplicate table rows fail closed rather than depending on order.
    return (matches[0], step) if len(matches) == 1 else None


def _matching_accept(ctx: _Context) -> AcceptTrace | None:
    if ctx.round_no != 1 or ctx.max_rounds != 1 or ctx.history:
        return None
    matches = []
    for trace in SINGLE_ROUND_ACCEPT_TRACES:
        if not (
            ctx.complete == trace.complete
            and ctx.horizon_known
            and _same_price(ctx.base, trace.base)
            and _same_price(ctx.own_value, trace.buyer_value)
            and ctx.messages_allowed == trace.messages_allowed
            and _same_price(ctx.incoming_price, trace.incoming_price)
            and ctx.incoming_message == trace.incoming_message
        ):
            continue
        if trace.complete:
            if not _same_price(ctx.other_value, trace.seller_value):
                continue
        elif ctx.other_value is not None:
            continue
        matches.append(trace)
    return matches[0] if len(matches) == 1 else None


def _identified_action(ctx: _Context) -> dict | None:
    accept = _matching_accept(ctx)
    if accept is not None:
        # Agreement records identify the decision, not an Athena response text;
        # omit message rather than inventing one.
        return {
            "decision": "AcceptOffer",
            "_plan": {
                "source": PLAN_SOURCE,
                "evidence": "exact_single_round_accept",
                "source_game_id": accept.source_game_id,
                "type_basis": accept.type_basis,
            },
        }

    counter = _matching_counter(ctx)
    if counter is None:
        return None
    trace, step = counter
    price = trace.buyer_prices[step]
    action = {
        "decision": "RejectOffer",
        "product_price": price,
        "_plan": {
            "source": PLAN_SOURCE,
            "evidence": "exact_complete_history_counter",
            "source_game_id": trace.source_game_id,
            "step": step,
        },
    }
    if trace.messages_allowed:
        action["message"] = _buyer_message(price, True)
    return action


def eligible(game: dict) -> bool:
    """Whether this exact public state has one point-supported Athena move."""
    try:
        ctx = _context(game)
        return ctx is not None and _identified_action(ctx) is not None
    except Exception:
        return False


def owns(game: dict) -> bool:
    """Own only supported candidate states, with both older clones disarmed."""
    try:
        return (enabled()
                and treatment_assignment(game.get("game_id")) is True
                and eligible(game))
    except Exception:
        return False


def action(game: dict) -> dict | None:
    """Return an exact observed treatment move; otherwise fall through."""
    if not owns(game):
        return None
    ctx = _context(game)
    return _identified_action(ctx) if ctx is not None else None


def matches_wire(game: dict, wire: dict) -> bool:
    """Whether ``wire`` is the exact semantic action produced by this clone."""
    if not isinstance(wire, dict):
        return False
    expected = action(game)
    if expected is None:
        return False
    semantic_keys = ("decision", "product_price", "message")
    return all(wire.get(key) == expected.get(key) for key in semantic_keys)
