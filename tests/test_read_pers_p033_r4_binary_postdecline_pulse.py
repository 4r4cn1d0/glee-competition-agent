"""Independent reader tests for the p=1/3, v=4P buyer pulse."""

from __future__ import annotations

import copy
import hashlib
import json
import sys

import pytest

from glee_agent.strategies import persuasion
from scripts import read_pers_p033_r4_binary_postdecline_pulse as reader


def _state(*, price=100.0, knowledge=True) -> dict:
    state = {
        "current_player": "player_2",
        "player_2_role": "buyer",
        "product_price": price,
        "p": 1.0 / 3.0,
        "v": 4.0 * price,
        "u": 0.0,
        "seller_message_type": "binary",
        "seller_message": "yes",
        "round": 1,
        "total_rounds": 20,
        "history": [],
    }
    if knowledge is not None:
        state["is_seller_know_cv"] = knowledge
    return state


def _candidate_gid() -> str:
    for index in range(1000):
        gid = f"reader-pulse-{index}"
        if reader.pulse_arm(gid) == "candidate":
            return gid
    raise AssertionError("candidate id not found")


def _arm_gid(arm: str) -> str:
    for index in range(1000):
        gid = f"reader-{arm}-{index}"
        if reader.pulse_arm(gid) == arm:
            return gid
    raise AssertionError(f"{arm} id not found")


def test_structural_cohort_ignores_seller_knowledge() -> None:
    for knowledge in (True, False, None):
        signal = reader.structural_signal(
            "player_2", _state(knowledge=knowledge))
        assert signal is not None
        assert signal["is_seller_know_cv"] is knowledge


@pytest.mark.parametrize(
    "mutate",
    [
        lambda state: state.update(seller_message_type="text"),
        lambda state: state.update(p=0.5),
        lambda state: state.update(v=300.0),
        lambda state: state.update(u=1.0),
        lambda state: state.update(total_rounds=10),
        lambda state: state.update(product_price="bad"),
        lambda state: state.update(player_2_role="seller"),
    ],
)
def test_structural_cohort_fails_closed_outside_exact_cell(mutate) -> None:
    state = _state()
    mutate(state)
    assert reader.structural_signal("player_2", state) is None


def test_reader_and_production_match_the_frozen_independent_game_hash() -> None:
    frozen_salt = "pers_p033_r4_binary_postdecline_pulse_v1|"
    for index in range(200):
        gid = f"reader-assignment-{index}"
        expected = bool(int(hashlib.sha256(
            (frozen_salt + gid).encode()).hexdigest(), 16) & 1)
        assert reader.pulse_arm(gid) == (
            "candidate" if expected else "control")
        assert persuasion.p033_r4_binary_postdecline_pulse_assignment(
            gid) is expected
    assert reader.pulse_arm("") is None


@pytest.mark.parametrize("message", ["buy", "YES!", "not recommended", "", 1])
def test_independent_reader_rejects_fuzzy_binary_messages_even_with_hint(
    message,
) -> None:
    assert reader._binary_signal({
        "seller_message": message,
        "recommended": True,
    }) is None


def test_independent_reader_accepts_only_exact_binary_wire_and_null_fallback(
) -> None:
    assert reader._binary_signal({"seller_message": " yes "}) is True
    assert reader._binary_signal({"seller_message": "NO"}) is False
    assert reader._binary_signal({"seller_message": True}) is True
    assert reader._binary_signal({
        "seller_message": None,
        "recommended": False,
    }) is False


def test_independent_replay_matches_motivating_pulse_rounds() -> None:
    stream = [
        ("yes", "high"), ("no", None), ("no", None), ("no", None),
        ("yes", "high"), ("yes", "low"), ("yes", "low"),
        ("yes", "low"), ("yes", "low"), ("yes", "low"),
        ("yes", "high"), ("yes", "low"), ("yes", "low"),
        ("yes", "high"), ("yes", "low"), ("yes", "low"),
        ("yes", "low"), ("yes", "low"), ("yes", "low"),
        ("yes", "low"),
    ]
    history = []
    pulses = []
    payoff_units = 0
    for round_no, (message, quality) in enumerate(stream, 1):
        replay = reader.replay_pulse(history, message)
        pulsed = replay["current_due"]
        bought = message == "yes" and not pulsed
        if pulsed:
            pulses.append(round_no)
        if bought:
            payoff_units += 3 if quality == "high" else -1
        history.append({
            "round": round_no,
            "seller_message": message,
            "bought": bought,
            "quality": quality if bought else None,
        })
    terminal = reader.replay_pulse(history)
    assert pulses == [9, 11, 13, 16, 18, 20]
    assert terminal["pulse_rounds"] == pulses
    assert terminal["audit_failures"] == []
    assert payoff_units == 1


def test_passed_quality_never_rearms_the_pulse() -> None:
    history = [
        {"round": 1, "seller_message": "no", "bought": False},
        {"round": 2, "seller_message": "yes", "bought": True,
         "quality": "low"},
        {"round": 3, "seller_message": "yes", "bought": True,
         "quality": "low"},
        {"round": 4, "seller_message": "yes", "bought": True,
         "quality": "low"},
        {"round": 5, "seller_message": "yes", "bought": False,
         "quality": "low"},
    ]
    replay = reader.replay_pulse(history, "yes")
    assert replay["pulse_rounds"] == [5]
    assert replay["postdecline_lows"] == 3
    assert replay["current_due"] is False


def test_bought_reconstructed_pulse_is_a_mechanism_failure() -> None:
    history = [
        {"round": 1, "seller_message": "no", "bought": False},
        {"round": 2, "seller_message": "yes", "bought": True,
         "quality": "low"},
        {"round": 3, "seller_message": "yes", "bought": True,
         "quality": "low"},
        {"round": 4, "seller_message": "yes", "bought": True,
         "quality": "low"},
        {"round": 5, "seller_message": "yes", "bought": True,
         "quality": "low"},
    ]
    replay = reader.replay_pulse(history, "yes")
    assert replay["pulse_rounds"] == [5]
    assert replay["audit_failures"] == [5]
    assert replay["current_due"] is False


def test_exposure_is_preoutcome_and_does_not_require_a_decline() -> None:
    gid = _candidate_gid()
    record = {
        "ts": 1234.5,
        "game_id": gid,
        "game_family": "persuasion",
        "your_player": "player_2",
        "phase": "buyer_decision",
        "action_type": "buyer_decision",
        "state": _state(),
        "action": {"decision": "yes"},
        "opponent": {"type": "hidden", "name": None},
    }
    exposure = reader._exposure_turn("champion", record)
    assert exposure is not None
    assert exposure[0] == ("champion", gid)
    assert exposure[1] == 1234.5
    assert exposure[2]["first_decision"] == "yes"


def test_missing_round1_log_cannot_enrol_a_midgame_turn() -> None:
    record = {
        "ts": 1235.0,
        "game_id": _candidate_gid(),
        "game_family": "persuasion",
        "your_player": "player_2",
        "phase": "buyer_decision",
        "action_type": "buyer_decision",
        "state": _state(),
        "action": {"decision": "yes"},
    }
    record["state"]["round"] = 2
    record["state"]["history"] = [
        {"round": 1, "seller_message": "yes", "bought": True,
         "quality": "high"},
    ]
    assert reader._exposure_turn("champion", record) is None


@pytest.mark.parametrize(
    "round_value,history",
    [
        (2, []),
        (1, [{"round": 1, "seller_message": "yes", "bought": True,
              "quality": "high"}]),
        (None, []),
        ("malformed", []),
    ],
)
def test_exposure_requires_round_one_and_independently_empty_history(
    round_value, history,
) -> None:
    state = _state()
    if round_value is None:
        state.pop("round")
    else:
        state["round"] = round_value
    state["history"] = history
    record = {
        "ts": 1235.0,
        "game_id": _candidate_gid(),
        "game_family": "persuasion",
        "your_player": "player_2",
        "phase": "buyer_decision",
        "action_type": "buyer_decision",
        "state": state,
        "action": {"decision": "yes"},
    }
    assert reader._exposure_turn("champion", record) is None


def test_trace_shape_requires_every_adjacent_field_and_one_gate() -> None:
    plan = {field: True for field in reader.TRACE_FIELDS}
    plan.update({
        reader.GATE: True,
        "gates_fired": [reader.GATE],
    })
    shape = reader._trace_shape(plan)
    assert shape["present"] is True
    assert set(shape["present_fields"]) == set(reader.TRACE_FIELDS)
    assert shape["gate_count"] == 1
    missing = copy.deepcopy(plan)
    missing.pop(f"{reader.GATE}_postdecline_lows")
    assert set(reader._trace_shape(missing)["present_fields"]) != set(
        reader.TRACE_FIELDS)


def test_history_metrics_keep_purchases_refusals_and_replayed_pulses() -> None:
    history = [
        {"round": 1, "seller_message": "no", "bought": False},
        {"round": 2, "seller_message": "yes", "bought": True,
         "quality": "low"},
        {"round": 3, "seller_message": "yes", "bought": True,
         "quality": "low"},
        {"round": 4, "seller_message": "yes", "bought": True,
         "quality": "low"},
        {"round": 5, "seller_message": "yes", "bought": False},
    ]
    metrics = reader._history_metrics(history)
    assert metrics["rounds"] == 5
    assert metrics["purchases"] == 3
    assert metrics["refusals"] == 2
    assert metrics["replayed_pulse_rounds"] == [5]


def test_replay_stack_can_be_frozen_independently_of_live_arms(tmp_path) -> None:
    path = tmp_path / "stacks.json"
    path.write_text(json.dumps({
        "frozen_at": 1234.0,
        "stacks": {
            "champion": {
                "GLEE_PERS_BUYER_V2": "1",
                reader.FLAG: "1",
            },
        },
    }), encoding="utf-8")
    control, candidate, frozen = reader._load_replay_flags(
        "champion", str(path))
    assert frozen is True
    assert control[reader.FLAG] == "0"
    assert candidate[reader.FLAG] == "1"
    with pytest.raises(ValueError):
        reader._load_replay_flags(
            "champion", str(path), activation_t0=1233.999)


@pytest.mark.parametrize(
    "document,slot",
    [
        ({"stacks": {"champion": {}}}, "champion"),
        ({"frozen_at": 1234.0}, "champion"),
        ({"frozen_at": 1234.0, "stacks": {}}, "champion"),
        ({"frozen_at": 1234.0, "stacks": {"champion": []}}, "champion"),
    ],
)
def test_replay_stack_rejects_missing_or_malformed_snapshot(
    tmp_path, document, slot,
) -> None:
    path = tmp_path / "bad-stacks.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError):
        reader._load_replay_flags(slot, str(path))


@pytest.mark.parametrize(
    "mismatch", [None, "action", "plan", "control-overlay", "round-gap"])
def test_trace_audit_replays_frozen_stack_and_compares_logged_action_and_plan(
    tmp_path, monkeypatch: pytest.MonkeyPatch, mismatch,
) -> None:
    arm = "control" if mismatch == "control-overlay" else "candidate"
    gid = _arm_gid(arm)
    expected_action = {"decision": "yes"}
    expected_plan = {
        "buy": True,
        "buyer_v2": True,
        "tight": False,
        "blocked": False,
        "expected_value": 150.0,
        "price": 100.0,
    }
    recorded_action = copy.deepcopy(expected_action)
    recorded_plan = copy.deepcopy(expected_plan)
    if mismatch == "action":
        recorded_action = {"decision": "no"}
    elif mismatch == "plan":
        recorded_plan["unexpected"] = True
    record = {
        "ts": 1235.0,
        "game_id": gid,
        "game_family": "persuasion",
        "your_player": "player_2",
        "phase": "buyer_decision",
        "action_type": "buyer_decision",
        "state": _state(),
        "action": recorded_action,
        "plan": recorded_plan,
    }
    log_dir = tmp_path / "champion"
    log_dir.mkdir()
    turns = log_dir / "turns.jsonl"
    records = [record]
    if mismatch == "round-gap":
        later = copy.deepcopy(record)
        later["ts"] = 1235.5
        later["state"]["round"] = 3
        records.append(later)
    turns.write_text("".join(json.dumps(item) + "\n" for item in records),
                     encoding="utf-8")
    monkeypatch.setattr(reader.glob, "glob", lambda _pattern: [str(turns)])

    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps({
        "frozen_at": 1234.0,
        "stacks": {"champion": {"GLEE_PERS_BUYER_V2": "1"}},
    }), encoding="utf-8")
    seen_flags = []

    def fake_replay(states, flags, probe_name="composite"):
        seen_flags.append((dict(flags), probe_name, len(states)))
        action = copy.deepcopy(expected_action)
        plan = copy.deepcopy(expected_plan)
        if mismatch == "control-overlay" and flags[reader.FLAG] == "1":
            action = {"decision": "no"}
            plan = {**plan, reader.GATE: True}
        return [(action, plan, set()) for _state_item in states]

    monkeypatch.setattr(reader.check_reachability, "_replay", fake_replay)
    rows = [("champion", None, gid, None, {"price": 100.0}, "pending")]
    enriched = reader._trace_audit(
        rows, 1.0, since=1234.0, until=1236.0,
        control_slot="champion", stack_snapshot=str(snapshot))
    audit = enriched[0][4]
    assert [item[0][reader.FLAG] for item in seen_flags] == ["0", "1"]
    expected_count = 2 if mismatch == "round-gap" else 1
    assert all(item[1:] == ("champion", expected_count) for item in seen_flags)
    assert audit["frozen_stack_replay"] == 1
    assert audit["replay_turns"] == expected_count
    assert audit["wire_failures"] == (0 if mismatch is None else 1)


def test_independent_reach_requires_a_control_buy_that_would_change() -> None:
    plan = {
        "buyer_v2": True,
        "tight": False,
        "blocked": False,
        "expected_value": 150.0,
        "price": 100.0,
    }
    assert reader._independent_would_change(
        True, {"decision": "yes"}, plan) is True
    assert reader._independent_would_change(
        True, {"decision": "no"}, plan) is False
    assert reader._independent_would_change(
        False, {"decision": "yes"}, plan) is False
    assert reader._independent_would_change(
        True, {"decision": "yes"}, {**plan, "gates_fired": ["other"]}
    ) is False


def test_trace_audit_detects_candidate_fire_on_an_unauthorized_host(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    wanted_gid = _arm_gid("candidate")
    unauthorized_gid = next(
        gid for gid in (f"unauthorized-{index}" for index in range(1000))
        if reader.pulse_arm(gid) == "candidate" and gid != wanted_gid)
    base_plan = {
        "buy": True,
        "buyer_v2": True,
        "tight": False,
        "blocked": False,
        "expected_value": 150.0,
        "price": 100.0,
    }
    wanted = {
        "ts": 1235.0,
        "game_id": wanted_gid,
        "game_family": "persuasion",
        "your_player": "player_2",
        "phase": "buyer_decision",
        "action_type": "buyer_decision",
        "state": _state(),
        "action": {"decision": "yes"},
        "plan": base_plan,
    }
    unauthorized = copy.deepcopy(wanted)
    unauthorized["game_id"] = unauthorized_gid
    unauthorized["plan"] = {reader.GATE: True}
    paths = []
    for slot, record in (("champion", wanted), ("hardliner", unauthorized)):
        directory = tmp_path / slot
        directory.mkdir()
        path = directory / "turns.jsonl"
        path.write_text(json.dumps(record) + "\n", encoding="utf-8")
        paths.append(str(path))
    monkeypatch.setattr(reader.glob, "glob", lambda _pattern: paths)
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps({
        "frozen_at": 1234.0,
        "stacks": {"champion": {"GLEE_PERS_BUYER_V2": "1"}},
    }), encoding="utf-8")
    monkeypatch.setattr(
        reader.check_reachability, "_replay",
        lambda states, _flags, probe_name="composite": [
            ({"decision": "yes"}, copy.deepcopy(base_plan), set())
            for _state_item in states
        ])
    rows = [("champion", None, wanted_gid, None,
             {"price": 100.0}, "pending")]
    enriched = reader._trace_audit(
        rows, 1.0, since=1234.0, until=1236.0,
        control_slot="champion", stack_snapshot=str(snapshot))
    assert enriched[0][4]["global_unauthorized_fires"] == 1


def _decision_observations(per_arm: int = 325) -> list[dict]:
    observations = []
    for arm in ("control", "candidate"):
        for index in range(per_arm):
            slot = reader.RESEARCH_SLOTS[index % len(reader.RESEARCH_SLOTS)]
            diagnostic = {
                "fleet_slots": (slot,),
                "price": reader.PRICE_SCALES[index % len(reader.PRICE_SCALES)],
                "is_seller_know_cv": bool(index % 2),
                "payoff_per_price": 1.1 if arm == "candidate" else 1.0,
                "zero_outcome": False,
                "negative_outcome": False,
                "severe_outcome": False,
                "pulse_traces": int(arm == "candidate" and index < 12),
                "action_changed": int(arm == "candidate" and index < 12),
                "predicate_turns": int(index < 12),
                "would_change_turns": int(index < 12),
                "wire_failures": 0,
                "control_trace_turns": 0,
                "global_non_target_fires": 0,
                "global_control_fires": 0,
                "frozen_stack_replay": 1,
            }
            observations.append({
                "slot": slot,
                "gid": f"{arm}-{index}",
                "arm": arm,
                "pct": 0.5,
                "completed": True,
                "resolution": "terminal",
                "diagnostic": diagnostic,
                "official": 2.0 if arm == "candidate" else 0.0,
                "official_join_failure": False,
            })
    return observations


def _patch_report_observations(monkeypatch, observations) -> None:
    monkeypatch.setattr(reader.lp, "_load_pers_official_records", lambda _: {})
    monkeypatch.setattr(
        reader, "_official_observations", lambda _rows, _official: observations)


def test_official_observations_retain_terminal_timeout_unresolved_and_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    diagnostic = {
        "price": 100.0,
        "p": 1.0 / 3.0,
        "v": 400.0,
        "u": 0.0,
        "mode": "binary",
        "seller_message_type": "binary",
        "payoff": 0.0,
        "payoff_per_price": 0.0,
        "zero_outcome": True,
        "negative_outcome": False,
        "severe_outcome": False,
        "immediate_terminal": False,
    }
    rows = [
        ("champion", 0.5, "terminal", True, dict(diagnostic), "terminal"),
        ("champion", 0.1, "timeout", False,
         {**diagnostic, "timeout": True, "negative_outcome": True},
         "terminal"),
        ("champion", None, "unresolved", None, dict(diagnostic), "pending"),
        ("champion", None, "invalid", None, dict(diagnostic), "invalid-final"),
    ]
    official = {
        ("champion", "terminal"): {"rating_delta": 1.0, "kind": "valid"},
        ("champion", "timeout"): {"rating_delta": -8.0, "kind": "valid"},
        ("champion", "invalid"): {"rating_delta": -2.0, "kind": "invalid"},
    }

    def recover(record, current):
        if not isinstance(record, dict):
            return None
        if record.get("kind") == "invalid":
            return False
        return {
            **current,
            "seller_messages": [],
            "buyer_decisions": [],
            "qualities": [],
        }

    monkeypatch.setattr(
        reader.lp, "_pers_p05_unlock_official_terminal", recover)
    observations = reader._official_observations(rows, official)
    assert [item["gid"] for item in observations] == [
        "terminal", "timeout", "unresolved", "invalid"]
    assert observations[0]["completed"] is True
    assert observations[1]["completed"] is False
    assert observations[2]["completed"] is None
    assert observations[3]["resolution"] == "invalid-final"
    assert observations[3]["official_join_failure"] is True


def test_terminal_transcript_round_count_must_match_contiguous_audited_turns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    diagnostic = {
        "price": 100.0,
        "p": 1.0 / 3.0,
        "v": 400.0,
        "u": 0.0,
        "mode": "binary",
        "rounds": 2,
        "audited_turn_rounds": [1],
        "wire_failures": 0,
    }
    monkeypatch.setattr(
        reader.lp, "_pers_p05_unlock_official_terminal",
        lambda _record, _diagnostic: None)
    observations = reader._official_observations(
        [("champion", 0.5, "missing-turn", True, diagnostic, "terminal")],
        {})
    observed = observations[0]["diagnostic"]
    assert observed["terminal_turn_count_verified"] is False
    assert observed["wire_failures"] == 1


def test_value_extraction_includes_timeouts_and_zero_negative_severe_outcomes(
) -> None:
    population = [
        {"arm": "candidate", "completed": True,
         "official": 0.0,
         "diagnostic": {"negative_outcome": False,
                        "severe_outcome": False}},
        {"arm": "candidate", "completed": False,
         "official": -8.0,
         "diagnostic": {"negative_outcome": True,
                        "severe_outcome": True}},
        {"arm": "candidate", "completed": None,
         "official": 9.0,
         "diagnostic": {"negative_outcome": False,
                        "severe_outcome": False}},
    ]
    assert reader._values(population, "candidate", "official") == [0.0, -8.0]
    assert reader._values(
        population, "candidate", "negative_outcome") == [0.0, 1.0]
    assert reader._values(
        population, "candidate", "severe_outcome") == [0.0, 1.0]


def test_report_can_promote_only_a_fully_ready_clean_cohort(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observations = _decision_observations()
    _patch_report_observations(monkeypatch, observations)
    assert reader.report([("synthetic",)], official_path="frozen.json") == 0


def test_report_blocks_a_negative_research_host_even_when_pooled_is_positive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observations = _decision_observations()
    for item in observations:
        if item["slot"] == "composite":
            item["official"] = 4.0 if item["arm"] == "candidate" else 5.0
        else:
            item["official"] = 10.0 if item["arm"] == "candidate" else 0.0
    _patch_report_observations(monkeypatch, observations)
    assert reader.report([("synthetic",)], official_path="frozen.json") == 1


def test_report_blocks_when_one_research_host_is_below_its_arm_minimum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observations = _decision_observations()
    candidate_seen = 0
    for item in observations:
        if item["arm"] != "candidate":
            continue
        item["slot"] = "composite" if candidate_seen < 29 else "champion"
        item["diagnostic"]["fleet_slots"] = (item["slot"],)
        candidate_seen += 1
    _patch_report_observations(monkeypatch, observations)
    assert reader.report([("synthetic",)], official_path="frozen.json") == 1


@pytest.mark.parametrize("subgroup", ["price", "knowledge"])
def test_report_blocks_when_a_price_or_knowledge_arm_is_underfilled(
    monkeypatch: pytest.MonkeyPatch, subgroup,
) -> None:
    observations = _decision_observations()
    candidate_seen = 0
    for item in observations:
        if item["arm"] != "candidate":
            continue
        if subgroup == "price":
            item["diagnostic"]["price"] = (
                reader.PRICE_SCALES[0] if candidate_seen < 29
                else reader.PRICE_SCALES[1 + candidate_seen % 2])
        else:
            item["diagnostic"]["is_seller_know_cv"] = candidate_seen >= 49
        candidate_seen += 1
    _patch_report_observations(monkeypatch, observations)
    assert reader.report([("synthetic",)], official_path="frozen.json") == 1


@pytest.mark.parametrize("underfilled_arm", ["control", "candidate"])
def test_report_requires_twelve_unique_would_pulse_games_in_each_arm(
    monkeypatch: pytest.MonkeyPatch, underfilled_arm,
) -> None:
    observations = _decision_observations()
    for item in observations:
        index = int(item["gid"].rsplit("-", 1)[1])
        threshold = 11 if item["arm"] == underfilled_arm else 12
        item["diagnostic"]["would_change_turns"] = int(index < threshold)
    _patch_report_observations(monkeypatch, observations)
    assert reader.report([("synthetic",)], official_path="frozen.json") == 1


def test_report_counts_unique_would_pulse_games_not_trace_turns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observations = _decision_observations()
    for item in observations:
        index = int(item["gid"].rsplit("-", 1)[1])
        item["diagnostic"]["would_change_turns"] = int(index < 2)
        if item["arm"] == "candidate":
            item["diagnostic"]["pulse_traces"] = 6 if index < 2 else 0
            item["diagnostic"]["action_changed"] = 6 if index < 2 else 0
    _patch_report_observations(monkeypatch, observations)
    assert reader.report([("synthetic",)], official_path="frozen.json") == 1


def test_report_rejects_harm_at_the_frozen_harm_look(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observations = _decision_observations(per_arm=50)
    for item in observations:
        item["official"] = -2.0 if item["arm"] == "candidate" else 0.0
    _patch_report_observations(monkeypatch, observations)
    assert reader.report([("synthetic",)], official_path="frozen.json") == 2


@pytest.mark.parametrize("underfilled_arm", ["control", "candidate"])
def test_harm_look_requires_four_unique_would_pulse_games_in_each_arm(
    monkeypatch: pytest.MonkeyPatch, underfilled_arm,
) -> None:
    observations = _decision_observations(per_arm=50)
    for item in observations:
        index = int(item["gid"].rsplit("-", 1)[1])
        threshold = 3 if item["arm"] == underfilled_arm else 4
        item["diagnostic"]["would_change_turns"] = int(index < threshold)
        item["official"] = -2.0 if item["arm"] == "candidate" else 0.0
    _patch_report_observations(monkeypatch, observations)
    assert reader.report([("synthetic",)], official_path="frozen.json") == 1


@pytest.mark.parametrize("integrity_failure", ["unresolved", "unfrozen"])
def test_harm_look_cannot_decide_on_unresolved_or_unfrozen_evidence(
    monkeypatch: pytest.MonkeyPatch, integrity_failure,
) -> None:
    observations = _decision_observations(per_arm=50)
    for item in observations:
        item["official"] = -2.0 if item["arm"] == "candidate" else 0.0
    if integrity_failure == "unresolved":
        pending = copy.deepcopy(observations[0])
        pending["gid"] = "still-pending"
        pending["completed"] = None
        pending["official"] = None
        observations.append(pending)
    else:
        for item in observations:
            item["diagnostic"]["frozen_stack_replay"] = 0
    _patch_report_observations(monkeypatch, observations)
    assert reader.report([("synthetic",)], official_path="frozen.json") == 1


def test_report_rejects_an_invalid_official_join(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observations = _decision_observations()
    observations[0]["official_join_failure"] = True
    _patch_report_observations(monkeypatch, observations)
    assert reader.report([("synthetic",)], official_path="frozen.json") == 2


@pytest.mark.parametrize(
    "missing_field",
    ["payoff_per_price", "zero_outcome", "negative_outcome", "severe_outcome"],
)
def test_report_cannot_promote_when_any_resolved_tail_value_is_missing(
    monkeypatch: pytest.MonkeyPatch, missing_field,
) -> None:
    observations = _decision_observations()
    observations[-1]["diagnostic"].pop(missing_field)
    _patch_report_observations(monkeypatch, observations)
    assert reader.report([("synthetic",)], official_path="frozen.json") == 1


def test_report_rejects_an_exact_candidate_fire_on_an_unauthorized_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observations = _decision_observations()
    for item in observations:
        item["diagnostic"]["global_unauthorized_fires"] = 1
    _patch_report_observations(monkeypatch, observations)
    assert reader.report([("synthetic",)], official_path="frozen.json") == 2


@pytest.mark.parametrize(
    "arguments",
    [
        ["--slots", "champion", "--control-slot", "champion",
         "--stack-snapshot", "snapshot.json"],
        ["--since", "1234", "--slots", "champion", "--control-slot",
         "champion"],
        ["--since", "1234", "--slots", "composite", "--control-slot",
         "champion", "--stack-snapshot", "snapshot.json"],
        ["--since", "1234", "--slots", "champion,composite",
         "--control-slot", "champion", "--stack-snapshot", "snapshot.json"],
        ["--since", "1234", "--slots", "randomized", "--control-slot",
         "randomized", "--stack-snapshot", "snapshot.json"],
        ["--host-boundary", "champion=1234", "--slots", "champion",
         "--stack-snapshot", "snapshot.json"],
        ["--host-boundary", "champion=1234"],
    ],
)
def test_cli_rejects_rolling_unfrozen_or_mixed_host_causal_reads(
    monkeypatch: pytest.MonkeyPatch, arguments,
) -> None:
    monkeypatch.setattr(
        sys, "argv", ["reader", *arguments, "--official-json", "official.json"])
    with pytest.raises(SystemExit) as exc:
        reader.main()
    assert exc.value.code == 2
