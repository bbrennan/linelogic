"""
Integration tests for data providers.

Uses mocked HTTP responses (no real API calls).
"""

import pytest
import responses

from linelogic.data.cache import Cache
from linelogic.data.providers.balldontlie import BalldontlieProvider
from linelogic.data.providers.base import PaidTierRequiredError


class TestBalldontlieProvider:
    """Test BALLDONTLIE provider with mocked responses."""

    @responses.activate
    def test_get_teams(self, tmp_path):
        # Mock API response
        responses.add(
            responses.GET,
            "https://api.balldontlie.io/v1/teams",
            json={
                "data": [
                    {
                        "id": 1,
                        "name": "Lakers",
                        "abbreviation": "LAL",
                        "city": "Los Angeles",
                        "conference": "West",
                        "division": "Pacific",
                    },
                    {
                        "id": 2,
                        "name": "Celtics",
                        "abbreviation": "BOS",
                        "city": "Boston",
                        "conference": "East",
                        "division": "Atlantic",
                    },
                ]
            },
            status=200,
        )

        provider = BalldontlieProvider(
            tier="free", rpm=60, cache=Cache(str(tmp_path / "cache.db"))
        )
        teams = provider.get_teams()

        assert len(teams) == 2
        assert teams[0]["abbreviation"] == "LAL"
        assert teams[1]["abbreviation"] == "BOS"

    @responses.activate
    def test_get_games(self):
        # Mock API response
        responses.add(
            responses.GET,
            "https://api.balldontlie.io/v1/games",
            json={
                "data": [
                    {
                        "id": 12345,
                        "date": "2026-01-15",
                        "home_team": {"id": 1, "name": "Lakers", "abbreviation": "LAL"},
                        "visitor_team": {
                            "id": 2,
                            "name": "Celtics",
                            "abbreviation": "BOS",
                        },
                        "status": "Final",
                        "home_team_score": 110,
                        "visitor_team_score": 105,
                    }
                ]
            },
            status=200,
        )

        provider = BalldontlieProvider(tier="free", rpm=60)
        games = provider.get_games("2026-01-15")

        assert len(games) == 1
        assert games[0]["id"] == 12345
        assert games[0]["home_team"]["abbreviation"] == "LAL"
        assert games[0]["away_team"]["abbreviation"] == "BOS"
        assert games[0]["home_score"] == 110

    @responses.activate
    def test_cache_usage(self, tmp_path):
        # Mock API response
        responses.add(
            responses.GET,
            "https://api.balldontlie.io/v1/teams",
            json={"data": []},
            status=200,
        )

        provider = BalldontlieProvider(
            tier="free", rpm=60, cache=Cache(str(tmp_path / "cache.db"))
        )

        # First call should hit API
        provider.get_teams()
        assert len(responses.calls) == 1

        # Second call should use cache (no additional API call)
        provider.get_teams()
        assert len(responses.calls) == 1

    def test_tier_gating_free_tier(self):
        provider = BalldontlieProvider(tier="free", rpm=60)

        # get_player_game_logs should raise PaidTierRequiredError on free tier
        with pytest.raises(PaidTierRequiredError) as exc_info:
            provider.get_player_game_logs(player_id=123, season="2024")

        assert "all-star" in str(exc_info.value).lower()
        assert "get_player_game_logs" in str(exc_info.value)

    @responses.activate
    def test_tier_gating_paid_tier(self):
        # Mock API response for stats
        responses.add(
            responses.GET,
            "https://api.balldontlie.io/v1/stats",
            json={
                "data": [
                    {
                        "game": {
                            "id": 123,
                            "date": "2024-01-15",
                            "home_team": {"id": 1, "abbreviation": "LAL"},
                            "visitor_team": {"id": 2, "abbreviation": "BOS"},
                        },
                        "team": {"id": 1},
                        "pts": 28,
                        "ast": 7,
                        "reb": 9,
                        "min": "35",
                    }
                ],
                "meta": {"total_pages": 1},
            },
            status=200,
        )

        provider = BalldontlieProvider(tier="all-star", rpm=60)

        # Should work on paid tier
        logs = provider.get_player_game_logs(player_id=123, season="2024")
        assert len(logs) == 1
        assert logs[0]["points"] == 28

    @responses.activate
    def test_rate_limiting(self):
        # Mock API response
        responses.add(
            responses.GET,
            "https://api.balldontlie.io/v1/teams",
            json={"data": []},
            status=200,
        )

        provider = BalldontlieProvider(tier="free", rpm=120)  # 2 per second

        # Should allow 2 requests immediately
        provider.cache.clear()  # Clear cache
        provider.get_teams()
        provider.cache.clear()
        provider.get_teams()

        # Third request should be delayed (or fail if non-blocking)
        # Note: This test is simplified; full integration would measure timing
        assert len(responses.calls) >= 2
