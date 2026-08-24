"""Prospective all-assigned reader tests for ``--ab pers-p05-unlock``."""

from __future__ import annotations

import json
import sys

import pytest

from glee_agent.strategies import persuasion
from scripts import live_percentile


def _gids(candidate: bool, count: int = 1, prefix: str = "gid") -> list[str]:
    found = []
    for index in range(100_000):
        gid = f"p05-unlock-{prefix}-{index}"
        if persuasion.p05_r12_selectivity_unlock_assignment(gid) is candidate:
            found.append(gid)
            if len(found) == count:
                return found
    raise AssertionError(f"could not find {count} assignment(s) for {candidate}")


def _gid(candidate: bool, prefix: str = "gid") -> str:
    return _gids(candidate, 1, prefix)[0]


def _state(*, mode="text", knows=True, message="yes", history=None,
           p=0.5, ratio=1.2, u=0.0, price=100.0, rounds=20.0) -> dict:
    return {
        "current_player": "player_2",
        "player_1_role": "seller",
        "player_2_role": "buyer",
        "product_price": price,
        "p": p,
        "v": ratio * price,
        "u": u,
        "is_seller_know_cv": knows,
        "seller_message_type": mode,
        "seller_message": message,
        "round": len(history or []) + 1,
        "total_rounds": rounds,
        "history": list(history or []),
    }


def _turn(gid: str, *, ts=100.0, state=None, plan=None, decision="no",
          slot="champion") -> dict:
    del slot
    return {
        "ts": ts,
        "game_id": gid,
        "game_family": "persuasion",
        "your_player": "player_2",
        "phase": "buyer_decision",
        "action_type": "buyer_decision",
        "state": state or _state(),
        "action": {"decision": decision},
        "plan": plan or {},
        "opponent": {"type": "named", "name": "opponent-a"},
    }


def _unlock_plan(*, expected=105.0, price=100.0, traced=True) -> dict:
    plan = {
        "buy": True if traced else False,
        "buyer_v2": True,
        "tight": True,
        "blocked": True,
        "expected_value": expected,
        "price": price,
    }
    if traced:
        plan.update({
            "p05_r12_selectivity_unlock": True,
            "p05_r12_selectivity_unlock_prior_declines": 1,
            "p05_r12_selectivity_unlock_expected_value": expected,
            "gates_fired": ["p05_r12_selectivity_unlock"],
        })
    return plan


def _final(gid: str, *, state=None, payoff=0.0, status="completed",
           outcome="completed") -> dict:
    return {
        "game_id": gid,
        "game_family": "persuasion",
        "your_player": "player_2",
        "status": status,
        "game_state": state or _state(history=[]),
        "result": {
            "outcome": outcome,
            "player_1_payoff": 0.0,
            "player_2_payoff": payoff,
        },
    }


def _write_jsonl(path, records) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records),
                    encoding="utf-8")


def _diagnostic(*, arm="control", mode="text", knows=True, price=100.0,
                slot="champion", payoff=0.5, zero=False, negative=False,
                opponent_name=None) -> dict:
    candidate = arm == "candidate"
    return {
        "price": price,
        "p": 0.5,
        "v": 1.2 * price,
        "u": 0.0,
        "ratio": 1.2,
        "mode": mode,
        "seller_message_type": mode,
        "is_seller_know_cv": knows,
        "total_rounds": 20,
        "payoff": payoff * price,
        "payoff_per_price": payoff,
        "zero_outcome": zero,
        "negative_outcome": negative,
        "purchases": 2 if candidate else 1,
        "refusals": 18 if candidate else 19,
        "purchase_rate": 0.1 if candidate else 0.05,
        "unknown_decisions": 0,
        "timeout": False,
        "immediate_terminal": False,
        "opponent_name": opponent_name,
        "opponent_type": "named" if opponent_name else "hidden",
        "opponent_visibility": "named" if opponent_name else "hidden",
        "fleet_slots": (slot,),
        "eligible_turns": 20,
        "predicate_turns": 1 if candidate else 0,
        "unlock_traces": 1 if candidate else 0,
        "action_changed": 1 if candidate else 0,
        "wire_failures": 0,
        "candidate_purchase_without_predicate": 0,
        "control_trace_turns": 0,
        "first_turn_audited": 1,
        "first_turn_trace": 0,
        "global_trace_turns": 1,
        "global_non_target_fires": 0,
        "global_control_fires": 0,
    }


def test_arm_recovery_uses_the_production_helper() -> None:
    for candidate in (False, True):
        gid = _gid(candidate, f"arm-{candidate}")
        assert live_percentile.pers_p05_unlock_arm(gid) == (
            "candidate" if candidate else "control")
    assert live_percentile.pers_p05_unlock_arm(None) is None


@pytest.mark.parametrize("mode", ["text", "binary"])
@pytest.mark.parametrize("knows", [True, False, None])
def test_structural_signal_includes_both_modes_and_knowledge_cells(
        mode, knows) -> None:
    signal = live_percentile._pers_p05_unlock_signal(
        "player_2", _state(mode=mode, knows=knows))
    assert signal is not None
    assert signal["mode"] == mode
    assert signal["is_seller_know_cv"] is knows


@pytest.mark.parametrize("change", [
    {"p": 0.8}, {"ratio": 1.25}, {"u": 1.0}, {"rounds": 19.0},
    {"mode": "silent"},
])
def test_structural_signal_rejects_neighbor_cells(change) -> None:
    assert live_percentile._pers_p05_unlock_signal(
        "player_2", _state(**change)) is None
    assert live_percentile._pers_p05_unlock_signal(
        "player_1", _state()) is None
    wrong_role = _state()
    wrong_role["player_2_role"] = "seller"
    assert live_percentile._pers_p05_unlock_signal(
        "player_2", wrong_role) is None


def test_exposure_is_first_structural_turn_not_a_firing_or_valid_outcome() -> None:
    gid = _gid(True, "exposure")
    rec = _turn(gid, ts=123.0, plan={}, decision="invalid")
    exposure = live_percentile._pers_p05_unlock_exposure_turn("champion", rec)
    assert exposure[:2] == (("champion", gid), 123.0)
    assert exposure[2]["first_decision"] == "invalid"
    assert exposure[2]["opponent_visibility"] == "named"
    assert exposure[2]["opponent_name"] == "opponent-a"


def test_predicate_reconstructs_strict_parser_plan_and_money_edge() -> None:
    history = [{"seller_message": "no", "bought": False}]
    state = _state(message="yes", history=history)
    predicate = live_percentile._pers_p05_unlock_predicate(
        state, _unlock_plan())
    assert predicate["predicate"] is True
    assert predicate["prior_declines"] == 1
    assert predicate["current_positive"] is True

    equality = live_percentile._pers_p05_unlock_predicate(
        state, _unlock_plan(expected=100.0, traced=False))
    assert equality["predicate"] is False
    ambiguous = _state(message="possibly", history=history)
    assert live_percentile._pers_p05_unlock_predicate(
        ambiguous, _unlock_plan())["predicate"] is False
    no_decline = _state(message="yes", history=[])
    assert live_percentile._pers_p05_unlock_predicate(
        no_decline, _unlock_plan())["predicate"] is False
    conflicted = _unlock_plan()
    conflicted["rank_gate_arm"] = True
    assert live_percentile._pers_p05_unlock_predicate(
        state, conflicted)["predicate"] is False


def test_terminal_row_retains_negative_payoff_purchases_and_refusals(
        monkeypatch) -> None:
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.03)
    gid = _gid(True, "negative-row")
    history = [
        {"seller_message": "yes", "buyer_decision": "buy", "bought": True,
         "quality": "high"},
        {"seller_message": "yes", "buyer_decision": "buy", "bought": True,
         "quality": "low"},
        {"seller_message": "no", "buyer_decision": "pass", "bought": False,
         "quality": "low"},
    ]
    row = live_percentile._pers_p05_unlock_row(
        "champion", {"game_id": gid},
        _final(gid, state=_state(history=history), payoff=-80.0),
    )
    assert row[:4] == ("champion", 0.03, gid, True)
    diagnostic = row[4]
    assert diagnostic["payoff_per_price"] == pytest.approx(-0.8)
    assert diagnostic["negative_outcome"] is True
    assert diagnostic["zero_outcome"] is False
    assert diagnostic["purchases"] == 2
    assert diagnostic["refusals"] == 1


def test_all_turn_audit_requires_adjacent_trace_and_finds_non_target_fire(
        monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))
    candidate = _gid(True, "audit-candidate")
    control = _gid(False, "audit-control")
    out_of_cell = _gid(True, "audit-nontarget")
    history = [{"seller_message": "no", "bought": False}]
    _write_jsonl(tmp_path / "logs/champion/turns.jsonl", [
        _turn(candidate, ts=100.0, state=_state(message="yes", history=[]),
              plan={"buy": False, "buyer_v2": True, "tight": True,
                    "blocked": True, "expected_value": 99.0,
                    "price": 100.0}, decision="no"),
        _turn(candidate, ts=101.0,
              state=_state(message="yes", history=history),
              plan=_unlock_plan(), decision="yes"),
        _turn(control, ts=102.0, state=_state(message="yes", history=history),
              plan={"buy": False, "buyer_v2": True, "tight": True,
                    "blocked": True, "expected_value": 105.0,
                    "price": 100.0}, decision="no"),
        _turn(out_of_cell, ts=103.0,
              state=_state(p=0.8, message="yes", history=history),
              plan=_unlock_plan(), decision="yes"),
    ])
    rows = [
        ("champion", 0.4, candidate, True,
         _diagnostic(arm="candidate"), "terminal"),
        ("champion", 0.4, control, True,
         _diagnostic(arm="control"), "terminal"),
    ]
    audited = live_percentile._pers_p05_unlock_trace_audit(
        rows, 24.0, since=99.0, until=110.0)
    candidate_diag = audited[0][4]
    control_diag = audited[1][4]
    assert candidate_diag["eligible_turns"] == 2
    assert candidate_diag["predicate_turns"] == 1
    assert candidate_diag["unlock_traces"] == 1
    assert candidate_diag["action_changed"] == 1
    assert candidate_diag["first_turn_audited"] == 1
    assert candidate_diag["first_turn_trace"] == 0
    assert candidate_diag["wire_failures"] == 0
    assert control_diag["control_trace_turns"] == 0
    assert candidate_diag["global_non_target_fires"] == 1


def test_trace_audit_rejects_candidate_purchase_without_strict_predicate(
        monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))
    gid = _gid(True, "bad-purchase")
    bad_plan = _unlock_plan()
    state = _state(message="yes", history=[])
    _write_jsonl(tmp_path / "logs/champion/turns.jsonl", [
        _turn(gid, state=state, plan=bad_plan, decision="yes"),
    ])
    rows = [("champion", 0.4, gid, True,
             _diagnostic(arm="candidate"), "terminal")]
    audited = live_percentile._pers_p05_unlock_trace_audit(
        rows, 24.0, since=0.0, until=200.0)
    diagnostic = audited[0][4]
    assert diagnostic["candidate_purchase_without_predicate"] == 1
    assert diagnostic["wire_failures"] == 1
    assert diagnostic["action_changed"] == 0


def test_cohort_keeps_zero_timeout_pending_invalid_and_immediate_terminal(
        monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))
    monkeypatch.setattr(live_percentile.time, "time", lambda: 10_000.0)
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.25)
    gids = [_gid(i % 2 == 0, f"cohort-{i}") for i in range(4)]
    _write_jsonl(tmp_path / "logs/champion/turns.jsonl", [
        _turn(gid, ts=9_950.0 + index, plan={}, decision="no")
        for index, gid in enumerate(gids)
    ])
    immediate = _final(gids[0], state=_state(history=[]), payoff=0.0)
    timeout = _final(
        gids[1], state=_state(history=[{
            "seller_message": "yes", "buyer_decision": "buy",
            "bought": True, "quality": "low",
        }]), payoff=-100.0, status="no_deal", outcome="timeout")
    active = _final(gids[2], status="active", outcome="active")
    invalid = _final(gids[3], status="completed", outcome="unknown")
    _write_jsonl(tmp_path / "logs/champion/results.jsonl", [
        {"ts": 9_990.0 + index, "game_id": gid, "final": final}
        for index, (gid, final) in enumerate(zip(
            gids, (immediate, timeout, active, invalid)))
    ])

    rows = list(live_percentile.pers_p05_unlock_games(
        24.0, since=9_900.0, until=10_000.0))
    assert len(rows) == 4
    by_gid = {row[2]: row for row in rows}
    assert by_gid[gids[0]][3] is True
    assert by_gid[gids[0]][4]["zero_outcome"] is True
    assert by_gid[gids[0]][4]["immediate_terminal"] is True
    assert by_gid[gids[1]][3] is False
    assert by_gid[gids[1]][4]["negative_outcome"] is True
    assert by_gid[gids[1]][4]["timeout"] is True
    assert by_gid[gids[2]][3] is None and by_gid[gids[2]][-1] == "pending"
    assert by_gid[gids[3]][3] is None and by_gid[gids[3]][-1] == "invalid-final"


def _official_record(gid: str, *, mode="text", knows=True, messages=None,
                     qualities=None, decisions=None, payoff=0.0) -> dict:
    messages = [] if messages is None else messages
    qualities = [] if qualities is None else qualities
    decisions = [] if decisions is None else decisions
    return {
        "source": "authenticated-dashboard-transcript",
        "family": "persuasion",
        "role": "buyer",
        "terminal": True,
        "slot": "champion",
        "game_id": gid,
        "rating_delta": 1.5,
        "persuasion": {
            "price": 100.0,
            "p": 0.5,
            "v": 120.0,
            "u": 0.0,
            "mode": mode,
            "is_seller_know_cv": knows,
            "rounds": 20,
            "seller_messages": messages,
            "qualities": qualities,
            "buyer_decisions": decisions,
            "buyer_payoff": payoff,
        },
    }


def test_authenticated_terminal_accepts_immediate_and_hidden_pass_quality() -> None:
    gid = _gid(True, "official-terminal")
    diagnostic = _diagnostic(arm="candidate", mode="text", knows=None)
    diagnostic.pop("payoff")
    diagnostic.pop("payoff_per_price")
    immediate = live_percentile._pers_p05_unlock_official_terminal(
        _official_record(gid, knows=False), diagnostic)
    assert immediate["immediate_terminal"] is True
    assert immediate["is_seller_know_cv"] is False
    assert immediate["zero_outcome"] is True

    # Passed-round quality is unavailable on the dashboard and is irrelevant
    # to buyer payoff; purchased quality remains mandatory.
    partial = live_percentile._pers_p05_unlock_official_terminal(
        _official_record(
            gid, messages=["yes", "no"], qualities=["high", None],
            decisions=["buy", "pass"], payoff=20.0),
        diagnostic,
    )
    assert partial["purchases"] == 1
    assert partial["refusals"] == 1
    assert partial["qualities"] == ["high", "hidden"]


def test_authenticated_terminal_fails_closed_on_knowledge_or_payoff() -> None:
    gid = _gid(True, "official-invalid")
    diagnostic = _diagnostic(arm="candidate", knows=None)
    missing_knowledge = _official_record(gid)
    missing_knowledge["persuasion"].pop("is_seller_know_cv")
    assert live_percentile._pers_p05_unlock_official_terminal(
        missing_knowledge, diagnostic) is False
    wrong_payoff = _official_record(
        gid, messages=["yes"], qualities=["high"], decisions=["buy"],
        payoff=99.0)
    assert live_percentile._pers_p05_unlock_official_terminal(
        wrong_payoff, diagnostic) is False


def test_report_joins_official_and_reports_required_strata(tmp_path, capsys) -> None:
    control = _gid(False, "report-control")
    candidate = _gid(True, "report-candidate")
    rows = [
        ("champion", 0.4, control, True,
         _diagnostic(arm="control", mode="binary", knows=False,
                     opponent_name=None), "terminal"),
        ("champion", 0.7, candidate, True,
         _diagnostic(arm="candidate", mode="text", knows=True,
                     opponent_name="expert"), "terminal"),
    ]
    official = tmp_path / "official.json"
    official.write_text(json.dumps([
        {"slot": "champion", "game_id": control, "rating_delta": -1.0},
        {"slot": "champion", "game_id": candidate, "rating_delta": 2.0},
    ]), encoding="utf-8")
    assert live_percentile.report_pers_p05_unlock(
        rows, 24.0, since=100.0, official_path=str(official)) == 1
    output = capsys.readouterr().out
    assert "OFFICIAL per-game rating delta: +3.0000" in output
    assert "normalized payoff / price" in output
    assert "mode=text" in output and "mode=binary" in output
    assert "terminal seller-knowledge=true" in output
    assert "scale=100" in output and "host=Test 1" in output
    assert "opponent=named" in output and "opponent=hidden" in output
    assert "purchases=" in output and "refusals=" in output
    assert "RESEARCH-ONLY" in output


def test_report_fails_closed_on_unavailable_terminal_knowledge(
        tmp_path, capsys) -> None:
    control = _gid(False, "knowledge-control")
    candidate = _gid(True, "knowledge-candidate")
    rows = [
        ("champion", 0.4, control, True,
         _diagnostic(arm="control", knows=None), "terminal"),
        ("champion", 0.6, candidate, True,
         _diagnostic(arm="candidate", knows=True), "terminal"),
    ]
    official = tmp_path / "official.json"
    official.write_text(json.dumps([
        {"slot": "champion", "game_id": control, "rating_delta": 0.0},
        {"slot": "champion", "game_id": candidate, "rating_delta": 1.0},
    ]), encoding="utf-8")
    assert live_percentile.report_pers_p05_unlock(
        rows, 24.0, official_path=str(official)) == 1
    output = capsys.readouterr().out
    assert "seller-knowledge unavailable=1" in output
    assert "PROMOTION BLOCKED" in output


def _balanced_rows_and_official(count_per_arm: int, *, candidate_delta=2.0,
                                control_delta=0.0, candidate_negative=False):
    slots = tuple(live_percentile.NAMES)
    scales = (100.0, 10000.0, 1000000.0)
    rows = []
    official = []
    for candidate in (False, True):
        arm = "candidate" if candidate else "control"
        for index, gid in enumerate(_gids(
                candidate, count_per_arm, f"balanced-{count_per_arm}-{arm}")):
            mode = ("text", "binary")[index % 2]
            knows = (index % 4) < 2
            price = scales[index % len(scales)]
            slot = slots[index % len(slots)]
            negative = candidate and candidate_negative
            payoff = -1.0 if negative else (1.0 if candidate else 0.5)
            diagnostic = _diagnostic(
                arm=arm, mode=mode, knows=knows, price=price, slot=slot,
                payoff=payoff, negative=negative,
                opponent_name="expert" if index % 2 else None)
            rows.append((slot, 0.7 if candidate else 0.4, gid, True,
                         diagnostic, "terminal"))
            official.append({
                "slot": slot,
                "game_id": gid,
                "rating_delta": candidate_delta if candidate else control_delta,
            })
    return rows, official


def test_harm_rule_rejects_wholly_negative_official_ci(tmp_path, capsys) -> None:
    rows, records = _balanced_rows_and_official(
        30, candidate_delta=-1.0, control_delta=1.0)
    official = tmp_path / "official.json"
    official.write_text(json.dumps(records), encoding="utf-8")
    assert live_percentile.report_pers_p05_unlock(
        rows, 24.0, official_path=str(official)) == 2
    assert "OFFICIAL HARM REJECTION" in capsys.readouterr().out


def test_harm_rule_rejects_ten_point_worse_negative_tail(
        tmp_path, capsys) -> None:
    rows, records = _balanced_rows_and_official(
        30, candidate_delta=0.0, control_delta=0.0,
        candidate_negative=True)
    official = tmp_path / "official.json"
    official.write_text(json.dumps(records), encoding="utf-8")
    assert live_percentile.report_pers_p05_unlock(
        rows, 24.0, official_path=str(official)) == 2
    assert "BOTTOM-TAIL HARM REJECTION" in capsys.readouterr().out


def test_full_precommit_can_pass_only_with_all_subgroup_support(
        tmp_path, capsys) -> None:
    rows, records = _balanced_rows_and_official(100)
    official = tmp_path / "official.json"
    official.write_text(json.dumps(records), encoding="utf-8")
    assert live_percentile.report_pers_p05_unlock(
        rows, 24.0, official_path=str(official)) == 0
    output = capsys.readouterr().out
    assert "PROMOTION GATE PASSED" in output
    assert ">=20/arm/mode" in output
    assert ">=15/arm/seller-knowledge" in output
    assert ">=15/arm/scale" in output
    assert ">=10/arm in every mode x seller-knowledge" in output


def test_cli_routes_pers_p05_unlock(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        live_percentile, "pers_p05_unlock_games",
        lambda _hours, **_kwargs: iter(()),
    )
    monkeypatch.setattr(
        sys, "argv", ["live_percentile.py", "--ab", "pers-p05-unlock",
                      "--since", "100", "--until", "200"],
    )
    assert live_percentile.main() == 1
    assert "no assigned structural-cell buyer games" in capsys.readouterr().out
