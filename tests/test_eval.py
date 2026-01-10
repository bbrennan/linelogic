"""
Tests for evaluation metrics.
"""

import pytest

from linelogic.eval.metrics import brier_score, calibration_buckets, clv, log_loss


class TestBrierScore:
    """Test Brier score calculation."""

    def test_brier_score_perfect(self):
        predictions = [1.0, 0.0, 1.0]
        outcomes = [1, 0, 1]
        score = brier_score(predictions, outcomes)
        assert score == pytest.approx(0.0)

    def test_brier_score_typical(self):
        predictions = [0.6, 0.6, 0.4]
        outcomes = [1, 0, 0]
        score = brier_score(predictions, outcomes)
        # (0.6-1)^2 + (0.6-0)^2 + (0.4-0)^2 = 0.16 + 0.36 + 0.16 = 0.68 / 3 = 0.227
        assert score == pytest.approx(0.227, abs=0.001)

    def test_brier_score_edge_cases(self):
        with pytest.raises(ValueError):
            brier_score([0.5], [1, 0])  # Length mismatch

        with pytest.raises(ValueError):
            brier_score([], [])  # Empty lists

        with pytest.raises(ValueError):
            brier_score([1.5], [1])  # Invalid prediction

        with pytest.raises(ValueError):
            brier_score([0.5], [2])  # Invalid outcome


class TestLogLoss:
    """Test log loss calculation."""

    def test_log_loss_typical(self):
        predictions = [0.6, 0.6, 0.4]
        outcomes = [1, 0, 0]
        score = log_loss(predictions, outcomes)
        # Should be higher than Brier score (penalizes confident errors more)
        assert score > 0.5
        assert score < 1.0

    def test_log_loss_edge_cases(self):
        with pytest.raises(ValueError):
            log_loss([0.5], [1, 0])  # Length mismatch

        with pytest.raises(ValueError):
            log_loss([], [])  # Empty lists

        with pytest.raises(ValueError):
            log_loss([0.0], [1])  # Zero probability

        with pytest.raises(ValueError):
            log_loss([1.0], [0])  # One probability


class TestCalibrationBuckets:
    """Test calibration bucketing."""

    def test_calibration_buckets(self):
        predictions = [0.52, 0.53, 0.57, 0.58, 0.62, 0.63, 0.67, 0.68]
        outcomes = [1, 0, 1, 1, 1, 0, 1, 1]

        buckets = calibration_buckets(predictions, outcomes, n_buckets=3)

        # Should have 3 buckets
        assert len(buckets) <= 3

        # Check bucket properties
        for bucket in buckets:
            assert 0 <= bucket.avg_predicted <= 1
            assert 0 <= bucket.empirical_win_rate <= 1
            assert bucket.wins <= bucket.total

    def test_calibration_buckets_empty(self):
        buckets = calibration_buckets([], [], n_buckets=10)
        assert len(buckets) == 0

    def test_calibration_buckets_length_mismatch(self):
        with pytest.raises(ValueError):
            calibration_buckets([0.5], [1, 0], n_buckets=10)


class TestCLV:
    """Test Closing Line Value calculation."""

    def test_clv_beat_close_over(self):
        # Bet Over at +110 (47.6%), closed at -110 (52.4%)
        clv_value = clv(0.476, 0.524, "over")
        assert clv_value == pytest.approx(0.048, abs=0.001)

    def test_clv_beat_close_under(self):
        # Bet Under at -110 (52.4%), closed at +110 (47.6%)
        clv_value = clv(0.524, 0.476, "under")
        assert clv_value == pytest.approx(0.048, abs=0.001)

    def test_clv_no_movement(self):
        clv_value = clv(0.50, 0.50, "over")
        assert clv_value == pytest.approx(0.0)

    def test_clv_lost_close(self):
        # Bet Over at -110 (52.4%), closed at +110 (47.6%) - got worse odds
        clv_value = clv(0.524, 0.476, "over")
        assert clv_value == pytest.approx(-0.048, abs=0.001)

    def test_clv_invalid_side(self):
        with pytest.raises(ValueError):
            clv(0.50, 0.50, "invalid_side")
