"""
Unit tests for data contracts and validators.
"""

import pytest
from datetime import datetime

from linelogic.data.contracts import Team, TeamRef, Game, TeamSeasonStats
from linelogic.data.validators import (
    validate_teams,
    validate_games,
    validate_team_stats,
    sanity_check_current_teams,
    sanity_check_games,
)


class TestContracts:
    def test_team_valid(self):
        team = Team(
            id=1,
            name="Hawks",
            full_name="Atlanta Hawks",
            abbreviation="ATL",
            city="Atlanta",
            conference="East",
            division="Southeast",
        )
        assert team.id == 1
        assert team.abbreviation == "ATL"

    def test_team_invalid_id(self):
        with pytest.raises(ValueError):
            Team(
                id=0,
                name="Hawks",
                full_name="Atlanta Hawks",
                abbreviation="ATL",
                city="Atlanta",
            )

    def test_game_valid(self):
        game = Game(
            id=123,
            date=datetime(2026, 1, 11, 19, 0),
            home_team=TeamRef(id=1, name="Hawks", abbreviation="ATL"),
            away_team=TeamRef(id=2, name="Celtics", abbreviation="BOS"),
            status="Final",
            home_score=110,
            away_score=105,
        )
        assert game.id == 123
        assert game.home_score == 110

    def test_team_season_stats_valid(self):
        stats = TeamSeasonStats(
            season=2025,
            team="Atlanta Hawks",
            win_pct=0.55,
            net_rating=2.5,
            pace=100.0,
            off_rating=112.0,
            def_rating=109.5,
            off_3pa_rate=0.40,
            def_opp_3pa_rate=0.38,
        )
        assert stats.season == 2025
        assert 0.0 <= stats.win_pct <= 1.0


class TestValidators:
    def test_validate_teams_success(self):
        raw = [
            {
                "id": 1,
                "name": "Hawks",
                "full_name": "Atlanta Hawks",
                "abbreviation": "ATL",
                "city": "Atlanta",
                "conference": "East",
                "division": "Southeast",
            }
        ]
        teams, errors = validate_teams(raw)
        assert len(teams) == 1
        assert len(errors) == 0

    def test_validate_teams_error(self):
        raw = [{"id": 0, "name": "Invalid"}]
        teams, errors = validate_teams(raw)
        assert len(teams) == 0
        assert len(errors) == 1

    def test_validate_games_success(self):
        raw = [
            {
                "id": 100,
                "date": "2026-01-11T19:00:00",
                "home_team": {"id": 1, "name": "Hawks", "abbreviation": "ATL"},
                "away_team": {"id": 2, "name": "Celtics", "abbreviation": "BOS"},
                "status": "Final",
                "home_score": 110,
                "away_score": 105,
            }
        ]
        games, errors = validate_games(raw)
        assert len(games) == 1
        assert len(errors) == 0

    def test_sanity_check_current_teams_count(self):
        teams = [
            Team(
                id=i,
                name=f"Team{i}",
                full_name=f"Full Team {i}",
                abbreviation=f"T{i:02d}",
                city=f"City{i}",
                conference="East" if i % 2 == 0 else "West",
            )
            for i in range(1, 31)
        ]
        errors = sanity_check_current_teams(teams)
        assert len(errors) == 0

    def test_sanity_check_games_duplicate_team(self):
        game = Game(
            id=1,
            date=datetime.now(),
            home_team=TeamRef(id=1, name="Hawks", abbreviation="ATL"),
            away_team=TeamRef(id=1, name="Hawks", abbreviation="ATL"),
            status="Final",
        )
        errors = sanity_check_games([game])
        assert len(errors) == 1
        assert "identical" in errors[0]
