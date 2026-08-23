"""Property test: what first_principles decides is what goes on the wire.

The cap-10 buyer bug was not a logic error inside the policy -- the policy chose
correctly and something downstream filled in a field it had left blank. A test
that only checks the policy's return value cannot see that class of defect, so
this one drives the FULL coerce() path over every owned state and asserts the
final wire action still carries the policy's intent.
"""

from __future__ import annotations

import itertools

import pytest

from glee_agent import actions, first_principles as fp, runtime_flags
from glee_agent.config import Config
from glee_agent.strategies import negotiation

ON = {"GLEE_NEGO_FIRST_PRINCIPLES": "1", "GLEE_NEGO_FP_ALWAYS": "1"}
# every guard that could plausibly rewrite a price, armed at once
HOSTILE = {
    "GLEE_NEGO_OPEN_CLAIM": "0.95", "GLEE_NEGO_CLAIM_FLOOR": "0.80",
    "GLEE_NEGO_OPEN_CLAIM_ALWAYS": "1", "GLEE_NEGO_ULT_FLOOR": "0.50",
    "GLEE_NEGO_ULT_CAP": "0.85", "GLEE_NEGO_ZOPA_CLAMP": "1",
    "GLEE_NEGO_HIDDEN_FLOOR": "1.15", "GLEE_NEGO_SPAN_INVARIANT": "0.40",
    "GLEE_NEGO_STALL_POLICY": "1", "GLEE_NEGO_CURVE_PRICING": "1",
}
GRID = (80.0, 100.0, 120.0, 150.0)
SCALES = (1.0, 100.0, 10000.0)


@pytest.fixture(autouse=True)
def _clear():
    runtime_flags._CACHE = None
    yield
    runtime_flags._CACHE = None


def mk(gid, *, complete, seller, mr, hk, my, their, phase, rnd, offered=None):
    me = "player_1" if seller else "player_2"
    them = "player_2" if seller else "player_1"
    st = {"game_family": "negotiation", "round": rnd, "max_rounds": mr,
          "horizon_known": hk, "phase": "ongoing", "current_player": me,
          f"{me}_role": "seller" if seller else "buyer",
          f"{them}_role": "buyer" if seller else "seller",
          f"{me}_value": my, "complete_information": complete,
          "messages_allowed": False, "history": []}
    if complete:
        st[f"{them}_value"] = their
    if offered is not None:
        st["last_offer"] = {"price": offered, "message": "", "from_player": them, "round": rnd}
    return {"game_family": "negotiation", "game_id": gid, "your_player": me,
            "game_state": st, "valid_actions": {"type": phase}}


def owned_states():
    """Every state first_principles claims, across scales, seats and rounds."""
    out, i = [], 0
    for scale in SCALES:
        for a, b in itertools.combinations(GRID, 2):
            lo, hi = a * scale, b * scale
            # single-round complete-info seller, and hidden-info seller
            for phase, rnd, off in (("offer", 1, None),):
                i += 1
                out.append(mk(f"s{i}", complete=True, seller=True, mr=1, hk=True,
                              my=lo, their=hi, phase=phase, rnd=rnd, offered=off))
                i += 1
                out.append(mk(f"h{i}", complete=False, seller=True, mr=1, hk=True,
                              my=lo, their=None, phase=phase, rnd=rnd, offered=off))
            # cap-10 complete-info buyer, offers and decisions across all rounds
            for rnd in range(1, 11):
                i += 1
                out.append(mk(f"o{i}", complete=True, seller=False, mr=10, hk=True,
                              my=hi, their=lo, phase="offer", rnd=rnd))
                for frac in (0.0, 0.25, 0.5, 0.75, 0.999):
                    i += 1
                    price = lo + frac * (hi - lo)
                    out.append(mk(f"d{i}", complete=True, seller=False, mr=10, hk=True,
                                  my=hi, their=lo, phase="decision", rnd=rnd, offered=price))
    return out


def test_every_owned_state_reaches_the_wire_intact(monkeypatch):
    for k, v in {**ON, **HOSTILE}.items():
        monkeypatch.setenv(k, v)
    states = owned_states()
    assert len(states) > 900, "battery too small"

    checked = bad = 0
    failures = []
    for g in states:
        if not fp.owns(g):
            continue
        checked += 1
        intent = fp.action(g)
        raw = negotiation.decide(g, Config())
        raw.pop("_plan", None)
        wire = actions.coerce(dict(raw), g)

        st = g["game_state"]
        me = st["current_player"]
        them = "player_2" if me == "player_1" else "player_1"
        my, their = st[f"{me}_value"], st.get(f"{them}_value")
        i_sell = st[f"{me}_role"] == "seller"

        if "product_price" in intent:
            if abs(wire.get("product_price", -1) - intent["product_price"]) > 0.011:
                failures.append(f"price rewritten: intent {intent['product_price']} "
                                f"-> wire {wire.get('product_price')} in {g['game_id']}")
                bad += 1
                continue
        if intent.get("decision") == "RejectOffer" and not (
                st["horizon_known"] is True and st["round"] >= st["max_rounds"]):
            if "product_price" not in wire:
                failures.append(f"no counteroffer on the wire in {g['game_id']}")
                bad += 1
                continue
            # the counteroffer must never be our own value: that is $0 for us
            if abs(wire["product_price"] - my) < 0.011:
                failures.append(f"counteroffer equals OUR OWN VALUE ({my}) in {g['game_id']}"
                                f" -- surrenders the entire zone")
                bad += 1
                continue
        # any price we put on the wire must leave us strictly better than no deal
        if "product_price" in wire and their is not None:
            px = wire["product_price"]
            gain = (px - my) if i_sell else (my - px)
            if gain <= 0:
                failures.append(f"wire price {px} gives us {gain} in {g['game_id']}")
                bad += 1

    assert checked > 500, f"only {checked} owned states exercised"
    assert not failures, f"{bad}/{checked} states broke:\n  " + "\n  ".join(failures[:12])


def test_hostile_guards_cannot_move_an_owned_price(monkeypatch):
    """Same states, guards on vs off: an owned price must be identical."""
    for k, v in ON.items():
        monkeypatch.setenv(k, v)
    for k in HOSTILE:
        monkeypatch.delenv(k, raising=False)
    runtime_flags._CACHE = None
    clean = {}
    for g in owned_states():
        if fp.owns(g):
            r = negotiation.decide(g, Config()); r.pop("_plan", None)
            clean[g["game_id"]] = actions.coerce(dict(r), g)

    for k, v in HOSTILE.items():
        monkeypatch.setenv(k, v)
    runtime_flags._CACHE = None
    moved = []
    for g in owned_states():
        if not fp.owns(g):
            continue
        r = negotiation.decide(g, Config()); r.pop("_plan", None)
        w = actions.coerce(dict(r), g)
        if w != clean[g["game_id"]]:
            moved.append(f"{g['game_id']}: {clean[g['game_id']]} -> {w}")
    assert not moved, f"{len(moved)} owned prices moved when guards armed:\n  " + "\n  ".join(moved[:10])
