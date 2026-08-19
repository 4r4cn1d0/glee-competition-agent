#!/usr/bin/env python
"""Drive the live fleet without editing code or restarting anything.

    python scripts/fleet.py status
    python scripts/fleet.py set composite GLEE_NEGO_SPLIT_CANDIDATE=1
    python scripts/fleet.py clear conceder
    python scripts/fleet.py stop randomized
    python scripts/fleet.py start randomized
    python scripts/fleet.py shift 600

Everything is applied at the agent's next SHIFT BOUNDARY, never by signalling a
running agent. That is not a limitation to work around, it is the safety
property: measured live, a healthy agent holds 6-9 games at all times and never
reaches zero, so interrupting one abandons real games. Abandoned games hit the
server's 120s turn clock, and three of them suspend the agent's queue joins for
30 minutes. The SDK's own drain (--max-time) stops starting games, finishes the
in-flight ones, and exits cleanly. Worst-case latency is one shift.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARMS = os.path.join(REPO, "arms.json")
CONTROL = os.path.join(REPO, "control.json")
STATE = os.path.join(REPO, "logs", "supervisor.json")


def _read(path: str, default):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return default


def _write(path: str, data) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    os.replace(tmp, path)          # atomic: the supervisor never sees a half file


def status() -> int:
    arms, control = _read(ARMS, {}), _read(CONTROL, {})
    state = _read(STATE, {})
    shift = control.get("shift_seconds", 900)
    disabled = set(control.get("disabled") or [])
    running = subprocess.run(["pgrep", "-f", "run_agent.py --probe"],
                             capture_output=True, text=True).stdout.split()
    print(f"shift {shift}s   supervisor {'up' if state.get('supervisor_pid') else 'down'}"
          f"   {len(running)} agent processes\n")
    print(f"  {'agent':12s} {'state':10s} {'age':>6s}  flags")
    for probe, pid in (state.get("agents") or {}).items():
        alive = pid and str(pid) in running
        age = "-"
        if alive:
            out = subprocess.run(["ps", "-o", "etime=", "-p", str(pid)],
                                 capture_output=True, text=True).stdout.strip()
            age = out or "-"
        label = "DISABLED" if probe in disabled else ("up" if alive else "down")
        flags = " ".join(f"{k}={v}" for k, v in sorted((arms.get(probe) or {}).items()))
        print(f"  {probe:12s} {label:10s} {age:>6s}  {flags or '<control>'}")
    for probe in sorted(set(arms) - set(state.get('agents') or {})):
        print(f"  {probe:12s} {'not in fleet':10s} {'-':>6s}")
    return 0


def set_flags(probe: str, pairs: list[str]) -> int:
    arms = _read(ARMS, {})
    entry = dict(arms.get(probe) or {})
    for pair in pairs:
        if "=" not in pair:
            print(f"expected KEY=VALUE, got {pair!r}", file=sys.stderr)
            return 1
        k, _, v = pair.partition("=")
        entry[k.strip()] = v.strip()
    arms[probe] = entry
    _write(ARMS, arms)
    print(f"{probe}: {json.dumps(entry)}")
    print("applies at this agent's next shift boundary "
          f"(within {_read(CONTROL, {}).get('shift_seconds', 900)}s)")
    return 0


def clear_flags(probe: str) -> int:
    arms = _read(ARMS, {})
    arms.pop(probe, None)
    _write(ARMS, arms)
    print(f"{probe}: flags cleared — reverts to base policy at its next boundary")
    return 0


def enable(probe: str, on: bool) -> int:
    control = _read(CONTROL, {})
    disabled = set(control.get("disabled") or [])
    disabled.discard(probe) if on else disabled.add(probe)
    control["disabled"] = sorted(disabled)
    _write(CONTROL, control)
    if on:
        print(f"{probe}: enabled — the supervisor relaunches it within ~30s")
    else:
        print(f"{probe}: will drain its current games and stay down "
              f"(no games abandoned)")
    return 0


def shift(seconds: int) -> int:
    control = _read(CONTROL, {})
    control["shift_seconds"] = int(seconds)
    _write(CONTROL, control)
    print(f"shift set to {seconds}s — applies to each agent's NEXT launch.\n"
          f"  shorter = changes land sooner, but each rotation spends ~1-3 min\n"
          f"  draining in-flight games instead of starting new ones.")
    return 0


def _slot_setting(key: str, probe: str, value: str | None, label: str) -> int:
    """Set or clear one per-slot launch override (policy / families).

    These apply at the slot's NEXT launch, not immediately: which policy an agent
    plays and which families it queues for are fixed when the process starts.
    Flags in arms.json are the live half of the control surface; this is the half
    that needs a rotation.
    """
    control = _read(CONTROL, {})
    table = dict(control.get(key) or {})
    if value is None or value == "-":
        table.pop(probe, None)
        print(f"{probe}: {label} override cleared — reverts to the default at next launch.")
    else:
        table[probe] = value
        print(f"{probe}: {label} = {value} — applies at next launch.")
    control[key] = table
    _write(CONTROL, control)
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "status":
        return status()
    if cmd == "set" and len(rest) >= 2:
        return set_flags(rest[0], rest[1:])
    if cmd == "clear" and rest:
        return clear_flags(rest[0])
    if cmd == "stop" and rest:
        return enable(rest[0], False)
    if cmd == "start" and rest:
        return enable(rest[0], True)
    if cmd == "shift" and rest:
        return shift(int(rest[0]))
    if cmd == "policy" and rest:
        return _slot_setting("policy", rest[0], rest[1] if len(rest) > 1 else None, "policy")
    if cmd == "families" and rest:
        return _slot_setting("families", rest[0], rest[1] if len(rest) > 1 else None, "families")
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
