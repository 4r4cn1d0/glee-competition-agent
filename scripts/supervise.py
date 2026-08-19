#!/usr/bin/env python
"""Keep the fleet playing, without stopping, until told otherwise.

    python scripts/supervise.py                 # run in the foreground
    nohup python scripts/supervise.py &         # detach and survive the terminal
    python scripts/supervise.py --stop          # stop everything cleanly

Why this exists: the competition ranks on a rating shrunk by g/(g+30), and the
top of the leaderboard has ~24,000 games per family against our ~80. At our
measured throughput that gap is closable in the time remaining — but only by
playing continuously. An hour not playing costs ~100 games per family and there
is no way to earn them back later. A bounded run that has to be relaunched by
hand is therefore the single largest risk to the result, larger than any
strategy bug.

So: no time bound, and anything that dies is restarted. Exits are expected
(a competition-closed error, a network drop, an OOM); the supervisor treats them
as events to recover from rather than reasons to stop.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(REPO, "logs", "supervisor.json")

FLEET = [
    ("GLEE_KEY_TEST1", "champion"),
    ("GLEE_KEY_TEST2", "hardliner"),
    ("GLEE_KEY_TEST3", "conceder"),
    ("GLEE_KEY_TEST4", "randomized"),
    ("GLEE_KEY_TEST5", "composite"),
]

#: Per-agent experiment arms. Only the named agent gets the flag, so every other
#: agent stays a control and the comparison is clean. Empty dict = no experiment.
#:
#: Ratings are permanently scored, so arms go on the agent with the most headroom
#: in the affected family, never on whichever agent currently holds our
#: leaderboard place.
ARMS = {
    # conceder's negotiation is the weakest cell in the fleet (41.1 percentile),
    # so it has the most room and the least to lose. The legacy clamp let an
    # opponent's lowball cap our anchor, collapsing a configured 4.00x ask to
    # 1.05x our own valuation and making the anchor knobs inert.
    "conceder": {"GLEE_NEGO_BOUND_AS_FLOOR": "1"},
}

#: Restart backoff. A tight relaunch loop against a server that is refusing us
#: wastes the rate limit and can trip the platform's crash-loop cooldown
#: (three consecutive self-timeouts closes the queue for 30 minutes).
BACKOFF = [5, 15, 30, 60, 120, 300]


def load_env() -> None:
    path = os.path.join(REPO, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


class Agent:
    def __init__(self, env_key: str, probe: str, args):
        self.env_key = env_key
        self.probe = probe
        self.args = args
        self.proc: subprocess.Popen | None = None
        self.restarts = 0
        self.started_at = 0.0
        self.next_try = 0.0

    @property
    def alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def launch(self) -> bool:
        key = os.environ.get(self.env_key)
        if not key:
            return False
        log_dir = os.path.join("logs", self.probe)
        cmd = [os.path.join(REPO, ".venv", "bin", "python"), "run_agent.py",
               "--probe", self.probe, "--log-dir", log_dir,
               "--llm-mode", self.args.llm_mode,
               "--concurrency", str(self.args.concurrency),
               "--poll-interval", str(self.args.poll_interval),
               "--families", self.args.families, "--quiet"]
        if self.probe == "randomized":
            cmd += ["--seed", "20260819"]
        env = dict(os.environ, GLEE_API_KEY=key, GLEE_LOG_DIR=log_dir)
        env.update(ARMS.get(self.probe, {}))
        out = open(os.path.join(REPO, "logs", f"{self.probe}.out"), "a", encoding="utf-8")
        arm = ARMS.get(self.probe) or {}
        out.write(f"\n===== supervisor launch {time.strftime('%Y-%m-%d %H:%M:%S')} "
                  f"(restart #{self.restarts}){' arm=' + repr(arm) if arm else ''} =====\n")
        out.flush()
        self.proc = subprocess.Popen(cmd, cwd=REPO, env=env, stdout=out,
                                     stderr=subprocess.STDOUT)
        self.started_at = time.time()
        return True

    def stop(self) -> None:
        """SIGINT so run_agent leaves the matchmaking queue on the way out.

        An agent left queued keeps getting matched after it stops polling, and
        loses every one of those games to the turn timeout.
        """
        if self.alive:
            try:
                self.proc.send_signal(signal.SIGINT)
            except ProcessLookupError:
                pass



def _claim_singleton(name: str) -> None:
    """Refuse to start if another instance is already running.

    Two supervisors each launch their own five agents and both overwrite
    logs/supervisor.json, so neither can see the other's children. That is
    exactly how fifteen agent processes ended up sharing five API keys, each
    key's 60 req/min budget split three ways and the processes racing each
    other for the same moves. A lock file holding a live PID makes the mistake
    impossible rather than merely unlikely.
    """
    import errno
    lock = os.path.join(REPO, "logs", f"{name}.lock")
    os.makedirs(os.path.dirname(lock), exist_ok=True)
    if os.path.exists(lock):
        try:
            with open(lock, encoding="utf-8") as handle:
                other = int(handle.read().strip())
        except (ValueError, OSError):
            other = None
        if other and other != os.getpid():
            try:
                os.kill(other, 0)          # signal 0 just tests existence
            except OSError as exc:
                if exc.errno != errno.ESRCH:
                    raise
            else:
                print(f"{name} already running as pid {other}; refusing to start "
                      f"a second one. Stop it first, or remove {lock} if stale.",
                      file=sys.stderr)
                raise SystemExit(1)
    with open(lock, "w", encoding="utf-8") as handle:
        handle.write(str(os.getpid()))
    import atexit
    atexit.register(lambda: os.path.exists(lock) and os.remove(lock))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--llm-mode", default="off", choices=("off", "messages", "full"))
    parser.add_argument("--families", default="bargaining,negotiation,persuasion")
    parser.add_argument("--only", help="comma-separated probe names")
    parser.add_argument("--check-interval", type=float, default=10.0)
    parser.add_argument("--stop", action="store_true")
    args = parser.parse_args()
    load_env()

    if args.stop:
        if not os.path.exists(STATE):
            print("no supervisor state; nothing to stop")
            return 0
        with open(STATE, encoding="utf-8") as handle:
            state = json.load(handle)
        for pid in [state.get("supervisor_pid")] + list(state.get("agents", {}).values()):
            if not pid:
                continue
            try:
                os.kill(int(pid), signal.SIGINT)
            except (ProcessLookupError, ValueError):
                pass
        print("sent SIGINT to the supervisor and its agents; they drain then exit")
        return 0

    _claim_singleton("supervisor")
    only = {p.strip() for p in args.only.split(",")} if args.only else None
    agents = [Agent(k, p, args) for k, p in FLEET if not only or p in only]

    stopping = {"flag": False}

    def handle(signum, frame):
        stopping["flag"] = True
    signal.signal(signal.SIGINT, handle)
    signal.signal(signal.SIGTERM, handle)

    print(f"supervising {len(agents)} agents "
          f"(concurrency={args.concurrency}, llm={args.llm_mode}). Ctrl-C to stop.", flush=True)
    started = time.time()
    while not stopping["flag"]:
        now = time.time()
        for agent in agents:
            if agent.alive or now < agent.next_try:
                continue
            if agent.proc is not None:                 # it died
                ran = now - agent.started_at
                agent.restarts += 1
                delay = BACKOFF[min(agent.restarts - 1, len(BACKOFF) - 1)] if ran < 60 else 5
                agent.next_try = now + delay
                print(f"  [{time.strftime('%H:%M:%S')}] {agent.probe} exited after "
                      f"{ran:.0f}s (rc={agent.proc.returncode}); restart #{agent.restarts} "
                      f"in {delay}s", flush=True)
                # Clear the dead handle, or the next pass re-enters this branch
                # instead of relaunching and the agent never comes back.
                agent.proc = None
                continue
            if agent.launch():
                print(f"  [{time.strftime('%H:%M:%S')}] {agent.probe} started "
                      f"pid={agent.proc.pid}", flush=True)
            else:
                print(f"  {agent.probe}: {agent.env_key} not set, skipping", flush=True)
                agent.next_try = float("inf")

        with open(STATE, "w", encoding="utf-8") as handle:
            json.dump({"supervisor_pid": os.getpid(),
                       "started": started,
                       "agents": {a.probe: (a.proc.pid if a.alive else None) for a in agents},
                       "restarts": {a.probe: a.restarts for a in agents}}, handle, indent=2)
        time.sleep(args.check_interval)

    print("\nstopping — agents drain their in-flight games first", flush=True)
    for agent in agents:
        agent.stop()
    deadline = time.time() + 180
    while time.time() < deadline and any(a.alive for a in agents):
        time.sleep(2)
    for agent in agents:
        if agent.alive:
            agent.proc.kill()
    if os.path.exists(STATE):
        os.remove(STATE)
    uptime = (time.time() - started) / 3600
    print(f"stopped after {uptime:.2f}h; restarts: "
          f"{ {a.probe: a.restarts for a in agents} }")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
