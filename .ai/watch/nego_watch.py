#!/usr/bin/env python3
"""Emit a line only when Test 2's negotiation rating does something worth acting on."""
import json, os, sys, time, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(REPO, ".ai", "watch", "nego_watch_state.json")
TARGETS = [("3rd place", 2137.2), ("2nd place", 2322.9), ("pct 0.55", 2400.0), ("1st place", 2618.1)]
MOVE = 30.0          # 5-game samples swing +/-15 on noise alone; only report real moves
HEARTBEAT = 3600     # and at least once an hour

def key(name):
    for l in open(os.path.join(REPO, ".env")):
        l = l.strip()
        if l.startswith(name + "="):
            return l.split("=", 1)[1]
    return None

def stats(k):
    r = urllib.request.Request("https://glee-competition.com/api/agent/stats",
                               headers={"Authorization": f"Bearer {k}", "User-Agent": "M/5"})
    return json.load(urllib.request.urlopen(r, timeout=20))

def load():
    try:
        return json.load(open(STATE))
    except Exception:
        return {}

def main():
    k = key("GLEE_KEY_TEST2")
    st = load()
    while True:
        try:
            d = stats(k)
            s = d["scores"]
            n = s["negotiation"]["rating"]; g = s["negotiation"].get("games_played")
            b = s["bargaining"]["rating"]; p = s["persuasion"]["rating"]
            overall = (n + b + p) / 3
            now = time.time()
            last_n = st.get("nego"); last_t = st.get("ts", 0)
            why = None
            if last_n is None:
                why = "baseline"
            elif abs(n - last_n) >= MOVE:
                why = f"moved {n - last_n:+.1f}"
            elif now - last_t >= HEARTBEAT:
                why = "hourly"
            for label, thr in TARGETS:
                if last_n is not None and last_n < thr <= n:
                    why = f"*** CROSSED {label} ({thr:.0f}) ***"
            if b < 2450:
                why = f"!!! BARGAINING DROPPED to {b:.1f} -- investigate !!!"
            if why:
                print(f"[{time.strftime('%H:%M:%SZ', time.gmtime())}] Test 2 nego {n:.1f} "
                      f"(n={g}) barg {b:.1f} pers {p:.1f} overall {overall:.1f} | {why}", flush=True)
                st = {"nego": n, "ts": now}
                json.dump(st, open(STATE, "w"))
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%SZ', time.gmtime())}] watch error: {str(e)[:80]}", flush=True)
        time.sleep(600)

if __name__ == "__main__":
    main()
