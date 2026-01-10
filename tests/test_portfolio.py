"""
Tests for portfolio/bankroll management.
"""

import pytest

from linelogic.portfolio.bankroll import (
    apply_per_bet_cap,
    calculate_stake_with_caps,
    check_correlation_heuristic,
    fractional_kelly,
    kelly_fraction,
)


class TestKellyCriterion:
    """Test Kelly Criterion calculations."""

    def test_kelly_fraction_positive_edge(self):
        # 55% win rate, even odds (2.0 decimal)
        kelly = kelly_fraction(0.55, 2.0)
        assert kelly == pytest.approx(0.1)

    def test_kelly_fraction_large_edge(self):
        # 60% win rate, +150 odds (2.5 decimal)
        kelly = kelly_fraction(0.60, 2.5)
        assert kelly == pytest.approx(0.267, abs=0.001)

    def test_kelly_fraction_no_edge(self):
        # 48% win rate, even odds
        kelly = kelly_fraction(0.48, 2.0)
        assert kelly == 0.0

    def test_kelly_fraction_edge_cases(self):
        # Invalid probabilities
        assert kelly_fraction(0.0, 2.0) == 0.0
        assert kelly_fraction(1.0, 2.0) == 0.0

        # Invalid odds
        assert kelly_fraction(0.55, 1.0) == 0.0
        assert kelly_fraction(0.55, 0.5) == 0.0


class TestFractionalKelly:
    """Test fractional Kelly calculations."""

    def test_fractional_kelly_quarter(self):
        # 55% win rate, even odds, 1/4 Kelly
        frac_kelly = fractional_kelly(0.55, 2.0, fraction=0.25)
        assert frac_kelly == pytest.approx(0.025)

    def test_fractional_kelly_half(self):
        # 60% win rate, +150 odds, 1/2 Kelly
        frac_kelly = fractional_kelly(0.60, 2.5, fraction=0.5)
        assert frac_kelly == pytest.approx(0.133, abs=0.001)

    def test_fractional_kelly_invalid_fraction(self):
        with pytest.raises(ValueError):
            fractional_kelly(0.55, 2.0, fraction=0.0)
        with pytest.raises(ValueError):
            fractional_kelly(0.55, 2.0, fraction=1.5)


class TestExposureCaps:
    """Test exposure cap logic."""

    def test_apply_per_bet_cap(self):
        assert apply_per_bet_cap(0.10, cap=0.05) == 0.05
        assert apply_per_bet_cap(0.03, cap=0.05) == 0.03
        assert apply_per_bet_cap(0.05, cap=0.05) == 0.05


class TestCorrelationHeuristic:
    """Test correlation detection."""

    def test_same_game_correlation(self):
        existing = [{"game_id": "LAL_BOS", "team": "LAL", "player": "LeBron"}]
        new = {"game_id": "LAL_BOS", "team": "BOS", "player": "Tatum"}
        assert check_correlation_heuristic(existing, new) is True

    def test_same_team_correlation(self):
        existing = [{"game_id": "LAL_BOS", "team": "LAL", "player": "LeBron"}]
        new = {"game_id": "LAL_GSW", "team": "LAL", "player": "Davis"}
        assert check_correlation_heuristic(existing, new) is True

    def test_same_player_correlation(self):
        existing = [{"game_id": "LAL_BOS", "team": "LAL", "player": "LeBron"}]
        new = {"game_id": "LAL_GSW", "team": "LAL", "player": "LeBron"}
        assert check_correlation_heuristic(existing, new) is True

    def test_no_correlation(self):
        existing = [{"game_id": "LAL_BOS", "team": "LAL", "player": "LeBron"}]
        new = {"game_id": "GSW_MIA", "team": "GSW", "player": "Curry"}
        assert check_correlation_heuristic(existing, new) is False


class TestStakeCalculation:
    """Test full stake calculation with caps."""

    def test_calculate_stake_with_caps(self):
        result = calculate_stake_with_caps(
            prob_win=0.60,
            odds_decimal=2.5,
            bankroll=10000,
            kelly_fraction_value=0.25,
        )

        assert "full_kelly" in result
        assert "fractional_kelly" in result
        assert "capped_fraction" in result
        assert "stake_dollars" in result
        assert "explanation" in result

        # Full Kelly should be ~26.7%
        assert result["full_kelly"] == pytest.approx(0.267, abs=0.001)

        # Fractional (0.25x) should be ~6.7%
        assert result["fractional_kelly"] == pytest.approx(0.0667, abs=0.001)

        # Capped at 5%
        assert result["capped_fraction"] == 0.05

        # Stake should be $500 (5% of $10,000)
        assert result["stake_dollars"] == 500.0

    def test_calculate_stake_no_cap_needed(self):
        result = calculate_stake_with_caps(
            prob_win=0.52,
            odds_decimal=2.0,
            bankroll=10000,
            kelly_fraction_value=0.25,
        )

        # Full Kelly = 2%, Fractional = 0.5%, under cap
        assert result["capped_fraction"] == result["fractional_kelly"]
        assert result["stake_dollars"] == pytest.approx(50.0, abs=1.0)
