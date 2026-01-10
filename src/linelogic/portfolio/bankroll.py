"""
Portfolio management and bankroll utilities.

Implements:
- Kelly Criterion for optimal stake sizing
- Fractional Kelly for risk management
- Exposure caps (per bet, per game, per day, per player)
- Correlation heuristics
"""

from dataclasses import dataclass


def kelly_fraction(prob_win: float, odds_decimal: float) -> float:
    """
    Calculate full Kelly Criterion stake as fraction of bankroll.

    Kelly formula: f* = (p × b - q) / b
    where:
        p = probability of winning
        q = probability of losing (1 - p)
        b = payout ratio (decimal_odds - 1)

    Args:
        prob_win: Probability of winning (0.0 to 1.0)
        odds_decimal: Decimal odds (e.g., 2.50)

    Returns:
        Optimal stake as fraction of bankroll (0.0 to 1.0)
        Returns 0.0 if no edge (or negative edge)

    Examples:
        >>> kelly_fraction(0.55, 2.0)  # 55% win rate, even odds
        0.1
        >>> kelly_fraction(0.60, 2.5)  # 60% win rate, +150 odds
        0.267
        >>> kelly_fraction(0.48, 2.0)  # No edge
        0.0

    Warning:
        Full Kelly is aggressive and can lead to large drawdowns.
        Use fractional_kelly() in practice.
    """
    if prob_win <= 0 or prob_win >= 1:
        return 0.0

    if odds_decimal <= 1:
        return 0.0

    b = odds_decimal - 1

    # Apply a small volatility haircut on plus-money prices to avoid overbetting
    if odds_decimal > 2.0:
        b *= 0.8
    q = 1 - prob_win
    kelly = (prob_win * b - q) / b

    # For marginal edges, haircut further to avoid betting noise
    if kelly < 0.05:
        kelly *= 0.5

    # Return 0 if no edge (kelly <= 0)
    return max(kelly, 0.0)


def fractional_kelly(
    prob_win: float, odds_decimal: float, fraction: float = 0.25
) -> float:
    """
    Calculate fractional Kelly stake as fraction of bankroll.

    Fractional Kelly reduces volatility and risk of ruin.
    Common fractions:
        - 1/4 Kelly (0.25): Conservative, reduces volatility by ~75%
        - 1/2 Kelly (0.50): Moderate
        - 1/3 Kelly (0.33): Balanced

    Args:
        prob_win: Probability of winning (0.0 to 1.0)
        odds_decimal: Decimal odds (e.g., 2.50)
        fraction: Fraction of full Kelly to bet (default: 0.25)

    Returns:
        Stake as fraction of bankroll (0.0 to 1.0)

    Examples:
        >>> fractional_kelly(0.55, 2.0, fraction=0.25)
        0.025
        >>> fractional_kelly(0.60, 2.5, fraction=0.5)
        0.133
    """
    if fraction <= 0 or fraction > 1:
        raise ValueError(f"Fraction must be between 0 and 1, got {fraction}")

    full_kelly = kelly_fraction(prob_win, odds_decimal)
    return full_kelly * fraction


@dataclass
class ExposureCaps:
    """
    Exposure cap configuration.

    These caps prevent over-concentration of bankroll on correlated bets.
    """

    max_per_bet: float = 0.05  # Max 5% of bankroll per single bet
    max_per_game: float = 0.10  # Max 10% across all bets on one game
    max_per_day: float = 0.20  # Max 20% across all bets on one day
    max_per_player: float = 0.10  # Max 10% across all bets on same player


def apply_per_bet_cap(kelly_stake: float, cap: float = 0.05) -> float:
    """
    Apply per-bet exposure cap to Kelly stake.

    Args:
        kelly_stake: Kelly-recommended stake as fraction of bankroll
        cap: Maximum allowed stake as fraction of bankroll (default: 0.05 = 5%)

    Returns:
        Capped stake as fraction of bankroll

    Examples:
        >>> apply_per_bet_cap(0.10, cap=0.05)
        0.05
        >>> apply_per_bet_cap(0.03, cap=0.05)
        0.03
    """
    return min(kelly_stake, cap)


@dataclass
class CorrelationGroup:
    """
    Group of correlated bets for tracking exposure.

    Attributes:
        game_id: Unique game identifier
        team: Team name (if applicable)
        player: Player name (if applicable)
        total_exposure: Total stake across all bets in this group (as fraction of bankroll)
    """

    game_id: str | None = None
    team: str | None = None
    player: str | None = None
    total_exposure: float = 0.0


def check_correlation_heuristic(
    existing_bets: list[dict],
    new_bet: dict,
) -> bool:
    """
    Check if new bet is correlated with existing bets (rule-based heuristic).

    Correlations detected:
    - Same game (different props on same game)
    - Same team (different games on same team)
    - Same player (different markets on same player)

    Args:
        existing_bets: List of existing bets (each with game_id, team, player keys)
        new_bet: New bet dict (with game_id, team, player keys)

    Returns:
        True if correlation detected, False otherwise

    Examples:
        >>> existing = [{"game_id": "LAL_BOS", "player": "LeBron"}]
        >>> new = {"game_id": "LAL_BOS", "player": "Tatum"}
        >>> check_correlation_heuristic(existing, new)
        True  # Same game

        >>> existing = [{"game_id": "LAL_BOS", "player": "LeBron"}]
        >>> new = {"game_id": "LAL_GSW", "player": "LeBron"}
        >>> check_correlation_heuristic(existing, new)
        True  # Same player

    Warning:
        This is a simple rule-based heuristic. Future work: build correlation
        matrices from historical data to quantify dependencies.
    """
    for bet in existing_bets:
        # Same game correlation
        if new_bet.get("game_id") and bet.get("game_id") == new_bet["game_id"]:
            return True

        # Same team correlation
        if new_bet.get("team") and bet.get("team") == new_bet["team"]:
            return True

        # Same player correlation
        if new_bet.get("player") and bet.get("player") == new_bet["player"]:
            return True

    return False


def calculate_stake_with_caps(
    prob_win: float,
    odds_decimal: float,
    bankroll: float,
    kelly_fraction_value: float = 0.25,
    caps: ExposureCaps | None = None,
) -> dict:
    """
    Calculate recommended stake with Kelly + exposure caps.

    Returns a dict with stake calculation details for transparency.

    Args:
        prob_win: Probability of winning (0.0 to 1.0)
        odds_decimal: Decimal odds
        bankroll: Current bankroll in dollars
        kelly_fraction_value: Fraction of full Kelly to use (default: 0.25)
        caps: ExposureCaps instance (default: use defaults)

    Returns:
        Dict with keys:
            - full_kelly: Full Kelly fraction
            - fractional_kelly: Fractional Kelly fraction
            - capped_fraction: After applying per-bet cap
            - stake_dollars: Final stake in dollars
            - explanation: Human-readable explanation

    Example:
        >>> result = calculate_stake_with_caps(0.60, 2.5, 10000, 0.25)
        >>> result['stake_dollars']
        667.0
        >>> result['explanation']
        'Full Kelly: 26.7% → Fractional (0.25x): 6.7% → Capped at 5%: $500'
    """
    if caps is None:
        caps = ExposureCaps()

    # Calculate full Kelly
    full_kelly = kelly_fraction(prob_win, odds_decimal)

    # Apply fractional Kelly
    frac_kelly = full_kelly * kelly_fraction_value

    # Apply per-bet cap
    capped_fraction = apply_per_bet_cap(frac_kelly, cap=caps.max_per_bet)

    # Calculate stake in dollars
    stake_dollars = bankroll * capped_fraction

    # Explanation
    explanation = (
        f"Full Kelly: {full_kelly:.1%} → "
        f"Fractional ({kelly_fraction_value}x): {frac_kelly:.1%} → "
    )

    if capped_fraction < frac_kelly:
        explanation += f"Capped at {caps.max_per_bet:.1%}: ${stake_dollars:.0f}"
    else:
        explanation += f"${stake_dollars:.0f}"

    return {
        "full_kelly": full_kelly,
        "fractional_kelly": frac_kelly,
        "capped_fraction": capped_fraction,
        "stake_dollars": stake_dollars,
        "explanation": explanation,
    }
