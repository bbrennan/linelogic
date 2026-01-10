"""
Tests for odds math utilities.
"""

import pytest

from linelogic.odds.math import (
    american_to_decimal,
    american_to_implied_prob,
    break_even_win_rate,
    decimal_to_american,
    decimal_to_implied_prob,
    edge,
    expected_value,
    implied_prob_to_american,
    implied_prob_to_decimal,
    payout_from_american_odds,
    remove_vig_two_way,
)


class TestOddsConversions:
    """Test odds format conversions."""

    def test_american_to_implied_prob_positive(self):
        assert american_to_implied_prob(+150) == pytest.approx(0.4)
        assert american_to_implied_prob(+100) == pytest.approx(0.5)
        assert american_to_implied_prob(+200) == pytest.approx(0.333, abs=0.001)

    def test_american_to_implied_prob_negative(self):
        assert american_to_implied_prob(-150) == pytest.approx(0.6)
        assert american_to_implied_prob(-110) == pytest.approx(0.524, abs=0.001)
        assert american_to_implied_prob(-200) == pytest.approx(0.667, abs=0.001)

    def test_implied_prob_to_american(self):
        assert implied_prob_to_american(0.4) == 150
        assert implied_prob_to_american(0.5) == 100
        assert implied_prob_to_american(0.6) == -150

    def test_implied_prob_to_american_edge_cases(self):
        with pytest.raises(ValueError):
            implied_prob_to_american(0.0)
        with pytest.raises(ValueError):
            implied_prob_to_american(1.0)
        with pytest.raises(ValueError):
            implied_prob_to_american(-0.1)

    def test_decimal_to_implied_prob(self):
        assert decimal_to_implied_prob(2.5) == pytest.approx(0.4)
        assert decimal_to_implied_prob(2.0) == pytest.approx(0.5)
        assert decimal_to_implied_prob(1.67) == pytest.approx(0.599, abs=0.001)

    def test_decimal_to_implied_prob_edge_cases(self):
        with pytest.raises(ValueError):
            decimal_to_implied_prob(1.0)
        with pytest.raises(ValueError):
            decimal_to_implied_prob(0.5)

    def test_implied_prob_to_decimal(self):
        assert implied_prob_to_decimal(0.4) == pytest.approx(2.5)
        assert implied_prob_to_decimal(0.5) == pytest.approx(2.0)
        assert implied_prob_to_decimal(0.6) == pytest.approx(1.667, abs=0.001)

    def test_american_to_decimal(self):
        assert american_to_decimal(+150) == pytest.approx(2.5)
        assert american_to_decimal(-110) == pytest.approx(1.909, abs=0.001)
        assert american_to_decimal(+100) == pytest.approx(2.0)

    def test_decimal_to_american(self):
        assert decimal_to_american(2.5) == 150
        assert decimal_to_american(2.0) == 100
        # Note: -110 converts to 1.909, which converts back to -110 (rounding)
        assert decimal_to_american(1.91) in [
            -110,
            -109,
            -111,
        ]  # Allow rounding variation


class TestVigRemoval:
    """Test vig removal."""

    def test_remove_vig_two_way_equal(self):
        # Both sides -110 (52.4% each)
        fair_a, fair_b = remove_vig_two_way(0.524, 0.524)
        assert fair_a == pytest.approx(0.5)
        assert fair_b == pytest.approx(0.5)

    def test_remove_vig_two_way_unequal(self):
        # Favorite -150 (60%), Underdog +130 (43.5%)
        fair_a, fair_b = remove_vig_two_way(0.6, 0.435)
        assert fair_a + fair_b == pytest.approx(1.0)
        assert fair_a == pytest.approx(0.580, abs=0.01)
        assert fair_b == pytest.approx(0.420, abs=0.01)

    def test_remove_vig_two_way_zero_sum(self):
        with pytest.raises(ValueError):
            remove_vig_two_way(0.0, 0.0)


class TestExpectedValue:
    """Test expected value calculations."""

    def test_expected_value_positive(self):
        # 55% win rate, +110 odds
        ev = expected_value(0.55, 110, 100)
        assert ev == pytest.approx(15.5)

    def test_expected_value_zero(self):
        # 50% win rate, even odds
        ev = expected_value(0.50, 100, 100)
        assert ev == pytest.approx(0.0)

    def test_expected_value_negative(self):
        # 45% win rate, even odds
        ev = expected_value(0.45, 100, 100)
        assert ev == pytest.approx(-10.0)


class TestEdge:
    """Test edge calculations."""

    def test_edge_positive(self):
        assert edge(0.60, 0.50) == pytest.approx(0.10)

    def test_edge_zero(self):
        assert edge(0.50, 0.50) == pytest.approx(0.0)

    def test_edge_negative(self):
        assert edge(0.48, 0.50) == pytest.approx(-0.02)


class TestPayoutCalculations:
    """Test payout calculations."""

    def test_payout_from_american_odds_positive(self):
        assert payout_from_american_odds(+150, 100) == 150.0
        assert payout_from_american_odds(+100, 100) == 100.0

    def test_payout_from_american_odds_negative(self):
        assert payout_from_american_odds(-150, 150) == 100.0
        assert payout_from_american_odds(-110, 110) == 100.0

    def test_break_even_win_rate(self):
        assert break_even_win_rate(+150) == pytest.approx(0.4)
        assert break_even_win_rate(-110) == pytest.approx(0.524, abs=0.001)
        assert break_even_win_rate(+100) == pytest.approx(0.5)
