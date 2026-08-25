#!/usr/bin/env python3
"""Authenticated one-minute, one-shot rating banks for every physical slot.

Only slots armed through ``fleet.py peak SLOT RATING`` consume API budget.  An
armed watcher resolves those slots' authenticated agent IDs, reads one overall
leaderboard per minute, and asks the runner to enter its SDK-native lossless
drain on the first observation at or above the threshold.  It never signals an
agent and never conditions the result on completed or successful games.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import NamedTuple

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from glee_sdk import GleeClient
from scripts import fleet


INTERVAL = 60.0
IDENTITY_REFRESH = 600.0
LOCK = REPO / "logs" / "peak_watch.lock"
OUT = REPO / "logs" / "peak_events.jsonl"
ENV_PATH = REPO / ".env"
ARMS_PATH = REPO / "arms.json"
HISTORY_PATH = REPO / "logs" / "ratings_history.jsonl"
KEYS = (
    ("GLEE_KEY_TEST1", "champion"),
    ("GLEE_KEY_TEST2", "hardliner"),
    ("GLEE_KEY_TEST3", "conceder"),
    ("GLEE_KEY_TEST4", "randomized"),
    ("GLEE_KEY_TEST5", "composite"),
)
FAMILIES = ("bargaining", "negotiation", "persuasion")


class PollResult(NamedTuple):
    triggered: list[str]
    missing_identity: list[str]


def _reject_constant(token: str):
    raise ValueError(f"non-finite JSON constant {token}")


def _read_json(path: Path, default):
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle, parse_constant=_reject_constant)
    except (OSError, UnicodeError, ValueError):
        return default


def read_control_strict() -> dict:
    """Read armed state without turning corruption into a silent disarm."""
    with Path(fleet.CONTROL).open(encoding="utf-8") as handle:
        control = json.load(handle, parse_constant=_reject_constant)
    if not isinstance(control, dict):
        raise ValueError("control.json root is not an object")
    fleet._validate_bank_control_schema(control)
    return control


def load_env() -> dict[str, str]:
    env = {}
    with ENV_PATH.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    return env


def _finite_positive(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def eligible_thresholds(control: dict) -> dict[str, float]:
    fleet._validate_bank_control_schema(control)
    disabled = set(control.get("disabled") or [])
    latched = set(control.get("bank_latched") or [])
    eligible = {}
    for slot, raw in (control.get("bank_thresholds") or {}).items():
        threshold = _finite_positive(raw)
        if (
            slot in fleet.FLEET_SLOTS
            and slot not in disabled
            and slot not in latched
            and threshold is not None
        ):
            eligible[slot] = threshold
    return eligible


def identify_agents(
    env: dict[str, str], slots: set[str]
) -> tuple[dict[str, str], dict[str, dict], dict[str, str]]:
    """Resolve only armed slots; isolate key failures and reject duplicate IDs."""
    candidates: dict[str, str] = {}
    stats: dict[str, dict] = {}
    errors: dict[str, str] = {}
    for key_name, slot in KEYS:
        if slot not in slots:
            continue
        key = env.get(key_name)
        if not key:
            errors[slot] = f"missing {key_name}"
            continue
        try:
            result = GleeClient(api_key=key).stats()
        except Exception as exc:
            errors[slot] = f"{type(exc).__name__}: {exc}"[:200]
            continue
        stats[slot] = result
        agent_id = result.get("agent_id")
        if not agent_id:
            errors[slot] = "stats response has no agent_id"
            continue
        candidates[slot] = str(agent_id)

    owners: dict[str, list[str]] = {}
    for slot, agent_id in candidates.items():
        owners.setdefault(agent_id, []).append(slot)
    ids = {}
    for agent_id, owner_slots in owners.items():
        if len(owner_slots) == 1:
            ids[agent_id] = owner_slots[0]
            continue
        message = f"duplicate authenticated agent_id {agent_id} for {owner_slots}"
        for slot in owner_slots:
            errors[slot] = message
    return ids, stats, errors


def fetch_overall(auth_key: str) -> list[dict]:
    params = urllib.parse.urlencode(
        {"player_type": "agent", "show_baselines": "false", "limit": "200"}
    )
    request = urllib.request.Request(
        "https://glee-competition.com/api/leaderboard/overall?" + params,
        headers={
            "Authorization": f"Bearer {auth_key}",
            "User-Agent": "Mozilla/5.0",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.load(response, parse_constant=_reject_constant)
    if not isinstance(data, list):
        raise ValueError("overall leaderboard response is not a list")
    return data


def matching_rows(board: list[dict], ids: dict[str, str]) -> dict[str, dict]:
    rows = {}
    for index, row in enumerate(board, start=1):
        slot = ids.get(str(row.get("player_id")))
        if slot:
            rows[slot] = {**row, "row": index}
    return rows


def _overlay_hash(slot: str) -> str:
    arm = (_read_json(ARMS_PATH, {}).get(slot) or {})
    payload = json.dumps(arm, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _code_head() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True
    )
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def capture_observation(slot: str, row: dict) -> dict:
    """Capture process/stack identity before the atomic bank mutation."""
    # Use the process table, not supervisor.json: the latter is written once per
    # loop and can still contain the prior PID during a fresh launch.
    pid, command = fleet._running_slot_command(slot)
    return {
        "observed_ts": time.time(),
        "leaderboard_rank": row.get("rank"),
        "leaderboard_row": row.get("row"),
        "player_id": row.get("player_id"),
        "pid": pid,
        "process_command": command,
        # These name the workspace/overlay at observation time. They are not
        # claimed to be a launch manifest for a pre-existing Python PID; the
        # process command and start PID are captured separately above.
        "arms_sha256_at_observation": _overlay_hash(slot),
        "workspace_head_at_observation": _code_head(),
    }


def game_count_deltas(slot: str, stats: dict, now: float | None = None) -> dict:
    """Compute authenticated 24h/48h per-family activity for the bank audit."""
    scores = stats.get("scores") or {}
    current = {
        family: (scores.get(family) or {}).get("games_played") for family in FAMILIES
    }
    if not all(isinstance(value, (int, float)) for value in current.values()):
        return {"current": current, "24h": None, "48h": None}
    now = time.time() if now is None else now
    cutoffs = {"24h": now - 86400, "48h": now - 172800}
    past: dict[str, dict | None] = {period: None for period in cutoffs}
    try:
        with HISTORY_PATH.open(encoding="utf-8") as handle:
            for raw in handle:
                try:
                    record = json.loads(raw, parse_constant=_reject_constant)
                    ts = float(record.get("ts"))
                except (TypeError, ValueError):
                    continue
                cell = record.get(slot)
                if not isinstance(cell, dict):
                    continue
                for period, cutoff in cutoffs.items():
                    # Use the first sample at/after the trailing cutoff.  The
                    # ten-minute history cadence then UNDER-counts activity by
                    # at most one interval, which is safe for decay defence;
                    # the old last-before sample over-counted and could claim a
                    # 24h/48h buffer was satisfied when it was not.
                    if past[period] is None and cutoff <= ts <= now:
                        past[period] = cell
    except OSError:
        return {"current": current, "24h": None, "48h": None}

    result: dict[str, dict | None] = {"current": current}
    for period in ("24h", "48h"):
        old = past[period]
        deltas = {}
        if old is None:
            result[period] = None
            continue
        for family in FAMILIES:
            value = old.get(family)
            old_count = value[1] if isinstance(value, list) and len(value) >= 2 else None
            if not isinstance(old_count, (int, float)):
                deltas = {}
                break
            deltas[family] = int(current[family] - old_count)
        result[period] = deltas or None
    return result


def record_event(
    slot: str,
    threshold: float,
    row: dict,
    observation: dict,
    stats: dict | None,
) -> None:
    event = {
        **observation,
        "slot": slot,
        "threshold": threshold,
        "observed_rating": row.get("rating"),
        "stats_after_request": stats,
        "activity_deltas": game_count_deltas(slot, stats or {}),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(event, sort_keys=True, allow_nan=False)
    with OUT.open("a", encoding="utf-8") as handle:
        handle.write(payload + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def poll_once(
    env: dict[str, str],
    ids: dict[str, str],
    *,
    control: dict | None = None,
) -> PollResult:
    control = read_control_strict() if control is None else control
    thresholds = eligible_thresholds(control)
    if not thresholds:
        return PollResult([], [])
    authenticated_slots = set(ids.values()) & set(thresholds)
    if not authenticated_slots:
        return PollResult([], sorted(thresholds))
    board = None
    failures = []
    # Use keys belonging to armed slots that have authenticated successfully in
    # identity discovery.  TEST1 is not privileged: a revoked TEST1 key must not
    # blind a healthy, armed Test5 (or any other slot).
    for key_name, slot in KEYS:
        key = env.get(key_name)
        if slot not in authenticated_slots or not key:
            continue
        try:
            board = fetch_overall(key)
            break
        except Exception as exc:
            failures.append(f"{slot}: {type(exc).__name__}: {exc}"[:200])
    if board is None:
        detail = "; ".join(failures) or "no authenticated armed key available"
        raise RuntimeError(f"all armed-slot leaderboard credentials failed: {detail}")
    rows = matching_rows(board, ids)
    triggered = []
    missing = []
    for slot, threshold in thresholds.items():
        row = rows.get(slot)
        if row is None:
            missing.append(slot)
            continue
        rating = _finite_positive(row.get("rating"))
        if rating is None or rating < threshold:
            continue
        observation = capture_observation(slot, row)
        if not fleet.bank_observed_peak(slot, rating, observation):
            continue
        key_name = next(key for key, candidate in KEYS if candidate == slot)
        try:
            detail = GleeClient(api_key=env[key_name]).stats()
        except Exception as exc:
            detail = {"error": f"{type(exc).__name__}: {exc}"[:200]}
        try:
            record_event(slot, threshold, row, observation, detail)
        except Exception as exc:
            print(
                f"[{time.strftime('%H:%M:%S')}] peak event append failed for "
                f"{slot}: {type(exc).__name__}: {exc}",
                file=sys.stderr,
                flush=True,
            )
        triggered.append(slot)
    return PollResult(triggered, missing)


def _claim_singleton():
    """Hold an OS lock for process lifetime; PID-file check-then-write is racy."""
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    handle = LOCK.open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.seek(0)
        owner = handle.read().strip() or "unknown"
        handle.close()
        raise SystemExit(f"peak watcher already running as pid {owner}")
    handle.seek(0)
    handle.truncate()
    handle.write(str(os.getpid()))
    handle.flush()
    os.fsync(handle.fileno())
    return handle


def _merge_identities(
    cached: dict[str, str], refreshed: dict[str, str], attempted: set[str]
) -> dict[str, str]:
    merged = {agent_id: slot for agent_id, slot in cached.items() if slot not in attempted}
    for agent_id, slot in refreshed.items():
        other = merged.get(agent_id)
        if other and other != slot:
            print(
                f"[{time.strftime('%H:%M:%S')}] identity collision: {agent_id} "
                f"maps to both {other} and {slot}; protecting neither",
                file=sys.stderr,
                flush=True,
            )
            merged.pop(agent_id, None)
            continue
        merged[agent_id] = slot
    return merged


def main() -> int:
    lock_handle = _claim_singleton()
    last_env: dict[str, str] | None = None
    env_fingerprint = None
    ids: dict[str, str] = {}
    next_identity_refresh = 0.0
    next_poll = time.monotonic()
    try:
        while True:
            status = "idle (no armed thresholds)"
            try:
                control = read_control_strict()
                thresholds = eligible_thresholds(control)
                if thresholds:
                    try:
                        candidate_env = load_env()
                        if not any(candidate_env.get(key) for key, _slot in KEYS):
                            raise ValueError("no fleet keys present")
                        last_env = candidate_env
                    except (OSError, UnicodeError, ValueError) as exc:
                        if last_env is None:
                            raise
                        print(
                            f"[{time.strftime('%H:%M:%S')}] peak watch warning: "
                            f"cannot reload .env ({exc}); using last good keys",
                            file=sys.stderr,
                            flush=True,
                        )
                    assert last_env is not None
                    fingerprint = tuple((key, last_env.get(key)) for key, _ in KEYS)
                    armed = set(thresholds)
                    known = set(ids.values())
                    now = time.monotonic()
                    refresh = (
                        armed
                        if fingerprint != env_fingerprint or now >= next_identity_refresh
                        else armed - known
                    )
                    if refresh:
                        fresh_ids, _stats, errors = identify_agents(last_env, refresh)
                        ids = _merge_identities(ids, fresh_ids, refresh)
                        for slot, error in errors.items():
                            print(
                                f"[{time.strftime('%H:%M:%S')}] peak identity "
                                f"warning for {slot}: {error}",
                                file=sys.stderr,
                                flush=True,
                            )
                        env_fingerprint = fingerprint
                        next_identity_refresh = now + (
                            IDENTITY_REFRESH if armed <= set(ids.values()) else INTERVAL
                        )
                    result = poll_once(last_env, ids, control=control)
                    if result.missing_identity:
                        next_identity_refresh = 0.0
                    status = (
                        "triggered " + ",".join(result.triggered)
                        if result.triggered
                        else f"poll ok (armed={len(thresholds)})"
                    )
                print(f"[{time.strftime('%H:%M:%S')}] peak watch {status}", flush=True)
            except Exception as exc:
                print(
                    f"[{time.strftime('%H:%M:%S')}] peak watch warning: "
                    f"{type(exc).__name__}: {exc}",
                    file=sys.stderr,
                    flush=True,
                )
            next_poll += INTERVAL
            now = time.monotonic()
            if next_poll < now:
                next_poll = now
            time.sleep(max(0.0, next_poll - now))
    finally:
        fcntl.flock(lock_handle, fcntl.LOCK_UN)
        lock_handle.close()


if __name__ == "__main__":
    raise SystemExit(main())
