#!/usr/bin/env python
"""Drive the live fleet without editing code or restarting anything.

    python scripts/fleet.py status
    python scripts/fleet.py set composite GLEE_NEGO_SPLIT_CANDIDATE=1
    python scripts/fleet.py clear conceder
    python scripts/fleet.py stop randomized
    python scripts/fleet.py start randomized
    python scripts/fleet.py llm composite off
    python scripts/fleet.py shift 600
    python scripts/fleet.py safe-restart   # supervisor code update, interlocked

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
    """Set or clear one per-slot launch override (policy / families / llm).

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


def drain(probe: str, timeout_s: int = 1800) -> int:
    """Empty a slot's in-flight games WITHOUT abandoning any of them.

    An agent launched with --max-time drains itself: it stops queueing, plays its
    in-flight games out, and exits 0. An agent adopted from an older launch has no
    such path, and SIGINT is not one -- it leaves the process alive while every
    held game runs out its 120s turn clock, scoring each at the 5th percentile and
    earning a 30-minute queue ban. That cost has been paid three times.

    This reproduces the drain from outside the process. The SDK's loop only starts
    games by calling queue(), at most once every topup_interval (15s), and it plays
    in-flight games from pending_games() regardless of queue state. So calling
    leave_queue() every few seconds starves it of NEW games while it finishes the
    ones it holds -- no timeouts, no ban, nothing abandoned. When active_games
    reaches zero the process can be killed for free.

    A game that slips through between a topup and our next leave just extends the
    drain; it is played normally and costs nothing.

    LIMITS -- read before using. The platform allows 60 requests per minute PER
    AGENT, and that budget is SHARED with the agent's own loop, which spends ~30
    of them polling pending_games every 2s. This drainer therefore has only ~20
    calls/min of headroom, i.e. one leave_queue every 3s, and it must never be run
    twice against the same slot: doing so pushed champion over the limit, and the
    429s it caused fall on the AGENT's own move submissions, which is precisely
    the timeout this command exists to avoid.

    Within that budget the drain reduces but does NOT reliably empty a slot. The
    SDK re-queues whenever active < concurrency, so an agent with concurrency=8
    actively refills toward 8 while we can only suppress ~20% of its topup window.
    Measured on champion: 10 -> 3 games, then back to 9. Treat this as a way to
    catch a low moment, not as a guaranteed drain. If you need a guaranteed one,
    the agent must have been launched with --max-time in the first place.
    """
    import time
    env = {}
    with open(os.path.join(REPO, ".env"), encoding="utf-8") as fh:
        for line in fh:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                env[k] = v
    slot_key = {"champion": "GLEE_KEY_TEST1", "hardliner": "GLEE_KEY_TEST2",
                "conceder": "GLEE_KEY_TEST3", "randomized": "GLEE_KEY_TEST4",
                "composite": "GLEE_KEY_TEST5"}.get(probe)
    if not slot_key or slot_key not in env:
        print(f"no API key for slot {probe!r}")
        return 1
    from glee_sdk import GleeClient, GleeAPIError
    c = GleeClient(api_key=env[slot_key])
    import subprocess as _sp
    if len(_sp.run(["pgrep", "-f", f"fleet.py drain {probe}"],
                   capture_output=True, text=True).stdout.split()) > 1:
        print(f"a drainer is already running for {probe}. Refusing to start a second:\n"
              f"  the 60 req/min budget is shared with the agent's own polling, and\n"
              f"  exceeding it makes the AGENT's moves fail, not just ours.")
        return 1
    print(f"draining {probe}: leaving the queue every 3s, letting in-flight games finish.")
    print("  nothing is abandoned; this only stops NEW games from starting.")
    print("  NOTE: reduces but may not empty -- the agent refills toward its concurrency.\n")
    start = time.time(); zero_streak = 0; last_report = 0.0
    while time.time() - start < timeout_s:
        try:
            c.leave_queue()
        except GleeAPIError as exc:
            if "429" in str(exc):
                time.sleep(5)
                continue
        now = time.time()
        if now - last_report >= 10:
            last_report = now
            try:
                n = c.stats().get("active_games", 0)
            except GleeAPIError:
                time.sleep(3); continue
            print(f"  [{time.strftime('%H:%M:%S')}] active_games={n}"
                  f"  ({now - start:.0f}s elapsed)")
            zero_streak = zero_streak + 1 if n == 0 else 0
            if zero_streak >= 2:
                print(f"\n{probe} is empty. It can now be stopped with zero games lost.")
                return 0
        time.sleep(3)
    print(f"\ntimed out after {timeout_s}s — do NOT kill it, games are still in flight.")
    return 1


def _etime_seconds(text: str) -> int | None:
    """Parse `ps -o etime=` ("[[dd-]hh:]mm:ss") into seconds.

    Returns None when the process is gone (ps prints nothing) or the field is
    not parseable, and every caller treats None as "cannot tell, do not act".
    """
    text = (text or "").strip()
    if not text:
        return None
    days = 0
    if "-" in text:
        head, _, text = text.partition("-")
        try:
            days = int(head)
        except ValueError:
            return None
    parts = text.split(":")
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return None
    while len(nums) < 3:
        nums.insert(0, 0)
    hours, minutes, seconds = nums[-3], nums[-2], nums[-1]
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def safe_restart() -> int:
    """Restart the supervisor ONLY at a provably quiet moment.

    The twin-ban incident (2026-08-20, ~-100 rating): the supervisor was
    restarted by hand while one slot drained and another cycled; the relaunch
    cut both transitions mid-flight and five held games timed out at the 5th
    percentile. The rule "never restart the supervisor while any slot is
    draining or cycling" now lives here instead of in anyone's memory:

      1. refuse while control.json has pending cycle_now entries;
      2. refuse while any drainer is running;
      3. refuse while any agent process is under 120s old (a fresh launch
         means a transition JUST happened and adoption may not be settled);
      4. only then SIGTERM the supervisor and relaunch its exact command
         line. The new supervisor ADOPTS the running agents by PID
         (supervise.py adopt()), so no agent restarts, no game is touched,
         and code changes still land at each slot's next natural boundary.
    """
    import signal
    import time
    control = _read(CONTROL, {})
    pending = control.get("cycle_now") or []
    if pending:
        print(f"REFUSED: cycle_now pending for {pending} — wait for the boundary to clear it.")
        return 1
    drainers = subprocess.run(["pgrep", "-f", "fleet.py drain"],
                              capture_output=True, text=True).stdout.split()
    if len(drainers) > 1:            # our own pgrep matches once
        print("REFUSED: a drainer is running — a restart now would cut it mid-flight.")
        return 1
    state = _read(STATE, {})
    for probe, pid in (state.get("agents") or {}).items():
        if not pid:
            continue
        # `etimes` (seconds, as an integer) is a Linux procps extension. On
        # macOS `ps` does not know it, prints its whole keyword list to STDOUT
        # instead of erroring, and int() raised ValueError -- so this interlock
        # crashed every time it was reached and safe-restart was unusable here.
        # It failed CLOSED, so nothing unsafe ever happened, but the safe path
        # was unavailable exactly when it was needed. `etime` is portable;
        # parse its [[dd-]hh:]mm:ss form.
        out = subprocess.run(["ps", "-o", "etime=", "-p", str(pid)],
                             capture_output=True, text=True).stdout.strip()
        age = _etime_seconds(out)
        if age is not None and age < 120:
            print(f"REFUSED: {probe} launched {age}s ago — a transition just "
                  f"happened; retry once it is 120s old.")
            return 1
    sup = state.get("supervisor_pid")
    if not sup:
        print("supervisor not recorded as running — nothing to restart safely.")
        return 1
    cmdline = subprocess.run(["ps", "-o", "command=", "-p", str(sup)],
                             capture_output=True, text=True).stdout.strip()
    if "supervise" not in cmdline:
        print(f"REFUSED: pid {sup} does not look like the supervisor ({cmdline!r}).")
        return 1
    print(f"quiet: no cycles pending, no drainers, all agents settled.")
    print(f"stopping supervisor {sup} ({cmdline})")
    os.kill(int(sup), signal.SIGTERM)
    for _ in range(20):
        if subprocess.run(["ps", "-p", str(sup)], capture_output=True).returncode != 0:
            break
        time.sleep(0.5)
    log = open(os.path.join(REPO, "logs", "supervisor.out"), "ab")
    subprocess.Popen(cmdline, shell=True, cwd=REPO, stdout=log, stderr=log,
                     start_new_session=True)
    time.sleep(5)
    new = _read(STATE, {})
    new_pid = new.get("supervisor_pid")
    same = sum(1 for p, pid in (new.get("agents") or {}).items()
               if pid and pid == (state.get("agents") or {}).get(p))
    print(f"relaunched: supervisor pid {new_pid}, {same} agents adopted unchanged.")
    return 0 if new_pid and new_pid != sup else 1


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "status":
        return status()
    if cmd == "safe-restart":
        return safe_restart()
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
    if cmd == "drain" and rest:
        return drain(rest[0], int(rest[1]) if len(rest) > 1 else 1800)
    if cmd == "families" and rest:
        return _slot_setting("families", rest[0], rest[1] if len(rest) > 1 else None, "families")
    # llm is the third per-slot launch override. It had no command, so the only
    # way to make control.json symmetric across slots was to hand-edit it -- the
    # one thing this tool exists to prevent.
    if cmd == "llm" and rest:
        return _slot_setting("llm", rest[0], rest[1] if len(rest) > 1 else None, "llm mode")
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
