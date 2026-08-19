"""Baseline opponent policies — the sparring partners the simulator plays against.

Tuning a strategy needs something to tune *against*. A single opponent teaches
you to beat that opponent; a spread of archetypes tells you which knobs are
robust and which ones only work against one kind of counterpart. So this module
carries the field in miniature: the reference agent the real queue is seeded
with, a hardliner and a conceder to bracket the concession spectrum, a mirror,
a noise floor, and the persuasion-specific honesty archetypes.

Every policy has the *same* signature as a competition strategy —
``(game: dict) -> dict`` over the exact shape ``GET /api/agent/games/pending``
returns — so any of them can be dropped into either seat of a simulated match,
and the agent under test can equally be dropped into a slot here. Policies are
stateless apart from ``random_valid``'s RNG: everything they adapt to is read
out of ``game_state["history"]``, exactly as the live server would present it.
That means one instance can play both seats of a match, and many matches at
once, without cross-talk.

Every policy is total. It returns a legal action for every phase it can face
and never raises, because a policy that crashes silently corrupts every
tournament result it appears in. The safety net is the agent's own
``glee_agent.actions.coerce`` / ``safe_action`` pair rather than a second
implementation of it, so a move this module considers legal is a move the agent
considers legal.

ASSUMPTIONS (not pinned down by docs/reference/glee-docs.md — revisit if the
platform ever says otherwise):

1. Concession schedules are linear in round progress. The docs describe no
   concession convention at all; these are archetypes of how a field behaves,
   not claims about the platform.
2. Uncapped games (``horizon_known`` false, ``max_rounds`` absent) are
   scheduled against an assumed 10-round horizon, matching
   ``glee_agent.config.Config.nego_assumed_horizon``. An infinite horizon has
   no "deadline pressure" to schedule against, so one has to be invented.
3. Text-mode seller messages carry no server-side "recommended" flag, so
   ``_is_recommendation`` classifies free text by keyword. Sellers who pitch are
   the overwhelming majority, so the default reading is "recommended" and only
   an explicit negative flips it.
4. ``random_valid``'s negotiation prices are drawn from [0, 2 x own valuation].
   The legal price set is unbounded above, and there is no uniform distribution
   over an unbounded set — the bound is arbitrary but has to exist.
5. Bargaining history entries are ``{round, proposer, offer, decision}`` (docs)
   and their ``offer`` sub-dict is assumed to use the same keys as
   ``last_offer`` (``player_N_gain``). Readers here tolerate its absence.
6. These baselines reason about NOMINAL shares and prices, ignoring the
   ``delta_1``/``delta_2`` inflation multipliers. That is a deliberate property
   of the archetypes — the reference agent ignores inflation too, and an
   opponent pool that all discounts correctly is not the pool the live queue is.
"""

from __future__ import annotations

import logging
import random

from glee_agent.actions import _num, coerce, is_final_round, safe_action

from .types import PLAYER_1

logger = logging.getLogger("sim.opponents")

# Planning horizon for games with no round limit (ASSUMPTION 2).
_ASSUMED_HORIZON = 10

# Phrases that flip a free-text seller message from a pitch to a warning
# (ASSUMPTION 3). Checked before anything else, so "I would not recommend this,
# it is low quality" reads as a non-recommendation despite the word "recommend".
_NEGATIVE_MARKERS = (
    "not recommend", "wouldn't recommend", "would not", "don't buy", "do not buy",
    "low quality", "low-quality", "not worth", "avoid", "skip this", "pass on",
    "poor quality", "disappoint",
)

_YES_WORDS = {"yes", "y", "true", "buy", "recommend", "recommended"}
_NO_WORDS = {"no", "n", "false", "pass", "decline", "reject"}


# --------------------------------------------------------------------------
# Shared readers over the observation dict.
#
# All of these tolerate a missing or malformed field: the guard in Policy would
# catch an exception anyway, but degrading to a sensible legal move beats
# degrading to the blanket fallback.
# --------------------------------------------------------------------------

def _state(game: dict) -> dict:
    return (game.get("game_state") or {}) if isinstance(game, dict) else {}


def _action_type(game: dict):
    return ((game.get("valid_actions") or {}).get("type")
            if isinstance(game, dict) else None)


def _me(game: dict) -> str:
    """The player whose move this is.

    ``coerce`` keys the bargaining offer off ``your_player``, so prefer that and
    agree with it; ``current_player`` is the fallback and, on your own turn, the
    same thing.
    """
    return game.get("your_player") or _state(game).get("current_player") or PLAYER_1


def _rounds_left(state: dict):
    """Rounds remaining including this one; None when the game is uncapped."""
    if state.get("horizon_known") is False or state.get("max_rounds") is None:
        return None
    remaining = int(_num(state.get("max_rounds"), 1)) - int(_num(state.get("round"), 1)) + 1
    return max(1, remaining)


def _progress(state: dict) -> float:
    """How far into the game this round is, in [0, 1]. 1.0 is the last round."""
    if _rounds_left(state) is None:
        round_no = int(_num(state.get("round"), 1))
        return min(max((round_no - 1) / max(_ASSUMED_HORIZON - 1, 1), 0.0), 1.0)
    max_rounds = int(_num(state.get("max_rounds"), 1))
    if max_rounds <= 1:
        return 1.0
    round_no = int(_num(state.get("round"), 1))
    return min(max((round_no - 1) / (max_rounds - 1), 0.0), 1.0)


def _at_the_edge(state: dict) -> bool:
    """Whether holding out any longer risks ending the game at $0.

    True on the final round of a capped game, and once an uncapped game has run
    past the assumed horizon (ASSUMPTION 2). The second half matters twice over:
    an uncapped game has no deadline to walk to, and without it two policies
    that only fold at a deadline would deadlock a simulated match forever.

    Kept separate from ``is_final_round``, which answers a different question —
    whether a rejection still needs a counteroffer attached — and must stay
    exactly the notion ``coerce`` uses.
    """
    return is_final_round(state) or _progress(state) >= 1.0


def _money(state: dict) -> float:
    return _num(state.get("money_to_divide"), 0.0)


def _offered_share(state: dict, me: str):
    """Share of the pot the standing offer gives me, or None if there is none."""
    offer = state.get("last_offer") or {}
    gain = offer.get(f"{me}_gain")
    if gain is None:
        return None
    money = _money(state)
    return _num(gain) / money if money > 0 else 0.0


def _offered_shares(state: dict, me: str) -> list:
    """Every share the opponent has proposed for me, oldest first.

    The concession *sequence*, which is what a mirroring policy needs; a single
    standing offer says nothing about how fast anyone is moving.
    """
    money = _money(state)
    if money <= 0:
        return []
    shares = []
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        offer = entry.get("offer") or {}
        proposer = offer.get("proposer") or entry.get("proposer")
        if proposer is None or proposer == me:
            continue
        gain = offer.get(f"{me}_gain")
        if gain is not None:
            shares.append(_num(gain) / money)
    last = state.get("last_offer") or {}
    if last.get("proposer") not in (None, me) and last.get(f"{me}_gain") is not None:
        shares.append(_num(last[f"{me}_gain"]) / money)
    return shares


def _bargaining_offer(game: dict, my_share: float, message: str | None = None) -> dict:
    """Build an offer keeping ``my_share`` of the pot for the mover."""
    state = _state(game)
    money = _money(state)
    mine = min(max(my_share, 0.0), 1.0) * money
    action = ({"alice_gain": mine, "bob_gain": money - mine}
              if _me(game) == PLAYER_1 else
              {"alice_gain": money - mine, "bob_gain": mine})
    if message:
        action["message"] = message
    return action


def _role(state: dict, me: str) -> str:
    role = state.get(f"{me}_role")
    if role in ("seller", "buyer"):
        return role
    return "seller" if me == PLAYER_1 else "buyer"       # docs: player_1 is the seller


def _my_value(state: dict, me: str) -> float:
    # Your own valuation is always visible; 1.0 matches ``safe_action``'s default
    # so a state missing it still produces the same conservative price.
    return _num(state.get(f"{me}_value"), 1.0)


def _last_price(state: dict):
    price = (state.get("last_offer") or {}).get("price")
    return None if price is None else _num(price)


def _opponent_prices(state: dict, me: str) -> list:
    """Every price the opponent has named, oldest first."""
    prices = []
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        for candidate in (entry.get("offer"), entry.get("counteroffer")):
            if not isinstance(candidate, dict):
                continue
            if candidate.get("from_player") in (None, me):
                continue
            if candidate.get("price") is not None:
                prices.append(_num(candidate["price"]))
    last = state.get("last_offer") or {}
    if last.get("from_player") not in (None, me) and last.get("price") is not None:
        prices.append(_num(last["price"]))
    return prices


def _profitable(price: float, my_value: float, role: str) -> bool:
    """Whether accepting ``price`` beats the $0 a no-deal pays."""
    return price >= my_value if role == "seller" else price <= my_value


def _is_recommendation(message) -> bool:
    """Whether a seller message reads as "buy this one" (ASSUMPTION 3)."""
    if message is None:
        return False                        # nothing said is nothing recommended
    text = str(message).strip().lower()
    if not text:
        return False
    if text in _YES_WORDS:
        return True
    if text in _NO_WORDS:
        return False
    return not any(marker in text for marker in _NEGATIVE_MARKERS)


def _is_high(state: dict) -> bool:
    return str(state.get("current_quality", "")).strip().lower() == "high"


def _prior_value(state: dict) -> float:
    """The buyer's expected value from the prior alone: p*v + (1-p)*u."""
    p = _num(state.get("p"), 0.5)
    return p * _num(state.get("v"), 0.0) + (1.0 - p) * _num(state.get("u"), 0.0)


def _persuasion_history(state: dict) -> list:
    return [h for h in (state.get("history") or []) if isinstance(h, dict)]


# --------------------------------------------------------------------------
# The reference agent, reproduced from docs/reference/example_simple_agent.py.
#
# Kept as free functions because it is also the default behaviour every other
# archetype falls back to for the phases it has no opinion about. The field
# expressions are transcribed verbatim, including the strict ``>`` in the buyer
# rule and the direct key indexing — a state the reference would crash on is one
# this module falls back on, which is the single deliberate deviation.
# --------------------------------------------------------------------------

def _baseline_bargaining_offer(game: dict) -> dict:
    money = _state(game)["money_to_divide"]
    half = money / 2
    return {"alice_gain": half, "bob_gain": half, "message": "Fair split?"}


def _baseline_bargaining_decision(game: dict) -> dict:
    state = _state(game)
    money = state["money_to_divide"]
    # In the decision phase, current_player is always the offer's receiver.
    my_gain = state["last_offer"][f"{state['current_player']}_gain"]
    return {"decision": "accept" if my_gain >= money * 0.4 else "reject"}


def _baseline_negotiation_offer(game: dict) -> dict:
    state = _state(game)
    me = state["current_player"]
    my_value = state[f"{me}_value"]
    if state[f"{me}_role"] == "seller":
        return {"product_price": my_value * 1.5, "message": "Good price"}
    return {"product_price": my_value * 0.7, "message": "Fair offer"}


def _baseline_negotiation_decision(game: dict) -> dict:
    state = _state(game)
    me = state["current_player"]
    my_value = state[f"{me}_value"]
    price = state["last_offer"]["price"]
    if state[f"{me}_role"] == "buyer":
        if price <= my_value:
            return {"decision": "AcceptOffer"}
        # The reference attaches a counteroffer on every rejection, final round
        # included, where none is required. Reproduced as written.
        return {"decision": "RejectOffer", "product_price": my_value * 0.8}
    if price >= my_value:
        return {"decision": "AcceptOffer"}
    return {"decision": "RejectOffer", "product_price": my_value * 1.3}


def _baseline_seller_message(game: dict) -> dict:
    return {"message": "This is a great product, I highly recommend it!"}


def _baseline_seller_recommendation(game: dict) -> dict:
    return {"decision": "yes"}


def _baseline_buyer_decision(game: dict) -> dict:
    state = _state(game)
    price = state["product_price"]
    expected_value = state["p"] * state["v"] + (1 - state["p"]) * state["u"]
    return {"decision": "yes" if expected_value > price else "no"}


# --------------------------------------------------------------------------
# The policy base class.
# --------------------------------------------------------------------------

class Policy:
    """Routes an observation to the handler for its phase, then guards it.

    Subclasses override only the phases their archetype has an opinion about;
    everything else stays on the reference agent's behaviour, which is both a
    legal move and the most representative one.
    """

    name = "policy"

    def __call__(self, game: dict) -> dict:
        try:
            return coerce(self._decide(game), game)
        except Exception:
            logger.exception("opponent %s raised; falling back", self.name)
        try:
            return safe_action(game)
        except Exception:
            # Only reachable when ``game`` is not even a dict. Submitting a
            # wrong-shaped action costs one attempt; submitting nothing costs
            # the whole game on the turn clock.
            logger.exception("opponent %s: safe_action failed", self.name)
            return {"decision": "accept"}

    def _decide(self, game: dict):
        family = game.get("game_family")
        action_type = _action_type(game)
        if family == "bargaining":
            if action_type == "offer":
                return self.bargaining_offer(game)
            if action_type == "decision":
                return self.bargaining_decision(game)
        elif family == "negotiation":
            if action_type == "offer":
                return self.negotiation_offer(game)
            if action_type == "decision":
                return self.negotiation_decision(game)
        elif family == "persuasion":
            if action_type == "seller_message":
                return self.seller_message(game)
            if action_type == "seller_recommendation":
                return self.seller_recommendation(game)
            if action_type == "buyer_decision":
                return self.buyer_decision(game)
        # Unknown family or phase: let the repair layer pick something legal.
        return None

    bargaining_offer = staticmethod(_baseline_bargaining_offer)
    bargaining_decision = staticmethod(_baseline_bargaining_decision)
    negotiation_offer = staticmethod(_baseline_negotiation_offer)
    negotiation_decision = staticmethod(_baseline_negotiation_decision)
    seller_message = staticmethod(_baseline_seller_message)
    seller_recommendation = staticmethod(_baseline_seller_recommendation)
    buyer_decision = staticmethod(_baseline_buyer_decision)


class DocsBaseline(Policy):
    """The reference agent from docs/reference/example_simple_agent.py.

    50/50 offers, accept at 40%, fixed anchor multiples off your own valuation,
    always recommend, buy when the prior expected value beats the price. The
    matchmaker falls back to an LLM baseline within 30 seconds and the published
    example is what most of the field starts from, so this is the archetype that
    has to be right: results against it are the closest thing the simulator has
    to results against the real queue.
    """

    name = "docs_baseline"


# --------------------------------------------------------------------------
# Hardliner.
# --------------------------------------------------------------------------

_HARD_OPEN_SHARE = 0.90         # bargaining: pot share demanded in round 1
_HARD_END_SHARE = 0.85          # ... and at the deadline. Almost nothing given.
_HARD_ACCEPT_SHARE = 0.80       # nothing below this is worth a round
_HARD_SELLER_ANCHOR = 2.00      # negotiation anchors, as multiples of own value
_HARD_BUYER_ANCHOR = 0.50
_HARD_MARGIN = 0.40             # profit demanded, as a fraction of own value


class Hardliner(Policy):
    """Concedes almost nothing and walks the deadline right to the edge.

    The archetype that punishes a strategy for conceding on a schedule: it holds
    its anchor for the whole game and takes a merely-profitable deal only at the
    edge of the horizon, where rejecting would end the game at $0. It never walks
    away — walking away pays exactly what rejecting pays, without the option
    value of another round.
    """

    name = "hardliner"

    def bargaining_offer(self, game: dict) -> dict:
        share = _HARD_OPEN_SHARE - (_HARD_OPEN_SHARE - _HARD_END_SHARE) * _progress(_state(game))
        return _bargaining_offer(game, share, "This is the split I need.")

    def bargaining_decision(self, game: dict):
        state = _state(game)
        share = _offered_share(state, _me(game))
        if share is None:
            return None                     # no offer to judge; take the fallback
        if _at_the_edge(state):
            # Rejecting now pays $0, so anything at all beats holding out.
            return {"decision": "accept"}
        return {"decision": "accept" if share >= _HARD_ACCEPT_SHARE else "reject"}

    def negotiation_offer(self, game: dict) -> dict:
        state = _state(game)
        me = _me(game)
        my_value = _my_value(state, me)
        anchor = _HARD_SELLER_ANCHOR if _role(state, me) == "seller" else _HARD_BUYER_ANCHOR
        return {"product_price": my_value * anchor, "message": "That is my price."}

    def negotiation_decision(self, game: dict):
        state = _state(game)
        me = _me(game)
        role = _role(state, me)
        my_value = _my_value(state, me)
        price = _last_price(state)
        if price is None:
            return None
        target = my_value * (1 + _HARD_MARGIN) if role == "seller" else my_value * (1 - _HARD_MARGIN)
        if _profitable(price, target, role) or (
                _at_the_edge(state) and _profitable(price, my_value, role)):
            return {"decision": "AcceptOffer"}
        if is_final_round(state):
            return {"decision": "RejectOffer"}       # no counteroffer exists
        anchor = _HARD_SELLER_ANCHOR if role == "seller" else _HARD_BUYER_ANCHOR
        return {"decision": "RejectOffer", "product_price": my_value * anchor,
                "message": "My price has not changed."}

    def seller_message(self, game: dict) -> dict:
        return {"message": "You will not find better. Take it or leave it."}

    def seller_recommendation(self, game: dict) -> dict:
        return {"decision": "yes"}          # every unit, every round, no exceptions

    def buyer_decision(self, game: dict) -> dict:
        # Cheap talk moves this buyer not at all: it prices off the prior and
        # demands a real margin on top before parting with money.
        state = _state(game)
        price = _num(state.get("product_price"), 0.0)
        return {"decision": "yes" if _prior_value(state) >= price * (1 + _HARD_MARGIN) else "no"}


# --------------------------------------------------------------------------
# Conceder.
# --------------------------------------------------------------------------

_CONCEDE_OPEN_SHARE = 0.50      # bargaining: opens on an even split
_CONCEDE_END_SHARE = 0.25       # ... and gives away half of that by the deadline
_CONCEDE_ACCEPT_SHARE = 0.25    # decayed to zero at the deadline
_CONCEDE_SELLER_OPEN = 1.30     # negotiation anchors, as multiples of own value
_CONCEDE_BUYER_OPEN = 0.70


class Conceder(Policy):
    """Concedes fast, accepts early, and almost never risks a no-deal.

    The mirror image of the hardliner, and the archetype that flatters an
    aggressive strategy. A knob that only looks good against this one is a knob
    tuned to a pushover.

    Persuasion has no literal concession, so it maps onto the trust dimension
    instead (ASSUMPTION 5): the seller gives up the sale rather than the lie,
    and the buyer takes the recommendation at face value.
    """

    name = "conceder"

    def bargaining_offer(self, game: dict) -> dict:
        share = _CONCEDE_OPEN_SHARE - (_CONCEDE_OPEN_SHARE - _CONCEDE_END_SHARE) * _progress(_state(game))
        return _bargaining_offer(game, share, "Let us not drag this out.")

    def bargaining_decision(self, game: dict):
        state = _state(game)
        share = _offered_share(state, _me(game))
        if share is None:
            return None
        threshold = _CONCEDE_ACCEPT_SHARE * (1.0 - _progress(state))
        return {"decision": "accept" if share >= threshold else "reject"}

    def negotiation_offer(self, game: dict) -> dict:
        state = _state(game)
        me = _me(game)
        my_value = _my_value(state, me)
        progress = _progress(state)
        if _role(state, me) == "seller":
            # Both schedules land on the reservation value: fast, but never at a loss.
            multiple = _CONCEDE_SELLER_OPEN - (_CONCEDE_SELLER_OPEN - 1.0) * progress
        else:
            multiple = _CONCEDE_BUYER_OPEN + (1.0 - _CONCEDE_BUYER_OPEN) * progress
        return {"product_price": my_value * multiple, "message": "I want this to work."}

    def negotiation_decision(self, game: dict):
        state = _state(game)
        me = _me(game)
        role = _role(state, me)
        my_value = _my_value(state, me)
        price = _last_price(state)
        if price is None:
            return None
        if _profitable(price, my_value, role):
            return {"decision": "AcceptOffer"}
        if is_final_round(state):
            return {"decision": "RejectOffer"}       # a losing deal is worse than none
        counter = self.negotiation_offer(game)
        return {"decision": "RejectOffer", "product_price": counter["product_price"],
                "message": "Close — try this."}

    def seller_message(self, game: dict) -> dict:
        if _is_high(_state(game)):
            return {"message": "This one is high quality. I recommend it."}
        return {"message": "I would not recommend this one — it is low quality."}

    def seller_recommendation(self, game: dict) -> dict:
        return {"decision": "yes" if _is_high(_state(game)) else "no"}

    def buyer_decision(self, game: dict) -> dict:
        state = _state(game)
        price = _num(state.get("product_price"), 0.0)
        if not _is_recommendation(state.get("seller_message")):
            return {"decision": "no"}
        # Takes the recommendation at face value: buys whenever a high-quality
        # unit would cover the price, without asking whether it is one.
        return {"decision": "yes" if _num(state.get("v"), 0.0) >= price else "no"}


# --------------------------------------------------------------------------
# Tit for tat.
# --------------------------------------------------------------------------

_TFT_BARG_ANCHOR = 0.75
_TFT_SELLER_ANCHOR = 1.60
_TFT_BUYER_ANCHOR = 0.60
_TFT_TOLERANCE = 0.02           # pot share; keeps float noise from a needless round


class TitForTat(Policy):
    """Mirrors the opponent's concession rate, read out of the history.

    It opens on its own anchor and then moves exactly as far as the opponent has
    moved since their first offer — no faster, and never past the mirror image
    of its anchor. Against a hardliner it deadlocks; against a conceder it
    collects; against itself it stalls. That is the point: a strategy that only
    wins by conceding first loses to this one.

    In persuasion, "concession" is cooperation: the seller stays honest while the
    buyer keeps buying, the buyer keeps trusting while the seller keeps telling
    the truth, and either side defects the round after being burned.
    """

    name = "tit_for_tat"

    @staticmethod
    def _target_share(state: dict, me: str) -> float:
        shares = _offered_shares(state, me)
        conceded = max(shares[-1] - shares[0], 0.0) if len(shares) >= 2 else 0.0
        return max(_TFT_BARG_ANCHOR - conceded, 1.0 - _TFT_BARG_ANCHOR)

    def bargaining_offer(self, game: dict) -> dict:
        state = _state(game)
        return _bargaining_offer(game, self._target_share(state, _me(game)),
                                 "I move as far as you do.")

    def bargaining_decision(self, game: dict):
        state = _state(game)
        me = _me(game)
        share = _offered_share(state, me)
        if share is None:
            return None
        if _at_the_edge(state):
            return {"decision": "accept" if share > 0 else "reject"}
        target = self._target_share(state, me)
        return {"decision": "accept" if share >= target - _TFT_TOLERANCE else "reject"}

    @staticmethod
    def _target_price(state: dict, me: str) -> float:
        role = _role(state, me)
        my_value = _my_value(state, me)
        prices = _opponent_prices(state, me)
        conceded = 0.0
        if len(prices) >= 2:
            # A conceding seller lowers their price; a conceding buyer raises it.
            conceded = max(prices[0] - prices[-1] if role == "buyer" else prices[-1] - prices[0], 0.0)
        if role == "seller":
            return max(my_value * _TFT_SELLER_ANCHOR - conceded, my_value)
        return min(my_value * _TFT_BUYER_ANCHOR + conceded, my_value)

    def negotiation_offer(self, game: dict) -> dict:
        state = _state(game)
        return {"product_price": self._target_price(state, _me(game)),
                "message": "I move as far as you do."}

    def negotiation_decision(self, game: dict):
        state = _state(game)
        me = _me(game)
        role = _role(state, me)
        price = _last_price(state)
        if price is None:
            return None
        if _profitable(price, self._target_price(state, me), role):
            return {"decision": "AcceptOffer"}
        if _at_the_edge(state):
            # Deadline: a profitable deal beats the $0 a rejection now pays.
            if _profitable(price, _my_value(state, me), role):
                return {"decision": "AcceptOffer"}
            if is_final_round(state):
                return {"decision": "RejectOffer"}
        return {"decision": "RejectOffer", "product_price": self._target_price(state, me),
                "message": "Meet me where I met you."}

    @staticmethod
    def _buyer_defected(state: dict) -> bool:
        """True when the buyer ignored a recommendation last round."""
        history = _persuasion_history(state)
        if not history:
            return False
        last = history[-1]
        return _is_recommendation(last.get("seller_message")) and not last.get("bought")

    @staticmethod
    def _seller_lied(state: dict) -> bool:
        """True when the last round whose quality the buyer saw was a lie.

        Quality is revealed only on rounds the buyer bought, so this is the whole
        of the buyer's evidence.
        """
        for entry in reversed(_persuasion_history(state)):
            quality = entry.get("quality")
            if not entry.get("bought") or quality is None:
                continue
            return (_is_recommendation(entry.get("seller_message"))
                    and str(quality).strip().lower() != "high")
        return False

    def seller_message(self, game: dict) -> dict:
        state = _state(game)
        if self._buyer_defected(state):
            return {"message": "You passed on the last one. This one is excellent."}
        if _is_high(state):
            return {"message": "This one is high quality. I recommend it."}
        return {"message": "I would not recommend this one — it is low quality."}

    def seller_recommendation(self, game: dict) -> dict:
        state = _state(game)
        if self._buyer_defected(state):
            return {"decision": "yes"}      # retaliate: recommend regardless of quality
        return {"decision": "yes" if _is_high(state) else "no"}

    def buyer_decision(self, game: dict) -> dict:
        state = _state(game)
        price = _num(state.get("product_price"), 0.0)
        if self._seller_lied(state):
            return {"decision": "yes" if _prior_value(state) >= price else "no"}
        if not _is_recommendation(state.get("seller_message")):
            return {"decision": "no"}
        return {"decision": "yes" if _num(state.get("v"), 0.0) >= price else "no"}


# --------------------------------------------------------------------------
# Random valid — the noise floor.
# --------------------------------------------------------------------------

_RANDOM_MESSAGES = (
    "Take a look at this one.",
    "This is a great product, I highly recommend it!",
    "I would not recommend this one — it is low quality.",
    "Your call.",
)


class RandomValid(Policy):
    """Draws uniformly from the legal moves.

    The noise floor. A strategy that cannot beat this one by a wide margin is
    not a strategy, and the gap to it is the cheapest sanity check there is on a
    tuning run. Carries its own RNG so tournaments are reproducible; construct
    ``RandomValid(seed)`` for an independent stream.

    Uniformity is only well defined on the discrete choices — the continuous
    ones (a pot split, a price, a free-text message) are drawn from bounded
    ranges instead, see ASSUMPTIONS 3 and 4.
    """

    name = "random_valid"

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)

    def bargaining_offer(self, game: dict) -> dict:
        return _bargaining_offer(game, self.rng.random(), self.rng.choice(_RANDOM_MESSAGES))

    def bargaining_decision(self, game: dict) -> dict:
        return {"decision": self.rng.choice(("accept", "reject", "walkaway"))}

    def _random_price(self, game: dict) -> float:
        state = _state(game)
        return self.rng.uniform(0.0, 2.0 * max(_my_value(state, _me(game)), 1.0))

    def negotiation_offer(self, game: dict) -> dict:
        return {"product_price": self._random_price(game),
                "message": self.rng.choice(_RANDOM_MESSAGES)}

    def negotiation_decision(self, game: dict) -> dict:
        decision = self.rng.choice(("AcceptOffer", "RejectOffer", "WalkAway"))
        if decision == "RejectOffer" and not is_final_round(_state(game)):
            return {"decision": decision, "product_price": self._random_price(game)}
        return {"decision": decision}

    def seller_message(self, game: dict) -> dict:
        return {"message": self.rng.choice(_RANDOM_MESSAGES)}

    def seller_recommendation(self, game: dict) -> dict:
        return {"decision": self.rng.choice(("yes", "no"))}

    def buyer_decision(self, game: dict) -> dict:
        return {"decision": self.rng.choice(("yes", "no"))}


# --------------------------------------------------------------------------
# Persuasion specialists.
#
# All three carry the reference agent's behaviour in bargaining and negotiation
# and on the seat they are not named for: an honest *seller* still needs a legal
# move when the draw seats it as the buyer.
# --------------------------------------------------------------------------

class HonestSeller(Policy):
    """Recommends a unit exactly when it is high quality.

    The upper bound on trust: a buyer who tracks truthfulness converges on
    believing this seller completely, which makes it the control case for
    measuring what a lie actually costs.
    """

    name = "honest_seller"

    def seller_message(self, game: dict) -> dict:
        state = _state(game)
        quality = str(state.get("current_quality", "")).strip().lower()
        if quality == "high":
            return {"message": "This one is high quality. I recommend it."}
        if quality == "low":
            return {"message": "I would not recommend this one — it is low quality."}
        return _baseline_seller_message(game)   # quality hidden: nothing to be honest about

    def seller_recommendation(self, game: dict) -> dict:
        return {"decision": "yes" if _is_high(_state(game)) else "no"}


class GreedySeller(Policy):
    """Recommends every unit, every round, whatever the quality.

    Maximal short-run extraction and zero reputation. In binary mode this is
    exactly the reference agent's seller — worth knowing, since it means the
    seeded field is already full of sellers whose recommendations carry no
    information at all.
    """

    name = "greedy_seller"

    def seller_message(self, game: dict) -> dict:
        return {"message": "This is an outstanding product — you should buy it."}

    def seller_recommendation(self, game: dict) -> dict:
        return {"decision": "yes"}


# Pseudo-observations of the prior in the buyer's honesty estimate. Keeps one
# unlucky round from swinging the posterior to an extreme.
_TRUST_PRIOR_STRENGTH = 2.0


class TrustTrackingBuyer(Policy):
    """A buyer that prices the seller's observed truthfulness, not the prior.

    Quality is revealed only on rounds it bought, so its evidence is exactly the
    purchases it has made. It scores how often a message of the same kind — a
    recommendation, or the absence of one — preceded a high-quality unit, shrinks
    that toward the prior, and buys when the resulting expected value covers the
    price. Against ``honest_seller`` it converges on buying; against
    ``greedy_seller`` it stops.
    """

    name = "trust_tracking_buyer"

    @staticmethod
    def _belief(state: dict, recommended: bool) -> float:
        """P(high quality | a message of this kind), shrunk toward the prior."""
        p = _num(state.get("p"), 0.5)
        highs = 0.0
        total = 0.0
        for entry in _persuasion_history(state):
            quality = entry.get("quality")
            if not entry.get("bought") or quality is None:
                continue                    # quality is revealed only on purchases
            if _is_recommendation(entry.get("seller_message")) != recommended:
                continue
            total += 1.0
            if str(quality).strip().lower() == "high":
                highs += 1.0
        return (p * _TRUST_PRIOR_STRENGTH + highs) / (_TRUST_PRIOR_STRENGTH + total)

    def buyer_decision(self, game: dict) -> dict:
        state = _state(game)
        price = _num(state.get("product_price"), 0.0)
        belief = self._belief(state, _is_recommendation(state.get("seller_message")))
        expected = belief * _num(state.get("v"), 0.0) + (1.0 - belief) * _num(state.get("u"), 0.0)
        # Ties go to buying: at equal expected value the purchase also buys the
        # observation of this round's quality, which nothing else can.
        return {"decision": "yes" if expected >= price else "no"}


OPPONENTS = {
    "docs_baseline": DocsBaseline(),
    "hardliner": Hardliner(),
    "conceder": Conceder(),
    "tit_for_tat": TitForTat(),
    "random_valid": RandomValid(),
    "honest_seller": HonestSeller(),
    "greedy_seller": GreedySeller(),
    "trust_tracking_buyer": TrustTrackingBuyer(),
}


def get(name: str):
    """The policy registered under ``name``."""
    try:
        return OPPONENTS[name]
    except KeyError:
        raise ValueError(f"unknown opponent {name!r}; "
                         f"available: {', '.join(sorted(OPPONENTS))}") from None
