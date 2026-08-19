"""Runtime configuration, all overridable by environment variable."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ[name])
    except (KeyError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ[name])
    except (KeyError, ValueError):
        return default


@dataclass
class Config:
    # --- platform ---
    api_key: str = ""
    base_url: str | None = None

    # --- run loop ---
    # 60 req/min per agent is the hard server limit. Polling alone at
    # poll_interval=2.0 costs ~30/min, so leave real headroom for moves.
    concurrency: int = 6
    poll_interval: float = 2.0
    max_games: int | None = None
    max_time: float | None = None
    families: tuple[str, ...] = ("bargaining", "negotiation", "persuasion")

    # --- LLM layer ---
    # "off"      : pure heuristics, zero LLM cost, maximum throughput
    # "messages" : heuristics decide the numbers, an LLM writes the free text
    # "full"     : the LLM proposes the whole action, heuristics validate/repair
    llm_mode: str = "messages"
    llm_model: str = "gemini/gemini-2.5-flash"
    llm_timeout: float = 25.0          # well inside the 120s turn clock
    llm_max_calls: int = 0             # 0 = unlimited; a hard stop on spend

    # --- strategy knobs (see strategies/ for how each is used) ---
    # Bargaining: how far to sit between the subgame-perfect share (1.0) and an
    # even split (0.0). Full SPE is optimal against a rational opponent and
    # risks no-deals against an LLM field that anchors on 50/50.
    barg_spe_weight: float = 0.65
    barg_unknown_delta: float = 0.90   # assumed opponent inflation when hidden
    # Undisclosed games still have a round limit; the server just does not state
    # it. A live game with horizon_known=false ran to round 99 and terminated
    # no_deal/round_cap_reached, and across 5,127 live bargaining turns
    # max_rounds is present exactly when horizon_known is true. Modelling the
    # cap as infinite discarded parity, the last word and the endgame rules in
    # the 48% of bargaining games that hide it.
    barg_undisclosed_horizon: int = 99
    # A 99-round cap is not the operative deadline: inflation is. This bounds
    # the concession schedule so the agent cannot stall until the pot is gone.
    barg_uncapped_horizon: int = 30
    # Minimum share the OPPONENT must be left. Distinct from barg_offer_floor,
    # which bounds OUR share: one stops us proposing ourselves nothing, the
    # other stops us demanding past the point the field will accept. Measured
    # cliff is 0.39 (95% set [0.38,0.40], p=5e-6). Default 0.0 = off, so a
    # restart cannot change live behaviour; set per-agent to deploy.
    barg_opponent_floor: float = 0.0
    # Empirical floor on our own share when proposing, as a fraction of the pot.
    # The equilibrium share is 0 whenever the opponent never discounts and holds
    # the last word, which is true and unplayable: the field pays us 39.3% of
    # the pot in those games (n=58) and 52.8% elsewhere (n=155). Measured over
    # 497 live proposals, the field accepts 4-11% of offers leaving it under 40%
    # of the pot and 47-64% of everything from 45% up, so its acceptance curve
    # is flat from an even split onward and conceding past that point buys
    # nothing. 0.0 restores the pre-fix behaviour for an A/B.
    barg_offer_floor: float = 0.50
    # Negotiation: opening anchor as a multiple of your own valuation.
    nego_seller_anchor: float = 2.20
    nego_buyer_anchor: float = 0.45
    nego_assumed_horizon: int = 10     # planning horizon for uncapped games
    # How much of the opening spread to keep rather than concede away. A deal at
    # your own valuation pays zero, so conceding to the floor is worth no more
    # than no deal at all.
    nego_min_margin: float = 0.12
    # Base odds that a negotiation still closes if we reject now. Scales the
    # continuation value; at 0 the agent accepts any profitable offer.
    nego_deal_odds: float = 0.65
    # Fraction of a KNOWN zone of agreement left to the opponent when both
    # valuations are visible. Targeting the ZOPA boundary hands them exactly
    # zero surplus, and the bargaining data says zero-surplus offers get
    # rejected (acceptance collapses below the 0.39-of-pot cliff). No
    # negotiation-specific cliff has been measured yet, so the bargaining
    # number is the prior; only read under GLEE_NEGO_HORIZON_V2.
    nego_zopa_share: float = 0.39
    # Persuasion: shade the optimal lie rate down; LLM buyers punish detected
    # lies harder than a Bayesian would.
    pers_lie_shading: float = 0.80
    pers_honest_rounds: int = 2        # build reputation before any shading

    log_dir: str = "logs"

    @classmethod
    def from_env(cls) -> "Config":
        fams = os.environ.get("GLEE_FAMILIES", "")
        max_games = os.environ.get("GLEE_MAX_GAMES")
        max_time = os.environ.get("GLEE_MAX_TIME")
        return cls(
            api_key=os.environ.get("GLEE_API_KEY", ""),
            base_url=os.environ.get("GLEE_API_URL") or None,
            concurrency=_env_int("GLEE_CONCURRENCY", 6),
            poll_interval=_env_float("GLEE_POLL_INTERVAL", 2.0),
            max_games=int(max_games) if max_games else None,
            max_time=float(max_time) if max_time else None,
            families=tuple(f.strip() for f in fams.split(",") if f.strip())
            or ("bargaining", "negotiation", "persuasion"),
            llm_mode=os.environ.get("GLEE_LLM_MODE", "messages"),
            llm_model=os.environ.get("LLM_MODEL", "gemini/gemini-2.5-flash"),
            llm_timeout=_env_float("GLEE_LLM_TIMEOUT", 25.0),
            llm_max_calls=_env_int("GLEE_LLM_MAX_CALLS", 0),
            barg_spe_weight=_env_float("GLEE_BARG_SPE_WEIGHT", 0.65),
            barg_unknown_delta=_env_float("GLEE_BARG_UNKNOWN_DELTA", 0.90),
            barg_undisclosed_horizon=_env_int("GLEE_BARG_UNDISCLOSED_HORIZON", 99),
            barg_uncapped_horizon=_env_int("GLEE_BARG_UNCAPPED_HORIZON", 30),
            barg_opponent_floor=_env_float("GLEE_BARG_OPPONENT_FLOOR", 0.0),
            barg_offer_floor=_env_float("GLEE_BARG_OFFER_FLOOR", 0.50),
            nego_seller_anchor=_env_float("GLEE_NEGO_SELLER_ANCHOR", 2.20),
            nego_buyer_anchor=_env_float("GLEE_NEGO_BUYER_ANCHOR", 0.45),
            nego_assumed_horizon=_env_int("GLEE_NEGO_HORIZON", 10),
            nego_min_margin=_env_float("GLEE_NEGO_MIN_MARGIN", 0.12),
            nego_deal_odds=_env_float("GLEE_NEGO_DEAL_ODDS", 0.65),
            nego_zopa_share=_env_float("GLEE_NEGO_ZOPA_SHARE", 0.39),
            pers_lie_shading=_env_float("GLEE_PERS_LIE_SHADING", 0.80),
            pers_honest_rounds=_env_int("GLEE_PERS_HONEST_ROUNDS", 2),
            log_dir=os.environ.get("GLEE_LOG_DIR", "logs"),
        )
