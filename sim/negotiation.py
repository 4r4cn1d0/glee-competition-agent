"""Negotiation (GLEE "Bilateral Trade") — the local engine.

Player 1 is always the seller (``player_1_value`` is their minimum acceptable
price), player 2 always the buyer (``player_2_value`` is their maximum). On an
agreement at price ``P`` the seller earns ``P - player_1_value`` and the buyer
``player_2_value - P``; every other ending pays both sides exactly $0.

The one structural fact that makes this family different from bargaining: a
rejection and the counteroffer are ONE action. ``{"decision": "RejectOffer",
"product_price": 60}`` both kills the standing offer and posts the next one, so
the standalone ``phase == "offer"`` happens exactly once per game — round 1, by
the seller. Every later move is a ``decision``, alternating. An engine that
emitted a separate offer phase in round 2+ would let a strategy branch on a
signal the live server never sends, which is the specific failure this package
exists to avoid.

Two invariants hold everywhere below, because the documented strategy idiom
``state[f"{state['current_player']}_value"]`` depends on them: in a decision
phase ``current_player`` is always the RECEIVER of ``last_offer`` (never its
author), and ``game_state["phase"]`` always equals the observation's top-level
``phase``.

ASSUMPTIONS (the docs do not pin these down; each is a place to revisit if the
platform clarifies):

1. NO DISCOUNTING. The negotiation prose has no analogue of bargaining's
   "Delays are costly: inflation erodes value each round", and both exhaustive
   ``game_state`` tables list ``delta_1``/``delta_2`` for bargaining only. So a
   deal struck in round 7 pays exactly what the same price would have paid in
   round 1, and this engine emits no delta keys at all. CONTINGENCY: if a live
   pending payload ever shows ``delta_1``/``delta_2`` in a negotiation game, adopt
   bargaining's convention — payoff times ``delta_self ** (round - 1)``, round 1
   undiscounted — behind a config flag rather than rewriting this.
2. SELLER OPENS. The docs never name the round-1 proposer for negotiation
   (there is no ``proposer`` key here). Player 1 is listed first, is the seller,
   and "single-round (take-it-or-leave-it)" is the classic seller-posted-price
   framing. Configurable via ``params["opener"]`` so the parity can be flipped if
   the live server turns out to randomise it.
3. ONE ROUND == ONE OFFER + ONE DECISION, and a counteroffer advances the round
   counter. Forced by the history schema (one offer and one decision per entry)
   plus ``max_rounds == 1`` being take-it-or-leave-it.
4. INVALID ATTEMPTS ARE PER GAME PER PLAYER. The docs contradict themselves
   ("5 attempts per game" beside the response shape, "5 attempts per move" under
   in-game limits); this takes the stricter reading, with
   ``attempts_per_game=False`` available to test the other.
5. PRICE DOMAIN. No numeric bound on ``product_price`` is documented, so any
   finite number is accepted — negative prices and prices far outside both
   valuations are legal-but-foolish. Only non-numeric and non-finite values are
   rejected, and numeric *strings* are rejected too rather than parsed: the
   simulator's job is to catch what the server would reject, and being stricter
   than the server can only surface bugs, never hide them.
6. A COUNTEROFFER ON THE FINAL ROUND IS INVALID. The mechanic is documented
   ("final round only: no counteroffer exists, ends the game"); that the extra
   key is *rejected* rather than ignored is the reading that keeps the state
   machine total — there is no round r+1 for the counter to occupy.
7. MESSAGE HANDLING. Over-long (>2,000 chars) and non-string messages are
   invalid moves. When ``messages_allowed`` is false the message is dropped
   rather than rejected — not documented as an invalid-move cause, and the
   agent's own ``coerce`` strips it first either way.
8. OUTCOME STRINGS are bargaining's vocabulary: "agreement" on an accept,
   "no_deal" on everything else.
9. WORDING of the offer phase's ``fields`` dict, and of the final round's
   downgraded ``product_price`` entry. Only the ordinary decision ``fields``
   dict is documented verbatim; that one is reproduced character for character.
10. A FINISHED GAME's observation mirrors ``GET /api/agent/games/{id}`` rather
    than ``/games/pending`` (which never shows one): ``valid_actions`` is None,
    ``status`` and ``result`` are added, and ``current_player`` leaves
    ``game_state`` because no move is awaited.

``hard_cap`` is a SIMULATOR ARTIFACT, not a mechanic: an uncapped, undiscounted
game between two stubborn strategies never terminates. It never appears in
``game_state`` — surfacing it would teach strategies a deadline the live server
does not have — and when it fires the game ends as a no-deal with
``result.detail["reason"] == "hard_cap"`` so a tuning run can measure how often
the artifact bit.
"""

from __future__ import annotations

import math
import random

from .types import (
    MAX_INVALID_ATTEMPTS,
    PLAYER_1,
    PLAYER_2,
    Config,
    GameResult,
    MoveResult,
    other_player,
)

SELLER = "seller"
BUYER = "buyer"

#: The three decision literals, CamelCase and exact. Not bargaining's lowercase
#: "accept"/"reject"/"walkaway" and not persuasion's "yes"/"no" — cross-family
#: string leakage is the likeliest way to burn an attempt live.
DECISIONS = ("AcceptOffer", "RejectOffer", "WalkAway")

MAX_MESSAGE_LEN = 2000

#: Backstop for unbounded-horizon games. See the module docstring: artifact, not
#: rule, and never visible to a strategy.
DEFAULT_HARD_CAP = 200

_OFFER_FIELDS = {"product_price": "number (required)",
                 "message": "string (optional)"}

# Documented verbatim in the SDK README; reproduced exactly.
_DECISION_FIELDS = {"decision": "'AcceptOffer', 'RejectOffer', or 'WalkAway'",
                    "product_price": "number (required if RejectOffer - your counteroffer)",
                    "message": "string (optional)"}

_FINAL_DECISION_FIELDS = {"decision": "'AcceptOffer', 'RejectOffer', or 'WalkAway'",
                          "product_price": "not applicable (final round - a rejection ends the game)",
                          "message": "string (optional)"}


class NegotiationEngine:
    """One bilateral-trade game in progress."""

    game_family = "negotiation"

    def __init__(self, config: Config, rng: random.Random, game_id: str = "local",
                 hard_cap: int = DEFAULT_HARD_CAP, attempts_per_game: bool = True):
        params = dict(config.params or {})
        self.config = config
        self.game_id = game_id
        self._rng = rng
        self._hard_cap = int(hard_cap)
        self._attempts_per_game = bool(attempts_per_game)

        self._value = {PLAYER_1: float(params.get("player_1_value", 0.0)),
                       PLAYER_2: float(params.get("player_2_value", 0.0))}

        max_rounds = params.get("max_rounds")
        # horizon_known is derived rather than read, so the two can never
        # disagree: the docs tie them together (true <=> max_rounds present).
        # An explicit horizon_known=False still wins, to protect against a grid
        # that sets both.
        if params.get("horizon_known") is False:
            max_rounds = None
        self._max_rounds = None if max_rounds is None else max(1, int(max_rounds))
        self._messages_allowed = bool(params.get("messages_allowed", True))
        self._complete_information = bool(params.get("complete_information", False))
        self._opponent = self._draw_opponent(params)

        self._round = 1
        self._phase = "offer"
        self._current = params.get("opener", PLAYER_1)
        self._last_offer = None
        self._history = []
        self._attempts = {PLAYER_1: 0, PLAYER_2: 0}
        self._result = None

    # --- Engine protocol ----------------------------------------------------

    @property
    def done(self) -> bool:
        return self._result is not None

    @property
    def current_player(self) -> str:
        return self._current

    @property
    def result(self) -> GameResult | None:
        return self._result

    def observation(self, player: str) -> dict:
        obs = {
            "game_id": self.game_id,
            "game_family": self.game_family,
            "your_player": player,
            "phase": self._phase,
            "opponent": dict(self._opponent),
            "game_state": self._state_for(player),
            "valid_actions": self._valid_actions(),
            "prompt": self._prompt(player),
        }
        if self._result is not None:
            # A finished game is only ever seen through GET /games/{id}, which
            # carries status and result (assumption 10).
            obs["status"] = "completed" if self._result.outcome == "agreement" else "no_deal"
            obs["result"] = self._result.as_dict()
        return obs

    def submit(self, player: str, action) -> MoveResult:
        # These three are 403/400 at the API layer — errors, not invalid moves,
        # so they must not cost an attempt.
        if player not in (PLAYER_1, PLAYER_2):
            return self._api_error(player, f"{player!r} is not a player in this game")
        if self._result is not None:
            return self._api_error(player, "game is not active")
        if player != self._current:
            return self._api_error(player, "not your turn")

        if not isinstance(action, dict):
            return self._reject(player, f"action must be a JSON object, got {type(action).__name__}")
        if self._phase == "offer":
            return self._submit_offer(player, action)
        return self._submit_decision(player, action)

    # --- injected endings ---------------------------------------------------

    def timeout(self, player: str) -> MoveResult:
        """Close the game the way the server's 120-second turn clock would.

        Wall-clock time cannot be simulated faithfully offline, so abandonment
        by timeout is an explicit injection rather than something this engine
        pretends does not exist. Payoffs are a plain no-deal — the asymmetry
        (the timing-out player scored at the 5th percentile, the opponent's copy
        voided) lives in the scoring layer, which reads ``detail``.
        """
        if self._result is not None:
            return self._api_error(player, "game is not active")
        return self._finish(0.0, 0.0, "no_deal", {"reason": "timeout", "by": player})

    # --- observation building -----------------------------------------------

    def _state_for(self, player: str) -> dict:
        state = {"phase": self._phase}
        if self._result is None:
            state["current_player"] = self._current
        state["player_1_role"] = SELLER
        state["player_2_role"] = BUYER
        # Filtering is by KEY OMISSION, never by null: a strategy that reads
        # state.get("player_1_value") must be able to tell "hidden" from "zero".
        if self._complete_information or player == PLAYER_1:
            state["player_1_value"] = self._value[PLAYER_1]
        if self._complete_information or player == PLAYER_2:
            state["player_2_value"] = self._value[PLAYER_2]
        state["last_offer"] = None if self._last_offer is None else dict(self._last_offer)
        state["history"] = [_copy_entry(entry) for entry in self._history]
        state["round"] = self._round
        if self._max_rounds is not None:
            state["max_rounds"] = self._max_rounds
        state["horizon_known"] = self._max_rounds is not None
        state["messages_allowed"] = self._messages_allowed
        state["complete_information"] = self._complete_information
        return state

    def _valid_actions(self):
        if self._result is not None:
            return None
        if self._phase == "offer":
            return {"type": "offer", "fields": dict(_OFFER_FIELDS)}
        fields = _FINAL_DECISION_FIELDS if self._is_final_round() else _DECISION_FIELDS
        return {"type": "decision", "fields": dict(fields)}

    def _prompt(self, player: str) -> str:
        role = _role(player)
        limit = "minimum" if role == SELLER else "maximum"
        where = (f"Round {self._round} of {self._max_rounds}" if self._max_rounds is not None
                 else f"Round {self._round}, no round limit")
        head = (f"You are the {role} ({player}); your {limit} acceptable price is "
                f"{_money(self._value[player])}. {where}.")

        if self._result is not None:
            if self._result.outcome == "agreement":
                price = self._last_offer["price"]
                return (f"{head} The negotiation closed at {_money(price)}; "
                        f"your payoff is {_money(self._result.payoff(player))}.")
            return f"{head} The negotiation ended with no deal; both sides get $0."

        if self._phase == "offer":
            return f"{head} Name your opening price for the product."

        offer = self._last_offer
        tail = ("You may accept it or walk away; rejecting now ends the negotiation "
                "with no deal for either side."
                if self._is_final_round() else
                "You may accept it, reject it with a counteroffer, or walk away.")
        return (f"{head} The {_role(offer['from_player'])} offered "
                f"{_money(offer['price'])}. {tail}")

    def _draw_opponent(self, params: dict) -> dict:
        """Who you are told you are playing — fixed for the whole game.

        "A random half of games disclose the opponent's identity from the first
        move; the other half keep it hidden for the whole game." The coin comes
        from the injected rng, so replaying a seed replays the disclosure.
        """
        disclosed = params.get("disclose_opponent")
        if disclosed is None:
            disclosed = self._rng.random() < 0.5
        if not disclosed:
            return {"type": "hidden", "name": None}
        return {"type": params.get("opponent_type", "agent"),
                "name": params.get("opponent_name", "opponent")}

    # --- moves --------------------------------------------------------------

    def _submit_offer(self, player: str, action: dict) -> MoveResult:
        price, error = _price(action)
        if error is not None:
            return self._reject(player, error)
        message, error = self._message(action)
        if error is not None:
            return self._reject(player, error)

        self._last_offer = {"price": price, "message": message,
                            "from_player": player, "round": self._round}
        self._phase = "decision"
        self._current = other_player(player)
        return self._accepted(player)

    def _submit_decision(self, player: str, action: dict) -> MoveResult:
        decision = action.get("decision")
        if decision not in DECISIONS:
            return self._reject(
                player, f"decision must be one of {', '.join(DECISIONS)}, got {decision!r}")
        message, error = self._message(action)
        if error is not None:
            return self._reject(player, error)

        if decision == "AcceptOffer":
            price = self._last_offer["price"]
            self._record_round(decision, player, message, None)
            return self._finish(price - self._value[PLAYER_1],
                                self._value[PLAYER_2] - price,
                                "agreement",
                                {"reason": "agreement", "price": price, "accepted_by": player})

        if decision == "WalkAway":
            self._record_round(decision, player, message, None)
            return self._finish(0.0, 0.0, "no_deal", {"reason": "walkaway", "by": player})

        # RejectOffer. On the final round of a capped game it takes no
        # counteroffer and ends the game; that is the only way the cap bites.
        if self._is_final_round():
            if "product_price" in action:
                return self._reject(
                    player, "round %d is the final round: a rejection takes no "
                            "counteroffer" % self._round)
            self._record_round(decision, player, message, None)
            return self._finish(0.0, 0.0, "no_deal",
                                {"reason": "final_round_rejection", "by": player})

        price, error = _price(action)
        if error is not None:
            return self._reject(player, f"off the final round a rejection must carry a "
                                        f"counteroffer: {error}")

        counter = {"price": price, "message": message, "from_player": player}
        self._record_round(decision, player, message, counter)
        # The counter is both the closing datum of round r and the standing
        # offer of round r+1; both representations are emitted.
        self._round += 1
        self._last_offer = dict(counter, round=self._round)
        self._current = other_player(player)
        if self._round > self._hard_cap:
            return self._finish(0.0, 0.0, "no_deal",
                                {"reason": "hard_cap", "hard_cap": self._hard_cap})
        return self._accepted(player)

    # --- bookkeeping --------------------------------------------------------

    def _is_final_round(self) -> bool:
        return self._max_rounds is not None and self._round >= self._max_rounds

    def _record_round(self, decision: str, player: str, message, counteroffer) -> None:
        """Close out the current round in history.

        ``message`` is the decider's, and deliberately not stored: the history
        schema carries the offer's message, the decision, and the counteroffer
        (which carries the decider's message when there is one).
        """
        offer = self._last_offer
        entry = {"round": self._round,
                 "offer": {"price": offer["price"], "message": offer["message"],
                           "from_player": offer["from_player"]},
                 "decision": decision}
        if counteroffer is not None:
            entry["counteroffer"] = dict(counteroffer)
        entry["decided_by"] = player
        self._history.append(entry)

    def _accepted(self, player: str) -> MoveResult:
        if not self._attempts_per_game:
            self._attempts[player] = 0
        return MoveResult(valid=True, game_over=False, result=None)

    def _finish(self, payoff_1: float, payoff_2: float, outcome: str, detail: dict) -> MoveResult:
        self._phase = "completed"
        self._result = GameResult(float(payoff_1), float(payoff_2), outcome,
                                  rounds_played=self._round, detail=detail)
        return MoveResult(valid=True, game_over=True, result=self._result.as_dict())

    def _api_error(self, player: str, message: str) -> MoveResult:
        """A 400/403/404 from the API layer: rejected, but no attempt spent."""
        return MoveResult(valid=False, error=message, attempts_left=self._left(player))

    def _reject(self, player: str, message: str) -> MoveResult:
        """An invalid move: costs an attempt, and never advances the game."""
        self._attempts[player] += 1
        left = self._left(player)
        if left > 0:
            return MoveResult(valid=False, error=message, attempts_left=left)
        self._finish(0.0, 0.0, "no_deal",
                     {"reason": "invalid_moves", "by": player, "last_error": message})
        return MoveResult(valid=False, game_over=True, error=message, attempts_left=0,
                          result=self._result.as_dict())

    def _left(self, player: str) -> int:
        if player not in self._attempts:
            return MAX_INVALID_ATTEMPTS
        return max(0, MAX_INVALID_ATTEMPTS - self._attempts[player])

    def _message(self, action: dict):
        """(message, error). Absent, null, and stripped all read as None."""
        if "message" not in action or action["message"] is None:
            return None, None
        message = action["message"]
        if not isinstance(message, str):
            return None, f"message must be a string, got {type(message).__name__}"
        if len(message) > MAX_MESSAGE_LEN:
            return None, (f"message is {len(message)} characters; the limit is "
                          f"{MAX_MESSAGE_LEN}")
        if not self._messages_allowed:
            return None, None          # assumption 7: dropped, not rejected
        return message, None


def _role(player: str) -> str:
    return SELLER if player == PLAYER_1 else BUYER


def _money(value) -> str:
    """Dollars as a prompt renders them: grouped, and never a number the rest of
    the observation contradicts.

    The docs' one sample prompt spells the pot out grouped and in full ("dividing
    $1,000 with Bob"), and ``prompt`` is the field an LLM strategy actually reads
    (glee_agent/llm.py feeds it straight to the model). A ``:g`` format — what this
    used — switches to scientific notation past six significant digits, so on two
    of the three money scales the model was shown "$1.2e+06" for a valuation and
    "$1.45e+06" for an offer whose ``last_offer["price"]`` was 1450000.5. Cents are
    shown when there are any, and a price with finer precision than that keeps its
    digits rather than being rounded into disagreement with ``game_state``.
    """
    value = float(value)
    if value.is_integer():
        return f"${value:,.0f}"
    text = f"{value:,.2f}"
    if float(text.replace(",", "")) != value:
        text = f"{value:,.10f}".rstrip("0").rstrip(".")
    return f"${text}"


def _price(action: dict):
    """(price, error) for the action's ``product_price``. Rejects, never repairs."""
    if "product_price" not in action:
        return None, "product_price is required"
    value = action["product_price"]
    # bool is an int subclass; True is not a price.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, f"product_price must be a number, got {type(value).__name__}"
    price = float(value)
    if not math.isfinite(price):
        return None, f"product_price must be finite, got {value!r}"
    return price, None


def _copy_entry(entry: dict) -> dict:
    """A history entry the caller can mutate without corrupting the engine."""
    copy = dict(entry)
    copy["offer"] = dict(entry["offer"])
    if "counteroffer" in entry:
        copy["counteroffer"] = dict(entry["counteroffer"])
    return copy
