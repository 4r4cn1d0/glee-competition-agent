#!/usr/bin/env python3
"""Join dashboard rating deltas to local negotiation game IDs, fail closed.

The dashboard export is JSON: either a list of history rows, or an object with
``games``/``history`` and an optional inherited ``slot``.  Each row must carry
``slot``, ``timestamp``, ``role``, ``outcome``, and ``rating_delta`` (``rating``
is accepted as an alias), plus a ``modal`` object with:

* ``setup``: own value, information condition, and horizon;
* ``transcript``: ordered offer/decision/counter records; and
* ``payoffs`` (or ``terminal_payoffs``): seller/buyer or own/opponent payoffs.

The matcher deliberately excludes rating and prose messages from its key.  It
uses exact-cent setup/transcript/payoff semantics, collapses the server's
counteroffer-as-next-offer echo, and accepts only a unique global one-to-one
match.  Timestamp semantics must either be explicit or be frozen by an
unconflicted calibration that distinguishes first local action from completion.

Example:

    python scripts/join_official_history.py export.json \
        --logs-root logs --slots conceder --timestamp-mode dual > official.json

Unresolved and ambiguous rows are reported on stderr and never guessed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


OUTPUT_SCHEMA = "glee.official-rating-join/v1"
REPORT_SCHEMA = "glee.official-rating-join-report/v1"
_CENT = Decimal("0.01")

_CAPTURE_CARD = re.compile(
    r"^Negotiation\s*You played\s*(Buyer|Seller)\s*vs an agent\s*"
    r"(Agreement|No deal|Walked away)\s*·\s*(.+?)\s*"
    r"Rating\s*([+-]?\d+(?:\.\d+)?)\s*›$",
    re.IGNORECASE,
)
_CAPTURE_ROUND = re.compile(r"(?m)^Round (\d+)\r?$")


class JoinInputError(ValueError):
    """The export or timestamp contract is not safe enough to join."""


@dataclass(frozen=True)
class DashboardRecord:
    row: int
    slot: str
    timestamp_raw: Any
    minute_utc: int
    role: str
    outcome: str
    rating_delta: int | float
    fingerprint: str


@dataclass(frozen=True)
class LocalRecord:
    slot: str
    game_id: str
    path: str
    fingerprint: str
    first_ts: float | None
    completion_ts: float | None

    @property
    def first_minute(self) -> int | None:
        return None if self.first_ts is None else math.floor(self.first_ts / 60)

    @property
    def completion_minute(self) -> int | None:
        return (None if self.completion_ts is None
                else math.floor(self.completion_ts / 60))


def money_to_cents(value: Any) -> int:
    """Convert a JSON money value to integer cents with decimal half-up rules."""
    if isinstance(value, bool) or value is None:
        raise JoinInputError("money value is missing or boolean")
    text = str(value).strip()
    if not text:
        raise JoinInputError("money value is empty")
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1].strip()
    text = text.replace(",", "")
    for symbol in ("$", "€", "£", "₹"):
        text = text.replace(symbol, "")
    multiplier = Decimal(1)
    if text and text[-1].lower() in {"k", "m", "b"}:
        multiplier = {
            "k": Decimal(1_000),
            "m": Decimal(1_000_000),
            "b": Decimal(1_000_000_000),
        }[text[-1].lower()]
        text = text[:-1].strip()
    try:
        amount = Decimal(text) * multiplier
    except (InvalidOperation, ValueError) as exc:
        raise JoinInputError(f"invalid money value {value!r}") from exc
    if not amount.is_finite():
        raise JoinInputError(f"non-finite money value {value!r}")
    if negative:
        amount = -amount
    return int((amount.quantize(_CENT, rounding=ROUND_HALF_UP)) * 100)


def _number(value: Any, *, field: str) -> int | float:
    if isinstance(value, bool) or value is None:
        raise JoinInputError(f"{field} is missing or boolean")
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise JoinInputError(f"invalid {field}: {value!r}") from exc
    if not number.is_finite():
        raise JoinInputError(f"non-finite {field}: {value!r}")
    if number == number.to_integral_value():
        return int(number)
    return float(number)


def _first(mapping: Mapping[str, Any], names: Iterable[str]) -> Any:
    for name in names:
        if name in mapping and mapping[name] is not None:
            return mapping[name]
    return None


def _normalize_role(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "seller": "seller",
        "sell": "seller",
        "buyer": "buyer",
        "buy": "buyer",
    }
    if text not in aliases:
        raise JoinInputError(f"unrecognized role {value!r}")
    return aliases[text]


def _role_map(setup: Mapping[str, Any]) -> dict[str, str]:
    output = {"seller": "seller", "buyer": "buyer"}
    p1 = setup.get("player_1_role")
    p2 = setup.get("player_2_role")
    if p1 is not None:
        output["player_1"] = _normalize_role(p1)
    if p2 is not None:
        output["player_2"] = _normalize_role(p2)
    if "player_1" in output and "player_2" not in output:
        output["player_2"] = ("buyer" if output["player_1"] == "seller" else "seller")
    if "player_2" in output and "player_1" not in output:
        output["player_1"] = ("buyer" if output["player_2"] == "seller" else "seller")
    # Negotiation wire semantics fix player_1 as seller and player_2 as buyer.
    output.setdefault("player_1", "seller")
    output.setdefault("player_2", "buyer")
    if {output["player_1"], output["player_2"]} != {"seller", "buyer"}:
        raise JoinInputError("setup player roles must be one seller and one buyer")
    return output


def _normalize_actor(value: Any, roles: Mapping[str, str]) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if text in roles:
        return roles[text]
    return _normalize_role(text)


def _normalize_outcome(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "agreement": "agreement",
        "agreed": "agreement",
        "deal": "agreement",
        "accepted": "agreement",
        "accept": "agreement",
        "no_deal": "no_deal",
        "nodeal": "no_deal",
        "timeout": "no_deal",
        "timed_out": "no_deal",
        "expired": "no_deal",
        # The negotiation wire reports every zero-payoff terminal route as
        # no_deal; the transcript still distinguishes an explicit walk action.
        "walked_away": "no_deal",
        "walkaway": "no_deal",
        "walk_away": "no_deal",
    }
    if text not in aliases:
        raise JoinInputError(f"unrecognized outcome {value!r}")
    return aliases[text]


def _normalize_decision(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    compact = text.replace("_", "")
    aliases = {
        "accept": "accept",
        "accepted": "accept",
        "acceptoffer": "accept",
        "reject": "reject",
        "rejected": "reject",
        "rejectoffer": "reject",
        "walk": "walk",
        "walkaway": "walk",
        "walkedaway": "walk",
        # A server-side timeout is a terminal wire event, not a rejection by
        # the timed-out player.  Keeping it distinct lets the official modal
        # join identify genuine timeouts without inventing an action.
        "timeout": "timeout",
        "timedout": "timeout",
    }
    if compact not in aliases:
        raise JoinInputError(f"unrecognized decision {value!r}")
    return aliases[compact]


def _boolean(value: Any, *, field: str) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if text in {"true", "1", "yes", "complete", "complete_information",
                "known", "visible", "visible_information"}:
        return True
    if text in {"false", "0", "no", "hidden", "hidden_information",
                "incomplete", "incomplete_information", "unknown"}:
        return False
    raise JoinInputError(f"unrecognized {field} {value!r}")


def _canonical_setup(source: Mapping[str, Any], role: str) -> dict[str, Any]:
    if not isinstance(source, Mapping):
        raise JoinInputError("modal setup must be an object")
    roles = _role_map(source)
    own_player = "player_1" if role == roles["player_1"] else "player_2"
    other_role = "buyer" if role == "seller" else "seller"
    other_player = "player_2" if own_player == "player_1" else "player_1"

    own_value = _first(source, (
        "own_value", "your_value", "value", f"{role}_value",
        f"{own_player}_value",
    ))
    if own_value is None:
        raise JoinInputError("setup is missing own value")

    complete_raw = _first(source, ("complete_information", "information_complete"))
    if complete_raw is None:
        information = _first(source, ("information", "information_condition"))
        if information is None:
            raise JoinInputError("setup is missing information condition")
        complete = _boolean(information, field="information condition")
    else:
        complete = _boolean(complete_raw, field="complete_information")

    opponent_value: int | str = "hidden"
    if complete:
        raw_opponent = _first(source, (
            "opponent_value", "other_value", f"{other_role}_value",
            f"{other_player}_value",
        ))
        if raw_opponent is None:
            raise JoinInputError("complete-information setup is missing opponent value")
        opponent_value = money_to_cents(raw_opponent)

    max_rounds = _first(source, ("max_rounds", "round_cap"))
    horizon_known_raw = source.get("horizon_known")
    horizon_label = _first(source, ("horizon", "horizon_type"))
    if horizon_known_raw is not None:
        horizon_known = _boolean(horizon_known_raw, field="horizon_known")
    elif horizon_label is not None:
        label = str(horizon_label).strip().lower().replace("-", "_").replace(" ", "_")
        if label in {"unknown", "unknown_horizon", "uncapped", "hidden",
                     "hidden_horizon", "indefinite"}:
            horizon_known = False
        elif label in {"known", "capped", "fixed"}:
            horizon_known = True
        else:
            try:
                max_rounds = int(label)
            except ValueError as exc:
                raise JoinInputError(f"unrecognized horizon {horizon_label!r}") from exc
            horizon_known = True
    elif max_rounds is not None:
        horizon_known = True
    else:
        raise JoinInputError("setup is missing horizon semantics")

    if horizon_known:
        if isinstance(max_rounds, bool) or max_rounds is None:
            raise JoinInputError("known horizon is missing max_rounds")
        try:
            rounds = int(max_rounds)
        except (TypeError, ValueError) as exc:
            raise JoinInputError(f"invalid max_rounds {max_rounds!r}") from exc
        if rounds <= 0:
            raise JoinInputError("max_rounds must be positive")
        horizon: dict[str, Any] = {"kind": "capped", "max_rounds": rounds}
    else:
        horizon = {"kind": "unknown"}

    return {
        "role": role,
        "own_value_cents": money_to_cents(own_value),
        "information": "complete" if complete else "hidden",
        "opponent_value_cents": opponent_value,
        "horizon": horizon,
    }


def _price_event(kind: str, value: Any, default_actor: Any,
                 roles: Mapping[str, str]) -> list[Any]:
    if isinstance(value, Mapping):
        price = _first(value, (
            "price", "offer_price", "counter_price", "product_price", "amount", "value"))
        actor = _first(value, (
            "role", "actor", "from_player", "offered_by", "by", "player"))
        if actor is None:
            actor = default_actor
    else:
        price = value
        actor = default_actor
    if price is None:
        raise JoinInputError(f"{kind} is missing price")
    if actor is None:
        raise JoinInputError(f"{kind} is missing actor")
    return [kind, _normalize_actor(actor, roles), money_to_cents(price)]


def _decision_event(value: Any, default_actor: Any,
                    roles: Mapping[str, str]) -> list[Any]:
    if isinstance(value, Mapping):
        action = _first(value, ("action", "decision", "value"))
        actor = _first(value, ("role", "actor", "decided_by", "by", "player"))
        if actor is None:
            actor = default_actor
    else:
        action = value
        actor = default_actor
    if action is None:
        raise JoinInputError("decision is missing action")
    if actor is None:
        raise JoinInputError("decision is missing actor")
    return ["decision", _normalize_actor(actor, roles), _normalize_decision(action)]


def _events_from_transcript_item(item: Mapping[str, Any],
                                 roles: Mapping[str, str]) -> list[list[Any]]:
    if not isinstance(item, Mapping):
        raise JoinInputError("each transcript item must be an object")
    event_type = str(item.get("type") or item.get("kind") or "").strip().lower()
    event_type = event_type.replace("-", "_").replace(" ", "_")
    if event_type in {"offer", "counter", "counteroffer", "counter_offer"}:
        kind = "counter" if event_type != "offer" else "offer"
        return [_price_event(
            kind,
            _first(item, (
                "price", "offer_price", "counter_price", "product_price",
                "amount", "value")),
            _first(item, (
                "role", "actor", "from_player", "offer_by", "counter_by",
                "offered_by", "by", "player")),
            roles,
        )]
    if event_type in {"decision", "accept", "reject", "walk", "walkaway"}:
        action = (_first(item, ("action", "decision", "value"))
                  if event_type == "decision" else event_type)
        return [_decision_event(
            action,
            _first(item, (
                "role", "actor", "decision_by", "decided_by", "by", "player")),
            roles,
        )]

    events: list[list[Any]] = []
    offer = _first(item, ("offer", "offer_price"))
    if offer is not None:
        events.append(_price_event(
            "offer", offer,
            _first(item, (
                "offer_role", "offer_by", "offered_by", "from_player", "actor")),
            roles))
    if item.get("decision") is not None:
        events.append(_decision_event(
            item["decision"],
            _first(item, ("decision_role", "decision_by", "decided_by", "actor")),
            roles))
    counter = _first(item, ("counteroffer", "counter", "counter_price"))
    if counter is not None:
        events.append(_price_event(
            "counter", counter,
            _first(item, (
                "counter_role", "counter_by", "decided_by", "actor")), roles))
    if not events:
        semantic_keys = {"offer", "decision", "counteroffer", "counter",
                         "counter_price", "offer_price", "price", "product_price"}
        if semantic_keys.intersection(item):
            raise JoinInputError("transcript item has incomplete semantic event")
        # Prose-only modal rows are intentionally outside the hard key.
    return events


def _canonical_transcript(source: Any, setup_source: Mapping[str, Any],
                          role: str) -> list[list[Any]]:
    if not isinstance(source, Sequence) or isinstance(source, (str, bytes)):
        raise JoinInputError("modal transcript must be an ordered list")
    roles = _role_map(setup_source)
    roles.update({
        "you": role,
        "your": role,
        "own": role,
        "self": role,
        "opponent": "buyer" if role == "seller" else "seller",
        "other": "buyer" if role == "seller" else "seller",
    })
    output: list[list[Any]] = []
    for index, item in enumerate(source):
        try:
            events = _events_from_transcript_item(item, roles)
        except JoinInputError as exc:
            raise JoinInputError(f"transcript item {index}: {exc}") from exc
        for event in events:
            # The server repeats a counteroffer as the next round's offer.  It
            # is one wire action, not two independent identifying observations.
            if (event[0] == "offer" and output and output[-1][0] == "counter"
                    and event[1:] == output[-1][1:]):
                continue
            output.append(event)
    if not output:
        raise JoinInputError("transcript has no semantic events")
    return output


def _payoff_value(source: Mapping[str, Any], names: Iterable[str]) -> Any:
    return _first(source, names)


def _canonical_payoffs(source: Mapping[str, Any], role: str,
                       roles: Mapping[str, str]) -> dict[str, int]:
    if not isinstance(source, Mapping):
        raise JoinInputError("terminal payoffs must be an object")
    seller_player = "player_1" if roles["player_1"] == "seller" else "player_2"
    buyer_player = "player_1" if seller_player == "player_2" else "player_2"
    seller = _payoff_value(source, (
        "seller", "seller_payoff", f"{seller_player}_payoff", seller_player,
    ))
    buyer = _payoff_value(source, (
        "buyer", "buyer_payoff", f"{buyer_player}_payoff", buyer_player,
    ))
    if seller is None or buyer is None:
        own = _payoff_value(source, (
            "own", "our", "you", "your", "your_payoff", "our_payoff"))
        opponent = _payoff_value(source, ("opponent", "opponent_payoff", "other"))
        if own is not None and opponent is not None:
            if role == "seller":
                seller, buyer = own, opponent
            else:
                seller, buyer = opponent, own
    if seller is None or buyer is None:
        raise JoinInputError("terminal payoffs need both seller and buyer values")
    return {"seller_cents": money_to_cents(seller),
            "buyer_cents": money_to_cents(buyer)}


def _fingerprint(role: str, outcome: str, setup: Mapping[str, Any],
                 transcript: Sequence[Any], payoffs: Mapping[str, Any]) -> str:
    payload = {
        "family": "negotiation",
        "role": role,
        "outcome": outcome,
        "setup": setup,
        "transcript": transcript,
        "payoffs": payoffs,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _timestamp_epoch(value: Any, timezone_name: str | None) -> float:
    if isinstance(value, bool) or value is None:
        raise JoinInputError("timestamp is missing or boolean")
    if isinstance(value, (int, float)):
        timestamp = float(value)
        if not math.isfinite(timestamp):
            raise JoinInputError(f"non-finite timestamp {value!r}")
        if abs(timestamp) >= 100_000_000_000:
            timestamp /= 1000.0
        return timestamp
    text = str(value).strip()
    if not text:
        raise JoinInputError("timestamp is empty")
    try:
        numeric = float(text)
    except ValueError:
        numeric = None
    if numeric is not None:
        if not math.isfinite(numeric):
            raise JoinInputError(f"non-finite timestamp {value!r}")
        if abs(numeric) >= 100_000_000_000:
            numeric /= 1000.0
        return numeric
    iso = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
    try:
        parsed = datetime.fromisoformat(iso)
    except ValueError:
        parsed = None
        # The authenticated dashboard renders this exact human-readable form.
        # It is intentionally parsed only with an explicit timezone below;
        # treating it as local-machine time would make the join nonportable.
        for pattern in ("%b %d, %Y %I:%M %p", "%b %d, %Y, %I:%M %p"):
            try:
                parsed = datetime.strptime(text, pattern)
                break
            except ValueError:
                continue
        if parsed is None:
            raise JoinInputError(f"invalid timestamp {value!r}")
    if parsed.tzinfo is None:
        if not timezone_name:
            raise JoinInputError(
                "naive dashboard timestamp requires --dashboard-timezone")
        try:
            parsed = parsed.replace(tzinfo=ZoneInfo(timezone_name))
        except ZoneInfoNotFoundError as exc:
            raise JoinInputError(f"unknown dashboard timezone {timezone_name!r}") from exc
    return parsed.astimezone(timezone.utc).timestamp()


def _capture_field(text: str, label: str) -> str | None:
    match = re.search(
        rf"(?im)^{re.escape(label)}:[ \t]*\r?\n\$?([^\r\n]+)$", text)
    return None if match is None else match.group(1).strip()


def _capture_dashboard_row(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a raw authenticated card/modal capture to the structured schema.

    Browser collection only needs the card's accessible text and the dialog's
    ``innerText``.  Parsing stays here, versioned and tested beside the exact
    join, instead of living in an ephemeral browser-session transform.
    """
    card = str(raw.get("card_text") or "").strip()
    modal = str(raw.get("modal_text") or "")
    card_match = _CAPTURE_CARD.match(card)
    if card_match is None:
        raise JoinInputError("raw dashboard capture has an unrecognized card")
    if not modal.strip():
        raise JoinInputError("raw dashboard capture is missing modal_text")
    role, outcome, timestamp, rating = card_match.groups()

    own_value = _capture_field(modal, "Your valuation")
    if own_value is None:
        raise JoinInputError("raw dashboard modal is missing own valuation")
    opponent_value = _capture_field(modal, "Opponent valuation")
    rounds_raw = _capture_field(modal, "Max rounds")
    if rounds_raw is None:
        raise JoinInputError("raw dashboard modal is missing max rounds")
    setup: dict[str, Any] = {
        "own_value": own_value,
        "complete_information": opponent_value is not None,
    }
    if opponent_value is not None:
        setup["opponent_value"] = opponent_value
    if rounds_raw.isdigit() and int(rounds_raw) > 0:
        setup["max_rounds"] = int(rounds_raw)
    elif rounds_raw.strip().lower() in {
            "no limit", "none", "unknown", "unlimited", "uncapped"}:
        setup["horizon"] = "unknown"
    else:
        raise JoinInputError(f"unrecognized captured max rounds {rounds_raw!r}")

    final_match = re.search(r"(?im)^FINAL RESULT\b", modal)
    if final_match is None:
        raise JoinInputError("raw dashboard modal is missing final result")
    transcript_text = modal[:final_match.start()]
    starts = list(_CAPTURE_ROUND.finditer(transcript_text))
    if not starts:
        raise JoinInputError("raw dashboard modal has no rounds")
    transcript: list[dict[str, Any]] = []
    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) \
            else len(transcript_text)
        block = transcript_text[start.start():end]
        header = re.match(
            r"^Round (\d+)\r?\n(?:You \((Buyer|Seller)\)|(Buyer|Seller))"
            r"[ \t]*\r?\n\s*Offered:\s*\$([0-9,().-]+)",
            block,
        )
        if header is None:
            raise JoinInputError(
                f"raw dashboard modal round {start.group(1)} is malformed")
        round_number = int(header.group(1))
        actor = (header.group(2) or header.group(3)).lower()
        other = "buyer" if actor == "seller" else "seller"
        decisions = list(re.finditer(
            r"(?im)^(Accept|Reject|Walk away|Walked away|Timeout|Timed out)"
            r"(?:counter:\s*\$([0-9,().-]+))?[ \t]*$",
            block,
        ))
        if not decisions:
            raise JoinInputError(
                f"raw dashboard modal round {round_number} is missing decision")
        decision = decisions[-1]
        item: dict[str, Any] = {
            "round": round_number,
            "offer": {"price": header.group(4), "role": actor},
            "decision": {"action": decision.group(1), "role": other},
        }
        if decision.group(2) is not None:
            item["counteroffer"] = {
                "price": decision.group(2), "role": other}
        transcript.append(item)
    transcript.sort(key=lambda item: item["round"])
    if [item["round"] for item in transcript] != sorted({
            item["round"] for item in transcript}):
        raise JoinInputError("raw dashboard modal has duplicate round numbers")

    result_text = modal[final_match.start():]
    own_payoff = re.search(
        r"(?im)^YOUR PAYOFF[ \t]*\r?\n\s*\$([0-9,().-]+)", result_text)
    opponent_payoff = re.search(
        r"(?im)^OPPONENT[ \t]*\r?\n\s*\$([0-9,().-]+)", result_text)
    if own_payoff is None or opponent_payoff is None:
        raise JoinInputError("raw dashboard modal is missing terminal payoffs")
    return {
        "slot": raw.get("slot"),
        "timestamp": timestamp,
        "role": role,
        "outcome": outcome,
        "rating_delta": rating,
        "modal": {
            "setup": setup,
            "transcript": transcript,
            "payoffs": {
                "own": own_payoff.group(1),
                "opponent": opponent_payoff.group(1),
            },
        },
    }


def _dashboard_records(export: Any, *, slots: set[str],
                       dashboard_timezone: str | None
                       ) -> tuple[list[DashboardRecord], list[dict[str, Any]]]:
    inherited_slot = None
    if isinstance(export, list):
        rows = export
    elif isinstance(export, Mapping):
        inherited_slot = export.get("slot")
        rows = export.get("games")
        if rows is None:
            rows = export.get("history")
        if not isinstance(rows, list):
            raise JoinInputError("dashboard export needs a games/history list")
    else:
        raise JoinInputError("dashboard export must be a list or object")

    valid: list[DashboardRecord] = []
    unresolved: list[dict[str, Any]] = []
    for row_index, raw in enumerate(rows):
        slot = ""
        try:
            if not isinstance(raw, Mapping):
                raise JoinInputError("dashboard row must be an object")
            if "card_text" in raw or "modal_text" in raw:
                captured = _capture_dashboard_row(raw)
                if captured.get("slot") is None:
                    captured["slot"] = inherited_slot
                raw = captured
            slot = str(raw.get("slot") or inherited_slot or "").strip()
            if not slot:
                raise JoinInputError("dashboard row is missing slot")
            if slot not in slots:
                raise JoinInputError(f"slot {slot!r} was not selected")
            timestamp_raw = _first(raw, ("timestamp", "time", "created_at"))
            minute = math.floor(_timestamp_epoch(timestamp_raw, dashboard_timezone) / 60)
            role = _normalize_role(_first(raw, ("role", "your_role")))
            outcome = _normalize_outcome(_first(raw, ("outcome", "result_outcome")))
            rating_raw = _first(raw, ("rating_delta", "rating"))
            if isinstance(rating_raw, Mapping):
                rating_raw = _first(rating_raw, ("delta", "rating_delta", "change"))
            rating_delta = _number(rating_raw, field="rating_delta")

            modal = raw.get("modal") or {}
            if not isinstance(modal, Mapping):
                raise JoinInputError("modal must be an object")
            setup_source = raw.get("setup") or modal.get("setup")
            transcript_source = (raw.get("transcript") or raw.get("history")
                                 or modal.get("transcript") or modal.get("history"))
            payoffs_source = (raw.get("terminal_payoffs") or raw.get("payoffs")
                              or modal.get("terminal_payoffs") or modal.get("payoffs")
                              or modal.get("result"))
            if setup_source is None:
                raise JoinInputError("dashboard row is missing modal setup")
            if transcript_source is None:
                raise JoinInputError("dashboard row is missing modal transcript")
            if payoffs_source is None:
                raise JoinInputError("dashboard row is missing terminal payoffs")
            setup = _canonical_setup(setup_source, role)
            transcript = _canonical_transcript(transcript_source, setup_source, role)
            payoffs = _canonical_payoffs(payoffs_source, role, _role_map(setup_source))
            valid.append(DashboardRecord(
                row=row_index,
                slot=slot,
                timestamp_raw=timestamp_raw,
                minute_utc=minute,
                role=role,
                outcome=outcome,
                rating_delta=rating_delta,
                fingerprint=_fingerprint(role, outcome, setup, transcript, payoffs),
            ))
        except (JoinInputError, TypeError, ValueError) as exc:
            unresolved.append({
                "dashboard_row": row_index,
                "slot": slot or None,
                "reason": str(exc),
                "candidate_count": 0,
            })
    return valid, unresolved


def _valid_timestamps(turns: Any) -> list[float]:
    timestamps: list[float] = []
    if not isinstance(turns, list):
        return timestamps
    for turn in turns:
        if (not isinstance(turn, Mapping)
                or not isinstance(turn.get("action"), Mapping)
                or isinstance(turn.get("ts"), bool)):
            continue
        try:
            ts = float(turn.get("ts"))
        except (TypeError, ValueError):
            continue
        if math.isfinite(ts):
            timestamps.append(ts)
    return sorted(timestamps)


def _terminal_actor(last: Mapping[str, Any], roles: Mapping[str, str]) -> str | None:
    actor = _first(last, ("decided_by", "decision_role"))
    if actor is None:
        counter = _first(last, ("counteroffer", "counter"))
        if isinstance(counter, Mapping):
            actor = _first(counter, ("from_player", "role", "actor", "by"))
    if actor is None:
        offer = last.get("offer")
        if isinstance(offer, Mapping):
            actor = _first(offer, ("from_player", "role", "actor", "by"))
    if actor is None:
        return None
    try:
        return _normalize_actor(actor, roles)
    except JoinInputError:
        return None


def _completion_timestamp(history: Any, turns: Any, role: str,
                          roles: Mapping[str, str]) -> float | None:
    timestamps = _valid_timestamps(turns)
    if not timestamps or not isinstance(history, list) or not history:
        return None
    last = history[-1]
    if not isinstance(last, Mapping):
        return None
    actor = _terminal_actor(last, roles)
    if actor == role:
        return timestamps[-1]
    response_ms = _first(last, ("response_time_ms", "response_ms"))
    if actor is None or response_ms is None or isinstance(response_ms, bool):
        return None
    try:
        delay = float(response_ms) / 1000.0
    except (TypeError, ValueError):
        return None
    if not math.isfinite(delay) or delay < 0:
        return None
    return timestamps[-1] + delay


def _local_record(raw: Mapping[str, Any], *, slot: str, path: Path) -> LocalRecord:
    if raw.get("game_family") != "negotiation":
        raise JoinInputError("not a negotiation game")
    status = raw.get("status")
    terminal_statuses = {"completed", "no_deal", "agreement", "walked_away", "finished"}
    if status is not None and str(status).lower() not in terminal_statuses:
        raise JoinInputError(f"game status is not completed: {status!r}")
    game_id = str(raw.get("game_id") or "").strip()
    if not game_id:
        raise JoinInputError("local game is missing game_id")
    setup_source = raw.get("config") or (raw.get("game_state") or {})
    if not isinstance(setup_source, Mapping):
        raise JoinInputError("local game is missing config")
    player = str(raw.get("your_player") or "").strip().lower()
    roles = _role_map(setup_source)
    if player not in roles:
        raise JoinInputError("local game is missing a valid your_player")
    role = roles[player]
    result = raw.get("result") or {}
    if not isinstance(result, Mapping):
        raise JoinInputError("local game is missing result")
    outcome = _normalize_outcome(result.get("outcome"))
    history = raw.get("history")
    if history is None:
        history = (raw.get("game_state") or {}).get("history")
    setup = _canonical_setup(setup_source, role)
    transcript = _canonical_transcript(history, setup_source, role)
    payoffs_source: dict[str, Any] = dict(result)
    if raw.get("our_payoff") is not None:
        payoffs_source.setdefault("our_payoff", raw.get("our_payoff"))
    if raw.get("opponent_payoff") is not None:
        payoffs_source.setdefault("opponent_payoff", raw.get("opponent_payoff"))
    payoffs = _canonical_payoffs(payoffs_source, role, roles)
    timestamps = _valid_timestamps(raw.get("our_turns"))
    first_ts = timestamps[0] if timestamps else None
    completion_ts = _completion_timestamp(history, raw.get("our_turns"), role, roles)
    return LocalRecord(
        slot=slot,
        game_id=game_id,
        path=str(path),
        fingerprint=_fingerprint(role, outcome, setup, transcript, payoffs),
        first_ts=first_ts,
        completion_ts=completion_ts,
    )


def _load_local_records(logs_root: Path, slots: set[str]
                        ) -> tuple[list[LocalRecord], list[dict[str, Any]]]:
    records: list[LocalRecord] = []
    errors: list[dict[str, Any]] = []
    for slot in sorted(slots):
        games_dir = logs_root / slot / "games"
        if not games_dir.is_dir():
            errors.append({"slot": slot, "path": str(games_dir),
                           "reason": "selected slot has no games directory"})
            continue
        for path in sorted(games_dir.glob("*.json")):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(raw, Mapping):
                    raise JoinInputError("local game JSON must be an object")
                if raw.get("game_family") != "negotiation":
                    continue
                # Live GameLog snapshots can coexist with finalized files.
                # They are not candidates and should not make an otherwise
                # exact historical join fail; unknown/malformed statuses still
                # flow into _local_record and remain reportable errors.
                if str(raw.get("status") or "").strip().lower() in {
                        "active", "pending", "in_progress", "running"}:
                    continue
                records.append(_local_record(raw, slot=slot, path=path))
            except (OSError, json.JSONDecodeError, JoinInputError,
                    TypeError, ValueError) as exc:
                errors.append({"slot": slot, "path": str(path), "reason": str(exc)})

    by_identity: dict[tuple[str, str], list[LocalRecord]] = defaultdict(list)
    for record in records:
        by_identity[(record.slot, record.game_id)].append(record)
    duplicates = {identity for identity, group in by_identity.items() if len(group) > 1}
    if duplicates:
        filtered: list[LocalRecord] = []
        for record in records:
            identity = (record.slot, record.game_id)
            if identity in duplicates:
                errors.append({"slot": record.slot, "path": record.path,
                               "reason": f"duplicate local game_id {record.game_id!r}"})
            else:
                filtered.append(record)
        records = filtered
    return records, errors


def _duplicate_dashboard_rows(records: Sequence[DashboardRecord]) -> set[int]:
    groups: dict[tuple[str, int, str], list[int]] = defaultdict(list)
    for record in records:
        # Rating is intentionally absent: different displayed deltas must never
        # turn otherwise duplicate dashboard rows into distinct join evidence.
        groups[(record.slot, record.minute_utc, record.fingerprint)].append(record.row)
    return {row for rows in groups.values() if len(rows) > 1 for row in rows}


def _calibrate_timestamp_mode(dashboard: Sequence[DashboardRecord],
                              local: Sequence[LocalRecord],
                              excluded_rows: set[int]) -> str:
    by_fingerprint: dict[tuple[str, str], list[LocalRecord]] = defaultdict(list)
    for record in local:
        by_fingerprint[(record.slot, record.fingerprint)].append(record)
    first_only = 0
    completion_only = 0
    for row in dashboard:
        if row.row in excluded_rows:
            continue
        candidates = by_fingerprint.get((row.slot, row.fingerprint), [])
        if len(candidates) != 1:
            continue
        candidate = candidates[0]
        first = (candidate.first_minute is not None
                 and row.minute_utc == candidate.first_minute)
        completion = (candidate.completion_minute is not None
                      and row.minute_utc == candidate.completion_minute)
        if first and not completion:
            first_only += 1
        elif completion and not first:
            completion_only += 1
    if first_only and not completion_only:
        return "first"
    if completion_only and not first_only:
        return "completion"
    if first_only and completion_only:
        raise JoinInputError(
            "timestamp calibration conflicts across rows; require explicit mode")
    raise JoinInputError(
        "timestamp calibration cannot distinguish first from completion; "
        "require explicit --timestamp-mode")


def _timestamp_matches(row: DashboardRecord, local: LocalRecord, *, mode: str,
                       tolerance: int) -> bool:
    anchors: list[int] = []
    if mode in {"first", "dual"} and local.first_minute is not None:
        anchors.append(local.first_minute)
    if mode in {"completion", "dual"} and local.completion_minute is not None:
        anchors.append(local.completion_minute)
    return any(abs(row.minute_utc - anchor) <= tolerance for anchor in anchors)


def _component_matchings(candidate_map: Mapping[int, set[int]],
                         dashboard_rows: set[int]) -> tuple[int, dict[int, int] | None]:
    """Count injective assignments up to two and retain the sole assignment."""
    ordered = sorted(dashboard_rows, key=lambda row: (len(candidate_map[row]), row))
    count = 0
    sole: dict[int, int] | None = None

    def search(position: int, used: set[int], assignment: dict[int, int]) -> None:
        nonlocal count, sole
        if count >= 2:
            return
        if position == len(ordered):
            count += 1
            if count == 1:
                sole = dict(assignment)
            return
        row = ordered[position]
        for local_index in sorted(candidate_map[row] - used):
            assignment[row] = local_index
            search(position + 1, used | {local_index}, assignment)
            assignment.pop(row, None)
            if count >= 2:
                return

    search(0, set(), {})
    return count, sole


def _unique_global_matches(candidate_map: Mapping[int, set[int]]
                           ) -> tuple[dict[int, int], dict[int, str]]:
    inverse: dict[int, set[int]] = defaultdict(set)
    for row, candidates in candidate_map.items():
        for local_index in candidates:
            inverse[local_index].add(row)
    unseen = set(candidate_map)
    matched: dict[int, int] = {}
    ambiguous: dict[int, str] = {}
    while unseen:
        start = min(unseen)
        rows: set[int] = set()
        locals_seen: set[int] = set()
        queue: deque[tuple[str, int]] = deque([("row", start)])
        while queue:
            kind, index = queue.popleft()
            if kind == "row":
                if index in rows:
                    continue
                rows.add(index)
                for local_index in candidate_map[index]:
                    queue.append(("local", local_index))
            else:
                if index in locals_seen:
                    continue
                locals_seen.add(index)
                for row in inverse[index]:
                    queue.append(("row", row))
        unseen -= rows
        count, assignment = _component_matchings(candidate_map, rows)
        if count == 1 and assignment is not None:
            matched.update(assignment)
        else:
            reason = ("one-to-one candidate conflict" if count == 0
                      else "multiple valid one-to-one assignments")
            ambiguous.update({row: reason for row in rows})
    return matched, ambiguous


def join_history(export: Any, *, logs_root: str | Path, slots: Iterable[str],
                 timestamp_mode: str = "auto",
                 dashboard_timezone: str | None = None,
                 minute_tolerance: int | None = None
                 ) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (official JSON document, diagnostic report) without guessing."""
    selected = {str(slot).strip() for slot in slots if str(slot).strip()}
    if not selected:
        raise JoinInputError("at least one slot must be selected")
    if isinstance(export, (str, Path)):
        try:
            export = json.loads(Path(export).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise JoinInputError(f"cannot read dashboard export: {exc}") from exc

    dashboard, unresolved = _dashboard_records(
        export, slots=selected, dashboard_timezone=dashboard_timezone)
    local, local_errors = _load_local_records(Path(logs_root), selected)
    duplicate_rows = _duplicate_dashboard_rows(dashboard)

    requested_mode = str(timestamp_mode or "").strip().lower()
    if requested_mode not in {"auto", "first", "completion", "dual"}:
        raise JoinInputError(
            "timestamp_mode must be auto, first, completion, or dual")
    if requested_mode == "auto":
        frozen_mode = _calibrate_timestamp_mode(dashboard, local, duplicate_rows)
        mode_source = "auto-calibrated"
    else:
        frozen_mode = requested_mode
        mode_source = "explicit"
    if minute_tolerance is None:
        tolerance = 1 if frozen_mode == "dual" else 0
    else:
        if isinstance(minute_tolerance, bool):
            raise JoinInputError("minute_tolerance must be a nonnegative integer")
        tolerance = int(minute_tolerance)
        if tolerance < 0 or tolerance != minute_tolerance:
            raise JoinInputError("minute_tolerance must be nonnegative")

    dashboard_by_row = {record.row: record for record in dashboard}
    ambiguous: list[dict[str, Any]] = []
    by_fingerprint: dict[tuple[str, str], list[int]] = defaultdict(list)
    for index, record in enumerate(local):
        by_fingerprint[(record.slot, record.fingerprint)].append(index)
    candidate_map: dict[int, set[int]] = {}
    candidate_counts: dict[int, int] = {}
    for record in dashboard:
        candidates = {
            index for index in by_fingerprint.get(
                (record.slot, record.fingerprint), [])
            if _timestamp_matches(record, local[index], mode=frozen_mode,
                                  tolerance=tolerance)
        }
        candidate_counts[record.row] = len(candidates)
        if record.row in duplicate_rows:
            ambiguous.append({
                "dashboard_row": record.row,
                "slot": record.slot,
                "reason": "duplicate dashboard join evidence (rating excluded)",
                "candidate_count": len(candidates),
            })
            continue
        if not candidates:
            unresolved.append({
                "dashboard_row": record.row,
                "slot": record.slot,
                "reason": "no local candidate satisfies fingerprint and timestamp",
                "candidate_count": 0,
            })
        else:
            candidate_map[record.row] = candidates

    matches, graph_ambiguity = _unique_global_matches(candidate_map)
    for row, reason in sorted(graph_ambiguity.items()):
        record = dashboard_by_row[row]
        ambiguous.append({
            "dashboard_row": row,
            "slot": record.slot,
            "reason": reason,
            "candidate_count": candidate_counts[row],
        })

    games: list[dict[str, Any]] = []
    for row, local_index in sorted(matches.items()):
        dashboard_record = dashboard_by_row[row]
        local_record = local[local_index]
        games.append({
            "slot": dashboard_record.slot,
            "game_id": local_record.game_id,
            "rating_delta": dashboard_record.rating_delta,
            "join_audit": {
                "dashboard_row": row,
                "dashboard_timestamp_raw": dashboard_record.timestamp_raw,
                "dashboard_minute_utc": dashboard_record.minute_utc,
                "timestamp_mode": frozen_mode,
                "timestamp_mode_source": mode_source,
                "minute_tolerance": tolerance,
                "local_first_ts": local_record.first_ts,
                "local_completion_ts": local_record.completion_ts,
                "fingerprint_sha256": dashboard_record.fingerprint,
                "candidate_count": candidate_counts[row],
                "match_rule": f"exact-modal-fingerprint+{frozen_mode}-minute/v1",
            },
        })

    document = {"_schema": OUTPUT_SCHEMA, "games": games}
    report = {
        "_schema": REPORT_SCHEMA,
        "timestamp_mode": frozen_mode,
        "timestamp_mode_source": mode_source,
        "minute_tolerance": tolerance,
        "matched": len(games),
        "unresolved": sorted(unresolved, key=lambda issue: issue["dashboard_row"]),
        "ambiguous": sorted(ambiguous, key=lambda issue: issue["dashboard_row"]),
        "local_errors": local_errors,
    }
    return document, report


def _parse_slots(values: Sequence[str]) -> list[str]:
    slots: list[str] = []
    for value in values:
        slots.extend(part.strip() for part in value.split(",") if part.strip())
    return slots


def _write_output(document: Mapping[str, Any], output: str) -> None:
    rendered = json.dumps(document, indent=2, sort_keys=False) + "\n"
    if output == "-":
        sys.stdout.write(rendered)
    else:
        Path(output).write_text(rendered, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dashboard_json", help="dashboard-export JSON file")
    parser.add_argument("--logs-root", default="logs",
                        help="root containing SLOT/games/*.json")
    parser.add_argument("--slots", action="append", required=True,
                        help="selected local slot, repeat or comma-separate")
    parser.add_argument("--timestamp-mode", default="auto",
                        choices=("auto", "first", "completion", "dual"),
                        help="dashboard timestamp semantics (default: calibrate)")
    parser.add_argument("--minute-tolerance", type=int, default=None,
                        help="minute distance allowed (dual defaults to 1; others 0)")
    parser.add_argument("--dashboard-timezone", default=None,
                        help="IANA timezone required for naive ISO timestamps")
    parser.add_argument("--output", default="-", help="output JSON path or -")
    args = parser.parse_args(argv)
    try:
        document, report = join_history(
            args.dashboard_json,
            logs_root=args.logs_root,
            slots=_parse_slots(args.slots),
            timestamp_mode=args.timestamp_mode,
            dashboard_timezone=args.dashboard_timezone,
            minute_tolerance=args.minute_tolerance,
        )
        _write_output(document, args.output)
    except JoinInputError as exc:
        print(f"join failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True), file=sys.stderr)
    return (1 if report["unresolved"] or report["ambiguous"]
            or report["local_errors"] else 0)


if __name__ == "__main__":
    raise SystemExit(main())
