#!/usr/bin/env python3
"""Build an auditable, incremental dossier of high-priority GLEE opponents.

This is an observation-only sidecar.  It never imports strategy code, reads API
keys, changes a fleet overlay, or touches a running process.  Canonical
``logs/<slot>/games/*.json`` files provide completed and unresolved histories;
the append-only turn streams provide low-latency records for games whose
canonical file has not arrived yet.

The output deliberately separates two claims:

* a disclosed-name encounter is direct identity evidence;
* a hidden-name encounter can at most be a *tactic match*.  Similar actions do
  not identify an agent because copied policies, common templates, private
  values, and our own preceding actions can all produce the same wire path.

Usage::

    .venv/bin/python scripts/opponent_intelligence.py refresh
    .venv/bin/python scripts/opponent_intelligence.py refresh --full-rebuild

Generated data lives in ``opponent_intelligence/`` (gitignored):

* ``opponent_intelligence.sqlite3`` -- indexed metadata, features, exact moves,
  and tactic-match evidence;
* ``INDEX.md`` -- fleet-wide summary;
* ``<opponent>/DOSSIER.md`` -- every disclosed encounter and opponent move;
* ``<opponent>/named_encounters.jsonl`` -- complete canonical source records;
* ``<opponent>/opponent_moves.jsonl`` -- one normalized opponent action per row;
* ``<opponent>/tactic_matches.jsonl`` -- hidden/name-disclosed lookalikes with
  calibration evidence and the exact observed action path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import statistics
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence


REPO = Path(__file__).resolve().parent.parent
DEFAULT_LOGS = REPO / "logs"
DEFAULT_OUTPUT = REPO / "opponent_intelligence"
PHYSICAL_SLOTS = ("champion", "hardliner", "conceder", "randomized", "composite")
SLOT_LABELS = {
    "champion": "Test 1",
    "hardliner": "Test 2",
    "conceder": "Test 3",
    "randomized": "Test 4",
    "composite": "Agent 5",
}
TARGET_DISPLAY = {
    "grok 4.6": "grok 4.6",
    "athena": "Athena",
    "gill bates": "gill bates",
}
TARGET_SLUG = {
    "grok 4.6": "grok-4-6",
    "athena": "athena",
    "gill bates": "gill-bates",
}
SCHEMA_VERSION = 1
NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\$?\d[\d,]*(?:\.\d+)?%?")
SPACE_RE = re.compile(r"\s+")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _safe_json(value: Any) -> str:
    try:
        return _json(value)
    except (TypeError, ValueError):
        return _json(str(value))


def normalize_name(value: Any) -> str:
    return SPACE_RE.sub(" ", str(value or "").strip()).casefold()


def normalize_message(value: Any) -> str:
    text = SPACE_RE.sub(" ", str(value or "").strip()).casefold()
    return NUMBER_RE.sub("<num>", text)


def message_class(value: Any) -> str:
    text = normalize_message(value)
    if not text:
        return "empty"
    if text in {"yes", "true", "buy"}:
        return "positive"
    if text in {"no", "false", "pass"}:
        return "negative"
    negative = ("not recommend", "do not recommend", "don't recommend", "avoid", "not worth")
    if any(token in text for token in negative):
        return "negative"
    if any(token in text for token in ("recommend", "worth", "buy", "good")):
        return "positive"
    return "other"


def _float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _round_number(value: Any, digits: int = 6) -> float | None:
    number = _float(value)
    return round(number, digits) if number is not None else None


def _player_other(player: str | None) -> str | None:
    if player == "player_1":
        return "player_2"
    if player == "player_2":
        return "player_1"
    return None


def _decision(value: Any) -> str:
    text = normalize_name(value).replace("_", "").replace(" ", "")
    if text in {"accept", "accepted", "acceptoffer", "yes"}:
        return "accept"
    if text in {"reject", "rejected", "rejectoffer", "no"}:
        return "reject"
    if text in {"walkaway", "walk", "leave", "left"}:
        return "walkaway"
    return text or "unknown"


def _bool_token(value: Any) -> str:
    if value is True:
        return "1"
    if value is False:
        return "0"
    return "?"


def _value_token(value: Any) -> str:
    number = _float(value)
    if number is None:
        return "?"
    return f"{number:.8g}"


def _horizon(config: Mapping[str, Any], family: str) -> str:
    if family == "persuasion":
        return str(config.get("total_rounds") or "?")
    known = config.get("horizon_known")
    if known is False:
        return "unknown"
    rounds = config.get("max_rounds")
    return str(rounds) if rounds is not None else ("unknown" if known is False else "?")


def opponent_role(game: Mapping[str, Any]) -> str:
    config = game.get("config") or {}
    them = _player_other(game.get("your_player"))
    role = config.get(f"{them}_role") if them else None
    if role:
        return str(role).lower()
    family = game.get("game_family")
    if family == "persuasion":
        return "seller" if them == "player_1" else "buyer"
    if family == "negotiation":
        return "seller" if them == "player_1" else "buyer"
    return them or "unknown"


def public_cells(game: Mapping[str, Any]) -> tuple[str, str]:
    """Return an exact public-configuration cell and a robust fallback cell."""
    family = str(game.get("game_family") or "unknown")
    config = game.get("config") or {}
    me = game.get("your_player")
    them = _player_other(me)
    role = opponent_role(game)
    messages = _bool_token(config.get("messages_allowed"))
    horizon = _horizon(config, family)

    if family == "bargaining":
        delta_me = config.get("delta_1" if me == "player_1" else "delta_2")
        delta_opponent = config.get("delta_2" if me == "player_1" else "delta_1")
        exact = "|".join((
            family,
            f"opp={them or '?'}",
            f"h={horizon}",
            f"hk={_bool_token(config.get('horizon_known'))}",
            f"msg={messages}",
            f"dme={_value_token(delta_me)}",
            f"dopp={_value_token(delta_opponent)}",
            f"first={config.get('proposer') or '?'}",
        ))
        coarse = "|".join((family, f"opp={them or '?'}", f"h={horizon}", f"msg={messages}"))
        return exact, coarse

    if family == "negotiation":
        info = "complete" if config.get("complete_information") else "hidden"
        exact = "|".join((family, f"role={role}", f"h={horizon}", f"info={info}", f"msg={messages}"))
        coarse = "|".join((family, f"role={role}", f"h={horizon}", f"info={info}"))
        return exact, coarse

    if family == "persuasion":
        price = _float(config.get("product_price")) or 1.0
        v_ratio = (_float(config.get("v")) or 0.0) / price
        u_ratio = (_float(config.get("u")) or 0.0) / price
        exact = "|".join((
            family,
            f"role={role}",
            f"mode={config.get('seller_message_type') or '?'}",
            f"p={_value_token(config.get('p'))}",
            f"v/P={v_ratio:.4g}",
            f"u/P={u_ratio:.4g}",
            f"seller_knows={_bool_token(config.get('is_seller_know_cv'))}",
        ))
        coarse = "|".join((family, f"role={role}", f"mode={config.get('seller_message_type') or '?'}", f"p={_value_token(config.get('p'))}"))
        return exact, coarse

    return family, family


def _my_reference_value(game: Mapping[str, Any]) -> float | None:
    config = game.get("config") or {}
    me = game.get("your_player")
    if me:
        value = _float(config.get(f"{me}_value"))
        if value and value > 0:
            return value
    return None


def extract_opponent_moves(game: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Reconstruct each opponent action once from a canonical final history."""
    family = game.get("game_family")
    config = game.get("config") or {}
    history = game.get("history") or []
    me = game.get("your_player")
    them = _player_other(me)
    if not me or not them:
        return []
    moves: list[dict[str, Any]] = []
    money = _float(config.get("money_to_divide"))
    reference = _my_reference_value(game)

    def add(
        row: Mapping[str, Any],
        move_type: str,
        action: Mapping[str, Any],
        context: Mapping[str, Any],
        normalized: Mapping[str, Any],
        message: Any = "",
        response_time_ms: Any = None,
    ) -> None:
        moves.append({
            "ordinal": len(moves) + 1,
            "round": int(row.get("round") or 0),
            "actor": them,
            "move_type": move_type,
            "action": dict(action),
            "context": dict(context),
            "normalized": {k: _round_number(v) if _float(v) is not None else v for k, v in normalized.items()},
            "message": str(message or ""),
            "message_template": normalize_message(message),
            "message_class": message_class(message),
            "response_time_ms": _round_number(response_time_ms, 3),
        })

    for raw in history:
        if not isinstance(raw, Mapping):
            continue
        row = dict(raw)
        offer = row.get("offer") or {}

        if family == "bargaining":
            proposer = row.get("proposer") or offer.get("proposer")
            if proposer == them:
                their_gain = _float(offer.get(f"{them}_gain"))
                our_gain = _float(offer.get(f"{me}_gain"))
                norm = {
                    "opponent_own_share": their_gain / money if money and their_gain is not None else None,
                    "our_share": our_gain / money if money and our_gain is not None else None,
                }
                add(row, "offer", offer, {"our_decision": row.get("decision")}, norm, offer.get("message"))
            if proposer == me and row.get("decision") is not None:
                offered = _float(offer.get(f"{them}_gain"))
                add(
                    row,
                    "decision",
                    {"decision": _decision(row.get("decision"))},
                    {"our_offer": offer},
                    {"share_offered_to_opponent": offered / money if money and offered is not None else None},
                    response_time_ms=row.get("response_time_ms"),
                )
            continue

        if family == "negotiation":
            proposer = offer.get("from_player")
            if proposer == them:
                price = _float(offer.get("price"))
                add(
                    row,
                    "offer",
                    offer,
                    {"our_decision": row.get("decision"), "decided_by": row.get("decided_by")},
                    {"price_over_our_value": price / reference if reference and price is not None else None},
                    offer.get("message"),
                )
            decided_by = row.get("decided_by")
            if row.get("decision") is not None and (decided_by == them or (not decided_by and proposer == me)):
                price = _float(offer.get("price"))
                add(
                    row,
                    "decision",
                    {"decision": _decision(row.get("decision"))},
                    {"our_offer": offer},
                    {"price_over_our_value": price / reference if reference and price is not None else None},
                    response_time_ms=row.get("response_time_ms"),
                )
            continue

        if family == "persuasion":
            role = opponent_role(game)
            if role == "seller" and row.get("seller_message") is not None:
                msg = row.get("seller_message")
                add(
                    row,
                    "seller_message",
                    {"seller_message": msg},
                    {
                        "our_buyer_decision": row.get("buyer_decision"),
                        "bought": row.get("bought"),
                        "quality_if_revealed": row.get("quality"),
                    },
                    {
                        "positive_signal": 1.0 if message_class(msg) == "positive" else 0.0,
                        "negative_signal": 1.0 if message_class(msg) == "negative" else 0.0,
                    },
                    msg,
                )
            elif role == "buyer" and row.get("buyer_decision") is not None:
                decision = _decision(row.get("buyer_decision"))
                add(
                    row,
                    "buyer_decision",
                    {"decision": decision},
                    {
                        "our_seller_message": row.get("seller_message"),
                        "quality": row.get("quality"),
                    },
                    {
                        "buy": 1.0 if decision == "accept" else 0.0,
                        "seller_signal_positive": 1.0 if message_class(row.get("seller_message")) == "positive" else 0.0,
                    },
                    response_time_ms=row.get("response_time_ms"),
                )

    result = game.get("result") or {}
    if result.get("walked_away_by") == them and not any(
        move["move_type"] == "decision" and move["action"].get("decision") == "walkaway"
        for move in moves
    ):
        add(
            {"round": game.get("rounds_played") or 0},
            "terminal_walkaway",
            {"decision": "walkaway"},
            {"result": result},
            {},
        )
    return moves


def _mean(values: Sequence[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _stdev(values: Sequence[float]) -> float | None:
    return statistics.pstdev(values) if len(values) >= 2 else (0.0 if values else None)


def build_features(moves: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    offers: list[float] = []
    decisions: list[str] = []
    response_ms: list[float] = []
    positive = negative = buys = buyer_decision_count = 0
    templates: list[str] = []
    tokens: list[str] = []

    for move in moves:
        normalized = move.get("normalized") or {}
        level = normalized.get("opponent_own_share")
        if level is None:
            level = normalized.get("price_over_our_value")
        number = _float(level)
        if number is not None:
            offers.append(number)
        action = move.get("action") or {}
        if move.get("move_type") in {"decision", "buyer_decision", "terminal_walkaway"}:
            decision = _decision(action.get("decision"))
            decisions.append(decision)
            if move.get("move_type") == "buyer_decision":
                buyer_decision_count += 1
                if decision == "accept":
                    buys += 1
        klass = move.get("message_class")
        positive += int(klass == "positive")
        negative += int(klass == "negative")
        template = str(move.get("message_template") or "")
        if template:
            templates.append(template)
        latency = _float(move.get("response_time_ms"))
        if latency is not None:
            response_ms.append(latency)
        tokens.append(action_token(move))

    features: dict[str, float] = {
        "coverage_moves": min(len(moves), 20) / 20.0,
        "offer_count_scaled": min(len(offers), 12) / 12.0,
        "decision_count_scaled": min(len(decisions), 12) / 12.0,
    }
    if offers:
        features.update({
            "first_level": offers[0],
            "last_level": offers[-1],
            "mean_level": statistics.fmean(offers),
            "min_level": min(offers),
            "max_level": max(offers),
            "level_std": _stdev(offers) or 0.0,
            "level_slope": (offers[-1] - offers[0]) / max(1, len(offers) - 1),
            "level_repeat_rate": sum(
                abs(a - b) <= 0.001 for a, b in zip(offers, offers[1:])
            ) / max(1, len(offers) - 1),
        })
    if decisions:
        features.update({
            "accept_rate": decisions.count("accept") / len(decisions),
            "reject_rate": decisions.count("reject") / len(decisions),
            "walk_rate": decisions.count("walkaway") / len(decisions),
        })
    if moves:
        features["positive_signal_rate"] = positive / len(moves)
        features["negative_signal_rate"] = negative / len(moves)
    if buyer_decision_count:
        features["buy_rate"] = buys / buyer_decision_count
    if templates:
        features["template_diversity"] = len(set(templates)) / len(templates)
    if response_ms:
        # Log scale prevents one network stall from dominating tactic distance.
        features["mean_log_response_ms"] = statistics.fmean(math.log1p(v) for v in response_ms) / 10.0
    features["wire_repeat_rate"] = (
        sum(a == b for a, b in zip(tokens, tokens[1:])) / max(1, len(tokens) - 1)
        if tokens else 0.0
    )
    return {key: round(value, 8) for key, value in features.items() if math.isfinite(value)}


def action_token(move: Mapping[str, Any]) -> str:
    move_type = str(move.get("move_type") or "unknown")
    normalized = move.get("normalized") or {}
    action = move.get("action") or {}
    if move_type == "offer":
        level = normalized.get("opponent_own_share")
        if level is None:
            level = normalized.get("price_over_our_value")
        number = _float(level)
        return f"offer:{_value_token(round(number, 3) if number is not None else None)}:{move.get('message_class') or 'empty'}"
    if move_type == "buyer_decision":
        # A buyer's accept/reject bit is only meaningful conditional on the
        # signal it answered. Without this context, common paths such as
        # "accept 12, reject 8" falsely look agent-specific.
        signal = message_class((move.get("context") or {}).get("our_seller_message"))
        return f"buyer_decision:{_decision(action.get('decision'))}:{signal}"
    if move_type in {"decision", "terminal_walkaway"}:
        context_level = normalized.get("share_offered_to_opponent")
        if context_level is None:
            context_level = normalized.get("price_over_our_value")
        number = _float(context_level)
        return (
            f"{move_type}:{_decision(action.get('decision'))}:"
            f"{_value_token(round(number, 3) if number is not None else None)}"
        )
    if move_type == "seller_message":
        return f"seller_message:{move.get('message_class') or 'other'}"
    return f"{move_type}:{_safe_json(action)}"


def _signature(cell: str, tokens: Sequence[str]) -> str:
    body = cell + "\x1f" + "\x1e".join(tokens)
    return hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()


def _timestamps(game: Mapping[str, Any]) -> tuple[float | None, float | None]:
    values = [
        _float(turn.get("ts"))
        for turn in (game.get("our_turns") or [])
        if isinstance(turn, Mapping) and _float(turn.get("ts")) is not None
    ]
    return (min(values), max(values)) if values else (None, None)


@dataclass(frozen=True)
class IndexedGame:
    encounter_id: str
    slot: str
    game_id: str
    source_path: str
    source_size: int
    source_mtime_ns: int
    opponent_type: str
    opponent_name: str
    opponent_name_norm: str
    target_key: str
    family: str
    status: str
    your_player: str
    opponent_role: str
    start_ts: float | None
    end_ts: float | None
    rounds_played: int
    public_cell: str
    coarse_cell: str
    outcome: str
    our_payoff: float | None
    opponent_payoff: float | None
    n_moves: int
    features_json: str
    tokens_json: str
    prefix_signature: str
    wire_signature: str
    templates_json: str
    config_json: str
    result_json: str


def index_game(slot: str, path: Path, game: Mapping[str, Any], stat: os.stat_result) -> tuple[IndexedGame, list[dict[str, Any]]]:
    game_id = str(game.get("game_id") or path.stem)
    opponent = game.get("opponent") or {}
    name = str(opponent.get("name") or "") if isinstance(opponent, Mapping) else ""
    norm = normalize_name(name)
    target = norm if norm in TARGET_DISPLAY else ""
    moves = extract_opponent_moves(game)
    cell, coarse = public_cells(game)
    tokens = [action_token(move) for move in moves]
    start_ts, end_ts = _timestamps(game)
    result = game.get("result") or {}
    templates = sorted({str(move.get("message_template") or "") for move in moves if move.get("message_template")})
    row = IndexedGame(
        encounter_id=f"{slot}:{game_id}",
        slot=slot,
        game_id=game_id,
        source_path=str(path),
        source_size=stat.st_size,
        source_mtime_ns=stat.st_mtime_ns,
        opponent_type=str(opponent.get("type") or "") if isinstance(opponent, Mapping) else "",
        opponent_name=name,
        opponent_name_norm=norm,
        target_key=target,
        family=str(game.get("game_family") or "unknown"),
        status=str(game.get("status") or "unknown"),
        your_player=str(game.get("your_player") or ""),
        opponent_role=opponent_role(game),
        start_ts=start_ts,
        end_ts=end_ts,
        rounds_played=int(game.get("rounds_played") or len(game.get("history") or [])),
        public_cell=cell,
        coarse_cell=coarse,
        outcome=str(result.get("outcome") or game.get("status") or "unknown"),
        our_payoff=_float(game.get("our_payoff")),
        opponent_payoff=_float(game.get("opponent_payoff")),
        n_moves=len(moves),
        features_json=_json(build_features(moves)),
        tokens_json=_json(tokens),
        prefix_signature=_signature(cell, tokens[: min(3, len(tokens))]),
        wire_signature=_signature(cell, tokens),
        templates_json=_json(templates),
        config_json=_safe_json(game.get("config") or {}),
        result_json=_safe_json(result),
    )
    return row, moves


def connect_db(output: Path) -> sqlite3.Connection:
    output.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(output / "opponent_intelligence.sqlite3")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS games (
            encounter_id TEXT PRIMARY KEY,
            slot TEXT NOT NULL,
            game_id TEXT NOT NULL,
            source_path TEXT NOT NULL UNIQUE,
            source_size INTEGER NOT NULL,
            source_mtime_ns INTEGER NOT NULL,
            opponent_type TEXT NOT NULL,
            opponent_name TEXT NOT NULL,
            opponent_name_norm TEXT NOT NULL,
            target_key TEXT NOT NULL,
            family TEXT NOT NULL,
            status TEXT NOT NULL,
            your_player TEXT NOT NULL,
            opponent_role TEXT NOT NULL,
            start_ts REAL,
            end_ts REAL,
            rounds_played INTEGER NOT NULL,
            public_cell TEXT NOT NULL,
            coarse_cell TEXT NOT NULL,
            outcome TEXT NOT NULL,
            our_payoff REAL,
            opponent_payoff REAL,
            n_moves INTEGER NOT NULL,
            features_json TEXT NOT NULL,
            tokens_json TEXT NOT NULL,
            prefix_signature TEXT NOT NULL,
            wire_signature TEXT NOT NULL,
            templates_json TEXT NOT NULL,
            config_json TEXT NOT NULL,
            result_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS games_target_idx ON games(target_key, start_ts);
        CREATE INDEX IF NOT EXISTS games_name_idx ON games(opponent_name_norm, family);
        CREATE INDEX IF NOT EXISTS games_cell_idx ON games(family, public_cell, coarse_cell);
        CREATE TABLE IF NOT EXISTS target_moves (
            encounter_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            round_no INTEGER NOT NULL,
            move_type TEXT NOT NULL,
            action_json TEXT NOT NULL,
            context_json TEXT NOT NULL,
            normalized_json TEXT NOT NULL,
            message TEXT NOT NULL,
            message_template TEXT NOT NULL,
            message_class TEXT NOT NULL,
            response_time_ms REAL,
            PRIMARY KEY(encounter_id, ordinal),
            FOREIGN KEY(encounter_id) REFERENCES games(encounter_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS streams (
            source_path TEXT PRIMARY KEY,
            inode INTEGER NOT NULL,
            offset INTEGER NOT NULL,
            updated_ts REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS live_target_turns (
            turn_id TEXT PRIMARY KEY,
            slot TEXT NOT NULL,
            game_id TEXT NOT NULL,
            target_key TEXT NOT NULL,
            ts REAL,
            round_no INTEGER,
            phase TEXT NOT NULL,
            record_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS live_target_game_idx ON live_target_turns(slot, game_id, ts);
        CREATE TABLE IF NOT EXISTS tactic_matches (
            encounter_id TEXT NOT NULL,
            target_key TEXT NOT NULL,
            disclosure TEXT NOT NULL,
            label TEXT NOT NULL,
            score REAL NOT NULL,
            fit_percentile REAL,
            specificity REAL,
            distance REAL,
            model_scope TEXT NOT NULL,
            target_n INTEGER NOT NULL,
            non_target_n INTEGER NOT NULL,
            exact_target_support INTEGER NOT NULL,
            exact_other_support INTEGER NOT NULL,
            reasons_json TEXT NOT NULL,
            PRIMARY KEY(encounter_id, target_key)
        );
        """
    )
    version = db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    if version and int(version[0]) != SCHEMA_VERSION:
        raise RuntimeError(
            f"database schema {version[0]} is incompatible with builder schema {SCHEMA_VERSION}; "
            "rerun with --full-rebuild"
        )
    db.execute(
        "INSERT INTO meta(key,value) VALUES('schema_version',?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(SCHEMA_VERSION),),
    )
    db.commit()
    return db


GAME_COLUMNS = tuple(field.name for field in IndexedGame.__dataclass_fields__.values())


def _upsert_game(db: sqlite3.Connection, row: IndexedGame, moves: Sequence[Mapping[str, Any]]) -> None:
    placeholders = ",".join("?" for _ in GAME_COLUMNS)
    updates = ",".join(f"{name}=excluded.{name}" for name in GAME_COLUMNS if name != "encounter_id")
    db.execute(
        f"INSERT INTO games({','.join(GAME_COLUMNS)}) VALUES({placeholders}) "
        f"ON CONFLICT(encounter_id) DO UPDATE SET {updates}",
        tuple(getattr(row, name) for name in GAME_COLUMNS),
    )
    db.execute("DELETE FROM target_moves WHERE encounter_id=?", (row.encounter_id,))
    if row.target_key:
        db.executemany(
            """
            INSERT INTO target_moves(
                encounter_id,ordinal,round_no,move_type,action_json,context_json,
                normalized_json,message,message_template,message_class,response_time_ms
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            [
                (
                    row.encounter_id,
                    int(move["ordinal"]),
                    int(move["round"]),
                    str(move["move_type"]),
                    _safe_json(move.get("action") or {}),
                    _safe_json(move.get("context") or {}),
                    _safe_json(move.get("normalized") or {}),
                    str(move.get("message") or ""),
                    str(move.get("message_template") or ""),
                    str(move.get("message_class") or ""),
                    _float(move.get("response_time_ms")),
                )
                for move in moves
            ],
        )


def scan_canonical_games(
    db: sqlite3.Connection,
    logs_root: Path,
    slots: Sequence[str],
    archive_start_ts: float,
) -> dict[str, int]:
    cached = {
        row["source_path"]: (row["source_size"], row["source_mtime_ns"], row["target_key"])
        for row in db.execute("SELECT source_path,source_size,source_mtime_ns,target_key FROM games")
    }
    counts = Counter()
    pending = 0
    for slot in slots:
        game_dir = logs_root / slot / "games"
        if not game_dir.is_dir():
            continue
        for path in game_dir.glob("*.json"):
            counts["files_seen"] += 1
            try:
                stat = path.stat()
            except OSError:
                counts["stat_errors"] += 1
                continue
            # A canonical file cannot contain an event newer than its own last
            # write.  This cheap cutoff avoids parsing hundreds of thousands of
            # historical JSON files when the archive has a recent fixed start.
            if stat.st_mtime < archive_start_ts:
                counts["before_archive_start"] += 1
                continue
            prior = cached.get(str(path))
            if prior and prior[:2] == (stat.st_size, stat.st_mtime_ns):
                counts["unchanged"] += 1
                continue
            try:
                with path.open(encoding="utf-8", errors="replace") as handle:
                    game = json.load(handle)
                if not isinstance(game, Mapping):
                    raise ValueError("game root is not an object")
                row, moves = index_game(slot, path, game, stat)
                event_ts = row.end_ts or row.start_ts or stat.st_mtime
                if event_ts < archive_start_ts:
                    db.execute("DELETE FROM games WHERE encounter_id=?", (row.encounter_id,))
                    counts["before_archive_start"] += 1
                    continue
                _upsert_game(db, row, moves)
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                counts["parse_errors"] += 1
                continue
            counts["updated"] += 1
            if row.target_key:
                counts["updated_targets"] += 1
            pending += 1
            if pending >= 750:
                db.commit()
                pending = 0
    db.commit()
    return dict(counts)


def scan_live_turns(
    db: sqlite3.Connection,
    logs_root: Path,
    slots: Sequence[str],
    initial_tail_mb: int,
    archive_start_ts: float,
) -> dict[str, int]:
    counts = Counter()
    tail_bytes = max(1, initial_tail_mb) * 1024 * 1024
    for slot in slots:
        path = logs_root / slot / "turns.jsonl"
        try:
            stat = path.stat()
        except OSError:
            continue
        saved = db.execute(
            "SELECT inode,offset FROM streams WHERE source_path=?", (str(path),)
        ).fetchone()
        if saved and saved["inode"] == stat.st_ino and 0 <= saved["offset"] <= stat.st_size:
            start = int(saved["offset"])
        else:
            start = max(0, stat.st_size - tail_bytes)
        with path.open("rb") as handle:
            handle.seek(start)
            if start:
                handle.readline()  # discard a partial first record
            committed_offset = handle.tell()
            while True:
                line_start = handle.tell()
                raw = handle.readline()
                if not raw:
                    break
                if not raw.endswith(b"\n"):
                    handle.seek(line_start)
                    break
                committed_offset = handle.tell()
                counts["turn_lines"] += 1
                try:
                    record = json.loads(raw)
                except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
                    counts["turn_parse_errors"] += 1
                    continue
                opponent = record.get("opponent") or {}
                name = normalize_name(opponent.get("name") if isinstance(opponent, Mapping) else "")
                if name not in TARGET_DISPLAY:
                    continue
                record_ts = _float(record.get("ts"))
                # A missing timestamp cannot be proven to satisfy the user's
                # fixed archive boundary, so fail closed instead of importing
                # an unverifiable old turn from the initial stream tail.
                if record_ts is None:
                    counts["target_turns_missing_ts"] += 1
                    continue
                if record_ts < archive_start_ts:
                    counts["target_turns_before_archive_start"] += 1
                    continue
                game_id = str(record.get("game_id") or "")
                if not game_id:
                    continue
                turn_id = hashlib.sha256(
                    f"{slot}|{game_id}|{record.get('ts')}|{record.get('round')}|{record.get('phase')}".encode()
                ).hexdigest()
                db.execute(
                    """
                    INSERT INTO live_target_turns(
                        turn_id,slot,game_id,target_key,ts,round_no,phase,record_json
                    ) VALUES(?,?,?,?,?,?,?,?)
                    ON CONFLICT(turn_id) DO UPDATE SET record_json=excluded.record_json
                    """,
                    (
                        turn_id,
                        slot,
                        game_id,
                        name,
                        record_ts,
                        int(record.get("round") or 0),
                        str(record.get("phase") or ""),
                        _safe_json(record),
                    ),
                )
                counts["target_turns"] += 1
        db.execute(
            """
            INSERT INTO streams(source_path,inode,offset,updated_ts) VALUES(?,?,?,?)
            ON CONFLICT(source_path) DO UPDATE SET
                inode=excluded.inode,offset=excluded.offset,updated_ts=excluded.updated_ts
            """,
            (str(path), stat.st_ino, committed_offset, time.time()),
        )
    db.commit()
    return dict(counts)


@dataclass
class MatchModel:
    target: str
    scope: str
    group: str
    keys: tuple[str, ...]
    center: dict[str, float]
    scale: dict[str, float]
    target_distances: list[float]
    other_distances: list[float]

    @property
    def target_n(self) -> int:
        return len(self.target_distances)

    @property
    def non_target_n(self) -> int:
        return len(self.other_distances)


FEATURE_FLOORS = defaultdict(
    lambda: 0.06,
    {
        "coverage_moves": 0.12,
        "offer_count_scaled": 0.12,
        "decision_count_scaled": 0.12,
        "mean_log_response_ms": 0.08,
        "level_slope": 0.025,
        "level_std": 0.035,
    },
)


def _median(values: Sequence[float]) -> float:
    return float(statistics.median(values))


def _distance(features: Mapping[str, float], keys: Sequence[str], center: Mapping[str, float], scale: Mapping[str, float]) -> float | None:
    pieces = []
    for key in keys:
        value = _float(features.get(key))
        if value is None:
            continue
        pieces.append(min(6.0, abs(value - center[key]) / scale[key]))
    if len(pieces) < min(5, len(keys)):
        return None
    return statistics.fmean(pieces)


def _make_model(
    target: str,
    scope: str,
    group: str,
    target_features: Sequence[Mapping[str, float]],
    other_features: Sequence[Mapping[str, float]],
) -> MatchModel | None:
    if len(target_features) < 5:
        return None
    all_keys = sorted({key for row in target_features for key in row})
    keys = tuple(
        key
        for key in all_keys
        if sum(_float(row.get(key)) is not None for row in target_features) >= max(4, math.ceil(0.65 * len(target_features)))
    )
    if len(keys) < 5:
        return None
    center: dict[str, float] = {}
    scale: dict[str, float] = {}
    for key in keys:
        values = [_float(row.get(key)) for row in target_features]
        clean = [value for value in values if value is not None]
        mid = _median(clean)
        mad = _median([abs(value - mid) for value in clean])
        center[key] = mid
        scale[key] = max(FEATURE_FLOORS[key], 1.4826 * mad)
    target_distances = [
        distance
        for row in target_features
        if (distance := _distance(row, keys, center, scale)) is not None
    ]
    other_distances = [
        distance
        for row in other_features
        if (distance := _distance(row, keys, center, scale)) is not None
    ]
    if len(target_distances) < 5:
        return None
    return MatchModel(target, scope, group, keys, center, scale, target_distances, other_distances)


def _percent_at_or_above(values: Sequence[float], value: float) -> float:
    return sum(candidate >= value for candidate in values) / len(values) if values else 0.0


def recompute_tactic_matches(db: sqlite3.Connection) -> dict[str, int]:
    """Match action paths, while keeping tactic similarity distinct from identity."""
    rows = list(
        db.execute(
            """
            SELECT encounter_id,opponent_type,opponent_name,opponent_name_norm,target_key,
                   family,opponent_role,public_cell,coarse_cell,n_moves,features_json,
                   tokens_json,prefix_signature
            FROM games
            """
        )
    )
    parsed = []
    for row in rows:
        item = dict(row)
        item["features"] = json.loads(item.pop("features_json"))
        item["tokens"] = json.loads(item.pop("tokens_json"))
        parsed.append(item)

    by_exact: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_coarse: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    prefix_named: Counter[tuple[str, str]] = Counter()
    prefix_target: Counter[tuple[str, str, str]] = Counter()
    for item in parsed:
        by_exact[(item["public_cell"], item["target_key"])].append(item)
        by_coarse[(item["coarse_cell"], item["target_key"])].append(item)
        if item["opponent_name_norm"] and item["n_moves"] >= 2:
            prefix_named[(item["public_cell"], item["prefix_signature"])] += 1
            if item["target_key"]:
                prefix_target[(item["target_key"], item["public_cell"], item["prefix_signature"])] += 1

    models: dict[tuple[str, str, str], MatchModel] = {}
    for target in TARGET_DISPLAY:
        exact_groups = {item["public_cell"] for item in parsed if item["target_key"] == target}
        for group in exact_groups:
            refs = by_exact.get((group, target), [])
            others = [
                item for item in parsed
                if item["public_cell"] == group and item["opponent_name_norm"] and item["target_key"] != target
            ]
            model = _make_model(target, "exact_cell", group, [x["features"] for x in refs], [x["features"] for x in others])
            if model:
                models[(target, "exact_cell", group)] = model
        coarse_groups = {item["coarse_cell"] for item in parsed if item["target_key"] == target}
        for group in coarse_groups:
            refs = by_coarse.get((group, target), [])
            others = [
                item for item in parsed
                if item["coarse_cell"] == group and item["opponent_name_norm"] and item["target_key"] != target
            ]
            model = _make_model(target, "coarse_cell", group, [x["features"] for x in refs], [x["features"] for x in others])
            if model:
                models[(target, "coarse_cell", group)] = model
    db.execute("DELETE FROM tactic_matches")
    inserted = Counter()
    for item in parsed:
        if item["target_key"] or item["n_moves"] < 2:
            continue
        possibilities = []
        for target in TARGET_DISPLAY:
            exact_support = prefix_target[(target, item["public_cell"], item["prefix_signature"])]
            all_named_support = prefix_named[(item["public_cell"], item["prefix_signature"])]
            other_support = max(0, all_named_support - exact_support)
            exact_unique = exact_support >= 2 and other_support == 0
            exact_dominant = exact_support >= 3 and exact_support / max(1, all_named_support) >= 0.8

            model = models.get((target, "exact_cell", item["public_cell"]))
            if model is None or model.non_target_n < 10:
                model = models.get((target, "coarse_cell", item["coarse_cell"]))
            if model is None:
                if not exact_unique and not exact_dominant:
                    continue
                distance = None
                fit = specificity = 1.0
                scope = "exact_wire_prefix"
                target_n = exact_support
                other_n = all_named_support
            else:
                distance = _distance(item["features"], model.keys, model.center, model.scale)
                if distance is None and not (exact_unique or exact_dominant):
                    continue
                fit = _percent_at_or_above(model.target_distances, distance) if distance is not None else 1.0
                specificity = _percent_at_or_above(model.other_distances, distance) if distance is not None else 1.0
                scope = model.scope
                target_n = model.target_n
                other_n = model.non_target_n

            score = 0.55 * fit + 0.45 * specificity
            if exact_unique:
                label = "high: exact target-unique tactic prefix"
                score = max(score, 0.99)
            elif exact_dominant:
                label = "high: target-dominant tactic prefix"
                score = max(score, 0.92)
            elif (
                target_n >= 8
                and other_n >= 20
                and fit >= 0.50
                and specificity >= 0.95
                and score >= 0.75
            ):
                label = "high: calibrated fuzzy tactic match"
            elif (
                target_n >= 5
                and other_n >= 10
                and fit >= 0.25
                and specificity >= 0.85
                and score >= 0.55
            ):
                label = "possible: calibrated fuzzy tactic match"
            else:
                continue
            reasons = {
                "identity_claim": False,
                "interpretation": "same observed tactic, not proof of the same agent",
                "public_cell": item["public_cell"],
                "coarse_cell": item["coarse_cell"],
                "opponent_moves": item["n_moves"],
                "exact_prefix_actions": item["tokens"][:3],
            }
            possibilities.append((score, target, label, fit, specificity, distance, scope, target_n, other_n, exact_support, other_support, reasons))

        if not possibilities:
            continue
        possibilities.sort(reverse=True)
        best = possibilities[0]
        # If two target agents are behaviorally indistinguishable in this cell,
        # retain both as ambiguous tactic matches instead of fabricating identity.
        selected = [best]
        if len(possibilities) > 1 and best[0] - possibilities[1][0] < 0.08:
            selected.append(possibilities[1])
        for match in selected:
            score, target, label, fit, specificity, distance, scope, target_n, other_n, exact_support, other_support, reasons = match
            if len(selected) > 1:
                label = "ambiguous: " + label.split(": ", 1)[-1]
                reasons["ambiguity"] = [candidate[1] for candidate in selected]
            disclosure = "hidden" if not item["opponent_name_norm"] or item["opponent_type"] == "hidden" else "named_other"
            db.execute(
                """
                INSERT INTO tactic_matches(
                    encounter_id,target_key,disclosure,label,score,fit_percentile,specificity,
                    distance,model_scope,target_n,non_target_n,exact_target_support,
                    exact_other_support,reasons_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    item["encounter_id"], target, disclosure, label, round(score, 6),
                    round(fit, 6), round(specificity, 6),
                    round(distance, 6) if distance is not None else None,
                    scope, target_n, other_n, exact_support, other_support, _json(reasons),
                ),
            )
            inserted[(target, disclosure)] += 1
    db.commit()
    summary = {f"{target}:{disclosure}": count for (target, disclosure), count in sorted(inserted.items())}
    summary["models"] = len(models)
    summary["matches"] = sum(inserted.values())
    return summary


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, path)


def _atomic_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    count = 0
    with temp.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(_safe_json(record) + "\n")
            count += 1
    os.replace(temp, path)
    return count


def _read_source(path: str) -> dict[str, Any] | None:
    try:
        with Path(path).open(encoding="utf-8", errors="replace") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else None
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def _time_label(value: Any) -> str:
    ts = _float(value)
    if ts is None:
        return "time unavailable"
    return datetime.fromtimestamp(ts).astimezone().isoformat(timespec="seconds")


def _md(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", "<br>")


def _pretty_action(move: Mapping[str, Any]) -> str:
    action = move.get("action") or {}
    if move.get("move_type") == "offer":
        return f"offer `{_safe_json(action)}`"
    if move.get("move_type") == "seller_message":
        return f"message `{_md(move.get('message'))}`"
    return f"`{_safe_json(action)}`"


def _target_game_records(db: sqlite3.Connection, target: str) -> list[sqlite3.Row]:
    return list(
        db.execute(
            "SELECT * FROM games WHERE target_key=? ORDER BY COALESCE(start_ts,0),slot,game_id",
            (target,),
        )
    )


def export_target(db: sqlite3.Connection, output: Path, target: str) -> dict[str, int]:
    slug = TARGET_SLUG[target]
    folder = output / slug
    rows = _target_game_records(db, target)
    full_records = []
    all_moves = []
    family_counts = Counter()
    slot_counts = Counter()
    outcome_counts = Counter()
    template_counts = Counter()
    for row in rows:
        source = _read_source(row["source_path"])
        if source is None:
            continue
        moves = extract_opponent_moves(source)
        intel = {
            "encounter_id": row["encounter_id"],
            "slot": row["slot"],
            "slot_label": SLOT_LABELS.get(row["slot"], row["slot"]),
            "source_path": row["source_path"],
            "start_time": _time_label(row["start_ts"]),
            "public_cell": row["public_cell"],
            "identity_evidence": "opponent name disclosed by the agent API",
        }
        full_records.append({"intel": intel, "game": source, "opponent_moves": moves})
        family_counts[row["family"]] += 1
        slot_counts[row["slot"]] += 1
        outcome_counts[row["outcome"]] += 1
        for move in moves:
            if move.get("message_template"):
                template_counts[move["message_template"]] += 1
            all_moves.append({
                **intel,
                "game_id": row["game_id"],
                "family": row["family"],
                "outcome": row["outcome"],
                **move,
            })

    _atomic_jsonl(folder / "named_encounters.jsonl", full_records)
    _atomic_jsonl(folder / "opponent_moves.jsonl", all_moves)

    match_rows = list(
        db.execute(
            """
            SELECT m.*,g.* FROM tactic_matches m
            JOIN games g USING(encounter_id)
            WHERE m.target_key=?
            ORDER BY m.score DESC,COALESCE(g.start_ts,0) DESC
            """,
            (target,),
        )
    )
    match_records = []
    for row in match_rows:
        source = _read_source(row["source_path"])
        if source is None:
            continue
        match_records.append({
            "match": {
                "target_tactic": TARGET_DISPLAY[target],
                "identity_claim": False,
                "label": row["label"],
                "score": row["score"],
                "fit_percentile": row["fit_percentile"],
                "specificity": row["specificity"],
                "distance": row["distance"],
                "model_scope": row["model_scope"],
                "target_reference_n": row["target_n"],
                "named_non_target_calibration_n": row["non_target_n"],
                "exact_target_support": row["exact_target_support"],
                "exact_other_support": row["exact_other_support"],
                "reasons": json.loads(row["reasons_json"]),
            },
            "encounter": {
                "encounter_id": row["encounter_id"],
                "slot": row["slot"],
                "game_id": row["game_id"],
                "disclosure": row["disclosure"],
                "disclosed_name": row["opponent_name"],
                "family": row["family"],
                "public_cell": row["public_cell"],
                "start_time": _time_label(row["start_ts"]),
                "outcome": row["outcome"],
                "source_path": row["source_path"],
            },
            "opponent_moves": extract_opponent_moves(source),
        })
    _atomic_jsonl(folder / "tactic_matches.jsonl", match_records)

    canonical_ids = {(row["slot"], row["game_id"]) for row in rows}
    live = [
        json.loads(row["record_json"])
        for row in db.execute(
            "SELECT * FROM live_target_turns WHERE target_key=? ORDER BY COALESCE(ts,0)",
            (target,),
        )
        if (row["slot"], row["game_id"]) not in canonical_ids
    ]
    _atomic_jsonl(folder / "live_unfinalized_turns.jsonl", live)

    archive_start_row = db.execute(
        "SELECT value FROM meta WHERE key='archive_start_ts'"
    ).fetchone()
    archive_start_label = _time_label(archive_start_row[0]) if archive_start_row else "time unavailable"

    lines = [
        f"# {TARGET_DISPLAY[target]} — complete opponent dossier",
        "",
        f"_Refreshed {_time_label(time.time())}. Identity is directly disclosed in the named corpus._",
        "",
        "## Scope",
        "",
        f"- Fixed archive boundary: **{archive_start_label}**; no earlier evidence is included",
        f"- Disclosed-name encounters: **{len(rows):,}**",
        f"- Reconstructed opponent moves: **{len(all_moves):,}**",
        f"- Live turn records awaiting a canonical final: **{len(live):,}**",
        f"- Hidden or differently named tactic-match candidates: **{len(match_records):,}**",
        "- A tactic match is not an identity claim. It means the public action path resembles this target's named reference corpus under the stated calibration.",
        "",
        "### Encounters by family",
        "",
        "| Family | Games |",
        "|---|---:|",
    ]
    lines.extend(f"| {_md(key)} | {value:,} |" for key, value in sorted(family_counts.items()))
    lines.extend(["", "### Encounters by fleet slot", "", "| Slot | Games |", "|---|---:|"])
    lines.extend(
        f"| {SLOT_LABELS.get(key,key)} (`{key}`) | {value:,} |" for key, value in sorted(slot_counts.items())
    )
    lines.extend(["", "### Outcomes (no outcomes dropped)", "", "| Outcome | Games |", "|---|---:|"])
    lines.extend(f"| {_md(key)} | {value:,} |" for key, value in sorted(outcome_counts.items()))
    lines.extend(["", "### Most repeated exact message templates", "", "| Template | Uses |", "|---|---:|"])
    if template_counts:
        lines.extend(f"| {_md(key)} | {value:,} |" for key, value in template_counts.most_common(30))
    else:
        lines.append("| _(none)_ | 0 |")

    lines.extend([
        "",
        "## Tactic-match candidates",
        "",
        "The full evidence, exact action path, calibration counts, and source file for every candidate are in `tactic_matches.jsonl`.",
        "",
        "| Confidence | Disclosure | Family | Score | Fit | Specificity | Game |",
        "|---|---|---|---:|---:|---:|---|",
    ])
    for record in match_records[:250]:
        match = record["match"]
        encounter = record["encounter"]
        lines.append(
            f"| {_md(match['label'])} | {encounter['disclosure']} | {encounter['family']} | "
            f"{match['score']:.3f} | {match['fit_percentile']:.3f} | {match['specificity']:.3f} | "
            f"`{encounter['game_id']}` ({SLOT_LABELS.get(encounter['slot'],encounter['slot'])}) |"
        )
    if not match_records:
        lines.append("| _(none pass the calibrated threshold)_ | — | — | — | — | — | — |")

    lines.extend(["", "## Chronological disclosed-name encounters", ""])
    for row in rows:
        source = _read_source(row["source_path"])
        if source is None:
            continue
        moves = extract_opponent_moves(source)
        config = source.get("config") or {}
        result = source.get("result") or {}
        lines.extend([
            "<details>",
            f"<summary><strong>{_time_label(row['start_ts'])}</strong> · {SLOT_LABELS.get(row['slot'],row['slot'])} · {row['family']} · {row['outcome']} · <code>{row['game_id']}</code></summary>",
            "",
            f"- Our seat: `{row['your_player']}`; opponent role: `{row['opponent_role']}`",
            f"- Status: `{row['status']}`; rounds recorded: `{row['rounds_played']}`",
            f"- Our payoff: `{row['our_payoff']}`; opponent payoff: `{row['opponent_payoff']}`",
            f"- Public comparison cell: `{row['public_cell']}`",
            f"- Canonical source: `{row['source_path']}`",
            f"- Exact config: `{_md(_safe_json(config))}`",
            f"- Exact result: `{_md(_safe_json(result))}`",
            "",
            "| # | Round | Opponent move | Exact normalized evidence | Context: our move/response |",
            "|---:|---:|---|---|---|",
        ])
        for move in moves:
            lines.append(
                f"| {move['ordinal']} | {move['round']} | {_md(_pretty_action(move))} | "
                f"`{_md(_safe_json(move.get('normalized') or {}))}` | "
                f"`{_md(_safe_json(move.get('context') or {}))}` |"
            )
        if not moves:
            lines.append("| — | — | _(no opponent action was exposed before termination)_ | — | — |")
        lines.extend(["", "</details>", ""])
    _atomic_text(folder / "DOSSIER.md", "\n".join(lines) + "\n")
    return {
        "named_games": len(rows),
        "moves": len(all_moves),
        "live_unfinalized_turns": len(live),
        "tactic_matches": len(match_records),
    }


def _active_slots(logs_root: Path) -> list[str]:
    state_path = logs_root / "supervisor.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return []
    return sorted(slot for slot, pid in (state.get("agents") or {}).items() if pid)


def export_index(
    db: sqlite3.Connection,
    output: Path,
    target_summaries: Mapping[str, Mapping[str, int]],
    scan: Mapping[str, int],
    turns: Mapping[str, int],
    match: Mapping[str, int],
    logs_root: Path,
    archive_start_ts: float,
) -> None:
    total = db.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    active = _active_slots(logs_root)
    lines = [
        "# GLEE opponent intelligence archive",
        "",
        f"_Refreshed {_time_label(time.time())}._",
        "",
        "This archive records every disclosed encounter with the three priority agents and reconstructs each opponent action exactly once. Hidden-name similarity is behavioral evidence only; it never upgrades into an identity claim.",
        "",
        f"- Fixed archive boundary: **{_time_label(archive_start_ts)}**; only games active at or after that boundary are retained",
        f"- Canonical games indexed at/after the fixed boundary: **{total:,}**",
        f"- Currently active slots included: **{', '.join(f'{SLOT_LABELS.get(s,s)} (`{s}`)' for s in active) or 'none observed'}**",
        f"- Canonical files new/changed this refresh: **{scan.get('updated',0):,}**",
        f"- New priority-agent live turn rows this refresh: **{turns.get('target_turns',0):,}**",
        f"- Qualified tactic-match rows: **{match.get('matches',0):,}**",
        "",
        "| Target | Named games | Opponent moves | Live unfinalized turns | Tactic matches | Dossier |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for target in TARGET_DISPLAY:
        summary = target_summaries[target]
        slug = TARGET_SLUG[target]
        lines.append(
            f"| {TARGET_DISPLAY[target]} | {summary['named_games']:,} | {summary['moves']:,} | "
            f"{summary['live_unfinalized_turns']:,} | {summary['tactic_matches']:,} | "
            f"[{slug}/DOSSIER.md]({slug}/DOSSIER.md) |"
        )
    lines.extend([
        "",
        "## Evidence rules",
        "",
        "1. Disclosed names are direct identity evidence from the agent API.",
        "2. Histories include agreements, no-deals, walkaways, zeros, timeouts, and unresolved canonical files; nothing is conditioned on success.",
        "3. Repeated history snapshots are deduplicated into one canonical action per actor and round.",
        "4. Hidden/name-different matches require either a target-unique repeated wire prefix in the same public configuration or calibrated feature similarity against named non-target games in the same or coarse public cell. Family/role-only matching is forbidden because it produced generic false positives.",
        "5. Private values remain unobserved in hidden games. Similar behavior can be caused by a copied policy or a different private type, so match files say tactic match, not agent identity.",
        "6. All source paths and exact action/context JSON are retained so every summary can be audited back to a canonical game file.",
        "",
        "## Useful SQLite queries",
        "",
        "```sql",
        "-- Every Grok 4.6 negotiation encounter, including no-deals",
        "SELECT slot, game_id, start_ts, outcome, our_payoff, opponent_payoff",
        "FROM games WHERE target_key='grok 4.6' AND family='negotiation'",
        "ORDER BY start_ts;",
        "",
        "-- Every exact opponent move by Athena",
        "SELECT g.slot,g.game_id,m.round_no,m.move_type,m.action_json,m.context_json",
        "FROM target_moves m JOIN games g USING(encounter_id)",
        "WHERE g.target_key='athena' ORDER BY g.start_ts,m.ordinal;",
        "",
        "-- Hidden games that strongly resemble gill bates' observed tactic",
        "SELECT g.slot,g.game_id,g.family,m.label,m.score,m.reasons_json",
        "FROM tactic_matches m JOIN games g USING(encounter_id)",
        "WHERE m.target_key='gill bates' AND m.disclosure='hidden'",
        "ORDER BY m.score DESC;",
        "```",
    ])
    _atomic_text(output / "INDEX.md", "\n".join(lines) + "\n")


def refresh(
    *,
    logs_root: Path = DEFAULT_LOGS,
    output: Path = DEFAULT_OUTPUT,
    slots: Sequence[str] = PHYSICAL_SLOTS,
    initial_tail_mb: int = 64,
    full_rebuild: bool = False,
    archive_start_ts: float | None = None,
) -> dict[str, Any]:
    output = output.resolve()
    if full_rebuild:
        db_path = output / "opponent_intelligence.sqlite3"
        # The command only removes its one explicit generated database.  It
        # never recursively deletes the output directory or source evidence.
        if db_path.exists():
            db_path.unlink()
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(db_path) + suffix)
            if sidecar.exists():
                sidecar.unlink()
    db = connect_db(output)
    stored_start = db.execute(
        "SELECT value FROM meta WHERE key='archive_start_ts'"
    ).fetchone()
    if archive_start_ts is None:
        archive_start_ts = (
            float(stored_start[0]) if stored_start else time.time() - 6 * 60 * 60
        )
    if not math.isfinite(archive_start_ts) or archive_start_ts < 0:
        raise ValueError("archive_start_ts must be a finite non-negative Unix timestamp")
    if stored_start and abs(float(stored_start[0]) - archive_start_ts) > 1e-6 and not full_rebuild:
        raise ValueError(
            "refusing to move an existing archive boundary without --full-rebuild"
        )
    db.execute(
        "INSERT INTO meta(key,value) VALUES('archive_start_ts',?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(archive_start_ts),),
    )
    # Defensive cleanup matters when a database was interrupted during an old,
    # broader scan.  It also guarantees that generated exports cannot retain a
    # pre-boundary row after the user narrows the archive with a full rebuild.
    db.execute(
        "DELETE FROM games WHERE COALESCE(end_ts,start_ts,source_mtime_ns/1000000000.0) < ?",
        (archive_start_ts,),
    )
    db.execute(
        "DELETE FROM live_target_turns WHERE ts IS NOT NULL AND ts < ?",
        (archive_start_ts,),
    )
    db.commit()
    before = {
        row[0] for row in db.execute("SELECT encounter_id FROM games WHERE target_key!=''")
    }
    scan = scan_canonical_games(db, logs_root, slots, archive_start_ts)
    turns = scan_live_turns(db, logs_root, slots, initial_tail_mb, archive_start_ts)
    match = recompute_tactic_matches(db)
    target_summaries = {
        target: export_target(db, output, target) for target in TARGET_DISPLAY
    }
    after = {
        row[0] for row in db.execute("SELECT encounter_id FROM games WHERE target_key!=''")
    }
    export_index(
        db, output, target_summaries, scan, turns, match, logs_root, archive_start_ts
    )
    summary: dict[str, Any] = {
        "refreshed_at": time.time(),
        "archive_start_ts": archive_start_ts,
        "archive_start": _time_label(archive_start_ts),
        "database": str(output / "opponent_intelligence.sqlite3"),
        "index": str(output / "INDEX.md"),
        "scan": scan,
        "turn_streams": turns,
        "matching": match,
        "new_named_encounters": len(after - before),
        "targets": target_summaries,
    }
    _atomic_text(output / "last_run.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    db.execute(
        "INSERT INTO meta(key,value) VALUES('last_refresh_ts',?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(summary["refreshed_at"]),),
    )
    db.commit()
    db.close()
    return summary


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="refresh", choices=("refresh",))
    parser.add_argument("--logs-root", type=Path, default=DEFAULT_LOGS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--slots", default=",".join(PHYSICAL_SLOTS))
    parser.add_argument("--initial-tail-mb", type=int, default=64)
    parser.add_argument("--full-rebuild", action="store_true")
    boundary = parser.add_mutually_exclusive_group()
    boundary.add_argument(
        "--since-hours",
        type=float,
        help="on a new/full archive, fix the start this many hours before this run",
    )
    boundary.add_argument(
        "--since-ts",
        type=float,
        help="on a new/full archive, fix the start to this Unix timestamp",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    slots = tuple(slot.strip() for slot in args.slots.split(",") if slot.strip())
    unknown = sorted(set(slots) - set(PHYSICAL_SLOTS))
    if unknown:
        print(f"unknown physical slots: {', '.join(unknown)}", file=sys.stderr)
        return 2
    archive_start_ts = args.since_ts
    if args.since_hours is not None:
        if not math.isfinite(args.since_hours) or args.since_hours < 0:
            print("--since-hours must be finite and non-negative", file=sys.stderr)
            return 2
        archive_start_ts = time.time() - args.since_hours * 60 * 60
    summary = refresh(
        logs_root=args.logs_root,
        output=args.output,
        slots=slots,
        initial_tail_mb=args.initial_tail_mb,
        full_rebuild=args.full_rebuild,
        archive_start_ts=archive_start_ts,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
