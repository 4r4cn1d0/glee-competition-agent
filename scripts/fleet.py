#!/usr/bin/env python
"""Drive the live fleet without editing code or restarting anything.

    python scripts/fleet.py status
    python scripts/fleet.py set composite GLEE_NEGO_SPLIT_CANDIDATE=1
    python scripts/fleet.py clear conceder
    python scripts/fleet.py stop randomized
    python scripts/fleet.py bank composite
    python scripts/fleet.py peak composite 2505
    python scripts/fleet.py peak-off composite
    python scripts/fleet.py start randomized
    python scripts/fleet.py llm composite off
    python scripts/fleet.py shift 600
    python scripts/fleet.py safe-restart   # supervisor code update, interlocked

Policy, family, LLM, and launch-duration changes apply at the agent's next SHIFT
BOUNDARY.  ``stop`` keeps that boundary behavior for ordinary rotations and
activity-defense shifts.  ``bank`` is the fast safe path: a code-loaded runner
observes the atomic drain request during its normal poll, enters the SDK's own
lossless drain, and stays down.  No path signals a busy agent: measured live, a
healthy agent holds 6-9 games, and interrupting it abandons scored games.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time
from contextlib import contextmanager

import fcntl

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARMS = os.path.join(REPO, "arms.json")
CONTROL = os.path.join(REPO, "control.json")
CONTROL_LOCK = os.path.join(REPO, "logs", "control.lock")
STATE = os.path.join(REPO, "logs", "supervisor.json")
FLEET_SLOTS = frozenset({"champion", "hardliner", "conceder", "randomized", "composite"})


class ControlUpdateError(RuntimeError):
    """Raised when a control mutation cannot preserve the existing document."""


def _finite_positive(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def _validate_bank_control_schema(control: dict) -> None:
    """Reject valid-JSON type corruption before any bank read or rewrite."""
    for field in ("disabled", "drain_now", "bank_latched", "cycle_now"):
        if field not in control:
            continue
        value = control[field]
        if not isinstance(value, list) or any(
            not isinstance(slot, str) or slot not in FLEET_SLOTS for slot in value
        ):
            raise ControlUpdateError(
                f"cannot safely use {CONTROL}: {field} must be a list of physical slots"
            )
    thresholds = control.get("bank_thresholds", {})
    if not isinstance(thresholds, dict) or any(
        slot not in FLEET_SLOTS or _finite_positive(value) is None
        for slot, value in thresholds.items()
    ):
        raise ControlUpdateError(
            f"cannot safely use {CONTROL}: bank_thresholds must map physical slots "
            "to finite positive ratings"
        )
    observations = control.get("bank_observations", {})
    if not isinstance(observations, dict) or any(
        slot not in FLEET_SLOTS or not isinstance(value, dict)
        for slot, value in observations.items()
    ):
        raise ControlUpdateError(
            f"cannot safely use {CONTROL}: bank_observations must map physical "
            "slots to objects"
        )


def _read(path: str, default):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return default


def _write(path: str, data) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        # JSON's NaN/Infinity spellings are not part of the JSON standard.  A
        # non-finite bank threshold also compares in surprising ways (NaN made
        # ``rating < threshold`` false and therefore banked immediately).
        json.dump(data, handle, indent=2, allow_nan=False)
        handle.write("\n")
    os.replace(tmp, path)          # atomic: the supervisor never sees a half file


def _read_control_for_update() -> dict:
    try:
        with open(CONTROL, encoding="utf-8") as handle:
            control = json.load(
                handle,
                parse_constant=lambda token: (_ for _ in ()).throw(
                    ValueError(f"non-finite JSON constant {token}")
                ),
            )
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeError, ValueError) as exc:
        raise ControlUpdateError(
            f"cannot safely read existing {CONTROL}: {type(exc).__name__}: {exc}"
        ) from exc
    if not isinstance(control, dict):
        raise ControlUpdateError(f"cannot safely update {CONTROL}: root is not an object")
    _validate_bank_control_schema(control)
    return control


@contextmanager
def _edit_control():
    """Serialize control.json read-modify-write transactions across operators."""
    os.makedirs(os.path.dirname(CONTROL_LOCK), exist_ok=True)
    with open(CONTROL_LOCK, "a+", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        control = _read_control_for_update()
        try:
            yield control
        except Exception:
            raise
        else:
            _write(CONTROL, control)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _status_label(
    probe: str,
    *,
    alive: bool,
    disabled: set[str],
    drain_now: set[str],
) -> str:
    if probe in drain_now and alive:
        return "BANKING"
    if probe in drain_now and probe in disabled:
        return "BANKED"
    if probe in disabled and alive:
        return "STOP-QUEUED"
    if probe in disabled:
        return "DISABLED"
    return "up" if alive else "down"


def _pid_alive(pid) -> bool:
    if not pid:
        return False
    return subprocess.run(
        ["ps", "-p", str(pid)], capture_output=True
    ).returncode == 0


def _live_banking_slots(control: dict, state: dict) -> list[str]:
    # supervisor.json is written once per loop and has a launch-sized blind
    # spot. Resolve the actual process table first so start/safe-restart cannot
    # cancel or interrupt a banked runner born between state writes.
    return sorted(
        probe for probe in set(control.get("drain_now") or [])
        if _running_slot_command(probe)[0]
    )


def _slot_processes_from_ps(output: str) -> dict[str, tuple[int, str]]:
    found = {}
    for raw in output.splitlines():
        line = raw.strip()
        if "run_agent.py" not in line or "--log-dir" not in line:
            continue
        parts = line.split()
        if len(parts) < 3 or not os.path.basename(parts[1]).lower().startswith("python"):
            continue
        try:
            pid = int(parts[0])
            log_dir = parts[parts.index("--log-dir") + 1]
        except (ValueError, IndexError):
            continue
        slot = os.path.basename(log_dir.rstrip("/"))
        if slot in FLEET_SLOTS:
            found.setdefault(slot, (pid, " ".join(parts[1:])))
    return found


def _running_slot_command(probe: str) -> tuple[int | None, str]:
    output = subprocess.run(
        ["ps", "-axo", "pid=,command="], capture_output=True, text=True
    ).stdout
    actual = _slot_processes_from_ps(output).get(probe)
    if actual:
        return actual
    # Fallback for a platform whose ps format differs. State is not sufficient
    # for the safety decision when ps works, but it is still better than assuming
    # a recorded, live PID is absent.
    state = _read(STATE, {})
    pid = (state.get("agents") or {}).get(probe)
    if not _pid_alive(pid):
        return None, ""
    command = subprocess.run(
        ["ps", "-o", "command=", "-p", str(pid)],
        capture_output=True,
        text=True,
    ).stdout.strip()
    return int(pid), command


def _running_peak_watch_pid() -> int | None:
    """Return the Python peak watcher PID, ignoring launch wrappers."""
    output = subprocess.run(
        ["ps", "-axo", "pid=,command="], capture_output=True, text=True
    ).stdout
    for raw in output.splitlines():
        line = raw.strip()
        if "scripts/peak_watch.py" not in line:
            continue
        parts = line.split()
        if len(parts) < 3 or not os.path.basename(parts[1]).lower().startswith("python"):
            continue
        try:
            return int(parts[0])
        except (ValueError, IndexError):
            continue
    return None


def _ensure_peak_watcher() -> int | None:
    """Start the durable minute watcher when arming the first threshold."""
    existing = _running_peak_watch_pid()
    if existing:
        return existing
    python = os.path.join(REPO, ".venv", "bin", "python")
    if not os.path.exists(python):
        python = sys.executable
    log_path = os.path.join(REPO, "logs", "peak_watch.out")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    try:
        with open(log_path, "a", encoding="utf-8") as output:
            proc = subprocess.Popen(
                [python, "scripts/peak_watch.py"],
                cwd=REPO,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                close_fds=True,
            )
    except OSError as exc:
        print(f"REFUSED: cannot start peak watcher: {exc}", file=sys.stderr)
        return None
    # Catch import/singleton failures before claiming the threshold is protected.
    for _ in range(8):
        time.sleep(0.25)
        running = _running_peak_watch_pid()
        if running:
            return running
        if proc.poll() is not None:
            break
    print(
        f"REFUSED: peak watcher exited during startup; inspect {log_path}.",
        file=sys.stderr,
    )
    return None


def _validate_bank_target(probe: str) -> bool:
    if probe not in FLEET_SLOTS:
        print(f"REFUSED: unknown physical slot {probe!r}; expected one of "
              f"{', '.join(sorted(FLEET_SLOTS))}.", file=sys.stderr)
        return False
    pid, command = _running_slot_command(probe)
    if pid and "--max-time" not in command:
        print(f"REFUSED: {probe} pid {pid} is an unbounded legacy runner and "
              f"cannot prove a safe fallback boundary. Leave it untouched until "
              f"a bounded code-loaded process replaces it.", file=sys.stderr)
        return False
    return True


def _mark_banked(control: dict, probe: str) -> None:
    disabled = set(control.get("disabled") or [])
    drain_now = set(control.get("drain_now") or [])
    latched = set(control.get("bank_latched") or [])
    disabled.add(probe)
    drain_now.add(probe)
    latched.add(probe)
    control["disabled"] = sorted(disabled)
    control["drain_now"] = sorted(drain_now)
    control["bank_latched"] = sorted(latched)


def status() -> int:
    arms, control = _read(ARMS, {}), _read(CONTROL, {})
    state = _read(STATE, {})
    shift = control.get("shift_seconds", 900)
    disabled = set(control.get("disabled") or [])
    drain_now = set(control.get("drain_now") or [])
    latched = set(control.get("bank_latched") or [])
    thresholds = control.get("bank_thresholds") or {}
    running = subprocess.run(["pgrep", "-f", "run_agent.py --probe"],
                             capture_output=True, text=True).stdout.split()
    watcher = _running_peak_watch_pid()
    print(f"shift {shift}s   supervisor {'up' if state.get('supervisor_pid') else 'down'}"
          f"   {len(running)} agent processes   peak-watch "
          f"{'up pid=' + str(watcher) if watcher else 'down'}\n")
    print(f"  {'agent':12s} {'state':10s} {'age':>6s}  flags")
    for probe, pid in (state.get("agents") or {}).items():
        alive = pid and str(pid) in running
        age = "-"
        if alive:
            out = subprocess.run(["ps", "-o", "etime=", "-p", str(pid)],
                                 capture_output=True, text=True).stdout.strip()
            age = out or "-"
        label = _status_label(
            probe, alive=bool(alive), disabled=disabled, drain_now=drain_now
        )
        flags = " ".join(f"{k}={v}" for k, v in sorted((arms.get(probe) or {}).items()))
        peak = _finite_positive(thresholds.get(probe))
        peak_state = []
        if peak is not None:
            peak_state.append(f"peak>={peak:.2f}")
        if probe in latched:
            peak_state.append("bank-latched")
        if peak_state:
            flags = " ".join(part for part in (flags, f"[{' '.join(peak_state)}]") if part)
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
    if probe not in FLEET_SLOTS:
        print(f"REFUSED: unknown physical slot {probe!r}.", file=sys.stderr)
        return 1
    # Never let ``start`` erase a fast-bank request before the still-live runner
    # has observed it.  Once the process is down, clearing drain_now is safe;
    # retain the one-shot latch so a planned activity-defense shift cannot bank
    # itself again immediately at the same already-observed peak.
    live_pid, _command = _running_slot_command(probe) if on else (None, "")
    with _edit_control() as control:
        if on and probe in set(control.get("drain_now") or []) and live_pid:
            print(
                f"REFUSED: {probe} is still banking as pid {live_pid}; wait until "
                "it is fully down before starting a defense shift.",
                file=sys.stderr,
            )
            return 1
        disabled = set(control.get("disabled") or [])
        disabled.discard(probe) if on else disabled.add(probe)
        control["disabled"] = sorted(disabled)
        if on:
            drain_now = set(control.get("drain_now") or [])
            drain_now.discard(probe)
            control["drain_now"] = sorted(drain_now)
    if on:
        print(f"{probe}: enabled; the one-shot bank latch is retained and the "
              f"supervisor relaunches it within ~30s")
    else:
        print(f"{probe}: stop queued for its normal shift boundary; it will drain "
              f"current games and stay down (no games abandoned)")
    return 0


def bank(probe: str) -> int:
    """Request the runner's immediate SDK-native drain and disable relaunch."""
    if not _validate_bank_target(probe):
        return 1
    with _edit_control() as control:
        _mark_banked(control, probe)
        observations = dict(control.get("bank_observations") or {})
        observations[probe] = {
            "kind": "manual",
            "ts": time.time(),
            "pid": _running_slot_command(probe)[0],
        }
        control["bank_observations"] = observations
    print(f"{probe}: bank requested — a code-loaded runner stops queueing on its "
          f"next poll, completes every in-flight game, and stays down. An older "
          f"runner safely falls back to its normal shift boundary.")
    return 0


def bank_observed_peak(
    probe: str, rating: float, observation: dict | None = None
) -> bool:
    """Atomically bank an armed, unlatched slot at an observed threshold."""
    if not _validate_bank_target(probe):
        return False
    clean_rating = _finite_positive(rating)
    if clean_rating is None:
        return False
    with _edit_control() as control:
        thresholds = control.get("bank_thresholds") or {}
        latched = set(control.get("bank_latched") or [])
        disabled = set(control.get("disabled") or [])
        threshold = _finite_positive(thresholds.get(probe))
        if threshold is None:
            return False
        if probe in latched or probe in disabled or clean_rating < threshold:
            return False
        _mark_banked(control, probe)
        event = {
            "kind": "authenticated-overall-peak",
            "ts": time.time(),
            "threshold": threshold,
            "observed_rating": clean_rating,
        }
        if observation:
            event.update(observation)
            # The authoritative values are those checked under this lock.
            event.update({"threshold": threshold, "observed_rating": clean_rating})
        # Validate before replacing control.json, so a bad enrichment can never
        # turn an observed peak into an unaudited or malformed control write.
        json.dumps(event, allow_nan=False)
        observations = dict(control.get("bank_observations") or {})
        observations[probe] = event
        control["bank_observations"] = observations
    print(f"{probe}: authenticated overall {clean_rating:.2f} reached armed bank "
          f"threshold {threshold:.2f}; immediate lossless drain requested.")
    return True


def set_peak(probe: str, value: str | None) -> int:
    """Arm/rearm or remove a one-shot authenticated overall-rating bank."""
    if probe not in FLEET_SLOTS:
        print(f"REFUSED: unknown physical slot {probe!r}.", file=sys.stderr)
        return 1
    threshold = None
    watcher_pid = None
    if value is not None:
        threshold = _finite_positive(value)
        if threshold is None:
            print(
                f"REFUSED: threshold must be a finite positive rating, got {value!r}.",
                file=sys.stderr,
            )
            return 1
        watcher_pid = _ensure_peak_watcher()
        if watcher_pid is None:
            return 1
    with _edit_control() as control:
        thresholds = dict(control.get("bank_thresholds") or {})
        latched = set(control.get("bank_latched") or [])
        observations = dict(control.get("bank_observations") or {})
        if value is None:
            thresholds.pop(probe, None)
            latched.discard(probe)
            observations.pop(probe, None)
            message = f"{probe}: automatic peak banking removed"
        else:
            assert threshold is not None
            thresholds[probe] = threshold
            latched.discard(probe)
            observations.pop(probe, None)
            message = (f"{probe}: automatic one-shot bank armed at authenticated "
                       f"overall rating >= {threshold:.2f} (watcher pid {watcher_pid})")
        control["bank_thresholds"] = thresholds
        control["bank_latched"] = sorted(latched)
        control["bank_observations"] = observations
    print(message)
    return 0


def shift(seconds: int) -> int:
    with _edit_control() as control:
        control["shift_seconds"] = int(seconds)
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
    with _edit_control() as control:
        table = dict(control.get(key) or {})
        if value is None or value == "-":
            table.pop(probe, None)
            print(f"{probe}: {label} override cleared — reverts to the default at next launch.")
        else:
            table[probe] = value
            print(f"{probe}: {label} = {value} — applies at next launch.")
        control[key] = table
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
    # A malformed control must not erase the very drain interlock that keeps a
    # banked agent's in-flight games safe.
    control = _read_control_for_update()
    pending = control.get("cycle_now") or []
    if pending:
        print(f"REFUSED: cycle_now pending for {pending} — wait for the boundary to clear it.")
        return 1
    state = _read(STATE, {})
    live_banks = _live_banking_slots(control, state)
    if live_banks:
        print(f"REFUSED: active bank drain for {live_banks} — restarting the "
              f"supervisor could interrupt scored in-flight games.")
        return 1
    drainers = subprocess.run(["pgrep", "-f", "fleet.py drain"],
                              capture_output=True, text=True).stdout.split()
    if len(drainers) > 1:            # our own pgrep matches once
        print("REFUSED: a drainer is running — a restart now would cut it mid-flight.")
        return 1
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
    # The supervisor's SIGTERM handler does NOT exit promptly: it sets a stop
    # flag, SIGINTs every agent, and then blocks until each one exits on its own
    # -- deliberately, because killing an agent mid-game abandons scored games.
    # That takes MINUTES, not milliseconds. The old code waited 10s and then
    # launched a replacement, which found the lock still held by the live old
    # supervisor and refused to start. safe_restart then read the STALE state
    # file and printed "relaunched: ... agents adopted unchanged", so the caller
    # was told it had succeeded while the fleet was in fact draining to zero with
    # no supervisor to bring it back. On 2026-08-22 that cost ~31 timed-out games
    # and a 30-minute queue ban on four agents.
    #
    # Wait for the process to ACTUALLY be gone, report honestly if it is not, and
    # never launch a replacement while the lock is still held.
    deadline = time.time() + 1800
    warned = False
    while subprocess.run(["ps", "-p", str(sup)], capture_output=True).returncode == 0:
        if time.time() > deadline:
            print(f"REFUSED to relaunch: supervisor {sup} is STILL draining after "
                  f"30 minutes. It is waiting for agents to finish their games and "
                  f"will not be interrupted. No replacement was started; re-run "
                  f"safe-restart once it has exited.")
            return 1
        if not warned:
            print("  supervisor is draining its agents -- this takes minutes, not "
                  "seconds. Waiting; nothing will be killed.", flush=True)
            warned = True
        time.sleep(5)
    lock = os.path.join(REPO, "logs", "supervisor.lock")
    if os.path.exists(lock):
        try:
            held = int(open(lock).read().strip())
        except (OSError, ValueError):
            held = None
        if held and subprocess.run(["ps", "-p", str(held)],
                                   capture_output=True).returncode == 0:
            print(f"REFUSED to relaunch: {lock} is held by LIVE pid {held}. "
                  f"A replacement would refuse to start and this command would "
                  f"report a success that did not happen.")
            return 1
        os.remove(lock)          # provably stale: the pid in it is not running
        print(f"  cleared stale lock (held dead pid {held})")
    log = open(os.path.join(REPO, "logs", "supervisor.out"), "ab")
    subprocess.Popen(cmdline, shell=True, cwd=REPO, stdout=log, stderr=log,
                     start_new_session=True)
    time.sleep(5)
    new = _read(STATE, {})
    new_pid = new.get("supervisor_pid")
    same = sum(1 for p, pid in (new.get("agents") or {}).items()
               if pid and pid == (state.get("agents") or {}).get(p))
    # Report the TRUTH. The old version printed success whenever it could read a
    # state file, including when that file was the dead supervisor's own.
    if not new_pid or new_pid == sup:
        print(f"FAILED: no new supervisor recorded (state still shows {new_pid}). "
              f"The fleet may have no supervisor -- check `fleet.py status` NOW.")
        return 1
    print(f"relaunched: supervisor pid {new_pid}, {same} agents adopted unchanged.")
    return 0


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
    if cmd == "bank" and rest:
        return bank(rest[0])
    if cmd == "peak" and len(rest) >= 2:
        return set_peak(rest[0], rest[1])
    if cmd == "peak-off" and rest:
        return set_peak(rest[0], None)
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
    try:
        raise SystemExit(main())
    except ControlUpdateError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        raise SystemExit(1)
