"""Local GLEE simulator — play the three game families offline.

Exists so strategy knobs can be tuned against evidence instead of theory. Every
live game is permanently percentile-scored, so tuning on the real server costs
rating; tuning here costs nothing and has no rate limit.

    from sim import make_engine, sample_config
    engine = make_engine(sample_config("bargaining", rng), rng)
    while not engine.done:
        p = engine.current_player
        engine.submit(p, strategies[p](engine.observation(p)))
    print(engine.result)
"""

from __future__ import annotations

import random

from .types import (
    MAX_INVALID_ATTEMPTS,
    PLAYER_1,
    PLAYER_2,
    Config,
    Engine,
    GameResult,
    MoveResult,
    other_player,
)

__all__ = [
    "MAX_INVALID_ATTEMPTS", "PLAYER_1", "PLAYER_2", "Config", "Engine",
    "GameResult", "MoveResult", "other_player", "make_engine", "sample_config",
]


def make_engine(config: Config, rng: random.Random, game_id: str = "local") -> Engine:
    """Build the engine for a drawn configuration."""
    from .bargaining import BargainingEngine
    from .negotiation import NegotiationEngine
    from .persuasion import PersuasionEngine

    engines = {
        "bargaining": BargainingEngine,
        "negotiation": NegotiationEngine,
        "persuasion": PersuasionEngine,
    }
    try:
        cls = engines[config.game_family]
    except KeyError:
        raise ValueError(f"unknown game family {config.game_family!r}") from None
    return cls(config, rng, game_id)


def sample_config(game_family: str, rng: random.Random) -> Config:
    """Draw one configuration the way the server draws from the GLEE grid."""
    from .grid import sample_config as _sample

    return _sample(game_family, rng)
