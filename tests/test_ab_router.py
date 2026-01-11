"""Tests for A/B testing router."""

import json
import tempfile
from pathlib import Path

import pytest

from linelogic.inference import ABTestRouter


class TestABTestRouter:
    """Test suite for ABTestRouter class."""

    def test_init_valid_percentage(self):
        """Router accepts valid staging percentages."""
        router = ABTestRouter(staging_percentage=10.0)
        assert router.staging_percentage == 10.0

    def test_init_invalid_percentage(self):
        """Router rejects invalid staging percentages."""
        with pytest.raises(ValueError, match="staging_percentage must be 0-100"):
            ABTestRouter(staging_percentage=150.0)

    def test_route_consistent_hashing(self):
        """Same user_id always routes to same stage."""
        router = ABTestRouter(staging_percentage=50.0)
        user_id = "game_123_home"

        # Call route() multiple times - should return same stage
        stages = [router.route(user_id) for _ in range(10)]
        assert len(set(stages)) == 1, "Same user_id must always get same stage"

    def test_route_percentage_distribution(self):
        """Routing respects staging percentage (approximately)."""
        router = ABTestRouter(staging_percentage=20.0)

        # Route 1000 unique users
        stages = [router.route(f"user_{i}") for i in range(1000)]
        staging_count = sum(1 for s in stages if s == "staging")

        # Should be ~20% staging (allow 5% tolerance)
        assert (
            150 <= staging_count <= 250
        ), f"Expected ~200 staging, got {staging_count}"

    def test_log_outcome_creates_file(self):
        """Logging outcome creates JSONL file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            router = ABTestRouter(staging_percentage=10.0, log_dir=tmpdir)
            router.log_outcome(user_id="game_1", prediction=0.65, actual=True)

            # Check log file exists
            log_files = list(Path(tmpdir).glob("outcomes_*.jsonl"))
            assert len(log_files) == 1, "Should create one log file"

            # Check content
            with open(log_files[0]) as f:
                line = f.readline()
                data = json.loads(line)
                assert data["user_id"] == "game_1"
                assert data["prediction"] == 0.65
                assert data["actual"] is True

    def test_get_metrics_empty(self):
        """Metrics return None for empty logs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            router = ABTestRouter(staging_percentage=10.0, log_dir=tmpdir)
            metrics = router.get_metrics()

            assert metrics["staging"]["count"] == 0
            assert metrics["staging"]["log_loss"] is None
            assert metrics["production"]["count"] == 0

    def test_get_metrics_with_outcomes(self):
        """Metrics compute log_loss and accuracy from outcomes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            router = ABTestRouter(staging_percentage=50.0, log_dir=tmpdir)

            # Log outcomes for users that hash to staging (need to find them)
            staging_users = []
            production_users = []
            for i in range(100):
                user_id = f"user_{i}"
                stage = router.route(user_id)
                if stage == "staging" and len(staging_users) < 10:
                    staging_users.append(user_id)
                elif stage == "production" and len(production_users) < 10:
                    production_users.append(user_id)

            # Staging model: perfect predictions
            for user_id in staging_users:
                router.log_outcome(user_id=user_id, prediction=0.99, actual=True)

            # Production model: random predictions
            for user_id in production_users:
                router.log_outcome(user_id=user_id, prediction=0.50, actual=True)

            metrics = router.get_metrics()

            # Staging should have lower log_loss (better predictions)
            assert metrics["staging"]["log_loss"] < metrics["production"]["log_loss"]
            assert metrics["staging"]["accuracy"] == 1.0  # Perfect accuracy
            assert metrics["staging"]["count"] == 10
            assert metrics["production"]["count"] == 10

    def test_compare_variants_report(self):
        """compare_variants() generates readable report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            router = ABTestRouter(staging_percentage=20.0, log_dir=tmpdir)

            # Find users in each variant
            staging_user = None
            production_user = None
            for i in range(100):
                user_id = f"user_{i}"
                stage = router.route(user_id)
                if stage == "staging" and staging_user is None:
                    staging_user = user_id
                elif stage == "production" and production_user is None:
                    production_user = user_id
                if staging_user and production_user:
                    break

            # Log better predictions for staging
            router.log_outcome(user_id=staging_user, prediction=0.95, actual=True)
            router.log_outcome(user_id=production_user, prediction=0.55, actual=True)

            report = router.compare_variants()

            assert "A/B Test Results" in report
            assert "STAGING:" in report
            assert "PRODUCTION:" in report
            assert "Predictions:" in report
            assert "Log Loss:" in report

    def test_route_0_percent_staging(self):
        """0% staging routes all traffic to production."""
        router = ABTestRouter(staging_percentage=0.0)
        stages = [router.route(f"user_{i}") for i in range(100)]
        assert all(s == "production" for s in stages)

    def test_route_100_percent_staging(self):
        """100% staging routes all traffic to staging."""
        router = ABTestRouter(staging_percentage=100.0)
        stages = [router.route(f"user_{i}") for i in range(100)]
        assert all(s == "staging" for s in stages)
