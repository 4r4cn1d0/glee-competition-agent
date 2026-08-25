#!/usr/bin/env python3
"""Regenerate .ai/CURRENT_STATE.md from the live fleet. Run before any analysis."""
import json, subprocess, datetime, urllib.request, os, sys
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
a=json.load(open("arms.json"))
try:
    control=json.load(open("control.json"))
except (OSError, ValueError):
    control={}
try:
    supervisor=json.load(open("logs/supervisor.json"))
except (OSError, ValueError):
    supervisor={}
names={"champion":"Test 1","hardliner":"Test 2","conceder":"Test 3","randomized":"Test 4","composite":"Agent 5"}
keys={"champion":"GLEE_KEY_TEST1","hardliner":"GLEE_KEY_TEST2","conceder":"GLEE_KEY_TEST3","randomized":"GLEE_KEY_TEST4","composite":"GLEE_KEY_TEST5"}
def live(kn):
    try:
        k=[l.strip().split("=",1)[1] for l in open(".env") if l.startswith(kn+"=")][0]
        r=urllib.request.Request("https://glee-competition.com/api/agent/stats",headers={"Authorization":f"Bearer {k}","User-Agent":"M/5"})
        d=json.load(urllib.request.urlopen(r,timeout=12)); s=d.get("scores") or {}
        if not s: return "no games (deactivated)"
        return f"{sum(v['rating'] for v in s.values())/3:.0f} overall | "+" ".join(f"{f[:4]} {v['rating']:.0f}" for f,v in s.items())
    except Exception as e: return f"unavailable ({str(e)[:24]})"
commit=subprocess.run(["git","rev-parse","--short","HEAD"],capture_output=True,text=True).stdout.strip()
now=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%MZ")
head=open(".ai/CURRENT_STATE.md").read().split("## Fleet")[0] if os.path.exists(".ai/CURRENT_STATE.md") else ""
import re
head=re.sub(r"_Snapshot .*?_", f"_Snapshot {now} · workspace HEAD `{commit}`_", head)
rows=[]
for slot in ("champion","composite","hardliner","conceder","randomized"):
    f=a.get(slot) or {}
    policy=(control.get("policy") or {}).get(slot) or slot
    families=(control.get("families") or {}).get(slot) or "bargaining,negotiation,persuasion"
    llm=(control.get("llm") or {}).get(slot) or "supervisor default"
    pid=(supervisor.get("agents") or {}).get(slot)
    live_policy=live_families=live_llm="unknown"
    if pid:
        command=subprocess.run(["ps","-o","command=","-p",str(pid)],
                               capture_output=True,text=True).stdout.strip()
        def arg(name, default="unknown"):
            m=re.search(rf"(?:^| )--{name} ([^ ]+)", command)
            return m.group(1) if m else default
        live_policy=arg("probe")
        live_families=arg("families")
        live_llm=arg("llm-mode")
    rows.append(f"### {names[slot]}  (slot `{slot}`)\n\n"
                f"- **live process**: pid `{pid}` | policy `{live_policy}` | families `{live_families}` | llm `{live_llm}`\n"
                f"- **configured next launch**: policy `{policy}` | families `{families}` | llm `{llm}`\n"
                f"- **live rating**: {live(keys[slot])}\n- **flags ({len(f)})**: "
                +(" ".join(f"`{k.replace('GLEE_','')}={v}`" for k,v in sorted(f.items())) or "_none_"))
# Do not preserve an old "Current experiments" narrative under a fresh
# timestamp.  That previously made the generated file claim stale policies,
# flags, and PIDs even while the fleet table above was current.  Keep only
# invariant mechanics here; EXPERIMENTS.md owns dated experiment history and
# the generated flag table above reports the present overlays.
tail="""## Deploy mechanics that bite

- `arms.json` is an OVERLAY read live (~3s). Setting a flag reaches a running
  agent immediately; **clearing a key does NOT** — `runtime_flags` falls back to
  the launch environment, so a revert needs an explicit disabling value
  (`FLAG=0`) or a rotation.
- Code changes reach an agent only at its next shift boundary (3600s).
- `check_reachability.py` must PASS (eligible>0, fired>0, action_changed>0)
  before any arena run on a new flag.

## Experiment-status source

- The fleet table and flag lists above are regenerated from current supervisor
  metadata, process commands, API ratings, `control.json`, and `arms.json`.
- This snapshot does **not** prove which commit a process loaded. Verify the PID,
  process start boundary, and deployment record before calling code live.
- See `.ai/EXPERIMENTS.md` for dated hypotheses and decision rules. This file
  intentionally does not carry experiment prose forward between refreshes.
"""
open(".ai/CURRENT_STATE.md","w").write(head+"## Fleet\n\n"+"\n".join(rows)+"\n\n"+tail)
print(f"refreshed .ai/CURRENT_STATE.md @ {now}")
