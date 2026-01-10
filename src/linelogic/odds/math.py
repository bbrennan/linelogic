"""
Odds mathematics and conversions.

This module provides utilities for:
- Converting between American, Decimal, and Implied Probability odds
- Removing vigorish (vig) to estimate fair odds
- Calculating expected value (EV) and edge
"""


def american_to_implied_prob(american_odds: int) -> float:
    """
    Convert American odds to implied probability.

    Args:
        american_odds: American odds (e.g., +150, -110)

    Returns:
        Implied probability as a decimal (0.0 to 1.0)

    Examples:
        >>> american_to_implied_prob(+150)
        0.4
        >>> american_to_implied_prob(-150)
        0.6
        >>> american_to_implied_prob(+100)
        0.5
    """
    if american_odds > 0:
        return 100 / (american_odds + 100)
    elif american_odds < 0:
        return -american_odds / (-american_odds + 100)
    else:
        return 0.5  # +100 or even odds


def implied_prob_to_american(prob: float) -> int:
    """
    Convert implied probability to American odds.

    Args:
        prob: Implied probability as a decimal (0.0 to 1.0)

    Returns:
        American odds (e.g., +150, -110)

    Examples:
        >>> implied_prob_to_american(0.4)
        150
        >>> implied_prob_to_american(0.6)
        -150
        >>> implied_prob_to_american(0.5)
        100
    """
    if prob <= 0 or prob >= 1:
        raise ValueError(f"Probability must be between 0 and 1, got {prob}")

    if prob == 0.5:
        return 100
    elif prob < 0.5:
        return int(round((100 / prob) - 100))
    else:
        # Negative odds for favorites: more than 50% implied probability
        return int(round(-(100 * prob) / (1 - prob)))


def decimal_to_implied_prob(decimal_odds: float) -> float:
    """
    Convert decimal odds to implied probability.

    Args:
        decimal_odds: Decimal odds (e.g., 2.50, 1.67)

    Returns:
        Implied probability as a decimal (0.0 to 1.0)

    Examples:
        >>> decimal_to_implied_prob(2.50)
        0.4
        >>> decimal_to_implied_prob(1.67)
        0.599
    """
    if decimal_odds <= 1:
        raise ValueError(f"Decimal odds must be > 1, got {decimal_odds}")

    return 1 / decimal_odds


def implied_prob_to_decimal(prob: float) -> float:
    """
    Convert implied probability to decimal odds.

    Args:
        prob: Implied probability as a decimal (0.0 to 1.0)

    Returns:
        Decimal odds (e.g., 2.50, 1.67)

    Examples:
        >>> implied_prob_to_decimal(0.4)
        2.5
        >>> implied_prob_to_decimal(0.6)
        1.667
    """
    if prob <= 0 or prob >= 1:
        raise ValueError(f"Probability must be between 0 and 1, got {prob}")

    return 1 / prob


def american_to_decimal(american_odds: int) -> float:
    """
    Convert American odds to decimal odds.

    Args:
        american_odds: American odds (e.g., +150, -110)

    Returns:
        Decimal odds (e.g., 2.50, 1.91)

    Examples:
        >>> american_to_decimal(+150)
        2.5
        >>> american_to_decimal(-110)
        1.909
    """
    prob = american_to_implied_prob(american_odds)
    return implied_prob_to_decimal(prob)


def decimal_to_american(decimal_odds: float) -> int:
    """
    Convert decimal odds to American odds.

    Args:
        decimal_odds: Decimal odds (e.g., 2.50, 1.91)

    Returns:
        American odds (e.g., +150, -110)

    Examples:
        >>> decimal_to_american(2.5)
        150
        >>> decimal_to_american(1.91)
        -110
    """
    prob = decimal_to_implied_prob(decimal_odds)
    return implied_prob_to_american(prob)


def remove_vig_two_way(prob_a: float, prob_b: float) -> tuple[float, float]:
    """
    Remove vigorish from two-way market using proportional method.

    The proportional method normalizes the implied probabilities so they sum to 1.0.

    Args:
        prob_a: Implied probability of outcome A
        prob_b: Implied probability of outcome B

    Returns:
        Tuple of (fair_prob_a, fair_prob_b) that sum to 1.0

    Examples:
        >>> remove_vig_two_way(0.524, 0.524)  # Both -110
        (0.5, 0.5)
        >>> remove_vig_two_way(0.6, 0.45)
        (0.571, 0.429)

    Note:
        This is the simplest vig removal method. Alternative methods include:
        - Margin proportional to odds (allocate vig inversely to implied prob)
        - Shin method (assumes informed insider trading)
        - Power method (raise each prob to a power, then normalize)

        For M0, we use proportional for simplicity.
    """
    total = prob_a + prob_b
    if total == 0:
        raise ValueError("Sum of probabilities cannot be zero")

    return prob_a / total, prob_b / total


def expected_value(prob_win: float, payout: float, stake: float) -> float:
    """
    Calculate expected value of a bet.

    EV = (prob_win × payout) - (prob_loss × stake)

    Args:
        prob_win: Probability of winning (0.0 to 1.0)
        payout: Amount won if bet wins (not including stake)
        stake: Amount bet

    Returns:
        Expected value (positive = +EV, negative = -EV)

    Examples:
        >>> expected_value(0.55, 110, 100)
        15.5
        >>> expected_value(0.50, 100, 100)
        0.0
        >>> expected_value(0.45, 100, 100)
        -10.0
    """
    prob_loss = 1 - prob_win
    return (prob_win * payout) - (prob_loss * stake)


def edge(prob_model: float, prob_market_fair: float) -> float:
    """
    Calculate edge: difference between model probability and fair market probability.

    Args:
        prob_model: Our model's estimated probability
        prob_market_fair: Market probability after vig removal

    Returns:
        Edge as decimal (e.g., 0.05 = 5% edge)

    Examples:
        >>> edge(0.60, 0.50)
        0.1
        >>> edge(0.52, 0.50)
        0.02
        >>> edge(0.48, 0.50)
        -0.02
    """
    return prob_model - prob_market_fair


def payout_from_american_odds(american_odds: int, stake: float) -> float:
    """
    Calculate payout (profit, not including stake) from American odds.

    Args:
        american_odds: American odds (e.g., +150, -110)
        stake: Amount bet

    Returns:
        Payout if bet wins (profit only, not including original stake)

    Examples:
        >>> payout_from_american_odds(+150, 100)
        150.0
        >>> payout_from_american_odds(-150, 150)
        100.0
        >>> payout_from_american_odds(+100, 100)
        100.0
    """
    if american_odds > 0:
        return stake * (american_odds / 100)
    elif american_odds < 0:
        return stake * (100 / -american_odds)
    else:
        return stake


def break_even_win_rate(american_odds: int) -> float:
    """
    Calculate the break-even win rate for given odds.

    This is the win rate needed to break even (0% ROI).

    Args:
        american_odds: American odds (e.g., +150, -110)

    Returns:
        Break-even win rate as decimal (0.0 to 1.0)

    Examples:
        >>> break_even_win_rate(+150)
        0.4
        >>> break_even_win_rate(-110)
        0.524
        >>> break_even_win_rate(+100)
        0.5
    """
    return american_to_implied_prob(american_odds)
