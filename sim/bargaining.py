"""Bargaining (Divide the Dollar) — alternating offers under inflation.

Two players split a constant pot. One round is exactly one offer plus exactly
one response; the receiver accepts, rejects, or walks away. A rejection swaps
the proposer role and advances the round, and every round of delay multiplies a
player's eventual take by that player's own discount multiplier. The pot itself
never shrinks — erosion is applied per player at settlement.

The whole value of this file is that it lies as little as possible. A strategy
written for the live server must run against it unmodified, so the observation
is the exact dict ``GET /api/agent/games/pending`` returns (including hiding the
opponent's delta by ABSENCE of the key, not by a None), and ``submit`` accepts
exactly what ``POST /api/agent/games/{id}/move`` accepts and rejects the rest
rather than repairing it. Repair belongs on the client side, before the wire
(``glee_agent/actions.py``); an engine that repairs teaches a strategy that its
own bugs are free.

ASSUMPTIONS — things the docs do not pin down. Each one is a place where a
future observation of live play should be allowed to overrule this file.

A1  player_1 (Alice) makes the round-1 offer. The pending-games example shows
    ``your_player: "player_1"`` with ``phase: "offer"`` at round 1.
A2  Strict alternation by round parity: player_1 proposes on odd rounds,
    player_2 on even ones. Equivalently, whoever rejects proposes next.
A3  The discount exponent is (round - 1): round 1 is UNDISCOUNTED and each
    rejection multiplies the eventual payoff by one further delta. Standard
    Rubinstein/GLEE reading. The alternative (exponent = round) rescales both
    players by a constant and leaves equilibrium SHARES identical, but it
    changes absolute payoffs — and the competition ranks absolute payoffs by
    percentile, so the convention matters for tuning.
A4  ``result`` carries the REALIZED (discounted) payoffs, not the nominal gains
    of the accepted offer. The documented example is a round-1 agreement, where
    the two coincide, so it does not discriminate.
A5  Every zero-payoff ending reports outcome ``"no_deal"``; the discriminating
    reason (accept / walkaway / max_rounds / invalid_attempts / safety_cap)
    lives only in ``GameResult.detail``, never on the wire.
A6  The five invalid-move attempts are per GAME: the counter is cumulative for
    the whole game and a valid move does NOT refund an attempt. The docs say
    this twice — the move response is captioned "Invalid move (5 attempts per
    game)", and the scoring rules abandon a game on "five invalid moves" —
    against once, "5 attempts per move" in the in-game limits list. Two
    readings out of three, and the one it is safe to be wrong about: under the
    per-move reading a strategy that emits an occasionally-malformed action is
    never punished locally, while live that same flakiness abandons the game at
    the 5th percentile. Erring toward the harsher local rule makes it visible
    during tuning instead of hiding it, and matches how sim/negotiation.py and
    sim/persuasion.py already read the same sentence.
A7  Unknown extra keys in an otherwise valid action are IGNORED, not rejected —
    a leaked ``_plan``, or ``player_1_gain`` sent redundantly beside
    ``alice_gain``. Rejecting them would make this simulator stricter than the
    server and mistrain a strategy into defensive shapes it does not need.
A8  A ``message`` on a decision, and a ``message`` when ``messages_allowed`` is
    false, are stripped rather than rejected (logged, so a strategy leaning on
    unsendable text stays visible during tuning). A non-string message is
    likewise dropped rather than rejected, for the same reason.
A9  Gains must be non-negative, hence at most ``money_to_divide``. Only the
    exact-sum rule is documented, and (1200, -200) satisfies it for a pot of
    1000. ``(money, 0)`` is legal.
A10 The exact-sum check uses a small absolute tolerance so float arithmetic on
    a non-integer pot cannot produce spurious rejections.
A11 ``last_offer`` persists after a rejection — it is the last offer MADE, not
    the live one, and carries its own ``round``/``proposer``. It is null (present
    as null) only before the first offer of the game.
A12 A history entry's ``offer`` sub-dict mirrors ``last_offer``'s naming
    (``player_1_gain``/``player_2_gain``/``message``) and carries no per-round
    payoff: bargaining settles once, at the end.
A13 The 120-second turn clock is not modelled. An engine driven synchronously
    by strategy calls has no wall clock; the live no-deal-on-timeout branch
    exists in the spec for completeness only.
A14 ``observation`` after termination emits phase ``"completed"`` and no
    actionable ``valid_actions`` (GET /games/{id} keeps working after a game
    ends); a driver should be reading ``engine.result`` instead.
A15 ``opponent`` is drawn once per game and never changes: disclosed in half of
    games, ``{"type": "hidden", "name": None}`` in the other half.
A17 The wording inside ``valid_actions["fields"]`` is unspecified; only the
    ``type`` string and the action key names are contractual. No strategy may
    parse the descriptions.
A20 An uncapped game with patient players can alternate forever, so the engine
    keeps a PRIVATE safety cap. It is never exposed in ``game_state`` or
    ``valid_actions``, and firing it is recorded in ``detail`` so a tuning run
    can see that it happened.
A23 (local) Transport-level failures — not your turn, game already over, not a
    player — are reported as ``MoveResult(valid=False, attempts_left=None)``.
    Live these are HTTP 4xx with a ``{"detail": ...}`` body, NOT ``valid: false``
    invalid moves; the Engine protocol has no separate channel for them, so
    ``attempts_left is None`` is the local marker. They never consume an attempt
    and never advance the game.
A24 (local) The wire response to the attempt-exhausting move is undocumented.
    It is emitted here as ``valid=False`` with ``attempts_left=0`` AND
    ``game_over=True`` plus the populated result, so a local driver can stop
    without a second call.
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
    other_player,
)

logger = logging.getLogger("sim.bargaining")

#: Documented message cap; longer is an invalid move and costs an attempt.
MAX_MESSAGE_LEN = 2000

#: A10 — absolute tolerance on ``alice_gain + bob_gain == money_to_divide``.
SUM_TOLERANCE = 1e-6

#: A20 — private backstop for uncapped games, never visible to a player. Far
#: past any plausible play (with delta 0.9 a round-500 agreement is worth
#: 1e-23 of the pot) and comfortably inside the arena's own turn cap, so a
#: runaway closes as a proper no-deal rather than as an arena timeout.
SAFETY_ROUND_CAP = 500

_DECISIONS = ("accept", "reject", "walkaway")

#: Names used only to fill the disclosed half of the ``opponent`` field. They
#: are flavour: nothing in the engine or in a strategy should key off them.
_OPPONENT_NAMES = ("GPT-4o", "Gemini-2.5-Flash", "Claude-Sonnet", "Llama-3.1",
                   "Qwen-2.5", "BaselineBot", "Mistral-Large", "DealBot")


class BargainingEngine:
    """One bargaining game, driven move by move.

    Roles are fixed identities for the whole game: player_1 is Alice, player_2
    is Bob. ``proposer`` says who offers this round; in the decision phase
    ``current_player`` is the OTHER player, the receiver — the SDK's own example
    reads its share as ``last_offer[f"{current_player}_gain"]``, so getting that
    backwards silently inverts every split.
    """

    game_family = "bargaining"

    def __init__(self, config: Config, rng, game_id: str = "local"):
        params = dict(config.params)
        self.config = config
        self.game_id = game_id
        self._rng = rng

        # Kept exactly as configured (an int pot stays an int) so the state a
        # strategy reads is the JSON the server would have sent, not a float
        # that only looks the same.
        self.money = params["money_to_divide"]
        if not _is_number(self.money):
            raise ValueError("money_to_divide must be a number")
        self.delta_1 = float(params["delta_1"])
        self.delta_2 = float(params["delta_2"])
        max_rounds = params.get("max_rounds")
        self.max_rounds = None if max_rounds is None else int(max_rounds)
        self.messages_allowed = bool(params.get("messages_allowed", True))
        self.complete_information = bool(params.get("complete_information", True))

        # A19 — horizon_known true <=> max_rounds present. A configuration that
        # claims otherwise would have the engine holding a secret deadline,
        # which is exactly the thing the docs rule out.
        horizon_known = params.get("horizon_known", self.max_rounds is not None)
        if bool(horizon_known) != (self.max_rounds is not None):
            raise ValueError("horizon_known must be true exactly when max_rounds is set")
        self.horizon_known = bool(horizon_known)

        if self.money <= 0:
            raise ValueError("money_to_divide must be positive")
        if not 0.0 < self.delta_1 <= 1.0 or not 0.0 < self.delta_2 <= 1.0:
            raise ValueError("delta_1 and delta_2 must lie in (0, 1]")
        if self.max_rounds is not None and self.max_rounds < 1:
            raise ValueError("max_rounds must be at least 1")

        self._round = 1
        self._phase = "offer"
        self._proposer = PLAYER_1                      # A1
        self._last_offer = None                        # A11: null, not absent
        self._history = []
        self._result = None
        self._ended_by = None

        # A6 — invalid moves burned so far this GAME, per player. Never reset;
        # also reported in the result detail so a tuning run can see a strategy
        # that is merely flaky as well as one that is fatally so.
        self._invalid = {PLAYER_1: 0, PLAYER_2: 0}

        self._opponent_view = self._draw_opponents()   # A15: drawn once

    # --- Engine protocol -----------------------------------------------------

    @property
    def done(self) -> bool:
        return self._result is not None

    @property
    def current_player(self) -> str:
        if self._phase == "offer":
            return self._proposer
        if self._phase == "decision":
            return other_player(self._proposer)
        return self._ended_by or self._proposer

    @property
    def result(self):
        return self._result

    def observation(self, player: str) -> dict:
        """The game dict as the API would send it to ``player``.

        Note that ``current_player`` is computed from the GAME, never from who
        is asking: a driver may legitimately call this for the non-moving player
        (logging, or a strategy that wants to see the board on the other side).
        """
        if player not in (PLAYER_1, PLAYER_2):
            raise ValueError(f"unknown player {player!r}")

        game = {
            "game_id": self.game_id,
            "game_family": self.game_family,
            "your_player": player,
            "phase": self._phase,
            "opponent": dict(self._opponent_view[player]),
            "game_state": self._game_state(player),
            "valid_actions": self._valid_actions(),
            "prompt": self._prompt(player),
        }
        if self.done:
            # A14 — the pending list never shows a finished game, but
            # GET /games/{id} does, with status and result populated.
            game["status"] = "completed" if self._result.outcome == "agreement" else "no_deal"
            game["result"] = self._result.as_dict()
        return game

    def submit(self, player: str, action) -> MoveResult:
        """Apply ``action`` for ``player``; reject anything the server rejects."""
        if player not in (PLAYER_1, PLAYER_2):
            return self._transport("not a player in this game")
        if self.done:
            return self._transport("game is not active")
        if player != self.current_player:
            return self._transport("not your turn")

        if self._phase == "offer":
            parsed, error = self._parse_offer(action)
        else:
            parsed, error = self._parse_decision(action)

        if error is not None:
            return self._reject(player, error)

        if self._phase == "offer":
            return self._apply_offer(player, parsed)
        return self._apply_decision(player, parsed)

    # --- validation ----------------------------------------------------------

    def _parse_offer(self, action):
        if not isinstance(action, dict):
            return None, f"action must be an object, got {type(action).__name__}"
        if "decision" in action and not _has_gains(action):
            return None, "this is the offer phase: submit alice_gain and bob_gain"
        if not _has_gains(action):
            return None, "alice_gain and bob_gain are required"

        gains = {}
        for key in ("alice_gain", "bob_gain"):
            value = action[key]
            if not _is_number(value):
                return None, f"{key} must be a number, got {value!r}"
            gains[key] = value            # as submitted; an int gain stays an int

        for key, value in gains.items():
            # A9 — undocumented, but (1200, -200) sums correctly for a pot of
            # 1000 and cannot be what the server means by a split.
            if value < 0:
                return None, f"{key} must not be negative"
            if value > self.money + SUM_TOLERANCE:
                return None, f"{key} must not exceed {_amount(self.money)}"

        total = gains["alice_gain"] + gains["bob_gain"]
        if abs(total - self.money) > SUM_TOLERANCE:
            return None, f"Gains must sum to {_amount(self.money)}"

        message, error = self._parse_message(action, on_offer=True)
        if error is not None:
            return None, error
        return {"alice_gain": gains["alice_gain"], "bob_gain": gains["bob_gain"],
                "message": message}, None

    def _parse_decision(self, action):
        if not isinstance(action, dict):
            return None, f"action must be an object, got {type(action).__name__}"
        if "decision" not in action:
            if _has_gains(action):
                return None, "this is the decision phase: submit a decision, not an offer"
            return None, "decision is required"

        decision = action["decision"]
        # A21 — bargaining's literals are lowercase where negotiation's are
        # CamelCase. That deliberate difference is strong evidence the server
        # compares exact strings, so case is never repaired here.
        if not isinstance(decision, str) or decision not in _DECISIONS:
            return None, f"decision must be one of {', '.join(_DECISIONS)}, got {decision!r}"

        # A8 — a decision has no documented message field; drop it.
        _, error = self._parse_message(action, on_offer=False)
        if error is not None:
            return None, error
        return {"decision": decision}, None

    def _parse_message(self, action, on_offer):
        """Return (message_or_None, error). Stripping is deliberate — see A8."""
        if "message" not in action or action["message"] is None:
            return None, None
        message = action["message"]
        if not on_offer:
            logger.debug("dropping message on a decision action: %r", message)
            return None, None
        if not self.messages_allowed:
            logger.debug("dropping message: messages_allowed is false: %r", message)
            return None, None
        if not isinstance(message, str):
            logger.debug("dropping non-string message: %r", message)
            return None, None
        if len(message) > MAX_MESSAGE_LEN:
            return None, f"message exceeds {MAX_MESSAGE_LEN} characters"
        return message, None

    # --- transitions ---------------------------------------------------------

    def _apply_offer(self, player, offer) -> MoveResult:
        # The action names gains by IDENTITY (Alice/Bob), the state by seat
        # (player_1/player_2). player_2 proposing still sends alice_gain/bob_gain
        # describing the same split from the same fixed viewpoint.
        self._last_offer = {
            "player_1_gain": offer["alice_gain"],
            "player_2_gain": offer["bob_gain"],
            "message": offer["message"],
            "proposer": player,
            "round": self._round,
        }
        self._phase = "decision"
        return MoveResult(valid=True, game_over=False, result=None)

    def _apply_decision(self, player, parsed) -> MoveResult:
        decision = parsed["decision"]
        offer = self._last_offer
        self._record_round(decision)

        if decision == "accept":
            payoff_1 = offer["player_1_gain"] * self.delta_1 ** (self._round - 1)
            payoff_2 = offer["player_2_gain"] * self.delta_2 ** (self._round - 1)
            return self._finish(player, payoff_1, payoff_2, "agreement", "accept",
                                nominal={"player_1_gain": offer["player_1_gain"],
                                         "player_2_gain": offer["player_2_gain"]})

        if decision == "walkaway":
            return self._finish(player, 0.0, 0.0, "no_deal", "walkaway")

        if self.max_rounds is not None and self._round >= self.max_rounds:
            return self._finish(player, 0.0, 0.0, "no_deal", "max_rounds")
        if self._round >= SAFETY_ROUND_CAP:
            # A20 — never a game rule, only a backstop against an unbounded
            # game between two players who will never concede.
            logger.warning("bargaining game %s hit the local safety cap at round %d",
                           self.game_id, self._round)
            return self._finish(player, 0.0, 0.0, "no_deal", "safety_cap")

        # The rejecter proposes next. Swapping on the round change rather than
        # on the phase change is what stops a player answering its own offer.
        self._round += 1
        self._proposer = player
        self._phase = "offer"
        return MoveResult(valid=True, game_over=False, result=None)

    def _record_round(self, decision) -> None:
        offer = self._last_offer
        self._history.append({
            "round": self._round,
            "proposer": offer["proposer"],
            "offer": {"player_1_gain": offer["player_1_gain"],
                      "player_2_gain": offer["player_2_gain"],
                      "message": offer["message"]},
            "decision": decision,
        })

    def _finish(self, player, payoff_1, payoff_2, outcome, reason, nominal=None) -> MoveResult:
        detail = {
            "reason": reason,
            "ended_by": player,
            "invalid_attempts": dict(self._invalid),
        }
        if nominal is not None:
            detail["nominal"] = nominal
        if reason == "invalid_attempts":
            # Rating-side, outside the engine's remit: the offender's game
            # scores at the 5th percentile and the opponent's game is voided.
            detail["offender"] = player
        self._result = GameResult(payoff_1, payoff_2, outcome,
                                  rounds_played=self._round, detail=detail)
        self._phase = "completed"
        self._ended_by = player
        return MoveResult(valid=True, game_over=True, result=self._result.as_dict())

    def _reject(self, player, error) -> MoveResult:
        """An invalid move: burn an attempt and change nothing else."""
        self._invalid[player] += 1
        attempts_left = MAX_INVALID_ATTEMPTS - self._invalid[player]
        if attempts_left > 0:
            return MoveResult(valid=False, error=error, attempts_left=attempts_left)

        # A24 — the exhausting attempt is still an invalid move, but it also
        # closes the game, so the result travels with it.
        closed = self._finish(player, 0.0, 0.0, "no_deal", "invalid_attempts")
        return MoveResult(valid=False, game_over=True, error=error,
                          attempts_left=0, result=closed.result)

    def _transport(self, error) -> MoveResult:
        # A23 — a 4xx, not an invalid move: no attempt is consumed, which is why
        # attempts_left is None rather than a number.
        return MoveResult(valid=False, error=error, attempts_left=None)

    # --- views ---------------------------------------------------------------

    def _game_state(self, player) -> dict:
        state = {
            "phase": self._phase,
            "current_player": self.current_player,
            "proposer": self._proposer,
            "round": self._round,
            "horizon_known": self.horizon_known,
            "money_to_divide": self.money,
            "last_offer": None if self._last_offer is None else dict(self._last_offer),
            "history": [self._history_entry(entry) for entry in self._history],
            "messages_allowed": self.messages_allowed,
            "complete_information": self.complete_information,
        }
        if self.max_rounds is not None:
            state["max_rounds"] = self.max_rounds

        # The one and only hidden thing in bargaining. Under incomplete
        # information the opponent's key is ABSENT, so state["delta_2"] raises
        # KeyError exactly as it would live — which is the point: a strategy's
        # .get() discipline is actually tested here.
        if self.complete_information or player == PLAYER_1:
            state["delta_1"] = self.delta_1
        if self.complete_information or player == PLAYER_2:
            state["delta_2"] = self.delta_2
        return state

    @staticmethod
    def _history_entry(entry) -> dict:
        out = dict(entry)
        out["offer"] = dict(entry["offer"])
        return out

    def _valid_actions(self) -> dict:
        if self._phase == "offer":
            fields = {
                "alice_gain": "number - Alice's (player_1's) share of the pot",
                "bob_gain": "number - Bob's (player_2's) share; must sum with "
                            "alice_gain to exactly money_to_divide",
            }
            if self.messages_allowed:
                fields["message"] = f"string (optional, max {MAX_MESSAGE_LEN} characters)"
            return {"type": "offer", "fields": fields}
        if self._phase == "decision":
            return {"type": "decision",
                    "fields": {"decision": "'accept', 'reject', or 'walkaway'"}}
        return {"type": None, "fields": {}}            # A14 — nothing to do

    def _prompt(self, player) -> str:
        """Short human-readable situation, in the style of the server's.

        A22: ``glee_agent/llm.py`` feeds this straight into the model, so an
        empty prompt would silently degrade every LLM-mode tuning run without
        raising anything.
        """
        me, them = _name(player), _name(other_player(player))
        my_delta = self.delta_1 if player == PLAYER_1 else self.delta_2
        parts = [f"You are {me}, dividing {_amount(self.money)} with {them}."]

        if self.max_rounds is not None:
            parts.append(f"Round {self._round} of {self.max_rounds}.")
        else:
            parts.append(f"Round {self._round}; there is no round limit.")

        if self._phase == "completed":
            parts.append("The game is over.")
            if self._result is not None:
                parts.append(f"Outcome: {self._result.outcome}; you earned "
                             f"{_amount(self._result.payoff(player))}.")
            return " ".join(parts)

        if self._phase == "offer":
            parts.append(f"It is your turn to propose: name alice_gain and bob_gain, "
                         f"summing to exactly {_amount(self.money)}.")
            if self.messages_allowed:
                parts.append("You may attach a message.")
            if self._last_offer is not None:
                rejected = self._last_offer[f"{player}_gain"]
                parts.append(f"Your opponent's last offer, which was rejected, left you "
                             f"{_amount(rejected)}.")
        else:
            mine = self._last_offer[f"{player}_gain"]
            theirs = self._last_offer[f"{other_player(player)}_gain"]
            parts.append(f"{_name(self._last_offer['proposer'])} offers you "
                         f"{_amount(mine)} and keeps {_amount(theirs)}.")
            if self._last_offer["message"]:
                parts.append(f'They say: "{self._last_offer["message"]}"')
            parts.append("You may accept, reject, or walk away "
                         "(walking away pays both sides $0).")

        multiplier = my_delta ** (self._round - 1)
        parts.append(f"Money you agree on this round is worth {multiplier:.4f} of its "
                     f"face value to you (your inflation multiplier is {my_delta} per round).")
        if not self.complete_information:
            parts.append("You cannot see your opponent's inflation rate.")
        if self.max_rounds is not None and self._round >= self.max_rounds:
            parts.append("This is the final round: without an agreement both sides get $0.")
        return " ".join(parts)

    def _draw_opponents(self) -> dict:
        """A15 — one draw for the whole game, from the injected rng only."""
        disclosed = self._rng.random() < 0.5
        if not disclosed:
            hidden = {"type": "hidden", "name": None}
            return {PLAYER_1: dict(hidden), PLAYER_2: dict(hidden)}
        views = {}
        for seat in (PLAYER_1, PLAYER_2):
            kind = "agent" if self._rng.random() < 0.5 else "human"
            views[seat] = {"type": kind, "name": _choice(self._rng, _OPPONENT_NAMES)}
        return views


# --- helpers -----------------------------------------------------------------


def _has_gains(action) -> bool:
    return "alice_gain" in action and "bob_gain" in action


def _is_number(value) -> bool:
    # bool is a subclass of int, and JSON's true is not a number.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return value == value and value not in (float("inf"), float("-inf"))


def _name(player) -> str:
    return "Alice" if player == PLAYER_1 else "Bob"


def _amount(value) -> str:
    value = float(value)
    return f"${value:,.0f}" if value.is_integer() else f"${value:,.2f}"


def _choice(rng, options):
    return options[rng.randrange(len(options))]
