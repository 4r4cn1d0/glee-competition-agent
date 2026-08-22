"""The field, fitted from our own logs: config census and cloned opponents.

The simulator's original weakness was synthetic: configs drawn from an assumed
grid (measured 63.7% no-ZOPA against ~100% live — a miscalibration that produced
a false null and nearly killed a good fix), and opponents written by hand. Both
halves are replaced here with measurements:

  * the CONFIG CENSUS is the empirical joint distribution of every configuration
    field we have observed, stored as literal (config, count) pairs and sampled
    by weight, so the simulated mix IS the live mix;
  * OPPONENTS are cloned from their logged behaviour. 26 of the 28 opponents
    with enough repeat observations respond >=95% consistently in a binned
    situation (most 99-100%), i.e. the mid-field is a set of lookup tables and
    we hold their transcripts: 131,963 observed rounds across 121 named
    opponents, plus a pooled FIELD clone for the hidden/unnamed half.

Fitting scans ~1GB of logs, so it runs offline (``python -m sim.field_data``)
and writes models/sim_field_v1.json; the evaluator loads that.

v1 covers bargaining and negotiation. Persuasion clones need the seller's
quality stream, which our buyer seat never observes for passed rounds, so a
clone fitted naively would be biased exactly where it matters; better
unmodelled than modelled wrong.
"""
from __future__ import annotations

import glob
import json
import os
import random
from collections import Counter, defaultdict

from glee_agent import runtime_flags

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "models", "sim_field_v1.json")

#: An opponent gets a personal clone only past this many observed responses;
#: thinner opponents fold into the pooled field clone rather than becoming a
#: lookup table of noise.
MIN_CLONE_OBS = 60

#: Switch the negotiation clone as one unit: the legacy price-bin/value-key
#: lookup algorithm remains the default until an evaluator explicitly opts
#: into the repaired instrument.
NEGO_RESP_V2_FLAG = "GLEE_SIM_NEGO_RESP_V2"

_BASES = (100.0, 1e4, 1e6)
_MULTS = (0.8, 1.0, 1.2, 1.5)


def infer_base(value):
    if not value:
        return None
    for m in _MULTS:
        for base in _BASES:
            if abs(value / m - base) <= base * 1e-6:
                return base
    return None


def _round_bin(r):
    return "1" if r <= 1 else ("2-3" if r <= 3 else "4+")


def _share_bin(x):
    return round(x * 25) / 25       # 4%-wide bins


def _price_bin(x):
    return round(min(max(x, 0.0), 4.0) * 10) / 10


def _proposer_share(price, proposer_role, proposer_value, responder_value):
    """Share of a positive visible span claimed by the player making ``price``."""
    values = (price, proposer_value, responder_value)
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) for v in values):
        return None
    if proposer_role == "seller":
        seller_value, buyer_value = proposer_value, responder_value
        proposer_gain = price - seller_value
    elif proposer_role == "buyer":
        seller_value, buyer_value = responder_value, proposer_value
        proposer_gain = buyer_value - price
    else:
        return None
    span = buyer_value - seller_value
    return proposer_gain / span if span > 0 else None


def _even_order_stats(values, limit=400):
    """At most ``limit`` equally weighted empirical quantile midpoints."""
    ordered = sorted(values)
    if len(ordered) <= limit:
        return ordered
    n = len(ordered)
    return [ordered[min((2 * i + 1) * n // (2 * limit), n - 1)]
            for i in range(limit)]


def _monotone_response(points, query):
    """Weighted non-increasing P(accept) and nonaccept mix at ``query``.

    ``points`` maps a scalar greed coordinate to accept/counter/walk counts.
    Weighted PAVA removes sampling-driven upward jumps.  Interior gaps use the
    greedier observed point, the generous edge is held flat, and a query beyond
    observed greedy support gets zero acceptance.  Those one-sided choices keep
    the clone from inventing willingness to accept an ask the logs never tested.
    """
    merged = defaultdict(Counter)
    for x, counts in points.items():
        try:
            x = float(x)
        except (TypeError, ValueError):
            continue
        if isinstance(counts, dict):
            merged[x].update(counts)

    blocks = []
    for x in sorted(merged):
        counts = merged[x]
        n = sum(counts.values())
        if n <= 0:
            continue
        blocks.append({"xs": [x], "counts": Counter(counts)})
        # Acceptance must be non-increasing as the candidate claims more.  A
        # lower-greed block below a higher-greed acceptance rate violates that
        # shape, so pool adjacent violators using their actual sample counts.
        while len(blocks) >= 2:
            left, right = blocks[-2], blocks[-1]
            ln = sum(left["counts"].values())
            rn = sum(right["counts"].values())
            lp = left["counts"].get("accept", 0) / ln
            rp = right["counts"].get("accept", 0) / rn
            if lp >= rp:
                break
            left["xs"].extend(right["xs"])
            left["counts"].update(right["counts"])
            blocks.pop()

    if not blocks:
        return None
    support = [x for block in blocks for x in block["xs"]]
    if query > support[-1] + 1e-12:
        return 0.0, None

    chosen = support[-1]
    for x in support:
        if x + 1e-12 >= query:
            chosen = x
            break
    for block in blocks:
        if chosen in block["xs"]:
            counts = block["counts"]
            n = sum(counts.values())
            return counts.get("accept", 0) / n, counts
    return None


def _iter_finals():
    seen = set()
    for path in glob.glob(os.path.join(REPO, "logs", "*", "results.jsonl")):
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                gid = rec.get("game_id")
                if gid in seen:
                    continue
                seen.add(gid)
                final = rec.get("final") or {}
                if final.get("game_state"):
                    final.setdefault("_ts", rec.get("ts"))
                    yield final
    for path in glob.glob(os.path.join(REPO, "logs", "*", "games", "*.json")):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                rec = json.load(fh)
        except (ValueError, OSError):
            continue
        gid = rec.get("game_id")
        if gid in seen:
            continue
        seen.add(gid)
        if rec.get("history"):
            yield {"game_family": rec.get("game_family"),
                   "your_player": rec.get("your_player"),
                   "opponent": rec.get("opponent"),
                   "game_state": {"history": rec.get("history"),
                                  **(rec.get("config") or {})}}


def fit() -> dict:
    census = {"bargaining": Counter(), "negotiation": Counter()}
    #: name -> {"barg_resp": {(share_bin, rbin): Counter(accept/reject)},
    #:          "barg_prop": {rbin: [share_they_keep]},
    #:          "nego_resp": {(pbin, seat, rbin): Counter(accept/counter/walk)},
    #:          "nego_resp_v2": {(axis, bin, seat, rbin, terminal): Counter(...)},
    #:          "nego_counter": {(seat, rbin): [price_over_B]},
    #:          "nego_counter_v2": {(seat, rbin): [price_over_B]}}
    clones = defaultdict(lambda: {"barg_resp": defaultdict(Counter),
                                  "barg_prop": defaultdict(list),
                                  "nego_resp": defaultdict(Counter),
                                  "nego_resp_v2": defaultdict(Counter),
                                  "nego_counter": defaultdict(list),
                                  "nego_counter_v2": defaultdict(list),
                                  "games": 0})
    delta_pairs = Counter()
    nego_value_marginal = Counter()

    for final in _iter_finals():
        fam = final.get("game_family")
        if fam not in ("bargaining", "negotiation"):
            continue
        gs = final.get("game_state") or {}
        me = final.get("your_player")
        if not me:
            continue
        them = "player_2" if me == "player_1" else "player_1"
        opp = final.get("opponent") or {}
        name = opp.get("name") if isinstance(opp, dict) else None
        who = name or "__field__"
        clones[who]["games"] += 1
        history = gs.get("history") or []

        if fam == "bargaining":
            money = gs.get("money_to_divide")
            if not money:
                continue
            cfg = {"money_to_divide": money,
                   "max_rounds": gs.get("max_rounds"),
                   "horizon_known": bool(gs.get("horizon_known")),
                   "messages_allowed": bool(gs.get("messages_allowed")),
                   "complete_information": bool(gs.get("complete_information")),
                   "delta_mine": gs.get(f"delta_{me[-1]}")}
            census["bargaining"][json.dumps(cfg, sort_keys=True)] += 1
            d1, d2 = gs.get("delta_1"), gs.get("delta_2")
            if d1 is not None and d2 is not None:
                delta_pairs[(round(float(d1), 2), round(float(d2), 2))] += 1
            for rnd in history:
                offer = rnd.get("offer") or {}
                dec = str(rnd.get("decision") or "").lower()
                rb = _round_bin(int(rnd.get("round") or 1))
                if offer.get("proposer") == me:
                    share = offer.get(f"{them}_gain")
                    if share is not None and dec in ("accept", "reject", "walkaway"):
                        key = (_share_bin(share / money), rb)
                        for tgt in (who, "__field__"):
                            clones[tgt]["barg_resp"][key][
                                "accept" if dec == "accept" else "reject"] += 1
                elif offer.get("proposer") == them:
                    keep = offer.get(f"{them}_gain")
                    if keep is not None:
                        for tgt in (who, "__field__"):
                            clones[tgt]["barg_prop"][rb].append(round(keep / money, 4))

        else:  # negotiation
            my_value = gs.get(f"{me}_value")
            base = infer_base(my_value)
            if base is None:
                continue
            my_mult = round(my_value / base, 2)
            their_value = gs.get(f"{them}_value")
            visible_their_value = (their_value
                                   if bool(gs.get("complete_information")) else None)
            cfg = {"base": base,
                   "my_mult": my_mult,
                   "their_mult": (round(their_value / base, 2) if their_value else None),
                   "my_role": gs.get(f"{me}_role"),
                   "max_rounds": gs.get("max_rounds"),
                   "horizon_known": bool(gs.get("horizon_known")),
                   "messages_allowed": bool(gs.get("messages_allowed")),
                   "complete_information": bool(gs.get("complete_information"))}
            census["negotiation"][json.dumps(cfg, sort_keys=True)] += 1
            nego_value_marginal[my_mult] += 1
            their_seat = gs.get(f"{them}_role") or "?"
            # their multiplier, observed (complete info) or inverted from a
            # closed deal's payoff -- lets the clone's behaviour be conditioned
            # on its drawn value, without which the arena is structurally blind
            # to any strategy that INFERS the hidden value
            their_mult = None
            tv = their_value
            res = final.get("result") or {}
            if tv is None and isinstance(res, dict) and res.get("outcome") == "agreement":
                pr, pay = res.get("agreed_price"), res.get(f"{them}_payoff")
                if isinstance(pr, (int, float)) and isinstance(pay, (int, float)):
                    tv = (pr - pay) if their_seat == "seller" else (pr + pay)
            if tv:
                for g_ in (0.8, 1.0, 1.2, 1.5):
                    if abs(tv / base - g_) < 0.05:
                        their_mult = g_
                        break
            for rnd in history:
                offer = rnd.get("offer") or {}
                price = offer.get("price")
                if price is None:
                    continue
                rb = _round_bin(int(rnd.get("round") or 1))
                dec = str(rnd.get("decision") or "").lower()
                if offer.get("from_player") == me and dec:
                    kind = ("accept" if "accept" in dec
                            else "walk" if "walk" in dec else "counter")
                    keys = [(_price_bin(price / base), their_seat, rb)]
                    if their_mult is not None:
                        keys.append((f"{_price_bin(price / base)}|m{their_mult}",
                                     their_seat, rb))
                    for key in keys:
                        for tgt in (who, "__field__"):
                            clones[tgt]["nego_resp"][key][kind] += 1

                    # V2 never conditions on the responder's private multiplier.
                    # In hidden games that label is recoverable only by inverting
                    # an AGREEMENT payoff: round 4+, buyer m1.5, price-bin 1.0
                    # measured 0.640 acceptance (n=25) versus 0.027 (n=2,793) in
                    # the all-outcome plain cell.  Reweighting cannot recover the
                    # missing types of no-deal games, so V2 drops the selected
                    # value key and records each response exactly once.
                    share = _proposer_share(price, gs.get(f"{me}_role"), my_value,
                                            visible_their_value)
                    max_rounds = gs.get("max_rounds")
                    terminal = ("final" if max_rounds is not None
                                and int(rnd.get("round") or 1) >= int(max_rounds)
                                else "continuing")
                    if share is not None:
                        v2_key = ("s", _share_bin(share), their_seat, rb, terminal)
                    else:
                        # Hidden offers do not reveal a truthful reservation
                        # bound, and using an agreement-inverted value recreates
                        # the selection above.  price/base is therefore the only
                        # scale-invariant observable shared by fitting and replay;
                        # responder seat supplies its monotonic direction.
                        v2_key = ("p", _price_bin(price / base), their_seat, rb,
                                  terminal)
                    # Round bin "1" otherwise mixes one-round ultimata with
                    # round-one play in longer games.  In the freshly fitted
                    # pooled share table that mixture rose from 3.9% acceptance
                    # at share 0.60 to 99.3% at 0.80; marking terminal state keeps
                    # the ultimatum mechanism out of the continuation curve.
                    v2_targets = (who,) if who == "__field__" else (who, "__field__")
                    for tgt in v2_targets:
                        clones[tgt]["nego_resp_v2"][v2_key][kind] += 1
                elif offer.get("from_player") == them:
                    ckeys = [(their_seat, rb)]
                    if their_mult is not None:
                        ckeys.append((f"{their_seat}|m{their_mult}", rb))
                    for ck in ckeys:
                        for tgt in (who, "__field__"):
                            clones[tgt]["nego_counter"][ck].append(
                                round(price / base, 4))
                    for tgt in ((who,) if who == "__field__" else (who, "__field__")):
                        clones[tgt]["nego_counter_v2"][(their_seat, rb)].append(
                            round(price / base, 4))

    def _pack(c):
        total = (sum(sum(v.values()) for v in c["barg_resp"].values())
                 + sum(sum(v.values()) for v in c["nego_resp"].values()))
        return total, {
            "games": c["games"],
            "barg_resp": {f"{k[0]}|{k[1]}": dict(v) for k, v in c["barg_resp"].items()},
            "barg_prop": {k: sorted(v)[:400] for k, v in c["barg_prop"].items()},
            "nego_resp": {f"{k[0]}|{k[1]}|{k[2]}": dict(v) for k, v in c["nego_resp"].items()},
            "nego_resp_v2": {f"{k[0]}|{k[1]}|{k[2]}|{k[3]}|{k[4]}": dict(v)
                             for k, v in c["nego_resp_v2"].items()},
            "nego_counter": {f"{k[0]}|{k[1]}": sorted(v)[:400]
                             for k, v in c["nego_counter"].items()},
            # Legacy ``sorted(v)[:400]`` kept only the lowest tail (the tracked
            # pooled buyer round-4+ sample ends at 0.1259*base and seller
            # round-4+ at 0.8000*base).  V2 retains equally weighted quantile
            # midpoints, so rejecting an ask does not manufacture a low
            # counteroffer next or overweight a singleton extreme.
            "nego_counter_v2": {f"{k[0]}|{k[1]}": _even_order_stats(v)
                                for k, v in c["nego_counter_v2"].items()},
        }

    packed = {}
    named_games = 0
    for who, c in clones.items():
        total, doc = _pack(c)
        if who == "__field__" or total >= MIN_CLONE_OBS:
            packed[who] = doc
            if who != "__field__":
                named_games += c["games"]
    total_games = sum(census["bargaining"].values()) + sum(census["negotiation"].values())
    return {
        "_schema": "glee.sim_field/v1",
        "_nego_resp_schema": "share-price-terminal/v2",
        "_games": total_games,
        "census": {fam: [[json.loads(k), n] for k, n in cnt.most_common()]
                   for fam, cnt in census.items()},
        "delta_pairs": [[list(k), n] for k, n in delta_pairs.most_common()],
        "nego_value_marginal": {str(k): n for k, n in nego_value_marginal.items()},
        "opponent_mix": {who: c["games"] for who, c in packed.items()},
        "clones": packed,
    }


# ---------------------------------------------------------------------------
# Runtime: clone policies over the fitted tables.
# ---------------------------------------------------------------------------

class Clone:
    """A logged opponent, replayed as a strategy callable.

    Reads the fitted response tables; where a situation was never observed it
    falls back to the pooled field clone, and past that to a conservative
    rational default -- so a thin table degrades toward typical-field behaviour
    rather than toward noise.
    """

    def __init__(self, name: str, table: dict, field_table: dict, rng: random.Random):
        self.name = name
        self._t = table
        self._f = field_table
        self._rng = rng

    def _lookup(self, section, key):
        for src in (self._t, self._f):
            hit = (src.get(section) or {}).get(key)
            if hit:
                return hit
        return None

    @staticmethod
    def _v2_points(src, axis, seat, rb, terminal):
        points = defaultdict(Counter)
        for key, counts in (src.get("nego_resp_v2") or {}).items():
            parts = key.split("|")
            if len(parts) != 5 or parts[0] != axis or parts[2] != seat \
                    or parts[3] != rb or parts[4] != terminal:
                continue
            try:
                value = float(parts[1])
            except ValueError:
                continue
            # Proposer share already increases with greed for either seat.  On
            # the coarse price backstop a seller proposer asks a buyer for MORE
            # as price rises, while a buyer proposer asks a seller for more as
            # price falls; negating seller-response prices unifies direction.
            greed = value if axis == "s" or seat == "buyer" else -value
            if isinstance(counts, dict):
                points[greed].update(counts)
        return points

    def _v2_curve(self, axis, seat, rb, terminal, query):
        personal = self._v2_points(self._t, axis, seat, rb, terminal)
        pooled = (personal if self._t is self._f
                  else self._v2_points(self._f, axis, seat, rb, terminal))

        # A named clone owns interpolation only within its observed support.
        # Outside it, the all-opponent curve has much more relevant support and
        # supplies the conservative edge extrapolation.  Never add the tables:
        # the pooled table already contains each named observation once.
        if self._t is not self._f and personal:
            xs = sorted(personal)
            if xs[0] - 1e-12 <= query <= xs[-1] + 1e-12:
                result = _monotone_response(personal, query)
                # MIN_CLONE_OBS already defines when a personal clone is more
                # than lookup-table noise.  Apply the same evidence floor to
                # the fitted block that would decide this response; a one-game
                # personal cell must not override the all-field curve with p=1.
                if result is not None and result[1] is not None \
                        and sum(result[1].values()) >= MIN_CLONE_OBS:
                    return result
        if pooled:
            return _monotone_response(pooled, query)
        if personal:
            return _monotone_response(personal, query)
        return None

    def __call__(self, game: dict) -> dict:
        state = game["game_state"]
        me = game["your_player"]
        fam = game["game_family"]
        rb = _round_bin(int(state.get("round") or 1))
        if fam == "bargaining":
            money = state["money_to_divide"]
            if game["valid_actions"]["type"] == "offer":
                keeps = (self._t.get("barg_prop") or {}).get(rb) \
                    or (self._f.get("barg_prop") or {}).get(rb) or [0.5]
                keep = self._rng.choice(keeps) * money
                mine = round(keep, 2)
                return ({"alice_gain": mine, "bob_gain": round(money - mine, 2)}
                        if me == "player_1" else
                        {"alice_gain": round(money - mine, 2), "bob_gain": mine})
            offer = state.get("last_offer") or {}
            my_gain = offer.get(f"{me}_gain") or 0.0
            hit = self._lookup("barg_resp", f"{_share_bin(my_gain / money)}|{rb}")
            if hit:
                p = hit.get("accept", 0) / max(sum(hit.values()), 1)
                return {"decision": "accept" if self._rng.random() < p else "reject"}
            return {"decision": "accept" if my_gain >= money * 0.4 else "reject"}

        # negotiation
        my_value = state.get(f"{me}_value") or 0.0
        base = infer_base(my_value) or my_value or 1.0
        role = state.get(f"{me}_role")
        seat = role or "?"

        my_mult = None
        for g_ in (0.8, 1.0, 1.2, 1.5):
            if base and abs(my_value / base - g_) < 0.05:
                my_mult = g_
                break

        v2_enabled = runtime_flags.enabled(NEGO_RESP_V2_FLAG)

        def counter_price(v2=False):
            if v2:
                key = f"{seat}|{rb}"
                sources = ((self._t,) if self._t is self._f else (self._t, self._f))
                for src in sources:
                    xs = (src.get("nego_counter_v2") or {}).get(key)
                    if xs:
                        # Match the response-side evidence floor: 178 of 637
                        # fitted personal counter cells had fewer than 10 draws,
                        # so a singleton proposal must defer to the pooled field.
                        if src is self._t and self._t is not self._f \
                                and len(xs) < MIN_CLONE_OBS:
                            continue
                        # Pooling without the selected private-value key is
                        # identified, but can draw a bid above this buyer's
                        # value or an ask below this seller's cost (49-60% in
                        # the vulnerable low/high-value cells).  Filter by the
                        # clone's known reservation value before sampling.
                        feasible = [x for x in xs
                                    if ((role == "seller" and x * base >= my_value)
                                        or (role == "buyer" and x * base <= my_value))]
                        if feasible:
                            return round(self._rng.choice(feasible) * base, 2)
                # A pre-V2 artifact has no evenly sampled table.  Falling back
                # only to the all-outcome plain key keeps private-value
                # survivorship out; it does not revive the selected |m key.
                for src in sources:
                    xs = (src.get("nego_counter") or {}).get(key)
                    if xs:
                        if src is self._t and self._t is not self._f \
                                and len(xs) < MIN_CLONE_OBS:
                            continue
                        feasible = [x for x in xs
                                    if ((role == "seller" and x * base >= my_value)
                                        or (role == "buyer" and x * base <= my_value))]
                        if feasible:
                            return round(self._rng.choice(feasible) * base, 2)
                return round(my_value * (1.3 if role == "seller" else 0.8), 2)
            keys = ([f"{seat}|m{my_mult}|{rb}"] if my_mult is not None else []) \
                + [f"{seat}|{rb}"]
            for src in (self._t, self._f):
                for k in keys:
                    xs = (src.get("nego_counter") or {}).get(k)
                    if xs:
                        return round(self._rng.choice(xs) * base, 2)
            return round(my_value * (1.3 if role == "seller" else 0.8), 2)

        if game["valid_actions"]["type"] == "offer":
            return {"product_price": counter_price(v2_enabled)}
        price = (state.get("last_offer") or {}).get("price") or 0.0

        if v2_enabled:
            curve = None
            other = "player_2" if me == "player_1" else "player_1"
            final = (state.get("max_rounds") is not None
                     and int(state.get("round") or 1) >= int(state["max_rounds"]))
            terminal = "final" if final else "continuing"
            if bool(state.get("complete_information")):
                share = _proposer_share(price, state.get(f"{other}_role"),
                                        state.get(f"{other}_value"), my_value)
                if share is not None:
                    curve = self._v2_curve("s", seat, rb, terminal,
                                           _share_bin(share))
            if curve is None:
                normalized = price / base
                binned = _price_bin(normalized)
                # Preserve the fitted key identity inside the [0,4] backstop.
                # Above its clamp, a seller ask to a buyer is greedier than all
                # represented bins and must remain outside support, not alias to
                # p=4.0 and inherit acceptance there.
                outside_greedy_clamp = ((seat == "buyer" and normalized > 4.0)
                                        or (seat == "seller" and normalized < 0.0))
                price_point = normalized if outside_greedy_clamp else binned
                price_greed = price_point if seat == "buyer" else -price_point
                curve = self._v2_curve("p", seat, rb, terminal, price_greed)

            # No curve and a greedier-than-support query both mean p=0.  Unlike
            # the legacy profitable-price fallback, this can withhold observed
            # acceptance but can never manufacture it in an untested region.
            p_accept, mix = curve if curve is not None else (0.0, None)
            profitable = (price >= my_value if role == "seller"
                          else price <= my_value)
            # Dropping outcome-selected value keys intentionally pools hidden
            # private types, but the clone still knows its own reservation.  A
            # raw pooled curve otherwise predicted acceptance as high as 0.646
            # for buyer m0.8 at p=1.0B and 0.208 for seller m1.5 at p=1.3B,
            # both losing trades.  Structural no-loss support overrides the fit.
            if not profitable:
                p_accept = 0.0
            if self._rng.random() < p_accept:
                return {"decision": "AcceptOffer"}
            nonaccept = ((mix.get("counter", 0) + mix.get("walk", 0))
                         if mix is not None else 0)
            if nonaccept and self._rng.random() < mix.get("walk", 0) / nonaccept:
                return {"decision": "WalkAway"}
            if final:
                return {"decision": "RejectOffer"}
            return {"decision": "RejectOffer", "product_price": counter_price(True)}

        hit = None
        if my_mult is not None:
            hit = self._lookup("nego_resp",
                               f"{_price_bin(price / base)}|m{my_mult}|{seat}|{rb}")
        if not hit:
            hit = self._lookup("nego_resp", f"{_price_bin(price / base)}|{seat}|{rb}")
        if hit:
            n = max(sum(hit.values()), 1)
            r = self._rng.random()
            if r < hit.get("accept", 0) / n:
                return {"decision": "AcceptOffer"}
            if r < (hit.get("accept", 0) + hit.get("walk", 0)) / n:
                return {"decision": "WalkAway"}
            return {"decision": "RejectOffer", "product_price": counter_price()}
        profitable = price >= my_value if role == "seller" else price <= my_value
        if profitable:
            return {"decision": "AcceptOffer"}
        return {"decision": "RejectOffer", "product_price": counter_price()}


class Field:
    """Loaded sim_field_v1.json: sample configs and opponents as observed."""

    def __init__(self, path: str = OUT):
        with open(path, encoding="utf-8") as fh:
            self.doc = json.load(fh)
        self._census = {fam: ([c for c, _ in rows], [n for _, n in rows])
                        for fam, rows in self.doc["census"].items()}
        mix = self.doc["opponent_mix"]
        self._names = [n for n in mix if n != "__field__"]
        self._weights = [mix[n] for n in self._names]
        #: the hidden/unnamed half plays as the pooled field clone
        self._field_weight = self.doc["clones"]["__field__"]["games"] - sum(self._weights)
        self._mults = {float(k): n for k, n in self.doc["nego_value_marginal"].items()}
        self._deltas = [(tuple(k), n) for k, n in self.doc["delta_pairs"]]

    def families(self):
        return [f for f, (c, _) in self._census.items() if c]

    def sample_config(self, family: str, rng: random.Random) -> tuple[dict, str]:
        """One observed configuration -> (engine params, our seat)."""
        configs, weights = self._census[family]
        raw = rng.choices(configs, weights=weights)[0]
        if family == "bargaining":
            if raw.get("delta_mine") is not None and self._deltas:
                pair = rng.choices([p for p, _ in self._deltas],
                                   weights=[n for _, n in self._deltas])[0]
            else:
                pair = (0.9, 0.9)
            params = {"money_to_divide": raw["money_to_divide"],
                      "delta_1": pair[0], "delta_2": pair[1],
                      "max_rounds": raw.get("max_rounds"),
                      "horizon_known": raw.get("horizon_known"),
                      "messages_allowed": raw.get("messages_allowed"),
                      "complete_information": raw.get("complete_information")}
            seat = rng.choice(["player_1", "player_2"])
            return params, seat
        base = raw["base"]
        my_mult = raw["my_mult"]
        their_mult = raw.get("their_mult")
        if their_mult is None:
            mults = sorted(self._mults)
            their_mult = rng.choices(mults, weights=[self._mults[m] for m in mults])[0]
        seat = "player_1" if raw.get("my_role") == "seller" else "player_2"
        seller_mult = my_mult if seat == "player_1" else their_mult
        buyer_mult = their_mult if seat == "player_1" else my_mult
        params = {"player_1_value": seller_mult * base,
                  "player_2_value": buyer_mult * base,
                  "max_rounds": raw.get("max_rounds"),
                  "horizon_known": raw.get("horizon_known"),
                  "messages_allowed": raw.get("messages_allowed"),
                  "complete_information": raw.get("complete_information")}
        return params, seat

    def sample_opponent(self, rng: random.Random) -> Clone:
        field_table = self.doc["clones"]["__field__"]
        total = sum(self._weights) + max(self._field_weight, 1)
        if self._names and rng.random() < sum(self._weights) / total:
            name = rng.choices(self._names, weights=self._weights)[0]
            return Clone(name, self.doc["clones"][name], field_table, rng)
        return Clone("__field__", field_table, field_table, rng)


def main() -> int:
    doc = fit()
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    os.replace(tmp, OUT)
    named = [n for n in doc["clones"] if n != "__field__"]
    print(f"fitted {doc['_games']:,} games -> {os.path.relpath(OUT, REPO)}")
    print(f"  configs: bargaining {len(doc['census']['bargaining'])} distinct, "
          f"negotiation {len(doc['census']['negotiation'])} distinct")
    print(f"  clones: {len(named)} named opponents + pooled field")
    size = os.path.getsize(OUT) / 1e6
    print(f"  file size: {size:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
