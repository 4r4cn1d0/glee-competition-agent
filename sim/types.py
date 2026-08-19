"""Shared types for the local simulator.

The whole point of this package is that a strategy written for the competition
runs unmodified against it. So an engine emits **exactly** the dict shape that
``GET /api/agent/games/pending`` returns, and accepts exactly the action dicts
that ``POST /api/agent/games/{id}/move`` accepts — including the same filtering
of private information, the same invalid-move accounting, and the same
termination rules.

Anything an engine cannot reproduce faithfully is better left unmodelled than
modelled wrong: a simulator that lies produces tuning that makes the live agent
worse.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

#: Attempts a player gets to submit a legal move before the game is force-closed
#: as a no-deal. Mirrors the server's "5 attempts per move".
MAX_INVALID_ATTEMPTS = 5

PLAYER_1 = "player_1"
PLAYER_2 = "player_2"


def other_player(player: str) -> str:
    return PLAYER_2 if player == PLAYER_1 else PLAYER_1


@dataclass
class MoveResult:
    """What ``submit`` returns — mirrors the REST move response."""

    valid: bool
    game_over: bool = False
    error: str | None = None
    attempts_left: int | None = None
    result: dict | None = None


@dataclass
class GameResult:
    """Final outcome of one game.

    ``outcome`` is one of ``"agreement"``, ``"no_deal"``, or ``"completed"``
    (persuasion, which always runs its full round count).
    """

    player_1_payoff: float
    player_2_payoff: float
    outcome: str
    rounds_played: int = 0
    detail: dict = field(default_factory=dict)

    def payoff(self, player: str) -> float:
        return self.player_1_payoff if player == PLAYER_1 else self.player_2_payoff

    def as_dict(self) -> dict:
        return {"player_1_payoff": self.player_1_payoff,
                "player_2_payoff": self.player_2_payoff,
                "outcome": self.outcome}


class Engine(Protocol):
    """One game in progress.

    Drive it with::

        while not engine.done:
            player = engine.current_player
            action = strategy(engine.observation(player))
            engine.submit(player, action)
        result = engine.result
    """

    game_family: str

    @property
    def done(self) -> bool: ...

    @property
    def current_player(self) -> str:
        """The player whose move is awaited. Undefined once ``done``."""

    @property
    def result(self) -> GameResult | None: ...

    def observation(self, player: str) -> dict:
        """The game dict as the API would send it to ``player``.

        Must carry: ``game_id``, ``game_family``, ``your_player``, ``phase``,
        ``opponent``, ``game_state``, ``valid_actions`` (with a ``fields`` dict),
        and ``prompt``. ``game_state`` must be filtered to that player's view —
        an opponent's private valuation or a hidden quality is *absent*, not
        None, exactly as the server omits it.
        """

    def submit(self, player: str, action: dict) -> MoveResult:
        """Apply ``action``. Illegal actions must be rejected, not repaired:
        the simulator's job is to catch what the live server would reject.
        """


@dataclass
class Config:
    """One drawn game configuration.

    ``params`` holds the family-specific settings; ``key`` identifies the
    configuration for percentile scoring, which compares payoffs only against
    other payoffs earned on the *same* configuration in the *same* role.
    """

    game_family: str
    params: dict[str, Any]

    @property
    def key(self) -> str:
        parts = [f"{k}={self.params[k]!r}" for k in sorted(self.params)]
        return f"{self.game_family}|" + "|".join(parts)
