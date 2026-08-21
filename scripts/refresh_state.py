#!/usr/bin/env python3
"""Regenerate .ai/CURRENT_STATE.md from the live fleet. Run before any analysis."""
import json, subprocess, datetime, urllib.request, os, sys
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
a=json.load(open("arms.json"))
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
head=re.sub(r"_Snapshot .*?_", f"_Snapshot {now} · repo commit `{commit}`_", head)
rows=[]
for slot in ("champion","composite","hardliner","conceder","randomized"):
    f=a.get(slot) or {}
    rows.append(f"### {names[slot]}  (slot `{slot}`)\n\n- **live rating**: {live(keys[slot])}\n- **flags ({len(f)})**: "
                +(" ".join(f"`{k.replace('GLEE_','')}={v}`" for k,v in sorted(f.items())) or "_none_"))
tail=open(".ai/CURRENT_STATE.md").read().split("## Deploy mechanics")[1] if os.path.exists(".ai/CURRENT_STATE.md") else ""
open(".ai/CURRENT_STATE.md","w").write(head+"## Fleet\n\n"+"\n".join(rows)+"\n\n## Deploy mechanics"+tail)
print(f"refreshed .ai/CURRENT_STATE.md @ {now}")
