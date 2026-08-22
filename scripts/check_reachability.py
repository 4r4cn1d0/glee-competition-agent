#!/usr/bin/env python3
"""Pre-deployment reachability check for a candidate flag.

Answers, BEFORE a 3,000-game arena run or a live deploy, the three questions a
"clean +0.0000 null" cannot: did the gate's preconditions ever hold, did the
gate actually fire, and did firing ever change a submitted action? Each of the
known traps this repo has already paid for shows up as a specific zero here:

  * a flag nested under a gate the control omits (the GLEE_BARG_STONEWALL /
    ACCEPT_FLOOR screen) -> the flag is never even consulted: eligible = 0;
  * a flag the probe transform overwrites (GLEE_BARG_SPE_WEIGHT under the
    composite probe, which replaces barg_spe_weight with the hardliner's 1.0)
    -> consulted state exists but nothing moves: action_changed = 0;
  * a typo'd or nonexistent flag -> all three are 0.

Method: draw N paired games with sim.replay_eval's own field/census machinery,
play them once under the CONTROL arm to bank every game-state our seat was
handed (states are engine-produced, so the record echo and the synthetic
planning clock are exactly as the live strategy sees them -- nothing is
reconstructed by hand), then push each banked state through the family's
decide() twice: control flags vs control + candidate. GLEE_TRACE_GATES=1 is
set on BOTH arms so each plan carries plan["gates_fired"], the ordered list of
gates that changed the pending target/decision that turn.

    .venv/bin/python scripts/check_reachability.py --flag GLEE_NEGO_ULTIMATUM_SHARE=0.80
    .venv/bin/python scripts/check_reachability.py --flag GLEE_BARG_SPE_WEIGHT=1.0
    .venv/bin/python scripts/check_reachability.py --flag GLEE_NEGO_NO_SUCH=1

Exit status is 0 only when eligible_count, fired_count and action_changed_count
are ALL positive. A nonzero exit means the candidate as configured cannot be
arena-tested meaningfully: fix the control nesting / flag name first.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from sim import replay_eval  # noqa: E402

TRACE_FLAG = "GLEE_TRACE_GATES"

#: flag -> (family, gate names in plan["gates_fired"], precondition predicate).
#: The predicate runs on (game, control_plan) and says whether the gate's
#: preconditions held in that state regardless of whether the gate is armed.
#: Gate names may be empty for pure value knobs that have no gate of their own
#: (their reachability is judged on consultation + action movement alone).
def _p_ultimatum(game, p):
    return (p.get("zopa") is not None and p.get("capped")
            and p.get("rounds_left", 99) <= 1)


def _p_final_hidden(game, p):
    return (p.get("their_value") is None and p.get("capped")
            and p.get("rounds_left", 99) <= 1)


def _p_rank_price(game, p):
    return (game.get("valid_actions", {}).get("type") == "offer"
            and p.get("capped") and p.get("rounds_left", 99) <= 1)


def _p_span(game, p):
    return (p.get("zopa") is not None and p.get("rounds_left", 0) >= 2
            and game.get("valid_actions", {}).get("type") == "decision")


def _p_offer(game, p):
    return game.get("valid_actions", {}).get("type") == "offer"


def _p_decision(game, p):
    return game.get("valid_actions", {}).get("type") == "decision"


def _p_complete_price(game, p):
    state = game.get("game_state") or {}
    return (state.get("complete_information") is True
            and state.get("player_1_value") is not None
            and state.get("player_2_value") is not None
            and game.get("valid_actions", {}).get("type") in ("offer", "decision"))


def _p_complete_ultimatum(game, p):
    state = game.get("game_state") or {}
    return (_p_complete_price(game, p)
            and game.get("valid_actions", {}).get("type") == "offer"
            and state.get("max_rounds") == 1)


def _p_barg_midgame_decision(game, p):
    return _p_decision(game, p) and p.get("rounds_left", 0) > 2


def _p_bob_offer(game, p):
    return (_p_offer(game, p) and not p.get("me_is_alice", True)
            and p.get("rounds_left", 0) > 2)


def _p_barg_message(game, p):
    return (_p_offer(game, p)
            and (game.get("game_state") or {}).get("messages_allowed") is True)


def _p_barg_no_regress(game, p):
    return (_p_decision(game, p) and p.get("rounds_left", 0) > 1
            and p.get("money", 0) > 0)


KNOWN = {
    "GLEE_NEGO_ZOPA_CLAMP": ("negotiation", (), _p_complete_price),
    "GLEE_NEGO_ULT_FLOOR": ("negotiation", (), _p_complete_ultimatum),
    "GLEE_NEGO_ULT_CAP": ("negotiation", (), _p_complete_ultimatum),
    "GLEE_NEGO_ULTIMATUM_SHARE": ("negotiation", ("ultimatum",), _p_ultimatum),
    "GLEE_NEGO_RANK_PRICE_AB": ("negotiation", ("rank_price",), _p_rank_price),
    "GLEE_NEGO_POSTERIOR": ("negotiation", ("posterior",), _p_final_hidden),
    "GLEE_NEGO_CURVE_PRICING": ("negotiation", ("curve_final",), _p_final_hidden),
    "GLEE_NEGO_ACCEPT_SPAN": ("negotiation", ("span_veto",), _p_span),
    "GLEE_NEGO_RECIP_DAMP": ("negotiation", ("recip_damp",), lambda g, p: True),
    "GLEE_NEGO_DEADGAME_V1": ("negotiation", ("deadgame", "deadgame_walk"),
                              lambda g, p: p.get("opponent_bound") is not None),
    "GLEE_NEGO_STALL_POLICY": ("negotiation", ("stall_park", "stall_accept"),
                               lambda g, p: True),
    "GLEE_NEGO_TABLE": ("negotiation", ("table", "table_accept"),
                        lambda g, p: p.get("their_value") is None),
    "GLEE_NEGO_PROBE_V1": ("negotiation", ("probe_hold", "time_driven"),
                           lambda g, p: True),
    "GLEE_NEGO_SPLIT_CANDIDATE": ("negotiation", ("split",), lambda g, p: True),
    "GLEE_BARG_ACCEPT_FLOOR": ("bargaining", ("accept_floor",),
                               _p_barg_midgame_decision),
    "GLEE_BARG_FLOOR_GAIN": ("bargaining", ("floor_gain",),
                             _p_barg_midgame_decision),
    "GLEE_BARG_STONEWALL": ("bargaining", ("stonewall_release",
                                           "stonewall_extortion"),
                            _p_barg_midgame_decision),
    "GLEE_BARG_STONEWALL_MIN": ("bargaining", ("stonewall_extortion",),
                                _p_barg_midgame_decision),
    "GLEE_BARG_BOB_OFFER": ("bargaining", ("bob_offer",), _p_bob_offer),
    "GLEE_BARG_NO_REGRESS": ("bargaining", ("no_regress",),
                             _p_barg_no_regress),
    "GLEE_BARG_MSG": ("bargaining", ("barg_msg",), _p_barg_message),
    "GLEE_BARG_OPPONENT_FLOOR": ("bargaining", ("opp_floor",), _p_offer),
    "GLEE_OPP_EXPLOIT": ("bargaining", ("opp_exploit",), lambda g, p: True),
    # Pure value knobs read through Config.from_env — no gate of their own.
    # NOTE: the composite probe transform (glee_agent/probes.py) OVERWRITES
    # barg_spe_weight, barg_uncapped_horizon and both nego anchors, so those
    # env flags are inert under the live composite: this checker reports that
    # as action_changed = 0.
    "GLEE_BARG_SPE_WEIGHT": ("bargaining", (), _p_offer),
    "GLEE_BARG_UNKNOWN_DELTA": ("bargaining", (), lambda g, p: True),
    "GLEE_NEGO_SELLER_ANCHOR": ("negotiation", (), lambda g, p: True),
    "GLEE_NEGO_BUYER_ANCHOR": ("negotiation", (), lambda g, p: True),
}

# These flags execute after the strategy plan is removed, in actions.coerce().
# Their firing evidence is consultation plus a changed final numeric action,
# rather than a name in plan["gates_fired"].
POSTCONDITION_FLAGS = {
    "GLEE_NEGO_ZOPA_CLAMP", "GLEE_NEGO_ULT_FLOOR", "GLEE_NEGO_ULT_CAP",
}

#: names consulted by runtime_flags.get during the current decide() call
_CONSULTED: set[str] = set()


def _install_flag_spy() -> None:
    from glee_agent import runtime_flags
    orig = runtime_flags.get

    def spy(name: str):
        _CONSULTED.add(name)
        return orig(name)

    runtime_flags.get = spy


def _collect_states(field, draws, flags, families):
    """Play the control arm once, banking a deep copy of every state our seat
    was handed (both offer and decision phases), in the wanted families."""
    from sim import Config as SimConfig
    from sim.arena import play

    strategy = replay_eval._build_strategy(flags)
    banked: list[dict] = []
    wanted = set(families)

    def recorder(game: dict) -> dict:
        if game.get("game_family") in wanted:
            banked.append(copy.deepcopy(game))
        return strategy(game)

    for family, params, seat, game_seed in draws:
        grng = random.Random(game_seed)
        opponent = field.sample_opponent(random.Random(game_seed + 1))
        params = dict(params)
        if opponent.name != "__field__":
            params["opponent_name"] = opponent.name
            params["disclose_opponent"] = random.Random(game_seed + 2).random() < 0.5
        s1, s2 = (recorder, opponent) if seat == "player_1" else (opponent, recorder)
        play(SimConfig(family, dict(params)), s1, s2, grng)
    return banked


def _replay(states, flags):
    """Run decide() directly on every banked state under this flag set.

    Direct decide() (not the dispatch wrapper) so the returned action still
    carries _plan — dispatch pops it before submission. The cfg goes through
    the SAME composite probe transform the arena and the live fleet use, which
    is exactly what makes transform-overwritten flags visibly inert here.
    """
    replay_eval._set_flags(flags)
    from glee_agent.config import Config
    from glee_agent.actions import coerce
    from glee_agent.dispatch import STRATEGIES
    from glee_agent.probes import make_probe

    _, cfg = make_probe("composite", Config.from_env())
    out = []
    for game in states:
        _CONSULTED.clear()
        action = STRATEGIES[game["game_family"]](copy.deepcopy(game), cfg)
        plan = action.pop("_plan", None) if isinstance(action, dict) else None
        # Final-action guards run here in production, after strategy planning.
        # Replaying through coerce makes action_changed describe the wire action.
        action = coerce(action, game)
        out.append((action, plan if isinstance(plan, dict) else {},
                    frozenset(_CONSULTED)))
    return out


_NUMERIC_KEYS = ("product_price", "alice_gain", "bob_gain")


def _action_differs(a: dict, b: dict) -> bool:
    if (a.get("decision") or None) != (b.get("decision") or None):
        return True
    if (a.get("message") or None) != (b.get("message") or None):
        return True
    for k in _NUMERIC_KEYS:
        va, vb = a.get(k), b.get(k)
        if (va is None) != (vb is None):
            return True
        if va is not None and abs(float(va) - float(vb)) > 1e-9:
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--flag", required=True, metavar="NAME=VALUE",
                    help="candidate flag, e.g. GLEE_NEGO_ULTIMATUM_SHARE=0.80")
    ap.add_argument("--family", default=None,
                    choices=("negotiation", "bargaining"),
                    help="restrict to one family (default: inferred from the "
                         "flag prefix, else both)")
    ap.add_argument("--n", type=int, default=800, help="games to draw")
    ap.add_argument("--seed", type=int, default=20260821)
    default_control = json.dumps(replay_eval.DEFAULT_CONTROL)
    ap.add_argument("--control", default=default_control,
                    help="JSON control flag dict (default: simulator snapshot; "
                         "pass the target's current stack before deployment)")
    args = ap.parse_args()

    if "=" not in args.flag:
        print(f"--flag must be NAME=VALUE, got {args.flag!r}")
        return 2
    name, value = args.flag.split("=", 1)
    name = name.strip()

    known = KNOWN.get(name)
    if args.family:
        families = [args.family]
    elif known:
        families = [known[0]]
    elif name.startswith("GLEE_NEGO"):
        families = ["negotiation"]
    elif name.startswith("GLEE_BARG"):
        families = ["bargaining"]
    else:
        families = ["bargaining", "negotiation"]

    control = dict(json.loads(args.control))
    if args.control == default_control:
        print("warning: using replay_eval.DEFAULT_CONTROL, which is a simulator "
              "snapshot; pass the actual target fleet stack with --control "
              "before treating this as deployment evidence.")
    control[TRACE_FLAG] = "1"
    candidate = dict(control)
    candidate[name] = value
    if control.get(name) == candidate[name]:
        print(f"note: control already carries {name}={value!r}; the two arms "
              "are identical and action_changed can only be 0.")

    _install_flag_spy()

    from sim.field_data import Field
    field = Field()
    draws = replay_eval._draw_games(field, families, args.n, args.seed)
    print(f"flag      : {name}={value}")
    print(f"families  : {', '.join(families)}")
    print(f"collecting states from {len(draws)} control-arm games...")
    states = _collect_states(field, draws, control, families)
    print(f"banked {len(states)} decision points; replaying twice "
          "(control vs control+candidate)...")

    ctl = _replay(states, control)
    cnd = _replay(states, candidate)

    gate_names = set(known[1]) if known else set()
    eligible = fired = changed = 0
    examples: list[str] = []
    for game, (a_ctl, p_ctl, _), (a_cnd, p_cnd, consulted) in zip(states, ctl, cnd):
        g_ctl = p_ctl.get("gates_fired") or []
        g_cnd = p_cnd.get("gates_fired") or []

        if known:
            try:
                ok = bool(known[2](game, p_ctl))
            except Exception:
                ok = False
        else:
            # Unknown flag: eligibility = the code actually read it. A flag
            # nested under a gate the control omits, or a nonexistent flag,
            # is never consulted and lands at 0 here.
            ok = name in consulted
        if ok:
            eligible += 1

        if name in POSTCONDITION_FLAGS:
            hit = name in consulted and _action_differs(a_ctl, a_cnd)
        elif gate_names:
            hit = any(g in g_cnd for g in gate_names)
        else:
            # No gate of its own: count states where arming the flag changed
            # WHICH gates fired (an indirect trace of reaching new code).
            hit = g_cnd != g_ctl
        if hit:
            fired += 1

        if _action_differs(a_ctl, a_cnd):
            changed += 1
            if len(examples) < 3:
                st = game.get("game_state") or {}
                examples.append(
                    f"    e.g. {game.get('game_family')}/"
                    f"{game.get('valid_actions', {}).get('type')}"
                    f" r{st.get('round')}: {a_ctl} -> {a_cnd}"
                    f" gates={g_cnd}")

    print()
    print(f"  eligible_count       {eligible:6d}   "
          "(states where the gate's preconditions held)")
    if name in POSTCONDITION_FLAGS:
        fired_basis = "final-action postcondition consulted and changed wire action"
    else:
        fired_basis = (f"gate {sorted(gate_names) if gate_names else '<trace diff>'} "
                       "in plan['gates_fired']")
    print(f"  fired_count          {fired:6d}   ({fired_basis})")
    print(f"  action_changed_count {changed:6d}   "
          "(submitted actions differ between the two arms)")
    for line in examples:
        print(line)

    failures = [label for label, v in
                (("eligible", eligible), ("fired", fired),
                 ("action_changed", changed)) if v <= 0]
    if failures:
        print(f"\nFAIL: {', '.join(failures)} = 0 -- the candidate as "
              "configured is not reachable/effective; do not arena-test or "
              "deploy it until this passes.")
        if eligible == 0:
            print("  hint: never consulted -> wrong name, or nested under a "
                  "gate this control leaves off (the STONEWALL/ACCEPT_FLOOR "
                  "trap).")
        elif changed == 0:
            print("  hint: consulted but inert -> check the probe transform "
                  "(glee_agent/probes.py overwrites several cfg knobs) and "
                  "whether another gate overrides it downstream.")
        return 1
    print("\nPASS: the candidate is reachable, fires, and moves real actions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
