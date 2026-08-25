"""Deterministic player-2 commitment policies for disclosed 12-round bargaining.

The component is intentionally narrow and owns an eligible turn end to end.
Player 2 (Bob) proposes on the even rounds of a disclosed 12-round game, so a
patient Bob or a Bob discounting at 0.95 can commit to a terminal floor and
price every earlier decision against that same floor.  Nothing here claims an
outcome or rating guarantee: an opponent can still reject out of spite, walk
away, time out, or simply refuse every offer.

Current live target wires are modal near a 61% Bob share.  The human D=.95
silent ladder below has round-1-equivalent realised shares of
0.57950/0.58302/0.57260/0.57264/0.57353/0.56874 on a $100 pot.  A retrospective
scope diagnostic would reject 315/336 resolved D=.95 agreements; that is not a
causal estimate because those agreements are selected on the old policy having
closed.  All three policies therefore land behind separate default-OFF flags.
"""

from __future__ import annotations

import math

from . import runtime_flags


D095_SILENT_FLAG = "GLEE_BARG_P2_H12_D095_SILENT_V1"
D095_MSG_FLAG = "GLEE_BARG_P2_H12_D095_MSG_COMMIT_V1"
D100_FLAG = "GLEE_BARG_P2_H12_D100_COMMIT_V1"
FLAGS = (D095_SILENT_FLAG, D095_MSG_FLAG, D100_FLAG)

D095_SILENT_GATE = "barg_p2_h12_d095_silent_v1"
D095_MSG_GATE = "barg_p2_h12_d095_msg_commit_v1"
D100_GATE = "barg_p2_h12_d100_commit_v1"
GATE_BY_FLAG = {
    D095_SILENT_FLAG: D095_SILENT_GATE,
    D095_MSG_FLAG: D095_MSG_GATE,
    D100_FLAG: D100_GATE,
}

# The pre-existing bargaining message bank is a per-game randomized experiment.
# A deterministic commitment message must not be overwritten by, or bundled
# with, that arm.  Message-bearing policies fail closed when it is enabled.
LEGACY_MESSAGE_FLAG = "GLEE_BARG_MSG"

DELTA_095 = 0.95
DELTA_100 = 1.0
MAX_ROUNDS = 12
EPS = 0.01

SILENT_SHARES = {
    2: 0.61,
    4: 0.68,
    6: 0.74,
    8: 0.82,
    10: 0.91,
}


def _num(value, default=math.nan) -> float:
    if isinstance(value, bool):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def _round(state: dict) -> int | None:
    raw = _num(state.get("round"))
    if not math.isfinite(raw) or not raw.is_integer():
        return None
    value = int(raw)
    return value if 1 <= value <= MAX_ROUNDS else None


def _enabled_flag() -> str | None:
    """The sole armed component flag, or None on an OFF/conflicting stack."""
    enabled = [flag for flag in FLAGS if runtime_flags.enabled(flag)]
    return enabled[0] if len(enabled) == 1 else None


def _phase_is_real(game: dict, state: dict, round_no: int) -> bool:
    """Validate the actual wire phase and Bob's turn, including provenance."""
    action_type = (game.get("valid_actions") or {}).get("type")
    if action_type not in ("offer", "decision"):
        return False
    if game.get("phase") != action_type or state.get("phase") != action_type:
        return False
    if game.get("your_player") != "player_2" or state.get("current_player") != "player_2":
        return False

    if action_type == "offer":
        return (round_no % 2 == 0
                and state.get("proposer") == "player_2")

    # Bob receives Alice's odd-round offer.  With an even disclosed cap he is
    # the proposer on round 12, never the receiver.  Fail closed on any even
    # decision observation instead of manufacturing endgame behaviour for a
    # state the live transition cannot reach.
    last = state.get("last_offer") or {}
    alice = _num(last.get("player_1_gain"))
    bob = _num(last.get("player_2_gain"))
    money = _num(state.get("money_to_divide"))
    last_round = _num(last.get("round"))
    return (isinstance(last, dict)
            and last.get("proposer") == "player_1"
            and state.get("proposer") == "player_1"
            and round_no % 2 == 1
            and last_round == float(round_no)
            and math.isfinite(alice) and alice >= 0.0
            and math.isfinite(bob) and bob >= 0.0
            and math.isfinite(money)
            and abs(alice + bob - money) <= 1e-6)


def eligible_for_flag(game: dict, flag: str) -> bool:
    """Public structural predicate for later reachability registration.

    This does not require ``flag`` itself to be enabled.  It does include all
    other static scope predicates so a reachability reader measures the exact
    cell that production would own.
    """
    try:
        if flag not in FLAGS or game.get("game_family") != "bargaining":
            return False
        state = game.get("game_state") or {}
        money = _num(state.get("money_to_divide"))
        max_rounds = _num(state.get("max_rounds"))
        round_no = _round(state)
        messages_allowed = state.get("messages_allowed")
        if (not math.isfinite(money) or money <= EPS
                or state.get("horizon_known") is not True
                or max_rounds != float(MAX_ROUNDS)
                or round_no is None
                or messages_allowed not in (True, False)
                or not _phase_is_real(game, state, round_no)):
            return False

        delta = _num(state.get("delta_2"))
        if flag in (D095_SILENT_FLAG, D095_MSG_FLAG) and delta != DELTA_095:
            return False
        if flag == D100_FLAG and delta != DELTA_100:
            return False
        if flag == D095_SILENT_FLAG and messages_allowed is not False:
            return False
        if flag == D095_MSG_FLAG and messages_allowed is not True:
            return False
        return True
    except Exception:
        return False


def active_flag(game: dict) -> str | None:
    """Return the policy that owns this turn, failing closed on conflicts."""
    flag = _enabled_flag()
    if flag is None or not eligible_for_flag(game, flag):
        return None
    state = game.get("game_state") or {}
    message_policy = (flag == D095_MSG_FLAG
                      or (flag == D100_FLAG
                          and state.get("messages_allowed") is True))
    if message_policy and runtime_flags.enabled(LEGACY_MESSAGE_FLAG):
        return None
    return flag


def owns(game: dict) -> bool:
    """Whether one unconflicted deterministic policy owns this exact turn."""
    return active_flag(game) is not None


def _floor(money: float, flag: str) -> float:
    if flag in (D095_SILENT_FLAG, D095_MSG_FLAG):
        return (money - EPS) * DELTA_095 ** (MAX_ROUNDS - 1)
    return money - EPS


def _offer_values(game: dict, flag: str) -> tuple[float, float] | None:
    state = game.get("game_state") or {}
    if (game.get("valid_actions") or {}).get("type") != "offer":
        return None
    round_no = _round(state)
    money = _num(state.get("money_to_divide"))
    if round_no is None or not math.isfinite(money):
        return None

    if round_no == MAX_ROUNDS or flag == D100_FLAG:
        # Spell Alice's crumb literally, then derive Bob's share.  This keeps
        # the intended one cent visible while the two floats sum to an integer
        # pot exactly on the wire.
        alice = EPS
        bob = money - alice
    elif flag == D095_SILENT_FLAG:
        share = SILENT_SHARES.get(round_no)
        if share is None:
            return None
        bob = money * share
        if abs(bob - round(bob)) <= 1e-9 * max(money, 1.0):
            bob = float(round(bob))
        alice = money - bob
    elif flag == D095_MSG_FLAG:
        floor = _floor(money, flag)
        # If Alice rejects, her next-round offer must leave Bob floor/d**r
        # nominal dollars to preserve the same round-1-equivalent floor.  Ask
        # one cent less now, so Alice keeps exactly $0.01 more nominally and
        # receives it one round earlier.  This is a payoff identity, not an
        # assertion that Alice will accept it.
        bob = floor / (DELTA_095 ** round_no) - EPS
        alice = money - bob
    else:
        return None
    if alice < 0.0 or bob < 0.0 or alice + bob != money:
        return None
    return alice, bob


def _fmt(value: float) -> str:
    return f"{value:,.2f}"


def _fmt_approx(value: float) -> str:
    """Expose enough precision for an honest approximate threshold claim."""
    return f"{value:,.6f}".rstrip("0").rstrip(".")


def _message(game: dict, flag: str, alice: float, bob: float) -> str | None:
    state = game.get("game_state") or {}
    if state.get("messages_allowed") is not True:
        return None
    round_no = _round(state)
    money = _num(state.get("money_to_divide"))
    if round_no is None or not math.isfinite(money):
        return None

    if round_no == MAX_ROUNDS:
        return (f"This is the last offer round. Accepting gives you "
                f"${_fmt(alice)} and me ${_fmt(bob)} now; rejecting ends "
                "without an agreement.")

    if flag == D095_MSG_FLAG:
        floor = _floor(money, flag)
        next_bob_required = floor / (DELTA_095 ** round_no)
        next_alice_max = money - next_bob_required
        # Values are derived from the submitted split and the exact threshold
        # used by decisions.  The wire uses binary floats, so display them as
        # approximate values rather than making false cent-rounded at-least or
        # at-most claims.  Avoid stronger claims about rating, acceptance, or
        # turn order: Alice does have an intervening offer if she rejects.
        return (f"Accepting now gives you about ${_fmt_approx(alice)} "
                f"nominally. In your "
                f"next-round offer, meeting my committed discounted floor "
                f"corresponds to about ${_fmt_approx(next_bob_required)} for "
                f"me and about ${_fmt_approx(next_alice_max)} for you. This "
                "offer is about one nominal cent better for you and pays one "
                "round earlier.")

    if flag == D100_FLAG:
        return (f"Accepting now gives you ${_fmt(alice)}. You may counter next "
                f"round, but meeting my unchanged ${_fmt(money - EPS)} floor "
                f"leaves you at most ${_fmt(EPS)}, one round later.")
    return None


def action(game: dict) -> dict | None:
    """Return the complete owned action, or None for the existing strategy."""
    flag = active_flag(game)
    if flag is None:
        return None
    state = game.get("game_state") or {}
    round_no = _round(state)
    money = _num(state.get("money_to_divide"))
    action_type = (game.get("valid_actions") or {}).get("type")
    gate = GATE_BY_FLAG[flag]
    plan = {
        "component": gate,
        "flag": flag,
        "round": round_no,
        "discounted_floor": _floor(money, flag),
    }
    if runtime_flags.enabled("GLEE_TRACE_GATES"):
        plan["gates_fired"] = [gate]

    if action_type == "offer":
        values = _offer_values(game, flag)
        if values is None:
            return None
        alice, bob = values
        out = {"alice_gain": alice, "bob_gain": bob, "_plan": plan}
        message = _message(game, flag, alice, bob)
        if message:
            out["message"] = message[:2000]
        return out

    last = state.get("last_offer") or {}
    bob = _num(last.get("player_2_gain"), 0.0)
    if not math.isfinite(bob):
        bob = 0.0
    delta = _num(state.get("delta_2"))
    discount = delta ** (round_no - 1)
    discounted = bob * discount
    threshold = _floor(money, flag)
    required_nominal = threshold / discount
    plan.update(offered_to_bob=bob, discounted_offer=discounted,
                required_nominal=required_nominal)
    return {
        "decision": "accept" if bob >= required_nominal else "reject",
        "_plan": plan,
    }


def exact_owned_offer(game: dict, candidate: dict) -> tuple[float, float] | None:
    """Prove ``candidate`` is the exact enabled component offer for coercion.

    The generic bargaining coercer rounds every integer pot to whole dollars.
    It may bypass that rule only after this helper proves both that an enabled,
    unconflicted component owns the turn and that both submitted gains exactly
    match the component's independently recomputed offer.
    """
    flag = active_flag(game)
    if flag is None or (game.get("valid_actions") or {}).get("type") != "offer":
        return None
    expected = _offer_values(game, flag)
    if expected is None or not isinstance(candidate, dict):
        return None
    alice = _num(candidate.get("alice_gain"))
    bob = _num(candidate.get("bob_gain"))
    if not math.isfinite(alice) or not math.isfinite(bob):
        return None
    if alice != expected[0] or bob != expected[1]:
        return None
    return expected
