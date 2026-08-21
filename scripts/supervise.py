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

#: Per-agent experiment arms live in arms.json, NOT in this file, so an arm can
#: be changed and applied to one agent without restarting the whole fleet.
#: Format: {"<probe>": {"ENV_VAR": "value"}}
ARMS_PATH = os.path.join(REPO, "arms.json")


#: A game we have not moved in for this long is probably one we are timing out.
#: The server closes a game after 120s on your turn, and three consecutive
#: self-timeouts suspend queue joins for 30 minutes. Catching the FIRST one is
#: the difference between a blip and a half-hour outage.
STALL_SECONDS = 100


def active_games(env_key: str) -> int | None:
    """How many games this agent currently has in flight, per the server.

    Authoritative, unlike the local move log: a game where we are waiting on the
    opponent produces no turns of ours, so log recency cannot tell "idle" from
    "mid-game". Returns None when the answer is unknown, which callers must
    treat as busy.
    """
    key = os.environ.get(env_key)
    if not key:
        return None
    try:
        from glee_sdk import GleeClient
        return int(GleeClient(api_key=key).stats().get("active_games", 0))
    except Exception:
        return None


def stalled_games(probe: str) -> int:
    """Games whose last move by us is old enough to be timing out right now."""
    path = os.path.join(REPO, "logs", probe, "turns.jsonl")
    if not os.path.exists(path):
        return 0
    now = time.time()
    last: dict = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle.readlines()[-4000:]:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                gid = rec.get("game_id")
                if gid:
                    last[gid] = max(last.get(gid, 0.0), rec.get("ts", 0.0))
    except OSError:
        return 0
    # Only count games touched recently enough to still be live.
    return sum(1 for t in last.values() if STALL_SECONDS < now - t < 600)


def load_arms() -> dict:
    """Read the arm assignments fresh. Called at every agent launch."""
    try:
        with open(ARMS_PATH, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


#: A cycle request names probes to drain and relaunch, one per line. Written by
#: `supervise.py --cycle <probe>` and consumed by the running supervisor, so a
#: deployment costs one agent's in-flight games instead of all five.
CYCLE_PATH = os.path.join(REPO, "logs", "cycle.request")

#: How long a draining agent gets to finish its games before we give up on it.
#: Measured live: persuasion games run a median 88s and negotiation p90 is 214s.
#: A SIGKILLed agent submits nothing, the server closes the game on its 120s
#: turn timeout, and an ABANDONED game is scored at the 5th percentile —
#: strictly worse than any legal move. Killing the fleet after 60s once cost
#: ~91 games across five agents. Never rush this.
DRAIN_SECONDS = 300

#: Stall watchdog. A LIVE process holding zero games and starting none is not a
#: state `alive` can see, and it is what cost the fleet an hour on 2026-08-22.
#: The check is deliberately conservative in three ways, because restarting an
#: agent that is merely between games would be worse than the stall:
#:   * it fires ONLY on an exact 0 from the server; None means "unknown", which
#:     callers must treat as busy (see active_games), so a flaky API never kills;
#:   * it needs the zero to PERSIST, since a healthy agent dips to 0 briefly
#:     between matches;
#:   * it leaves a fresh process alone, so a slow start is not mistaken for a
#:     stall.
#: Cost is one request per agent per HEALTH_EVERY seconds, which has to fit
#: inside the 60/min per-key budget the agent's own polling already shares.
STALL_GRACE = 420.0      # ignore a process younger than this
STALL_SECONDS = 300.0    # active_games must read 0 for this long
HEALTH_EVERY = 120.0     # seconds between health probes per agent

#: Each agent is launched with a bounded --max-time and then relaunched. This is
#: the ONLY safe way to apply a config change.
#:
#: SIGINT does not drain: it propagates straight out of the SDK's poll loop, so
#: every in-flight game is abandoned and hits the server's 120s turn clock.
#: Three such timeouts suspend queue joins for 30 minutes, and cycling caused
#: exactly that outage three separate times.
#:
#: --max-time uses the SDK's own drain instead: it stops STARTING games, plays
#: the in-flight ones to completion, and exits 0. Zero games abandoned, ever.
#: The cost is that an arms.json change lands at the next boundary rather than
#: instantly, which is a trade worth making.
AGENT_MAX_TIME = 900

#: Live control surface, re-read every loop. Nothing here needs a code change or
#: a supervisor restart.
#:   {"shift_seconds": 900,
#:    "disabled": ["conceder"],        # drain at next boundary, do not relaunch
#:    "cycle_now": ["composite"]}      # apply arms.json at next boundary
CONTROL_PATH = os.path.join(REPO, "control.json")


def load_control() -> dict:
    try:
        with open(CONTROL_PATH, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}

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
        self.adopted_pid: int | None = None
        self.restarts = 0
        self.started_at = 0.0
        self.next_try = 0.0
        #: Stall watchdog state. `alive` only asks whether the PROCESS exists,
        #: which is exactly the question that missed the 2026-08-22 outage: three
        #: agents sat at 82-90% CPU, past their shift boundary, holding zero
        #: games and queueing none, for over an hour. The process was up the
        #: whole time, so nothing here noticed until a human asked.
        self.zero_since = 0.0        # when active_games first read 0
        self.last_health = 0.0       # last time we spent an API call on it
        self.stall_kills = 0

    @property
    def alive(self) -> bool:
        if self.adopted_pid is not None:
            try:
                os.kill(self.adopted_pid, 0)   # signal 0 only tests existence
                return True
            except OSError:
                self.adopted_pid = None        # it exited; we may relaunch now
                return False
        return self.proc is not None and self.proc.poll() is None

    @property
    def pid(self) -> int | None:
        if self.adopted_pid is not None:
            return self.adopted_pid
        return self.proc.pid if self.proc else None

    def adopt(self, pid: int) -> None:
        """Supervise an already-running agent without disturbing it.

        A running agent holds 6-9 scored games at all times, so stopping one to
        bring it under supervision would abandon them and risk a 30-minute queue
        ban. We do not need to own the process to supervise it — only to notice
        when it exits and start its replacement. The adopted process keeps its
        original (unbounded) shift, so an arms.json change reaches it only when
        it eventually exits; its replacement is launched with a bounded shift and
        joins the normal rotation from then on.
        """
        self.adopted_pid = pid

    def launch(self) -> bool:
        key = os.environ.get(self.env_key)
        if not key:
            return False
        log_dir = os.path.join("logs", self.probe)
        ctl = load_control()
        # A slot (key + log dir + arms entry) is separate from the POLICY it plays
        # and the FAMILIES it queues for. Keeping them separate lets a slot be
        # repurposed -- e.g. spending our weakest agent as a single-family probe to
        # triple the sample rate in the family we are trying to fix -- without
        # moving API keys around or losing that slot's log history.
        policy = (ctl.get("policy") or {}).get(self.probe) or self.probe
        llm_mode = (ctl.get("llm") or {}).get(self.probe) or self.args.llm_mode
        families = (ctl.get("families") or {}).get(self.probe) or self.args.families
        cmd = [os.path.join(REPO, ".venv", "bin", "python"), "run_agent.py",
               "--probe", policy, "--log-dir", log_dir,
               "--llm-mode", llm_mode,
               "--concurrency", str(self.args.concurrency),
               "--poll-interval", str(self.args.poll_interval),
               "--families", families, "--quiet",
               "--max-time", str(int(ctl.get("shift_seconds")
                                     or self.args.agent_max_time))]
        if policy == "randomized":
            cmd += ["--seed", "20260819"]
        # GLEE_PROBE lets the agent re-read its own arm from arms.json while it
        # runs, so a flag change lands without a restart -- and therefore without
        # abandoning the 6-9 games a restart costs, each scored at the 5th
        # percentile, three of which in a row earn a 30-minute queue ban.
        env = dict(os.environ, GLEE_API_KEY=key, GLEE_LOG_DIR=log_dir,
                   GLEE_PROBE=self.probe)
        if llm_mode != "off":
            env_file = {}
            with open(os.path.join(REPO, ".env"), encoding="utf-8") as fh:
                for line in fh:
                    if "=" in line and not line.strip().startswith("#"):
                        k2, v2 = line.strip().split("=", 1)
                        env_file[k2] = v2
            for k2 in ("ANTHROPIC_API_KEY", "LLM_MODEL"):
                if env_file.get(k2):
                    env[k2] = env_file[k2]
            env.setdefault("GLEE_LLM_MAX_CALLS", "800")
            # the $15 budget survives only on the cheap prompts: LLM wording is
            # fenced to persuasion; negotiation/bargaining stay fully programmatic
            env.setdefault("GLEE_LLM_FAMILIES", "persuasion")
        env.update(load_arms().get(self.probe, {}))
        out = open(os.path.join(REPO, "logs", f"{self.probe}.out"), "a", encoding="utf-8")
        arm = load_arms().get(self.probe) or {}
        out.write(f"\n===== supervisor launch {time.strftime('%Y-%m-%d %H:%M:%S')} "
                  f"(restart #{self.restarts}) policy={policy} families={families}"
                  f"{' arm=' + repr(arm) if arm else ''} =====\n")
        out.flush()
        self.proc = subprocess.Popen(cmd, cwd=REPO, env=env, stdout=out,
                                     stderr=subprocess.STDOUT)
        self.started_at = time.time()
        return True

    def quiet(self) -> bool:
        """True only if the server says this agent holds no games right now.

        SIGINT makes run_agent stop queueing AND stop submitting moves for games
        already in progress, so every in-flight game is then guaranteed to hit
        the 120s turn clock. Three such timeouts suspend the agent's queue joins
        for 30 minutes. Cycling has caused that outage three separate times.
        Waiting for a genuinely quiet moment is the only safe way to signal.
        """
        n = active_games(self.env_key)
        return n == 0

    def drain(self, seconds: float = DRAIN_SECONDS) -> bool:
        """Stop this agent and wait, however long it takes, for it to exit.

        There is deliberately no give-up path. Once SIGINT is sent the agent has
        stopped queueing and is playing out its in-flight games — that decision
        cannot be un-sent. An earlier version bailed out after a deadline and
        "left it alone", which meant a half-drained agent sat there not
        submitting moves; three of its games hit the 120s turn timeout and the
        platform suspended the agent's queue joins for 30 minutes ("last 3 games
        all timed out on its turn"). Waiting is always cheaper than that.

        ``seconds`` now only controls how often we complain while waiting.
        """
        self.stop()
        started = time.time()
        warned = False
        while self.alive:
            waited = time.time() - started
            if waited > seconds and not warned:
                print(f"  [{time.strftime('%H:%M:%S')}] {self.probe} still draining "
                      f"after {waited:.0f}s — waiting rather than abandoning its "
                      f"games", flush=True)
                warned = True
            time.sleep(2)
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
    parser.add_argument("--agent-max-time", type=float, default=AGENT_MAX_TIME,
                        help="seconds before an agent drains and is relaunched; "
                             "this is how config changes are applied safely")
    parser.add_argument("--check-interval", type=float, default=10.0)
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("--cycle", metavar="PROBE",
                        help="drain and relaunch just these agents (comma-separated) "
                             "so an arms.json change applies without restarting the fleet")
    args = parser.parse_args()
    load_env()

    if args.cycle:
        os.makedirs(os.path.join(REPO, "logs"), exist_ok=True)
        with open(CYCLE_PATH, "w", encoding="utf-8") as handle:
            handle.write("\n".join(p.strip() for p in args.cycle.split(",") if p.strip()))
        print(f"requested cycle of {args.cycle}; the running supervisor will drain "
              f"and relaunch them (up to {DRAIN_SECONDS}s each)")
        return 0

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
    def _running_probe_pids() -> dict:
        out = subprocess.run(["ps", "-axo", "pid=,command="],
                             capture_output=True, text=True).stdout
        found = {}
        for line in out.splitlines():
            line = line.strip()
            if "run_agent.py" not in line or "--probe" not in line:
                continue
            if "/python" not in line.lower() and "Python" not in line:
                continue
            parts = line.split()
            try:
                pid = int(parts[0])
            except (ValueError, IndexError):
                continue
            # Key on the SLOT, which is the log directory, NOT on --probe.
            # --probe carries the POLICY, and control.json's policy override
            # lets several slots run the same one: with conceder mapped to the
            # composite policy, both its command line and Agent 5's say
            # "--probe composite". Keyed that way, setdefault recorded only the
            # first, the other slot looked unadopted, and the supervisor
            # launched a SECOND process against a key that already had one --
            # two agents sharing one 60/min budget, which is how this fleet has
            # earned rate-limit bans before. Observed 2026-08-22 immediately
            # after a safe-restart: it reported "2 agents adopted" with four
            # running, then started a duplicate conceder.
            if "--log-dir" in parts:
                slot = os.path.basename(parts[parts.index("--log-dir") + 1].rstrip("/"))
                found.setdefault(slot, pid)
            elif "--probe" in parts:
                found.setdefault(parts[parts.index("--probe") + 1], pid)
        return found

    only = {p.strip() for p in args.only.split(",")} if args.only else None
    agents = [Agent(k, p, args) for k, p in FLEET if not only or p in only]

    stopping = {"flag": False}

    def handle(signum, frame):
        stopping["flag"] = True
    signal.signal(signal.SIGINT, handle)
    signal.signal(signal.SIGTERM, handle)

    pending_cycle: set = set()
    existing = _running_probe_pids()
    for agent in agents:
        pid = existing.get(agent.probe)
        if pid:
            agent.adopt(pid)
            print(f"  adopted already-running {agent.probe} pid={pid} "
                  f"(no games disturbed)", flush=True)

    print(f"supervising {len(agents)} agents "
          f"(concurrency={args.concurrency}, llm={args.llm_mode}). Ctrl-C to stop.", flush=True)
    started = time.time()
    while not stopping["flag"]:
        now = time.time()
        control = load_control()
        disabled = set(control.get("disabled") or [])
        for agent in agents:
            if agent.probe in disabled:
                if agent.alive:
                    continue          # let its shift finish; do not signal it
                if agent.proc is not None:
                    print(f"  [{time.strftime('%H:%M:%S')}] {agent.probe} disabled via "
                          f"control.json; leaving it down", flush=True)
                    agent.proc = None
                agent.next_try = now + 30
                continue
            if agent.alive:
                # STALL WATCHDOG -- see STALL_GRACE. A live process is normally
                # skipped entirely, which is precisely how three agents idled
                # for an hour with the supervisor reporting them healthy.
                if (agent.probe not in pending_cycle
                        and now - agent.started_at >= STALL_GRACE
                        and now - agent.last_health >= HEALTH_EVERY):
                    agent.last_health = now
                    live = active_games(agent.env_key)
                    if live is None or live > 0:
                        agent.zero_since = 0.0        # unknown counts as busy
                    else:
                        if agent.zero_since == 0.0:
                            agent.zero_since = now
                        elif now - agent.zero_since >= STALL_SECONDS:
                            pid = agent.pid
                            agent.stall_kills += 1
                            print(f"  [{time.strftime('%H:%M:%S')}] {agent.probe} STALLED: "
                                  f"alive as pid={pid} but active_games=0 for "
                                  f"{now - agent.zero_since:.0f}s. Restarting "
                                  f"(stall kill #{agent.stall_kills}). Nothing is in "
                                  f"flight, so no games are stranded.", flush=True)
                            agent.zero_since = 0.0
                            try:
                                if pid:
                                    os.kill(pid, signal.SIGKILL)
                            except OSError as exc:
                                print(f"    could not signal {pid}: {exc}", flush=True)
                            agent.adopted_pid = None
                            agent.proc = None
                            agent.next_try = now + 5
                continue
            if now < agent.next_try:
                continue
            if agent.proc is not None:                 # it exited
                ran = now - agent.started_at
                rc = agent.proc.returncode if agent.proc else 0
                # A clean exit at the --max-time boundary is the DESIGNED
                # rotation, not a failure. Relaunch at once and do not let the
                # crash backoff escalate.
                if rc == 0 and ran >= agent.args.agent_max_time * 0.8:
                    print(f"  [{time.strftime('%H:%M:%S')}] {agent.probe} completed its "
                          f"{ran:.0f}s shift and drained cleanly; relaunching",
                          flush=True)
                    agent.proc = None
                    agent.next_try = 0.0
                    continue
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
                      f"pid={agent.pid}", flush=True)
            else:
                print(f"  {agent.probe}: {agent.env_key} not set, skipping", flush=True)
                agent.next_try = float("inf")

        # A cycle request drains and relaunches only the named agents, so an
        # arm change costs one agent's in-flight games rather than the fleet's.
        if os.path.exists(CYCLE_PATH):
            try:
                with open(CYCLE_PATH, encoding="utf-8") as handle:
                    wanted = {line.strip() for line in handle if line.strip()}
                os.remove(CYCLE_PATH)
            except OSError:
                wanted = set()
            for agent in agents:
                if agent.probe not in wanted or not agent.alive:
                    continue
                pending_cycle.add(agent.probe)
                print(f"  [{time.strftime('%H:%M:%S')}] {agent.probe} queued for cycle; "
                      f"will apply when it next holds zero games or completes its "
                      f"shift", flush=True)

        # Cycle each queued agent the moment the SERVER says it is holding no
        # games. Signalling a busy agent abandons those games to the turn clock.
        for agent in agents:
            if agent.probe not in pending_cycle or not agent.alive:
                continue
            if not agent.quiet():
                continue
            print(f"  [{time.strftime('%H:%M:%S')}] cycling {agent.probe}: idle, "
                  f"draining", flush=True)
            agent.drain()
            agent.proc = None
            agent.next_try = 0.0
            pending_cycle.discard(agent.probe)
            print(f"  [{time.strftime('%H:%M:%S')}] {agent.probe} cycled with zero "
                  f"games abandoned", flush=True)

        with open(STATE, "w", encoding="utf-8") as handle:
            json.dump({"supervisor_pid": os.getpid(),
                       "started": started,
                       "agents": {a.probe: (a.pid if a.alive else None) for a in agents},
                       "restarts": {a.probe: a.restarts for a in agents}}, handle, indent=2)
        time.sleep(args.check_interval)

    print("\nstopping — agents drain their in-flight games first", flush=True)
    for agent in agents:
        agent.stop()
    # DEFENCE: there is no kill path here, deliberately. An agent that is still
    # alive is still playing scored games. Killing it abandons them, they hit the
    # 120s turn timeout, and three such timeouts suspend the agent's queue joins
    # for 30 minutes. Waiting is always cheaper. This loop ends only when every
    # agent has exited on its own.
    started_wait = time.time()
    while any(a.alive for a in agents):
        waited = time.time() - started_wait
        if waited > DRAIN_SECONDS and int(waited) % 60 < 2:
            still = [a.probe for a in agents if a.alive]
            print(f"  still draining after {waited:.0f}s: {still} — waiting, never "
                  f"killing", flush=True)
        time.sleep(2)
    if os.path.exists(STATE):
        os.remove(STATE)
    uptime = (time.time() - started) / 3600
    print(f"stopped after {uptime:.2f}h; restarts: "
          f"{ {a.probe: a.restarts for a in agents} }")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
