"""Pure executable reference for selected policy and mathematical rules.

This module is deliberately nonoperational. It has no network, environment,
logging, or mutable runtime interface. It specifies only the disclosed excerpts
needed by the synthetic tests and mathematical checks.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from math import ceil, isclose, log


PRICE_TICK = 0.01
PLAYER2_SHARES = (0.61, 0.68, 0.74, 0.82, 0.91)
VALUE_SUPPORT = (0.8, 1.0, 1.2, 1.5)


def empirical_midrank(reference: Iterable[float], payoff: float, atol: float = 1e-9) -> float:
    """Return the tolerance-aware empirical midrank used by local diagnostics."""

    values = tuple(float(value) for value in reference)
    if not values:
        raise ValueError("reference must be nonempty")
    below = sum(value < payoff and not isclose(value, payoff, abs_tol=atol) for value in values)
    equal = sum(isclose(value, payoff, abs_tol=atol) for value in values)
    return (below + 0.5 * equal) / len(values)


def game_rating(adjusted_percentile: float) -> float:
    """Map an adjusted percentile to the completed-game rating target."""

    if not 0.0 <= adjusted_percentile <= 1.0:
        raise ValueError("adjusted_percentile must lie in [0, 1]")
    return 2000.0 + 8000.0 * (adjusted_percentile - 0.5)


def raw_rating_update(
    current: float,
    adjusted_percentile: float,
    eta: float = 0.002,
    lower: float = 100.0,
    upper: float = 5000.0,
) -> float:
    """Apply the normal completed-game update and rating clamp."""

    target = game_rating(adjusted_percentile)
    updated = current + eta * (target - current)
    return min(upper, max(lower, updated))


def displayed_rating(raw_rating: float, games: int) -> float:
    """Apply the public finite-game display shrinkage."""

    if games < 0:
        raise ValueError("games must be nonnegative")
    return 1000.0 + games / (games + 30.0) * (raw_rating - 1000.0)


def final_block_weight(games: int, eta: float = 0.002) -> float:
    """Return total geometric weight placed on a final block of games."""

    if games < 0:
        raise ValueError("games must be nonnegative")
    return 1.0 - (1.0 - eta) ** games


def effective_bargaining_clock(own_discount: float, cap: int = 60) -> int:
    """Return the inflation-aware concession clock for a hidden horizon."""

    if not 0.0 < own_discount <= 1.0:
        raise ValueError("own_discount must lie in (0, 1]")
    if cap < 4:
        raise ValueError("cap must be at least four")
    if own_discount >= 1.0:
        return cap
    rounds = ceil(log(0.05) / log(own_discount))
    return int(max(4, min(rounds, cap)))


def terminal_proposal_rank(
    acceptance_probability: float,
    accepted_payoff: float,
    reference: Iterable[float],
) -> float:
    """Expected raw rank of an accepted payoff versus rejection payoff zero."""

    if not 0.0 <= acceptance_probability <= 1.0:
        raise ValueError("acceptance_probability must lie in [0, 1]")
    zero_rank = empirical_midrank(reference, 0.0)
    accepted_rank = empirical_midrank(reference, accepted_payoff)
    return zero_rank + acceptance_probability * (accepted_rank - zero_rank)


def finite_proposer_share(delta_self: float, delta_other: float, opportunities: int) -> float:
    """Finite alternating-offer proposer share under the stated benchmark."""

    if opportunities < 1:
        raise ValueError("opportunities must be positive")
    if not 0.0 <= delta_self <= 1.0 or not 0.0 <= delta_other <= 1.0:
        raise ValueError("discounts must lie in [0, 1]")
    if opportunities == 1:
        return 1.0
    return 1.0 - delta_other * finite_proposer_share(
        delta_other, delta_self, opportunities - 1
    )


def stationary_proposer_share(delta_self: float, delta_other: float) -> float:
    """Stationary Rubinstein benchmark when the denominator is nonzero."""

    denominator = 1.0 - delta_self * delta_other
    if denominator <= 0.0:
        raise ValueError("stationary share is not selected at this boundary")
    return (1.0 - delta_other) / denominator


def player2_offer_payoff(proposal_number: int, pot: float = 1.0, tick: float = PRICE_TICK) -> float:
    """Return player 2's payoff in its fixed six-step disclosed-horizon ladder."""

    if proposal_number < 1:
        raise ValueError("proposal_number must be positive")
    if pot <= tick:
        raise ValueError("pot must exceed tick")
    if proposal_number <= len(PLAYER2_SHARES):
        return pot * PLAYER2_SHARES[proposal_number - 1]
    return pot - tick


def player2_accepts(
    own_payoff: float,
    round_number: int,
    pot: float = 1.0,
    discount: float = 0.95,
    tick: float = PRICE_TICK,
) -> bool:
    """Apply the disclosed odd-round discounted terminal floor."""

    if round_number < 1 or round_number > 11 or round_number % 2 == 0:
        raise ValueError("reference floor is defined for odd decision rounds 1 through 11")
    present = own_payoff * discount ** (round_number - 1)
    terminal = (pot - tick) * discount**11
    return present >= terminal


def strict_trade_interval(seller_value: float, buyer_value: float) -> tuple[float, float] | None:
    """Return the open strict-gains interval, if it exists."""

    if buyer_value <= seller_value:
        return None
    return seller_value, buyer_value


def one_round_seller_ask(
    seller_value: float,
    buyer_value: float | None = None,
    scale: float = 1.0,
    tick: float = PRICE_TICK,
) -> float:
    """Return the disclosed one-round complete or hidden seller ask."""

    if buyer_value is not None:
        return buyer_value - tick
    normalized = seller_value / scale
    hidden_table = {
        0.8: 1.2 * scale - tick,
        1.0: 1.2 * scale - tick,
        1.2: 1.5 * scale - tick,
        1.5: 2.0 * scale,
    }
    for support_value, ask in hidden_table.items():
        if isclose(normalized, support_value, abs_tol=1e-9):
            return ask
    raise ValueError("seller_value is outside the disclosed hidden support")


def hidden_terminal_buyer_bid(
    own_value: float,
    seller_asks: Sequence[float],
    seller_support: Sequence[float] = VALUE_SUPPORT,
    tick: float = PRICE_TICK,
) -> float | None:
    """Apply the conditional offer-derived upper-bound rule."""

    retained = [ask for ask in seller_asks if ask < own_value]
    if not retained:
        return None
    upper_bound = min(retained)
    candidates = [value for value in seller_support if value < own_value and value <= upper_bound]
    if not candidates:
        return None
    return max(candidates) + tick


def persuasion_commitment_threshold(
    prior_high: float,
    high_value: float,
    low_value: float,
    price: float,
) -> float:
    """Return the one-shot low-quality recommendation threshold, clipped to one."""

    if not 0.0 < prior_high < 1.0:
        raise ValueError("prior_high must lie strictly between zero and one")
    if not high_value > price > low_value:
        raise ValueError("values must satisfy high_value > price > low_value")
    threshold = prior_high * (high_value - price) / (
        (1.0 - prior_high) * (price - low_value)
    )
    return min(1.0, max(0.0, threshold))


def buyer_break_even_probability(high_value: float, low_value: float, price: float) -> float:
    """Return the posterior high-quality probability needed to break even."""

    if high_value <= low_value:
        raise ValueError("high_value must exceed low_value")
    return (price - low_value) / (high_value - low_value)


def persuasion_seller_recommendation(
    quality: str,
    price: float,
    prior_expected_value: float | None,
    historical_buy_rate: float | None,
    buyer_value_known: bool,
) -> str:
    """Return the disclosed seller yes/no rule."""

    if quality not in {"high", "low"}:
        raise ValueError("quality must be high or low")
    if quality == "high":
        return "yes"
    if buyer_value_known:
        if prior_expected_value is None:
            raise ValueError("known-value rule requires prior_expected_value")
        return "yes" if prior_expected_value >= price else "no"
    return "yes" if historical_buy_rate is None or historical_buy_rate >= 0.5 else "no"


def persuasion_buyer_action(
    posterior_high: float,
    high_value: float,
    low_value: float,
    price: float,
    explicit_decline: bool = False,
) -> str:
    """Apply the monetary gate followed by the directional decline veto."""

    expected_value = posterior_high * high_value + (1.0 - posterior_high) * low_value
    action = "buy" if expected_value >= price else "pass"
    if explicit_decline and action == "buy":
        action = "pass"
    return action


def select_owner(state: Mapping[str, object]) -> str:
    """Return a public alias for the highest eligible disclosed owner."""

    family = state.get("family")
    role = state.get("role")
    horizon = state.get("horizon")
    information = state.get("information")
    messages = bool(state.get("messages"))
    terminal = bool(state.get("terminal"))

    if family == "bargaining":
        if (
            role == "player_2"
            and horizon == 12
            and isclose(float(state.get("own_discount", -1.0)), 0.95)
            and not messages
        ):
            return "player2_fixed_disclosed_12"
        return "generic_bargaining_reference"

    if family == "negotiation":
        if role == "seller" and horizon == 1:
            return "one_round_seller"
        if role == "buyer" and horizon == 10 and information == "complete":
            return "complete_disclosed_10_buyer"
        if role == "buyer" and horizon == 10 and information == "hidden" and terminal:
            return "hidden_disclosed_10_terminal_bound"
        return "buyer_fallback_reference" if role == "buyer" else "seller_fallback_reference"

    if family == "persuasion":
        return "seller_value_or_history_rule" if role == "seller" else "buyer_pipeline"

    raise ValueError("unsupported family")
