#!/usr/bin/env python3
"""Read the all-assigned official ITT for the binary post-decline buyer pulse.

Run one host at a time from its clean activation boundary so a later host's
pre-activation games can never enter another host's cohort, for example:

    .venv/bin/python scripts/read_pers_p033_r4_binary_postdecline_pulse.py \
      --slots champion --since T0 --control-slot champion \
      --stack-snapshot .ai/PERS_P033_R4_T0_STACKS.json \
      --official-json .ai/PERSUASION_OFFICIAL.json

The cohort is fixed at the first structural buyer decision.  A decline, pulse,
purchase, completion, or favorable outcome is never required for enrollment.
"""

from __future__ import annotations

import argparse
import copy
from collections import Counter, defaultdict
import glob
import hashlib
import json
import math
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from scripts import check_reachability  # noqa: E402
from scripts import live_percentile as lp  # noqa: E402


FLAG = "GLEE_PERS_P033_R4_BINARY_POSTDECLINE_PULSE_AB"
GATE = "p033_r4_binary_postdecline_pulse"
ASSIGNMENT_SALT = "pers_p033_r4_binary_postdecline_pulse_v1|"
TRACE_FIELDS = (
    GATE,
    f"{GATE}_first_decline_round",
    f"{GATE}_postdecline_highs",
    f"{GATE}_postdecline_lows",
    f"{GATE}_postdecline_margin",
    f"{GATE}_prior_pulses",
    f"{GATE}_last_pulsed_low_count",
)
PRICE_SCALES = (100.0, 10_000.0, 1_000_000.0)
RESEARCH_SLOTS = ("champion", "composite")


def _number(value) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        value = value.strip().replace("$", "").replace(",", "")
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _binary_signal(entry: dict) -> bool | None:
    """Read only the public raw binary protocol, independently of production."""
    value = entry.get("seller_message")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        token = value.strip().lower()
        if token == "yes":
            return True
        if token == "no":
            return False
    recommended = entry.get("recommended")
    if value is None and isinstance(recommended, bool):
        return recommended
    return None


def structural_signal(seat: str, state: dict) -> dict | None:
    """Public pre-treatment cell, without inspecting history or seller knowledge."""
    if (seat != "player_2"
            or (state.get("player_2_role") is not None
                and state.get("player_2_role") != "buyer")
            or state.get("seller_message_type") != "binary"):
        return None
    price = _number(state.get("product_price"))
    prior = _number(state.get("p"))
    high_value = _number(state.get("v"))
    low_value = _number(state.get("u"))
    rounds = _number(state.get("total_rounds"))
    if None in (price, prior, high_value, low_value, rounds) or price <= 0.0:
        return None
    scale = max(1.0, abs(price), abs(high_value), abs(low_value))
    if (abs(prior - (1.0 / 3.0)) > 1e-9
            or abs(high_value / price - 4.0) > 1e-9
            or abs(low_value) > 1e-9 * scale
            or abs(rounds - 20.0) > 20e-9):
        return None
    return {
        "price": price,
        "p": prior,
        "v": high_value,
        "u": low_value,
        "ratio": high_value / price,
        "mode": "binary",
        "seller_message_type": "binary",
        # This label is unavailable to production and is never an eligibility
        # condition. Authenticated finals supply it for the frozen subgroup.
        "is_seller_know_cv": state.get("is_seller_know_cv"),
        "total_rounds": 20,
    }


def replay_pulse(history, current_message=None) -> dict:
    """Reconstruct pulse state from observable history without production code."""
    entries = [entry for entry in history or [] if isinstance(entry, dict)]
    seen_decline = False
    first_decline_round = None
    highs = lows = 0
    last_pulsed_low_count = 0
    pulse_rounds: list[int] = []
    audit_failures: list[int] = []
    for index, entry in enumerate(entries):
        signal = _binary_signal(entry)
        pulse_due = (
            signal is True
            and seen_decline
            and lows >= 3
            and 3 * highs - lows <= 0
            and lows > last_pulsed_low_count
        )
        round_no = int(_number(entry.get("round")) or index + 1)
        if pulse_due:
            pulse_rounds.append(round_no)
            last_pulsed_low_count = lows
            if entry.get("bought") is True:
                audit_failures.append(round_no)
        elif signal is True and seen_decline and entry.get("bought") is True:
            quality = str(entry.get("quality") or "").strip().lower()
            if quality == "high":
                highs += 1
            elif quality == "low":
                lows += 1
            else:
                audit_failures.append(round_no)
        if signal is False and not seen_decline:
            seen_decline = True
            first_decline_round = round_no

    current_due = (
        not audit_failures
        and _binary_signal({"seller_message": current_message}) is True
        and seen_decline
        and lows >= 3
        and 3 * highs - lows <= 0
        and lows > last_pulsed_low_count
    )
    return {
        "seen_decline": seen_decline,
        "first_decline_round": first_decline_round,
        "postdecline_highs": highs,
        "postdecline_lows": lows,
        "postdecline_margin": 3 * highs - lows,
        "last_pulsed_low_count": last_pulsed_low_count,
        "pulse_rounds": pulse_rounds,
        "prior_pulses": len(pulse_rounds),
        "audit_failures": audit_failures,
        "current_due": current_due,
    }


def pulse_arm(game_id) -> str | None:
    gid = str(game_id or "")
    if not gid:
        return None
    digest = hashlib.sha256((ASSIGNMENT_SALT + gid).encode()).hexdigest()
    assigned = bool(int(digest, 16) & 1)
    return "candidate" if assigned else "control"


def _exposure_turn(slot: str, record: dict):
    if (record.get("game_family") != "persuasion"
            or record.get("action_type") != "buyer_decision"
            or record.get("phase") not in (None, "buyer_decision")):
        return None
    gid = str(record.get("game_id") or "")
    seat = record.get("your_player")
    state = record.get("state") or {}
    signal = structural_signal(seat, state)
    if (not gid or signal is None
            or (state.get("current_player") or seat) != seat
            or _number(state.get("round")) != 1.0
            or [entry for entry in (state.get("history") or [])
                if isinstance(entry, dict)]):
        return None
    timestamp = _number(record.get("ts"))
    if timestamp is None:
        return None
    action = record.get("action") or {}
    opponent = record.get("opponent") or {}
    signal.update({
        "first_decision_ts": timestamp,
        "first_decision": action.get("decision"),
        "first_message": state.get("seller_message"),
        "opponent_name": (opponent.get("name")
                          if isinstance(opponent, dict) else None),
        "opponent_type": (opponent.get("type")
                          if isinstance(opponent, dict) else None),
    })
    return (slot, gid), timestamp, signal


def _history_metrics(history) -> dict:
    entries = [entry for entry in history or [] if isinstance(entry, dict)]
    purchases = sum(entry.get("bought") is True for entry in entries)
    refusals = sum(entry.get("bought") is False for entry in entries)
    replay = replay_pulse(entries)
    return {
        "rounds": len(entries),
        "purchases": purchases,
        "refusals": refusals,
        "purchase_rate": purchases / len(entries) if entries else None,
        "seller_messages": [entry.get("seller_message") for entry in entries],
        "buyer_decisions": [entry.get("buyer_decision") for entry in entries],
        "qualities": [entry.get("quality") for entry in entries],
        "replayed_pulse_rounds": replay["pulse_rounds"],
        "replay_audit_failures": replay["audit_failures"],
    }


def _outcome_row(slot: str, record: dict, final: dict):
    if final.get("game_family") != "persuasion":
        return None
    gid = str(record.get("game_id") or final.get("game_id") or "")
    seat = final.get("your_player")
    state = final.get("game_state") or {}
    signal = structural_signal(seat, state)
    completed = lp._terminal_close(final)
    if not gid or signal is None or completed is None:
        return None
    payoff = lp._result_payoff(final.get("result") or {}, seat, seat)
    pct = (lp.percentile("persuasion", dict(state), seat, payoff)
           if payoff is not None else None)
    status = str(final.get("status") or "").strip().lower()
    outcome = str((final.get("result") or {}).get("outcome") or "").strip().lower()
    metrics = _history_metrics(state.get("history"))
    diagnostic = {
        **signal,
        **metrics,
        "payoff": payoff,
        "payoff_per_price": (
            payoff / signal["price"] if payoff is not None else None),
        "zero_outcome": payoff == 0.0 if payoff is not None else None,
        "negative_outcome": payoff < 0.0 if payoff is not None else None,
        "severe_outcome": (
            payoff / signal["price"] <= -2.0
            if payoff is not None else None),
        "status": status,
        "outcome": outcome,
        "timeout": status == "timeout" or outcome == "timeout",
        "immediate_terminal": metrics["rounds"] == 0,
    }
    return slot, pct, gid, completed, diagnostic


def _trace_shape(plan: dict) -> dict:
    plan = plan if isinstance(plan, dict) else {}
    gates = plan.get("gates_fired")
    gates = gates if isinstance(gates, list) else []
    present = tuple(field for field in TRACE_FIELDS if field in plan)
    return {
        "present": bool(present or GATE in gates),
        "present_fields": present,
        "gate_count": sum(item == GATE for item in gates),
        "gates": gates,
    }


def _turn_game(record: dict) -> dict:
    return {
        "game_id": record.get("game_id"),
        "game_family": "persuasion",
        "your_player": record.get("your_player"),
        "valid_actions": {"type": record.get("action_type")},
        "game_state": copy.deepcopy(record.get("state") or {}),
    }


def _independent_would_change(due: bool, action: dict, plan: dict) -> bool:
    """Whether assignment could change this frozen control action."""
    action = action if isinstance(action, dict) else {}
    plan = plan if isinstance(plan, dict) else {}
    gates = plan.get("gates_fired")
    gates = gates if isinstance(gates, list) else []
    expected_value = _number(plan.get("expected_value"))
    plan_price = _number(plan.get("price"))
    return (
        due
        and str(action.get("decision") or "").strip().lower() == "yes"
        and plan.get("buyer_v2") is True
        and plan.get("tight") is False
        and plan.get("blocked") is False
        and not gates
        and expected_value is not None
        and plan_price is not None
        and expected_value >= plan_price
    )


def _load_replay_flags(control_slot: str | None, snapshot_path=None,
                       activation_t0=None):
    if not control_slot:
        return None
    if snapshot_path:
        with open(snapshot_path, encoding="utf-8") as handle:
            document = json.load(handle)
        arms = document.get("stacks") if isinstance(document, dict) else None
        frozen_at = (_number(document.get("frozen_at"))
                     if isinstance(document, dict) else None)
        boundary = _number(activation_t0)
        if (not isinstance(arms, dict) or frozen_at is None
                or (activation_t0 is not None and boundary is None)
                or (boundary is not None and frozen_at > boundary)):
            raise ValueError(
                "stack snapshot must contain a finite pre-T0 'frozen_at' and "
                "a 'stacks' mapping")
        frozen = True
    else:
        # Current arms are useful only for preflight. A post-T0 causal replay
        # must pass the immutable snapshot captured before activation.
        with open(os.path.join(REPO, "arms.json"), encoding="utf-8") as handle:
            arms = json.load(handle)
        frozen = False
    if control_slot not in arms or not isinstance(arms[control_slot], dict):
        raise ValueError(f"unknown control slot {control_slot!r}")
    control = dict(arms[control_slot])
    control[FLAG] = "0"
    control[check_reachability.TRACE_FLAG] = "1"
    candidate = dict(control)
    candidate[FLAG] = "1"
    return control, candidate, frozen


def _trace_audit(rows, hours, since=None, until=None, control_slot=None,
                 stack_snapshot=None):
    """Audit all turns and replay OFF/ON on the same recorded public state."""
    wanted = {(row[0], row[2]) for row in rows}
    by_key = defaultdict(list)
    now = time.time()
    lower = float(since) if since is not None else now - hours * 3600
    upper = float(until) if until is not None else now
    global_non_target_fires = global_control_fires = 0
    global_unauthorized_fires = 0

    for path in sorted(glob.glob(os.path.join(REPO, "logs", "*", "turns.jsonl"))):
        slot = os.path.basename(os.path.dirname(path))
        if slot not in lp.NAMES:
            continue
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if (record.get("game_family") != "persuasion"
                        or record.get("action_type") != "buyer_decision"):
                    continue
                gid = str(record.get("game_id") or "")
                state = record.get("state") or {}
                plan = record.get("plan") or {}
                shape = _trace_shape(plan)
                signal = structural_signal(record.get("your_player"), state)
                timestamp = _number(record.get("ts"))
                if (shape["present"] and timestamp is not None
                        and lower <= timestamp < upper):
                    if signal is None:
                        global_non_target_fires += 1
                    elif pulse_arm(gid) == "control":
                        global_control_fires += 1
                    elif slot not in RESEARCH_SLOTS:
                        global_unauthorized_fires += 1
                if (slot, gid) in wanted:
                    by_key[(slot, gid)].append(record)

    replay_flags = _load_replay_flags(
        control_slot, stack_snapshot, activation_t0=since)
    audits = {}
    for key in wanted:
        records = sorted(by_key.get(key, []),
                         key=lambda item: _number(item.get("ts")) or math.inf)
        audit = {
            "eligible_turns": 0,
            "predicate_turns": 0,
            "pulse_traces": 0,
            "action_changed": 0,
            "wire_failures": 0,
            "control_trace_turns": 0,
            "first_turn_audited": 0,
            "global_non_target_fires": global_non_target_fires,
            "global_control_fires": global_control_fires,
            "global_unauthorized_fires": global_unauthorized_fires,
            "replay_turns": 0,
            "replay_control_mismatches": 0,
            "replay_candidate_mismatches": 0,
            "frozen_stack_replay": int(bool(replay_flags and replay_flags[2])),
            "audited_turn_count": 0,
            "audited_turn_rounds": [],
            "turn_log_contiguous": 0,
            "would_change_turns": 0,
        }
        arm = pulse_arm(key[1])
        target_records = []
        for record in records:
            state = record.get("state") or {}
            if structural_signal(record.get("your_player"), state) is not None:
                target_records.append(record)
        turn_rounds = []
        for record in target_records:
            number = _number((record.get("state") or {}).get("round"))
            turn_rounds.append(
                int(number) if number is not None and number.is_integer()
                else None)
        audit["audited_turn_count"] = len(target_records)
        audit["audited_turn_rounds"] = turn_rounds
        audit["turn_log_contiguous"] = int(
            turn_rounds == list(range(1, len(target_records) + 1)))
        if target_records and not audit["turn_log_contiguous"]:
            audit["wire_failures"] += 1
        replay_control = replay_candidate = None
        if replay_flags and target_records:
            states = [_turn_game(record) for record in target_records]
            replay_control = check_reachability._replay(
                states, replay_flags[0], probe_name=control_slot)
            replay_candidate = check_reachability._replay(
                states, replay_flags[1], probe_name=control_slot)

        for index, record in enumerate(target_records):
            audit["eligible_turns"] += 1
            audit["first_turn_audited"] |= int(index == 0)
            state = record.get("state") or {}
            independent = replay_pulse(
                state.get("history"), state.get("seller_message"))
            due = independent["current_due"] is True
            audit["predicate_turns"] += int(due)
            plan = record.get("plan") or {}
            action = record.get("action") or {}
            decision = str(action.get("decision") or "").strip().lower()
            shape = _trace_shape(plan)
            audit["pulse_traces"] += int(shape["present"])
            expected_values = {
                f"{GATE}_first_decline_round": independent["first_decline_round"],
                f"{GATE}_postdecline_highs": independent["postdecline_highs"],
                f"{GATE}_postdecline_lows": independent["postdecline_lows"],
                f"{GATE}_postdecline_margin": independent["postdecline_margin"],
                f"{GATE}_prior_pulses": independent["prior_pulses"],
                f"{GATE}_last_pulsed_low_count": independent[
                    "last_pulsed_low_count"],
            }
            trace_complete = (
                plan.get(GATE) is True
                and set(shape["present_fields"]) == set(TRACE_FIELDS)
                and shape["gate_count"] == 1
                and shape["gates"] == [GATE]
                and all(plan.get(field) == expected
                        for field, expected in expected_values.items())
            )
            if arm == "control":
                audit["control_trace_turns"] += int(shape["present"])
                mechanism_ok = not shape["present"]
            else:
                mechanism_ok = (
                    (not shape["present"] or
                     (due and trace_complete and decision == "no"))
                    and not independent["audit_failures"]
                )
            audit["wire_failures"] += int(not mechanism_ok)

            if replay_control is not None and replay_candidate is not None:
                audit["replay_turns"] += 1
                ctl_action, ctl_plan, _ = replay_control[index]
                cnd_action, cnd_plan, _ = replay_candidate[index]
                differs = (ctl_action != cnd_action or ctl_plan != cnd_plan)
                audit["action_changed"] += int(ctl_action != cnd_action)
                audit["would_change_turns"] += int(
                    _independent_would_change(due, ctl_action, ctl_plan))
                if arm == "control" and differs:
                    audit["replay_control_mismatches"] += 1
                    audit["wire_failures"] += 1
                expected_recorded = (cnd_action if arm == "candidate"
                                     else ctl_action)
                expected_plan = (cnd_plan if arm == "candidate" else ctl_plan)
                if action != expected_recorded:
                    audit["replay_candidate_mismatches"] += 1
                    audit["wire_failures"] += 1
                if plan != expected_plan:
                    audit["replay_candidate_mismatches"] += 1
                    audit["wire_failures"] += 1
                if arm == "candidate":
                    if ctl_action != cnd_action:
                        directional = (ctl_action.get("decision") == "yes"
                                       and cnd_action.get("decision") == "no"
                                       and trace_complete)
                        audit["wire_failures"] += int(not directional)
                    elif ctl_plan != cnd_plan:
                        audit["wire_failures"] += 1

        if not target_records:
            audit["wire_failures"] += 1
        audits[key] = audit

    enriched = []
    for row in rows:
        slot, pct, gid, completed, *metadata = row
        merged = False
        output = []
        for item in metadata:
            if isinstance(item, dict) and not merged:
                output.append({**item, **audits[(slot, gid)]})
                merged = True
            else:
                output.append(item)
        if not merged:
            output.insert(0, dict(audits[(slot, gid)]))
        enriched.append((slot, pct, gid, completed, *output))
    return enriched


def pulse_games(hours, since=None, until=None, control_slot=None, slots=None,
                stack_snapshot=None):
    rows = list(lp._price_arm_games(
        hours, _exposure_turn, _outcome_row, since=since, until=until))
    if slots:
        rows = [row for row in rows if row[0] in set(slots)]
    yield from _trace_audit(
        rows, hours, since=since, until=until, control_slot=control_slot,
        stack_snapshot=stack_snapshot)


def _official_observations(rows, official):
    observations = []
    for row in rows:
        slot, pct, gid, completed, *metadata = row
        diagnostic = next(
            (item for item in metadata if isinstance(item, dict)), {})
        resolution = next(
            (item for item in metadata if isinstance(item, str)),
            "unresolved" if completed is None else "terminal")
        record = official.get((slot, gid))
        recovered = lp._pers_p05_unlock_official_terminal(record, diagnostic)
        join_failure = recovered is False
        if isinstance(recovered, dict):
            history = [
                {
                    "round": index + 1,
                    "seller_message": message,
                    "buyer_decision": decision,
                    "bought": str(decision).lower() in (
                        "yes", "buy", "bought", "purchase"),
                    "quality": quality,
                }
                for index, (message, decision, quality) in enumerate(zip(
                    recovered.get("seller_messages") or [],
                    recovered.get("buyer_decisions") or [],
                    recovered.get("qualities") or [],
                ))
            ]
            diagnostic = {**diagnostic, **recovered, **_history_metrics(history)}
            payoff = _number(diagnostic.get("payoff"))
            price = _number(diagnostic.get("price"))
            diagnostic["severe_outcome"] = (
                payoff / price <= -2.0
                if payoff is not None and price else None)
            if completed is None:
                completed = True
                resolution = "official-terminal"
        elif recovered is False and completed is None:
            resolution = "invalid-final"
        if completed is not None:
            expected_rounds = _number(diagnostic.get("rounds"))
            audited_rounds = diagnostic.get("audited_turn_rounds")
            turn_log_complete = (
                expected_rounds is not None
                and expected_rounds.is_integer()
                and isinstance(audited_rounds, list)
                and audited_rounds == list(range(1, int(expected_rounds) + 1))
            )
            diagnostic["terminal_turn_count_verified"] = turn_log_complete
            if not turn_log_complete:
                diagnostic["wire_failures"] = int(
                    diagnostic.get("wire_failures") or 0) + 1
        else:
            diagnostic["terminal_turn_count_verified"] = None
        observations.append({
            "slot": slot,
            "gid": gid,
            "arm": pulse_arm(gid),
            "pct": pct,
            "completed": completed,
            "resolution": resolution,
            "diagnostic": diagnostic,
            "official": (record.get("rating_delta")
                         if isinstance(record, dict) else None),
            "official_join_failure": join_failure,
        })
    return observations


def _values(population, arm, field, *, subgroup=None):
    output = []
    for item in population:
        if item["arm"] != arm or item["completed"] is None:
            continue
        if subgroup is not None and not subgroup(item):
            continue
        value = (item["official"] if field == "official"
                 else item["diagnostic"].get(field))
        if isinstance(value, bool):
            output.append(float(value))
        else:
            number = _number(value)
            if number is not None:
                output.append(number)
    return output


def _render_delta(candidate, control):
    delta, low, high = lp._delta_ci(candidate, control)
    if delta is None:
        return "unavailable", delta, low, high
    if low is None:
        return f"{delta:+.4f} (CI unavailable)", delta, low, high
    return f"{delta:+.4f} [{low:+.4f},{high:+.4f}]", delta, low, high


def report(rows, official_path=None) -> int:
    try:
        official = lp._load_pers_official_records(official_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot load official delta export: {exc}")
        return 2
    observations = _official_observations(rows, official)
    print(f"{FLAG}: buyer/binary/p=1/3/v=4P/u=0/20 rounds")
    print("primary: authenticated official per-game rating delta over every "
          "structural assignment; local percentile is diagnostic only")
    print("includes purchases, refusals, zeros, negative/severe outcomes, "
          "timeouts, unresolved games, and immediate terminals")
    if not observations:
        print("no structural assignments in this host-specific window")
        return 1

    key_counts = Counter((item["slot"], item["gid"]) for item in observations)
    duplicate_keys = {key for key, count in key_counts.items() if count > 1}
    gid_slots = defaultdict(set)
    for item in observations:
        slots = item["diagnostic"].get("fleet_slots")
        gid_slots[item["gid"]].update(
            slots if isinstance(slots, (list, tuple, set)) else [item["slot"]])
    cross_slot = {gid for gid, slots in gid_slots.items() if len(slots) > 1}
    contaminated = cross_slot | {gid for _slot, gid in duplicate_keys}
    independent = [item for item in observations
                   if item["gid"] not in contaminated]

    for slot in sorted({item["slot"] for item in observations}):
        for arm in ("control", "candidate"):
            assigned = [item for item in observations
                        if item["slot"] == slot and item["arm"] == arm]
            official_values = _values(assigned, arm, "official")
            mean, low, high, count = lp.mean_ci(official_values)
            rendered = ("unavailable" if mean is None else
                        f"{mean:+.3f} [{low:+.3f},{high:+.3f}]")
            terminals = sum(item["completed"] is not None for item in assigned)
            pending = len(assigned) - terminals
            traces = sum(int(item["diagnostic"].get("pulse_traces") or 0)
                         for item in assigned)
            changed = sum(int(item["diagnostic"].get("action_changed") or 0)
                          for item in assigned)
            failures = sum(int(item["diagnostic"].get("wire_failures") or 0)
                           for item in assigned)
            print(f"{lp.NAMES.get(slot, slot):9} {arm:9} assigned={len(assigned)} "
                  f"terminal={terminals} pending={pending} official={rendered} "
                  f"n={count} traces={traces} changed={changed} failures={failures}")

    official_groups = {
        arm: _values(independent, arm, "official")
        for arm in ("control", "candidate")
    }
    rendered, official_delta, official_low, official_high = _render_delta(
        official_groups["candidate"], official_groups["control"])
    print(f"POOLED official candidate-control: {rendered}; "
          f"n={len(official_groups['candidate'])}/{len(official_groups['control'])}")

    tail_results = {}
    tail_counts_complete = True
    for field in ("payoff_per_price", "zero_outcome", "negative_outcome",
                  "severe_outcome"):
        groups = {arm: _values(independent, arm, field)
                  for arm in ("control", "candidate")}
        rendered_field, delta, low, high = _render_delta(
            groups["candidate"], groups["control"])
        tail_results[field] = (delta, low, high)
        tail_counts_complete &= all(
            len(groups[arm]) == len(official_groups[arm])
            for arm in ("control", "candidate"))
        print(f"  {field}: {rendered_field}; "
              f"n={len(groups['candidate'])}/{len(groups['control'])}")

    subgroup_ready = True
    subgroup_nonnegative = True
    for price in PRICE_SCALES:
        groups = {arm: _values(
            independent, arm, "official",
            subgroup=lambda item, price=price: math.isclose(
                _number(item["diagnostic"].get("price")) or -1.0,
                price, rel_tol=1e-9, abs_tol=1e-9))
            for arm in ("control", "candidate")}
        rendered_group, point, _low, _high = _render_delta(
            groups["candidate"], groups["control"])
        subgroup_ready &= all(len(groups[arm]) >= 30
                              for arm in ("control", "candidate"))
        subgroup_nonnegative &= point is not None and point >= 0.0
        print(f"  price={price:g}: {rendered_group}; "
              f"n={len(groups['candidate'])}/{len(groups['control'])}")
    for knowledge in (True, False):
        groups = {arm: _values(
            independent, arm, "official",
            subgroup=lambda item, knowledge=knowledge:
                item["diagnostic"].get("is_seller_know_cv") is knowledge)
            for arm in ("control", "candidate")}
        rendered_group, point, _low, _high = _render_delta(
            groups["candidate"], groups["control"])
        subgroup_ready &= all(len(groups[arm]) >= 50
                              for arm in ("control", "candidate"))
        subgroup_nonnegative &= point is not None and point >= 0.0
        print(f"  seller_knows={knowledge}: {rendered_group}; "
              f"n={len(groups['candidate'])}/{len(groups['control'])}")
    for slot in RESEARCH_SLOTS:
        groups = {arm: _values(
            independent, arm, "official",
            subgroup=lambda item, slot=slot: item["slot"] == slot)
            for arm in ("control", "candidate")}
        rendered_group, point, _low, _high = _render_delta(
            groups["candidate"], groups["control"])
        subgroup_ready &= all(len(groups[arm]) >= 30
                              for arm in ("control", "candidate"))
        subgroup_nonnegative &= point is not None and point >= 0.0
        print(f"  host={slot}: {rendered_group}; "
              f"n={len(groups['candidate'])}/{len(groups['control'])}")

    unresolved = sum(item["completed"] is None for item in observations)
    missing_official = sum(item["completed"] is not None
                           and item["official"] is None for item in observations)
    join_failures = sum(item["official_join_failure"] for item in observations)
    wire_failures = sum(int(item["diagnostic"].get("wire_failures") or 0)
                        for item in observations)
    control_traces = sum(int(item["diagnostic"].get("control_trace_turns") or 0)
                         for item in observations)
    non_target = max((int(item["diagnostic"].get(
        "global_non_target_fires") or 0) for item in observations), default=0)
    global_control = max((int(item["diagnostic"].get(
        "global_control_fires") or 0) for item in observations), default=0)
    unauthorized = max((int(item["diagnostic"].get(
        "global_unauthorized_fires") or 0) for item in observations), default=0)
    unfrozen_stack_rows = sum(
        int(item["diagnostic"].get("frozen_stack_replay") or 0) != 1
        for item in observations)
    candidate_traces = sum(int(item["diagnostic"].get("pulse_traces") or 0)
                           for item in observations if item["arm"] == "candidate")
    changed = sum(int(item["diagnostic"].get("action_changed") or 0)
                  for item in observations if item["arm"] == "candidate")
    trace_games = sum(
        int(item["diagnostic"].get("pulse_traces") or 0) > 0
        for item in observations if item["arm"] == "candidate")
    changed_games = sum(
        int(item["diagnostic"].get("action_changed") or 0) > 0
        for item in observations if item["arm"] == "candidate")
    would_pulse = {
        arm: sum(int(item["diagnostic"].get("would_change_turns") or 0) > 0
                 for item in observations if item["arm"] == arm)
        for arm in ("control", "candidate")
    }
    print(f"mechanism: traces={candidate_traces} in {trace_games} games; "
          f"changed={changed} in {changed_games} games; "
          f"would-pulse-games={would_pulse['candidate']}/"
          f"{would_pulse['control']} "
          f"wire-failures={wire_failures} control-traces={control_traces} "
          f"non-target={non_target} global-control={global_control} "
          f"unauthorized-host={unauthorized}")
    print(f"integrity: unresolved={unresolved} official-missing={missing_official} "
          f"join-failures={join_failures} duplicate/self-play={len(contaminated)} "
          f"unfrozen-stack-rows={unfrozen_stack_rows} "
          f"complete-tail-rows={tail_counts_complete}")
    print("DECISION RULE: harm-only look at 50 official games/arm and >=4 "
          "would-pulse games/arm; fixed final 325/arm, >=12 would-pulse/arm, "
          ">=30/arm/scale, >=30/arm/research-host, >=50/arm/seller-knowledge. "
          "Promote only with official "
          "95% CI >0, payoff/P nonnegative, zero/negative/severe rates not worse, "
          "nonnegative subgroup points, and every join/mechanism check clean.")

    if unfrozen_stack_rows:
        print("INTEGRITY BLOCKED: causal decisions require frozen-stack replay")
        return 1
    if (wire_failures or control_traces or non_target or global_control
            or unauthorized):
        print("MECHANISM REJECTION: disarm immediately")
        return 2
    if contaminated or join_failures:
        print("INTEGRITY REJECTION: contaminated or invalid official join")
        return 2

    harm_ready = (
        all(len(official_groups[arm]) >= 50
            for arm in ("control", "candidate"))
        and all(would_pulse[arm] >= 4
                for arm in ("control", "candidate"))
        and not unresolved
        and not missing_official
        and tail_counts_complete
    )
    neg_delta, neg_low, _neg_high = tail_results["negative_outcome"]
    if harm_ready and (
            (official_high is not None and official_high < 0.0)
            or (neg_delta is not None and neg_low is not None
                and neg_delta >= 0.10 and neg_low > 0.0)):
        print("OFFICIAL HARM REJECTION")
        return 2

    sample_ready = all(len(official_groups[arm]) >= 325
                       for arm in ("control", "candidate"))
    payoff_delta = tail_results["payoff_per_price"][0]
    tails_ok = all(
        tail_results[field][0] is not None
        and tail_results[field][0] <= 0.0
        for field in ("zero_outcome", "negative_outcome", "severe_outcome")
    )
    promotable = (
        sample_ready and subgroup_ready and subgroup_nonnegative
        and all(would_pulse[arm] >= 12
                for arm in ("control", "candidate"))
        and trace_games >= 12 and changed_games >= 12
        and official_low is not None and official_low > 0.0
        and payoff_delta is not None and payoff_delta >= 0.0
        and tails_ok and tail_counts_complete
        and not unresolved and not missing_official
        and not unfrozen_stack_rows
    )
    if promotable:
        print("PROMOTION GATE PASSED")
        return 0
    print("PROMOTION BLOCKED: continue the all-assigned research window")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--hours", type=float, default=24.0)
    parser.add_argument("--since", type=float, default=None)
    parser.add_argument("--until", type=float, default=None)
    parser.add_argument("--slots", default="",
                        help="comma-separated slots; invoke separately per T0")
    parser.add_argument("--control-slot", default=None,
                        help="exact live stack used to replay flag OFF and ON")
    parser.add_argument(
        "--stack-snapshot", default=None,
        help="immutable pre-activation JSON with {'stacks': {slot: flags}}; "
             "required for causal reads, omitted only for current-stack preflight")
    parser.add_argument(
        "--host-boundary", action="append", default=[], metavar="SLOT=T0",
        help="repeat to pool distinct clean host T0s at the final read")
    parser.add_argument("--official-json", required=True)
    args = parser.parse_args()
    if args.since is not None and args.until is not None and args.until <= args.since:
        parser.error("--until must be greater than --since")
    keep = {slot.strip() for slot in args.slots.split(",") if slot.strip()}
    if args.host_boundary:
        if (args.since is not None or args.control_slot is not None
                or keep):
            parser.error("--host-boundary cannot be combined with --since or "
                         "--control-slot/--slots")
        if not args.stack_snapshot:
            parser.error("pooled --host-boundary reads require --stack-snapshot")
        rows = []
        seen_slots = set()
        for value in args.host_boundary:
            if "=" not in value:
                parser.error(f"invalid --host-boundary {value!r}; use SLOT=T0")
            slot, boundary = value.split("=", 1)
            slot = slot.strip()
            if slot not in RESEARCH_SLOTS or slot in seen_slots:
                parser.error(f"invalid/duplicate research slot {slot!r}")
            try:
                timestamp = float(boundary)
            except ValueError:
                parser.error(f"invalid timestamp in --host-boundary {value!r}")
            seen_slots.add(slot)
            rows.extend(pulse_games(
                args.hours, since=timestamp, until=args.until,
                control_slot=slot, slots={slot},
                stack_snapshot=args.stack_snapshot))
    else:
        if (args.since is None or not args.stack_snapshot
                or args.control_slot not in RESEARCH_SLOTS
                or keep != {args.control_slot}):
            parser.error(
                "single-boundary causal reads require --since, "
                "--stack-snapshot, and exactly one matching research host in "
                "--slots/--control-slot")
        rows = list(pulse_games(
            args.hours, since=args.since, until=args.until,
            control_slot=args.control_slot, slots=keep,
            stack_snapshot=args.stack_snapshot))
    return report(rows, official_path=args.official_json)


if __name__ == "__main__":
    raise SystemExit(main())
