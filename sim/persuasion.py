"""Persuasion (strategic information transmission) — the local engine.

A seller who sees each round's quality talks to a buyer who sees only the prior.
The price is fixed, the seller is paid it on every sale whatever the quality, and
the buyer pays it hoping the unit is worth ``v`` rather than ``u``. Payoffs sum
over ``total_rounds`` rounds, so the seller's only cost of lying is the buyer's
future belief — which is why this family is really about reputation.

This engine exists to let a strategy be tuned offline, so it copies the wire
format rather than a convenient abstraction of it: ``observation`` emits exactly
what ``GET /api/agent/games/pending`` returns (envelope keys, the filtered
``game_state``, ``valid_actions`` with its self-documenting ``fields``), and
``submit`` accepts exactly what ``POST /api/agent/games/{id}/move`` accepts.
Illegal actions are rejected, never repaired: catching them here is the whole
point, because live they cost one of five attempts and eventually the game.

Turn structure, per round r = 1..total_rounds:

    nature draws quality_r ~ Bernoulli(p)  ->  seller moves  ->  buyer moves
    ->  round resolves (payoffs, history entry)  ->  r += 1

Exactly ``2 * total_rounds`` moves, strictly alternating, seller first. The only
non-degenerate ending is running out of rounds; the only other ending is a
force-close (five invalid moves, or — live — a turn timeout), which zeroes both
sides.

ASSUMPTIONS (the docs do not pin these down; each is the standard reading, and
each is one edit away from its alternative):

* NO DISCOUNTING. "Payoffs sum across rounds", every round weighted 1.0. The
  persuasion field list carries no delta/discount key — inflation is discussed
  only under bargaining — so this engine deliberately does NOT put one into
  ``game_state``. If this is ever wrong it flatters late rounds.
* QUALITY is drawn i.i.d. Bernoulli(p) per round, independent of history and of
  either player's actions, and realised BEFORE the seller speaks (the seller
  moves first and "knows each round's quality"). Drawn lazily, one draw per
  round, from the injected rng so replays reproduce.
* OUTCOME STRINGS: "completed" for a full run (from sim/types.GameResult),
  "no_deal" for a force-close (from the documented game-status vocabulary).
* FORCE-CLOSE ZEROES ACCRUED PAYOFFS. "Use them up and the game ends as no-deal
  (both get 0)" — read as discarding everything already earned. The alternative
  (keep what the completed rounds paid) has no support in the docs.
* ATTEMPT BUDGET IS PER GAME, not reset by a valid move. The docs say both;
  this is the stricter reading, so an agent tuned against it is safe under
  either. Change MAX_INVALID_ATTEMPTS' use in ``_reject`` to reset per move.
* DECISIONS ARE CASE-SENSITIVE lowercase "yes"/"no" (bargaining is lowercase,
  negotiation is CamelCase — the server clearly compares literal strings).
* ``seller_message`` holds only the CURRENT round's message and is present-but-
  null before the seller has spoken this round (mirrors ``last_offer``, which
  the other two families document as "null before the first offer"). Older
  messages live in ``history``.
* ``history[i].seller_message`` in binary mode is the literal string "yes"/"no",
  mirroring the submitted action value.
* ``history[i].seller_payoff`` / ``buyer_payoff`` are that round's INCREMENT;
  the running totals are the separate ``*_total_payoff`` keys.
* ``buyer_total_payoff`` and ``history[i].buyer_payoff`` are WITHHELD FROM THE
  SELLER when ``is_seller_know_cv`` is false: together with the qualities and
  the purchase record they reveal ``v``, which the family-wide filtering rule
  ("anything you may not see is simply absent") forbids the seller. Judgement
  call, and deliberately the restrictive one — if the sim hides what the server
  sends the agent merely forgoes information, whereas if the sim shows what the
  server hides the live agent hits a KeyError mid-game.
* ``is_seller_know_cv`` IS NOT EMITTED IN ``game_state`` — it is a configuration
  knob here, nothing more. The two docs disagree: the platform documentation's
  persuasion field list (glee-docs.md) names it only as the parenthetical
  CONDITION on the v/u bullet, while the SDK README's "keys you can rely on"
  table lists it as a field. The platform docs are authoritative, and the
  restrictive reading is the safe one either way by the rule above: a sim that
  hides a key the server sends costs the agent some information, whereas a sim
  that emits a key the server withholds invites ``state["is_seller_know_cv"]``
  in tuned code and a live KeyError. A strategy that wants it anyway should read
  ``state.get("is_seller_know_cv")``; the seller can also infer it exactly, from
  whether ``v`` is present in its own view. To flip this, re-add the key in
  ``_game_state``.
* ``current_quality`` is in the seller's view for the whole active round (both
  phases — GET works between turns) and is dropped once the game completes.
* AN EMPTY OR WHITESPACE-ONLY SELLER MESSAGE IS LEGAL and is stored verbatim.
  Over-length is the only message condition the docs make invalid, and fair play
  lists "silence" among the legal message contents, so refusing "" here would
  burn an attempt the server has no documented reason to burn. ``seller_message``
  therefore distinguishes ``None`` (the seller has not moved yet this round) from
  ``""`` (the seller moved and said nothing).
* CROSS-FAMILY ACTION KEYS (product_price / alice_gain / bob_gain) are rejected;
  other unknown keys are ignored with a warning. Persuasion has no price channel
  at all, so a leaked one means the strategy dispatched on the wrong family —
  better caught here than live. Ignoring the rest avoids inventing invalid-move
  statistics the server may not produce.
* On the FIFTH rejection ``submit`` returns ``attempts_left=0`` and additionally
  carries ``game_over``/``result`` for the local driver's convenience; the
  server's documented invalid-move body has neither. Nothing a strategy sees.
* ``valid_actions["type"]`` is None once the game is completed (the server never
  lists a finished game as pending, so it has no documented shape), and the
  ``fields`` wordings are illustrative — only the type string and the field KEY
  names are contractual.
* OPPONENT DISCLOSURE is drawn here, 50/50, once per game and fixed for its
  whole life, matching "a random half of games disclose the opponent's identity".

Config params (``Config.params``) use the same names as the state fields:
``product_price``, ``p``, ``v``, ``u``, ``total_rounds``, ``seller_message_type``
("text" | "binary"), plus ``is_seller_know_cv``, which is a config knob only and
never reaches ``game_state``. Optional: ``opponent_name``, ``opponent_type``,
``disclose_opponent`` (bool, to pin the coin flip).
"""

from __future__ import annotations

import logging

from .types import (
    MAX_INVALID_ATTEMPTS,
    PLAYER_1,
    PLAYER_2,
    Config,
    GameResult,
    MoveResult,
)

logger = logging.getLogger("sim.persuasion")

#: Live cap: "max 2,000 characters. Longer is an invalid move and costs an attempt."
MAX_MESSAGE_LEN = 2000

SELLER = PLAYER_1
BUYER = PLAYER_2

PHASE_SELLER = "seller_message"
PHASE_BUYER = "buyer_decision"
PHASE_DONE = "completed"

DECISIONS = ("yes", "no")

# Action keys belonging to the other two families. Persuasion has no price and
# no gains, so one of these appearing means the strategy dispatched on the wrong
# family — a bug worth failing loudly on locally.
FOREIGN_KEYS = ("product_price", "alice_gain", "bob_gain")

# The `fields` dicts self-document the move for a human or an LLM reading the
# observation. The KEYS are contractual, the prose is not.
FIELDS_SELLER_MESSAGE = {"message": "string (your pitch to the buyer, max 2000 characters)"}
FIELDS_SELLER_RECOMMENDATION = {"decision": "'yes' (recommend) or 'no' (do not recommend)"}
FIELDS_BUYER_DECISION = {"decision": "'yes' (buy) or 'no' (pass)"}


def _money(amount) -> str:
    try:
        value = float(amount)
    except (TypeError, ValueError):
        return str(amount)
    if value == int(value):
        return f"${int(value):,}"
    return f"${value:,.2f}"


class PersuasionEngine:
    """One persuasion game, driven move by move."""

    game_family = "persuasion"

    def __init__(self, config: Config, rng, game_id: str = "local"):
        params = config.params
        self.config = config
        self.game_id = game_id
        self._rng = rng

        self.product_price = params["product_price"]
        self.p = params["p"]
        self.v = params["v"]
        self.u = params.get("u", 0)          # "$0 in our configurations"
        self.total_rounds = max(1, int(params["total_rounds"]))
        self.seller_message_type = params.get("seller_message_type", "text")
        self.is_seller_know_cv = bool(params.get("is_seller_know_cv", False))

        # Fixed for the whole game from the first move, like the server's.
        disclose = params.get("disclose_opponent")
        if disclose is None:
            disclose = self._rng.random() < 0.5
        if disclose:
            self._opponent = {"type": params.get("opponent_type", "agent"),
                              "name": params.get("opponent_name", "opponent")}
        else:
            self._opponent = {"type": "hidden", "name": None}

        self._round = 1
        self._phase = PHASE_SELLER
        self._current = SELLER
        self._quality = self._draw_quality()
        self._seller_message = None          # this round's message; reset each round
        self._history = []
        self._seller_total = 0
        self._buyer_total = 0
        self._invalid = {SELLER: 0, BUYER: 0}
        self._result = None

    # ------------------------------------------------------------------ state

    @property
    def done(self) -> bool:
        return self._result is not None

    @property
    def current_player(self) -> str:
        return self._current

    @property
    def result(self) -> GameResult | None:
        return self._result

    def _draw_quality(self) -> str:
        return "high" if self._rng.random() < self.p else "low"

    def _round_value(self, quality: str):
        return self.v if quality == "high" else self.u

    # ------------------------------------------------------------ observation

    def observation(self, player: str) -> dict:
        return {
            "game_id": self.game_id,
            "game_family": self.game_family,
            "your_player": player,
            "phase": self._phase,
            "opponent": dict(self._opponent),
            "game_state": self._game_state(player),
            "valid_actions": self._valid_actions(),
            "prompt": self._prompt(player),
        }

    def _valid_actions(self) -> dict:
        if self._phase == PHASE_BUYER:
            return {"type": "buyer_decision", "fields": dict(FIELDS_BUYER_DECISION)}
        if self._phase == PHASE_SELLER:
            if self.seller_message_type == "binary":
                # The phase string stays "seller_message" in binary mode: the
                # mode shows up here and nowhere else, which is why every
                # official example dispatches on valid_actions["type"].
                return {"type": "seller_recommendation",
                        "fields": dict(FIELDS_SELLER_RECOMMENDATION)}
            return {"type": "seller_message", "fields": dict(FIELDS_SELLER_MESSAGE)}
        return {"type": None, "fields": {}}

    def _game_state(self, player: str) -> dict:
        state = {
            "phase": self._phase,
            "current_player": self._current,
            "product_price": self.product_price,
            "p": self.p,
            "seller_message": self._seller_message,
            "seller_message_type": self.seller_message_type,
            "round": self._round,
            "total_rounds": self.total_rounds,
            "seller_total_payoff": self._seller_total,
            "history": [self._history_entry(entry, player) for entry in self._history],
        }
        if player == BUYER:
            state["v"] = self.v
            state["u"] = self.u
            state["buyer_total_payoff"] = self._buyer_total
            return state

        # Seller's view.
        if self.is_seller_know_cv:
            state["v"] = self.v
            state["u"] = self.u
            state["buyer_total_payoff"] = self._buyer_total
        if self._phase != PHASE_DONE:
            state["current_quality"] = self._quality
        return state

    def _history_entry(self, entry: dict, player: str) -> dict:
        """One past round, filtered. Absent keys are omitted, never nulled."""
        view = {"round": entry["round"],
                "seller_message": entry["seller_message"],
                "buyer_decision": entry["buyer_decision"],
                "bought": entry["bought"],
                "seller_payoff": entry["seller_payoff"]}
        if player == BUYER:
            # The buyer can only ever audit the rounds it paid for; a pass
            # leaves a permanent hole in the record.
            if entry["bought"]:
                view["quality"] = entry["quality"]
            view["buyer_payoff"] = entry["buyer_payoff"]
        else:
            view["quality"] = entry["quality"]
            if self.is_seller_know_cv:
                view["buyer_payoff"] = entry["buyer_payoff"]
        return view

    def _prompt(self, player: str) -> str:
        price = _money(self.product_price)
        where = f"Round {self._round} of {self.total_rounds}."

        if self._phase == PHASE_DONE:
            if player == BUYER or self.is_seller_know_cv:
                return (f"The game is over after {len(self._history)} rounds. "
                        f"Seller earned {_money(self._seller_total)}, "
                        f"buyer earned {_money(self._buyer_total)}.")
            return (f"The game is over after {len(self._history)} rounds. "
                    f"You earned {_money(self._seller_total)}.")

        if player != self._current:
            waiting = "buyer" if self._current == BUYER else "seller"
            return f"{where} Waiting for the {waiting} to move."

        if player == SELLER:
            head = (f"{where} You are the seller. This round's product is "
                    f"{self._quality} quality and sells for {price} either way. "
                    f"You have earned {_money(self._seller_total)} so far.")
            if self.seller_message_type == "binary":
                return (f"{head} Recommend it ('yes') or not ('no') — you have no "
                        "other way to speak to the buyer.")
            return f"{head} Send the buyer a message (max 2,000 characters)."

        said = self._seller_message
        if self.seller_message_type == "binary":
            heard = {"yes": "The seller recommends buying.",
                     "no": "The seller does not recommend buying."}.get(
                         said, "The seller said nothing.")
        elif isinstance(said, str) and said.strip():
            heard = f'The seller says: "{said}".'
        else:
            heard = "The seller said nothing."
        return (f"{where} You are the buyer. {heard} The price is {price}; a "
                f"high-quality unit is worth {_money(self.v)} to you and a "
                f"low-quality one {_money(self.u)}, and {self.p:.0%} of units are "
                f"high quality. Buy ('yes') or pass ('no')? You have earned "
                f"{_money(self._buyer_total)} so far.")

    # ----------------------------------------------------------------- moves

    def submit(self, player: str, action: dict) -> MoveResult:
        # API-level rejections (HTTP 400) — these are NOT invalid moves and burn
        # no attempt.
        if self.done:
            return MoveResult(valid=False, error="game not active")
        if player != self._current:
            return MoveResult(valid=False, error="not your turn")

        problem = self._validate(action)
        if problem is not None:
            return self._reject(player, problem)

        self._warn_extra_keys(action)
        if self._phase == PHASE_SELLER:
            return self._apply_seller(action)
        return self._apply_buyer(action)

    def _expected_keys(self) -> set:
        if self._phase == PHASE_SELLER and self.seller_message_type == "text":
            return {"message"}
        return {"decision"}

    def _validate(self, action) -> str | None:
        if not isinstance(action, dict):
            return "action must be a JSON object"
        for key in FOREIGN_KEYS:
            if key in action:
                return f"{key!r} belongs to another game family; persuasion has no price field"

        if self._phase == PHASE_SELLER and self.seller_message_type == "text":
            if "message" not in action:
                return "missing 'message'"
            message = action["message"]
            if not isinstance(message, str):
                return "'message' must be a string"
            # No emptiness check: silence is documented as legal content, and
            # length is the only documented way a message can be invalid.
            if len(message) > MAX_MESSAGE_LEN:
                return (f"message is {len(message)} characters; "
                        f"the limit is {MAX_MESSAGE_LEN}")
            return None

        # Binary recommendation and buyer decision share the yes/no vocabulary.
        if "decision" not in action:
            return "missing 'decision'"
        decision = action["decision"]
        if not isinstance(decision, str) or decision not in DECISIONS:
            return "'decision' must be exactly 'yes' or 'no'"
        return None

    def _warn_extra_keys(self, action: dict) -> None:
        extra = set(action) - self._expected_keys()
        if extra:
            logger.warning("persuasion %s: ignoring unexpected action keys %s",
                           self.game_id, sorted(extra))

    def _reject(self, player: str, error: str) -> MoveResult:
        """Burn one attempt. The game does not advance and the turn does not pass."""
        self._invalid[player] += 1
        left = MAX_INVALID_ATTEMPTS - self._invalid[player]
        if left > 0:
            return MoveResult(valid=False, error=error, attempts_left=left)

        result = self._force_close(player)
        return MoveResult(valid=False, error=error, attempts_left=0,
                          game_over=True, result=result.as_dict())

    def _force_close(self, offender: str) -> GameResult:
        """Five invalid moves (or, live, a turn timeout): no-deal, both get 0."""
        self._phase = PHASE_DONE
        self._result = GameResult(0, 0, "no_deal",
                                  rounds_played=len(self._history),
                                  detail={"abandoned_by": offender,
                                          "reason": "invalid_moves"})
        return self._result

    def _apply_seller(self, action: dict) -> MoveResult:
        if self.seller_message_type == "binary":
            self._seller_message = action["decision"]
        else:
            self._seller_message = action["message"]
        self._phase = PHASE_BUYER
        self._current = BUYER
        return MoveResult(valid=True)

    def _apply_buyer(self, action: dict) -> MoveResult:
        bought = action["decision"] == "yes"
        value = self._round_value(self._quality)
        seller_payoff = self.product_price if bought else 0
        buyer_payoff = (value - self.product_price) if bought else 0

        self._seller_total += seller_payoff
        self._buyer_total += buyer_payoff
        self._history.append({"round": self._round,
                              "seller_message": self._seller_message,
                              "buyer_decision": action["decision"],
                              "bought": bought,
                              "quality": self._quality,
                              "seller_payoff": seller_payoff,
                              "buyer_payoff": buyer_payoff})

        if self._round >= self.total_rounds:
            self._phase = PHASE_DONE
            self._result = GameResult(self._seller_total, self._buyer_total,
                                      "completed", rounds_played=len(self._history))
            return MoveResult(valid=True, game_over=True,
                              result=self._result.as_dict())

        self._round += 1
        self._phase = PHASE_SELLER
        self._current = SELLER
        self._seller_message = None
        self._quality = self._draw_quality()
        return MoveResult(valid=True)
