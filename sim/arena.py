"""Match runner and percentile scoring for the local simulator.

Two jobs. ``play``/``run_matches`` drive engines to completion the way the SDK
run loop drives live games; ``percentile_scores`` turns the resulting payoffs
into the number the competition actually optimises.

That second job is the reason this module exists. The competition does not
score win/loss: a payoff is converted to a percentile against every payoff
earned on the SAME configuration in the SAME role, and the percentile maps to
``game_rating = 2000 + 8000 * (percentile - 0.5)``. Tuning a knob on mean payoff
or on win rate optimises the wrong thing — a config where every seat earns
$900 and one where every seat earns $90 contribute equally to rating, and being
$1 ahead of the field is worth as much as being $500 ahead. So the local loop
scores the same way the server does.

What is deliberately NOT modelled, because it needs the live field and faking it
would produce confidently wrong tuning:

- the opponent-strength adjustment (an hourly-fitted model predicts the field's
  percentile on this configuration against an opponent of that rating, and you
  are scored against that prediction),
- the rating update itself (``delta_R = eta * (game_rating - R)``, eta decaying
  with games played, clamped to [100, 5000]),
- the displayed/ranked shrinkage toward 1000 by ``g / (g + 30)``.

So ``mean_game_rating`` here is a *relative* yardstick for comparing strategies
against each other on one shared pool of records. It is not a prediction of the
rating a strategy would hold on the leaderboard, and its absolute value is only
as meaningful as the pool it was computed against.

ASSUMPTIONS (the docs do not pin these down; revisit if the platform clarifies):

1. Percentile convention is the midrank / mid-distribution one:
   ``(below + 0.5 * equal) / n``, counting the record's own payoff in the
   group. It is the standard sample percentile, handles ties symmetrically, and
   is the only convention under which a balanced field averages exactly 2000 —
   which the docs assert ("average game = 2000"). ``rank / n`` and
   ``rank / (n + 1)`` both fail that.
2. Live groups are seeded with the GLEE research dataset and joined by every
   competition game ever played on that configuration; a local group holds only
   the games in the pool handed to ``percentile_scores``. Percentiles are
   therefore relative to the local field, and a two-strategy pool gives every
   record a percentile of 0.25 or 0.75. Compare strategies, never absolutes.
3. A strategy that RAISES is charged an invalid attempt. Live, the SDK logs the
   traceback and submits nothing, so the game stalls until the 120-second turn
   timeout closes it as a no-deal; the SDK re-calls the strategy on each poll
   until then. There is no wall clock here, so attempts are the local proxy:
   both routes end in the same no-deal, and both give a flaky strategy several
   chances first.
4. Abandonment (attempts exhausted) is scored at the documented 5th percentile
   rather than by ranking its $0 payoff, the opponent's game in that pair is
   voided, and an abandonment with no valid move ever made is dropped. Those
   three rules are documented; what is not is whether an abandoned game's payoff
   still joins the field's ranking pool. It does not here — a crash-produced $0
   is not evidence about the configuration.
5. Payoffs are compared for ties with exact equality. Any tolerance would be
   arbitrary, and equal payoffs on the same configuration (two $0 no-deals, two
   50/50 splits) are exactly equal in practice.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .types import (
    MAX_INVALID_ATTEMPTS,
    PLAYER_1,
    PLAYER_2,
    Config,
    GameResult,
    MoveResult,
    other_player,
)

__all__ = [
    "MatchRecord", "play", "run_matches", "percentile_scores", "game_rating",
    "MAX_TURNS_PER_GAME", "ABANDONMENT_PERCENTILE",
]

#: Backstop only, not a game rule: a buggy engine or a pair of strategies that
#: never agree in an unbounded-horizon game would otherwise spin forever.
MAX_TURNS_PER_GAME = 5000

#: "Abandoning a game (turn timeout or five invalid moves) scores it at the 5th
#: percentile -- the bottom of the scale."
ABANDONMENT_PERCENTILE = 0.05

#: Submitted on the strategy's behalf when it produced no usable action. No
#: phase of any family accepts it, so the engine's own validator rejects it and
#: burns an attempt exactly as the server would.
_NO_ACTION = {"_arena_no_action": True}


@dataclass
class MatchRecord:
    """One game seen from one seat — the unit percentile scoring ranks.

    ``role`` is the seat this record's player held (``player_1``/``player_2``),
    and it is part of the grouping key: seller and buyer payoffs on the same
    configuration are not comparable quantities.
    """

    config: Config
    game_family: str
    role: str
    payoff: float
    opponent_payoff: float
    outcome: str
    rounds_played: int
    opponent_name: str
    name: str = "strategy"
    game_id: str = ""
    moves_made: int = 0
    invalid_actions: int = 0
    abandoned: bool = False
    opponent_abandoned: bool = False

    @property
    def group(self) -> tuple:
        return (self.config.key, self.role)


def game_rating(percentile: float) -> float:
    """The documented percentile -> game rating map. An average game is 2000."""
    return 2000.0 + 8000.0 * (percentile - 0.5)


def play(config, strategy_1, strategy_2, rng, game_id="local") -> GameResult:
    """Drive one engine to completion and return its result.

    ``strategy_1``/``strategy_2`` are the live-competition callables: they take
    the ``pending`` game dict and return an action dict. Nothing either of them
    does may end the run — a strategy that raises, returns garbage, or returns a
    move the engine rejects burns attempts and, once they are gone, force-closes
    the game as a no-deal, which is what the server does to it.

    Arena bookkeeping (per-player valid moves, invalid attempts, who abandoned)
    is attached under ``result.detail["arena"]`` so ``run_matches`` can apply
    the abandonment scoring rules without re-deriving them.
    """
    from . import make_engine

    engine = make_engine(config, rng, game_id)
    strategies = {PLAYER_1: strategy_1, PLAYER_2: strategy_2}
    invalid = {PLAYER_1: 0, PLAYER_2: 0}   # cumulative, reported
    streak = {PLAYER_1: 0, PLAYER_2: 0}    # consecutive, the local backstop
    moves = {PLAYER_1: 0, PLAYER_2: 0}
    errors = []
    abandoned_by = None
    forced = None
    turns = 0

    while not engine.done:
        if turns >= MAX_TURNS_PER_GAME:
            forced = "turn_cap"
            break
        turns += 1

        player = engine.current_player
        # An engine that cannot describe its own state is a simulator bug, and
        # swallowing it here would silently poison the scores. Let it raise.
        observation = engine.observation(player)

        action, failure = _ask(strategies[player], observation)
        if failure is not None:
            errors.append(f"{player}: {failure}")

        move = _submit(engine, player, action)
        if move.valid:
            moves[player] += 1
            streak[player] = 0
            continue

        invalid[player] += 1
        streak[player] += 1
        if move.error:
            errors.append(f"{player}: rejected: {move.error}")
        exhausted = (streak[player] >= MAX_INVALID_ATTEMPTS
                     or move.attempts_left == 0
                     or engine.done)
        if exhausted:
            abandoned_by = player
            forced = forced or "attempts"
            break

    result = engine.result if engine.done else None
    if result is None:
        # Either we broke out of the loop, or the engine claims to be done
        # without producing a result. Both are a no-deal: nobody was paid.
        forced = forced or "no_result"
        result = GameResult(0.0, 0.0, "no_deal", rounds_played=_rounds(engine))

    result.detail = dict(result.detail or {})
    result.detail["arena"] = {
        "moves": dict(moves),
        "invalid": dict(invalid),
        "abandoned_by": abandoned_by,
        "forced": forced,
        "turns": turns,
        "errors": errors,
    }
    return result


def run_matches(game_family, strategy, opponent, n, seed, swap_roles=True,
                name=None, opponent_name=None) -> list:
    """Play ``n`` freshly drawn configurations and return ``strategy``'s records.

    With ``swap_roles`` every drawn configuration is played twice, once from
    each seat, because payoffs are role-asymmetric: a seller's $40 margin and a
    buyer's $40 surplus on the same trade are different numbers drawn from
    different distributions, and averaging across seats hides which half of the
    strategy is weak. Both plays of a pair share one engine seed (common random
    numbers), so a persuasion quality sequence or any other engine draw is
    identical in both — the seats differ only by who sat where.

    ``seed`` drives the configuration draw, so two runs with the same
    ``game_family``, ``n`` and ``seed`` see exactly the same configurations.
    That is what makes the records poolable: to compare strategies, run each
    against the same opponent on the same seed and hand the concatenated lists
    to ``percentile_scores``. A pool from one run alone has one payoff per
    (configuration, role) group and scores nothing.
    """
    from . import sample_config

    rng = random.Random(seed)
    my_name = name or _callable_name(strategy)
    their_name = opponent_name or _callable_name(opponent)
    seats = (PLAYER_1, PLAYER_2) if swap_roles else (PLAYER_1,)

    records = []
    for index in range(n):
        config = sample_config(game_family, rng)
        game_seed = rng.randrange(1 << 62)
        for seat in seats:
            gid = f"{game_family}-{index:04d}-{seat}"
            if seat == PLAYER_1:
                first, second = strategy, opponent
            else:
                first, second = opponent, strategy
            result = play(config, first, second, random.Random(game_seed), gid)
            records.append(_record(config, result, seat, my_name, their_name, gid))
    return records


def percentile_scores(records, min_group=2) -> dict:
    """Score a pool of records the way the competition scores games.

    Each payoff is ranked against every payoff in the pool earned on the same
    ``config.key`` in the same role, converted to a percentile, and mapped
    through ``game_rating = 2000 + 8000 * (percentile - 0.5)``. The headline
    number is ``mean_game_rating``; ``by_name`` breaks it down per strategy,
    which is the comparison a tuning run is actually making.

    Groups with fewer than ``min_group`` rankable payoffs are reported under
    ``unscored`` rather than given a percentile: one payoff ranked against
    itself is 0.5 by construction, i.e. exactly 2000, and averaging that in
    would drag every comparison toward the middle while looking like data.

    This deliberately omits the opponent-strength adjustment and the hourly
    fitted model the live scorer applies before the percentile-to-rating map,
    and it omits the rating update and the ``g / (g + 30)`` display shrinkage.
    Those need the live field; see the module docstring.
    """
    records = list(records)
    scored, unscored, voided, dropped = [], [], [], []

    # Abandonment is scored by rule, not by rank, so those records are also
    # kept out of the pool their group ranks against.
    rankable = []
    for record in records:
        if record.abandoned and record.moves_made <= 0:
            # "if you never made a single move, the game is dropped"
            dropped.append(_entry(record, None, "never_moved"))
        elif record.abandoned:
            scored.append(_entry(record, ABANDONMENT_PERCENTILE, "abandoned"))
        elif record.opponent_abandoned:
            # "Your opponent's game is voided (neither helps nor hurts)."
            voided.append(_entry(record, None, "opponent_abandoned"))
        else:
            rankable.append(record)

    groups = {}
    for record in rankable:
        groups.setdefault(record.group, []).append(record)

    group_info = {}
    for key, members in sorted(groups.items()):
        payoffs = [m.payoff for m in members]
        big_enough = len(members) >= min_group
        group_info[_group_name(key)] = {
            "config_key": key[0],
            "role": key[1],
            "size": len(members),
            "scored": big_enough,
        }
        for member in members:
            if not big_enough:
                unscored.append(_entry(member, None, "group_too_small"))
                continue
            # O(n^2) and deliberately so: groups are tiny and the midrank is
            # easier to check by eye written this way than via a sort.
            below = sum(1 for value in payoffs if value < member.payoff)
            equal = sum(1 for value in payoffs if value == member.payoff)
            scored.append(_entry(member, (below + 0.5 * equal) / len(payoffs), "ranked"))

    summary = {
        "mean_game_rating": _mean([e["game_rating"] for e in scored]),
        "mean_percentile": _mean([e["percentile"] for e in scored]),
        "n_records": len(records),
        "n_scored": len(scored),
        "n_unscored": len(unscored),
        "n_voided": len(voided),
        "n_dropped": len(dropped),
        "n_groups": len(group_info),
        "n_groups_scored": sum(1 for g in group_info.values() if g["scored"]),
        "min_group": min_group,
        "scored": scored,
        "unscored": unscored,
        "voided": voided,
        "dropped": dropped,
        "groups": group_info,
    }
    for label, getter in (("by_name", "name"),
                          ("by_family", "game_family"),
                          ("by_role", "role")):
        summary[label] = _breakdown(scored, unscored, getter)
    return summary


# --- internals ---------------------------------------------------------------


def _ask(strategy, observation):
    """Call a strategy, converting any misbehaviour into an unusable action."""
    try:
        action = strategy(observation)
    except Exception as exc:
        return dict(_NO_ACTION), f"strategy raised {type(exc).__name__}: {exc}"
    if not isinstance(action, dict):
        return dict(_NO_ACTION), f"strategy returned {type(action).__name__}, not a dict"
    return action, None


def _submit(engine, player, action) -> MoveResult:
    """Hand an action to the engine, treating a raise as a rejection.

    A conforming engine reports an illegal action as ``valid=False``. But the
    action came from a strategy and may be arbitrary garbage, so an engine that
    raises on it must not take the whole tournament down with it; the failure is
    recorded in the result detail instead.
    """
    try:
        move = engine.submit(player, action)
    except Exception as exc:
        return MoveResult(valid=False, error=f"engine raised {type(exc).__name__}: {exc}")
    if move is None:
        return MoveResult(valid=False, error="engine returned no MoveResult")
    return move


def _rounds(engine) -> int:
    try:
        return int(engine.observation(PLAYER_1)["game_state"].get("round", 0))
    except Exception:
        return 0


def _callable_name(fn) -> str:
    return getattr(fn, "__name__", None) or type(fn).__name__


def _record(config, result, seat, name, opponent_name, game_id) -> MatchRecord:
    info = (result.detail or {}).get("arena", {})
    foe = other_player(seat)
    return MatchRecord(
        config=config,
        game_family=config.game_family,
        role=seat,
        payoff=result.payoff(seat),
        opponent_payoff=result.payoff(foe),
        outcome=result.outcome,
        rounds_played=result.rounds_played,
        opponent_name=opponent_name,
        name=name,
        game_id=game_id,
        moves_made=info.get("moves", {}).get(seat, 0),
        invalid_actions=info.get("invalid", {}).get(seat, 0),
        abandoned=info.get("abandoned_by") == seat,
        opponent_abandoned=info.get("abandoned_by") == foe,
    )


def _entry(record, percentile, status) -> dict:
    return {
        "name": record.name,
        "game_id": record.game_id,
        "game_family": record.game_family,
        "role": record.role,
        "config_key": record.config.key,
        "group": _group_name(record.group),
        "payoff": record.payoff,
        "opponent_payoff": record.opponent_payoff,
        "outcome": record.outcome,
        "status": status,
        "percentile": percentile,
        "game_rating": None if percentile is None else game_rating(percentile),
    }


def _group_name(key) -> str:
    return f"{key[0]}#role={key[1]}"


def _mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def _breakdown(scored, unscored, key) -> dict:
    out = {}
    for entry in scored:
        bucket = out.setdefault(entry[key], {"ratings": [], "percentiles": [], "unscored": 0})
        bucket["ratings"].append(entry["game_rating"])
        bucket["percentiles"].append(entry["percentile"])
    for entry in unscored:
        bucket = out.setdefault(entry[key], {"ratings": [], "percentiles": [], "unscored": 0})
        bucket["unscored"] += 1
    return {
        name: {
            "n_scored": len(bucket["ratings"]),
            "n_unscored": bucket["unscored"],
            "mean_game_rating": _mean(bucket["ratings"]),
            "mean_percentile": _mean(bucket["percentiles"]),
        }
        for name, bucket in sorted(out.items())
    }
