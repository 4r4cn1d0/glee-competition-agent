#!/usr/bin/env python3
"""The persuasion arena: seller policies vs field-fitted buyer clones, locally.

Persuasion had no offline referee -- every experiment burned instrument hours.
The unlock: buyers ARE clonable (our seller seat observes quality, message, and
decision every round; sim's earlier exclusion applied to seller clones only).
Buyer clone = the fitted P(buy | mode, prior bucket, recommendation, lies
caught) table from scripts/fit_buyers.py, with the trust state simulated
forward exactly as buyers experience it: a lie is caught only when they BUY a
recommended low-quality item.

Calibration anchors (live instrument blocks): shading 0.3/2 measured 53.2%
sale rate; honest history ~52%. The arena must reproduce those before its
ladder interpolation is trusted.

    python -m sim.pers_arena --games 4000
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

CANDIDATES = [("honest", "0.0", "99"), ("s015", "0.15", "2"),
              ("s030", "0.3", "2"), ("s050", "0.5", "2"),
              ("s080", "0.8", "2"), ("s100", "1.0", "0")]


def load_configs():
    from sim.field_data import _iter_finals
    out = []
    for final in _iter_finals():
        if final.get("game_family") != "persuasion":
            continue
        gs = final.get("game_state") or {}
        if gs.get("p") is None or gs.get("v") is None:
            continue
        out.append({"p": gs["p"], "v": gs["v"], "u": gs.get("u", 0) or 0,
                    "price": gs.get("product_price"),
                    "mode": gs.get("seller_message_type") or "text",
                    "rounds": gs.get("total_rounds") or 20})
        if len(out) >= 4000:
            break
    return [c for c in out if c["price"]]


class BuyerClone:
    def __init__(self, table, mode, p, rng):
        self.t, self.mode, self.rng = table, mode, rng
        self.pb = "lo" if p < 0.45 else ("mid" if p < 0.65 else "hi")
        self.lies = 0

    def decide(self, rec: bool) -> bool:
        lb = "0" if self.lies == 0 else ("1" if self.lies == 1 else "2+")
        cell = (self.t.get(f"{self.mode}|{self.pb}|{'yes' if rec else 'no'}|{lb}")
                or self.t.get(f"{self.mode}|{self.pb}|{'yes' if rec else 'no'}|0"))
        pr = cell["p"] if cell else (0.5 if rec else 0.1)
        return self.rng.random() < pr

    def observe(self, bought: bool, rec: bool, quality_low: bool):
        if bought and rec and quality_low:
            self.lies += 1


def play(cfg, strategy_cfg, table, seed):
    from glee_agent.strategies import persuasion as P
    rng = random.Random(seed)
    buyer = BuyerClone(table, cfg["mode"], cfg["p"], random.Random(seed + 1))
    history = []
    revenue = 0.0
    sales = 0
    for rnd in range(1, cfg["rounds"] + 1):
        quality = "high" if rng.random() < cfg["p"] else "low"
        state = {"game_family": "persuasion", "round": rnd,
                 "total_rounds": cfg["rounds"], "phase": "seller_message",
                 "current_player": "player_1", "player_1_role": "seller",
                 "player_2_role": "buyer", "product_price": cfg["price"],
                 "p": cfg["p"], "v": cfg["v"], "u": cfg["u"],
                 "current_quality": quality, "is_seller_know_cv": True,
                 "seller_message_type": cfg["mode"], "history": list(history)}
        game = {"game_family": "persuasion", "your_player": "player_1",
                "game_state": state,
                "valid_actions": {"type": ("seller_recommendation"
                                           if cfg["mode"] == "binary"
                                           else "seller_message")}}
        try:
            action = P.decide(game, strategy_cfg)
        except Exception:
            action = {"decision": "yes"}
        raw = action.get("decision") or action.get("message") or "yes"
        s = str(raw).lower()
        rec = not ("no" == s or "hold off" in s or "not recommend" in s
                   or "skip" in s or s == "false")
        bought = buyer.decide(rec)
        buyer.observe(bought, rec, quality == "low")
        if bought:
            revenue += cfg["price"]
            sales += 1
        history.append({"round": rnd, "seller_message": raw,
                        "buyer_decision": "yes" if bought else "no",
                        "bought": bought, "quality": quality,
                        "seller_payoff": cfg["price"] if bought else 0,
                        "buyer_payoff": ((cfg["v"] if quality == "high"
                                          else cfg["u"]) - cfg["price"]) if bought else 0})
    return sales, cfg["rounds"], revenue / (cfg["price"] * cfg["rounds"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=515)
    args = ap.parse_args()
    table = json.load(open(os.path.join(REPO, "models",
                                        "pers_buyer_response_v2.json")))["table"]
    configs = load_configs()
    rng = random.Random(args.seed)
    draws = [(configs[rng.randrange(len(configs))], rng.randrange(2 ** 30))
             for _ in range(args.games)]
    from glee_agent.config import Config
    from glee_agent.probes import PROBES
    print(f"{len(draws)} paired games x {len(CANDIDATES)} seller configs, "
          f"buyers cloned from 3,327 live seller games\n")
    res = {}
    for name, shading, honest in CANDIDATES:
        for k in ("GLEE_PERS_LIE_SHADING", "GLEE_PERS_HONEST_ROUNDS", "GLEE_PROBE"):
            os.environ.pop(k, None)
        os.environ.update(GLEE_PERS_LIE_SHADING=shading,
                          GLEE_PERS_HONEST_ROUNDS=honest, GLEE_LLM_MODE="off")
        from glee_agent import runtime_flags
        runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
        cfg = PROBES["champion"][0](Config.from_env())
        sold = tot = 0
        rev = []
        for c, seed in draws:
            s, r, rv = play(c, cfg, table, seed)
            sold += s
            tot += r
            rev.append(rv)
        res[name] = (sold / tot, sum(rev) / len(rev))
        print(f"  {name:8s} shading={shading:>4s}/{honest:<3s} "
              f"sale rate {sold/tot:6.1%}   revenue/max {sum(rev)/len(rev):.3f}")
    print("\n  calibration anchors: live 0.3/2 block = 53.2%; live honest ~52%; "
          "champion-default 0.8/2 morning read ~44% (weak n)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
