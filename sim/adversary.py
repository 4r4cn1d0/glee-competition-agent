"""A parameterised ADVERSARY — the policy the red-team evolver searches over.

The cloned field (``sim/field_data.py``) answers "how do we do against the
opponents we have actually met". It cannot answer the question this module
exists for: *what would an opponent who was TRYING to exploit us look like, and
how much would they take?* A clone is a lookup table of observed behaviour, so
it can only ever replay the field's mistakes; it has no knobs to turn and
nothing to search over.

So this is a small, fully parametric negotiator — an opening anchor, a
concession curve, a stall/repeat run, an acceptance threshold, and a patience
horizon — chosen so that every one of our own measured decision rules has a
genome that pokes at it:

  * ``*_hold`` produces a literal stonewall (N identical offers in a row), which
    is the trigger for ``GLEE_BARG_STONEWALL`` and for
    ``negotiation._their_stall_price``;
  * ``*_accept`` sets how much of the pot/surplus the adversary demands before
    it will close, i.e. how hard it is to buy off;
  * ``*_patience`` is when it gives up and takes anything positive, which bounds
    game length and models an opponent with a real clock;
  * the anchor/curve pair is the classic Boulware family our continuation-value
    estimator projects trends from.

Everything is scale-free: bargaining works in shares of the pot, negotiation in
multiples of the adversary's own valuation, so one genome plays every drawn
configuration in the census. Persuasion is out of scope for the same reason it
is out of scope for the rest of the simulator.

The policy is a ``sim.opponents.Policy`` subclass, so it inherits the same
coerce/guard net every other sparring partner uses: a genome that would produce
an illegal move gets repaired, exactly as a live opponent's client would repair
it, rather than winning by making US eat an abandonment.
"""

from __future__ import annotations

from glee_agent.actions import _num, is_final_round

from .opponents import Policy, _bargaining_offer, _me, _money, _offered_share, _state

__all__ = ["GENOME_SPACE", "ARCHETYPES", "Adversary", "clamp_genome", "default_genome"]

#: knob -> (lo, hi, sigma, doc). ``sigma`` is the mutation step the evolver uses.
GENOME_SPACE = {
    # --- bargaining ------------------------------------------------------
    "b_open": (0.50, 0.99, 0.06,
               "share of the pot the adversary keeps in its first offer"),
    "b_end": (0.20, 0.99, 0.06,
              "share it keeps once its planning horizon is spent"),
    "b_curve": (0.30, 4.00, 0.40,
                "concession exponent; >1 holds near the anchor then collapses"),
    "b_hold": (0.0, 8.0, 1.2,
               "how many of its own offers it repeats VERBATIM before conceding "
               "at all -- the stonewall run length"),
    "b_accept": (0.00, 0.95, 0.08,
                 "share of the pot it must be offered to accept, round 1"),
    "b_accept_end": (0.00, 0.60, 0.06,
                     "... and once its planning horizon is spent"),
    "b_patience": (2.0, 60.0, 6.0,
                   "round after which it takes any positive offer"),
    # --- negotiation -----------------------------------------------------
    "n_open": (0.02, 2.50, 0.20,
               "opening price as a markup (seller) or discount (buyer) on its "
               "own valuation, as a fraction of it"),
    "n_end": (0.00, 1.00, 0.10,
              "terminal markup/discount, i.e. where the concession walk lands"),
    "n_curve": (0.30, 4.00, 0.40, "concession exponent"),
    "n_hold": (0.0, 8.0, 1.2,
               "how many of its own prices it repeats VERBATIM before conceding "
               "-- three is what our stall detector keys on"),
    "n_accept": (0.00, 1.20, 0.10,
                 "surplus it demands before accepting, as a fraction of its own "
                 "valuation"),
    "n_patience": (2.0, 40.0, 4.0,
                   "round after which it takes any profitable price"),
}

#: Planning horizons for games whose cap is hidden. The adversary is not allowed
#: to see a deadline the server does not send, so like every other policy here
#: it invents one. These bound simulated game length too.
_BARG_ASSUMED = 12
_NEGO_ASSUMED = 10


def default_genome() -> dict:
    """Mid-range genome: a plain linear conceder. The evolver's starting point."""
    return {k: (lo + hi) / 2.0 for k, (lo, hi, _s, _d) in GENOME_SPACE.items()}


def clamp_genome(genome: dict) -> dict:
    out = {}
    for key, (lo, hi, _s, _d) in GENOME_SPACE.items():
        out[key] = min(max(float(genome.get(key, (lo + hi) / 2.0)), lo), hi)
    return out


# --------------------------------------------------------------------------
# History readers. Deliberately independent of the ones the agent uses: the
# adversary must reason from the observation the SERVER sends it, and sharing a
# helper with the code under attack is how a red team fools itself.
# --------------------------------------------------------------------------

def _my_barg_offers(state: dict, me: str) -> list:
    """Every gain the adversary has proposed FOR ITSELF, oldest first."""
    out = []
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        offer = entry.get("offer") or {}
        if not isinstance(offer, dict):
            continue
        if (offer.get("proposer") or entry.get("proposer")) != me:
            continue
        gain = offer.get(f"{me}_gain")
        if gain is not None:
            out.append(_num(gain))
    return out


def _my_nego_prices(state: dict, me: str) -> list:
    """Every price the adversary has named, oldest first, echo collapsed.

    A counteroffer is re-recorded as the next round's opening offer at the same
    price. Counting the echo would make a two-price schedule look like a
    stonewall, i.e. it would fake the very behaviour the search is trying to
    discover.
    """
    seq: list = []
    prev = None
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        for key in ("offer", "counteroffer"):
            off = entry.get(key)
            if not isinstance(off, dict) or off.get("price") is None:
                continue
            if off.get("from_player") != me:
                continue
            price = _num(off["price"])
            if key == "offer" and prev == "counteroffer" and seq and price == seq[-1]:
                prev = key
                continue
            seq.append(price)
            prev = key
    return seq


def _horizon(state: dict, assumed: int) -> int:
    cap = state.get("max_rounds")
    if state.get("horizon_known") is False or cap is None:
        return assumed
    return max(1, int(_num(cap, assumed)))


def _round(state: dict) -> int:
    return int(_num(state.get("round"), 1))


def _walk(open_x: float, end_x: float, step: int, steps: int, curve: float) -> float:
    """Concession value after ``step`` moves of a ``steps``-long schedule."""
    if steps <= 0:
        return end_x
    t = min(max(step / float(steps), 0.0), 1.0)
    return open_x + (end_x - open_x) * (t ** max(curve, 0.05))


class Adversary(Policy):
    """One genome, playing as a competition strategy callable.

    Stateless: the stall run, the concession step and the deadline are all read
    back out of ``game_state["history"]``, so a single instance can play both
    seats of many concurrent games without cross-talk — the same property every
    other policy in ``sim.opponents`` has.
    """

    def __init__(self, genome: dict, name: str = "adversary"):
        self.g = clamp_genome(genome)
        self.name = name

    # --- bargaining -------------------------------------------------------

    def bargaining_offer(self, game: dict) -> dict:
        state = _state(game)
        me = _me(game)
        money = _money(state)
        g = self.g
        mine = _my_barg_offers(state, me)
        hold = int(round(g["b_hold"]))
        if money > 0 and mine and len(mine) <= hold:
            # Stonewall: repeat the previous number to the cent. Anything else
            # is a concession, and a concession is what the run must not contain.
            return _bargaining_offer(game, mine[-1] / money, "Same offer as before.")
        steps = max(1, _horizon(state, _BARG_ASSUMED) // 2 - hold)
        share = _walk(g["b_open"], min(g["b_end"], g["b_open"]),
                      max(0, len(mine) - hold), steps, g["b_curve"])
        return _bargaining_offer(game, share, "This is what I need.")

    def bargaining_decision(self, game: dict):
        state = _state(game)
        share = _offered_share(state, _me(game))
        if share is None:
            return None
        g = self.g
        if is_final_round(state):
            return {"decision": "accept" if share > 0 else "reject"}
        if _round(state) >= g["b_patience"]:
            return {"decision": "accept" if share > 0 else "reject"}
        horizon = _horizon(state, _BARG_ASSUMED)
        t = min(max((_round(state) - 1) / max(1, horizon - 1), 0.0), 1.0)
        thr = g["b_accept"] + (g["b_accept_end"] - g["b_accept"]) * t
        return {"decision": "accept" if share >= thr else "reject"}

    # --- negotiation ------------------------------------------------------

    def _price(self, game: dict) -> float:
        state = _state(game)
        me = _me(game)
        my_value = _num(state.get(f"{me}_value"), 1.0)
        seller = (state.get(f"{me}_role") or
                  ("seller" if me == "player_1" else "buyer")) == "seller"
        g = self.g
        mine = _my_nego_prices(state, me)
        hold = int(round(g["n_hold"]))
        if mine and len(mine) <= hold:
            return mine[-1]                     # verbatim repeat: the stall
        steps = max(1, _horizon(state, _NEGO_ASSUMED) - 1 - hold)
        end = min(g["n_end"], g["n_open"])
        frac = _walk(g["n_open"], end, max(0, len(mine) - hold), steps, g["n_curve"])
        return my_value * (1.0 + frac) if seller else my_value * max(1.0 - frac, 0.0)

    def negotiation_offer(self, game: dict) -> dict:
        return {"product_price": round(self._price(game), 2),
                "message": "Here is my price."}

    def negotiation_decision(self, game: dict):
        state = _state(game)
        me = _me(game)
        price = (state.get("last_offer") or {}).get("price")
        if price is None:
            return None
        price = _num(price)
        my_value = _num(state.get(f"{me}_value"), 1.0)
        seller = (state.get(f"{me}_role") or
                  ("seller" if me == "player_1" else "buyer")) == "seller"
        surplus = (price - my_value) if seller else (my_value - price)
        final = is_final_round(state)
        if final or _round(state) >= self.g["n_patience"]:
            if surplus > 0:
                return {"decision": "AcceptOffer"}
            return {"decision": "RejectOffer"} if final else \
                {"decision": "RejectOffer", "product_price": round(self._price(game), 2)}
        if surplus >= self.g["n_accept"] * max(my_value, 1e-9):
            return {"decision": "AcceptOffer"}
        return {"decision": "RejectOffer", "product_price": round(self._price(game), 2),
                "message": "Not yet."}


#: Hand-written reference attacks. The evolver searches the same space, but a
#: named archetype is what makes a finding legible ("a stonewaller takes X"),
#: and running them alongside the evolved winner shows whether the search found
#: a genuinely new shape or just a sharpened version of a known one.
ARCHETYPES = {
    "field_linear": dict(default_genome(),
                         b_open=0.70, b_end=0.45, b_curve=1.0, b_hold=0,
                         b_accept=0.40, b_accept_end=0.10, b_patience=12,
                         n_open=0.40, n_end=0.05, n_curve=1.0, n_hold=0,
                         n_accept=0.10, n_patience=10),
    "stonewaller": dict(default_genome(),
                        b_open=0.85, b_end=0.85, b_curve=1.0, b_hold=8,
                        b_accept=0.80, b_accept_end=0.50, b_patience=60,
                        n_open=1.00, n_end=1.00, n_curve=1.0, n_hold=8,
                        n_accept=0.60, n_patience=40),
    "lowball_repeater": dict(default_genome(),
                             b_open=0.95, b_end=0.95, b_curve=1.0, b_hold=6,
                             b_accept=0.90, b_accept_end=0.60, b_patience=60,
                             n_open=0.02, n_end=0.02, n_curve=1.0, n_hold=6,
                             n_accept=0.80, n_patience=40),
    "boulware": dict(default_genome(),
                     b_open=0.92, b_end=0.55, b_curve=3.5, b_hold=0,
                     b_accept=0.60, b_accept_end=0.20, b_patience=20,
                     n_open=1.50, n_end=0.05, n_curve=3.5, n_hold=0,
                     n_accept=0.30, n_patience=20),
    "fast_conceder": dict(default_genome(),
                          b_open=0.60, b_end=0.30, b_curve=0.4, b_hold=0,
                          b_accept=0.25, b_accept_end=0.05, b_patience=6,
                          n_open=0.20, n_end=0.02, n_curve=0.4, n_hold=0,
                          n_accept=0.02, n_patience=5),
}
