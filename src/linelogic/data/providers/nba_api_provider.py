"""
nba_api provider implementation (unofficial).

IMPORTANT: This uses an unofficial scraper that violates NBA.com ToS.
Use for research and backfilling only. NOT for production.

Behind feature flag: USE_NBA_API (default: false)
"""

from typing import Any

from linelogic.config.settings import settings
from linelogic.data.providers.base import ProviderAPIError, StatsProvider


class NbaApiProvider(StatsProvider):
    """
    nba_api provider (unofficial).

    WARNING: This is an unofficial scraper. Use at your own risk.
    - No API key required
    - No official rate limits (but be respectful)
    - Can break without notice

    Use cases:
    - Historical data backfilling
    - Research and model training
    - Fallback when BALLDONTLIE unavailable

    NOT for:
    - Real-time production systems
    - High-frequency requests
    """

    def __init__(self):
        """
        Initialize nba_api provider.

        Raises:
            ImportError: If nba_api not installed or USE_NBA_API=false
        """
        if not settings.use_nba_api:
            raise ImportError(
                "nba_api provider is disabled. Set USE_NBA_API=true in .env to enable."
            )

        try:
            # Import nba_api here (optional dependency)
            from nba_api.stats.endpoints import (
                CommonAllPlayers,
                LeagueGameLog,
                PlayerGameLog,
            )
            from nba_api.stats.static import teams

            self.CommonAllPlayers = CommonAllPlayers
            self.LeagueGameLog = LeagueGameLog
            self.PlayerGameLog = PlayerGameLog
            self.teams_module = teams
        except ImportError as e:
            raise ImportError(
                "nba_api is not installed. Install with: pip install nba_api"
            ) from e

    def get_players(self, season: str = "2024-25", **kwargs: Any) -> list[dict]:
        """
        Get all NBA players for a season.

        Args:
            season: Season string (e.g., "2024-25")

        Returns:
            List of player dicts
        """
        try:
            players_data = self.CommonAllPlayers(
                season=season, is_only_current_season=1
            ).get_data_frames()[0]

            players = []
            for _, row in players_data.iterrows():
                players.append(
                    {
                        "id": row["PERSON_ID"],
                        "first_name": (
                            row["DISPLAY_FIRST_LAST"].split()[0]
                            if row["DISPLAY_FIRST_LAST"]
                            else ""
                        ),
                        "last_name": (
                            row["DISPLAY_FIRST_LAST"].split()[-1]
                            if row["DISPLAY_FIRST_LAST"]
                            else ""
                        ),
                        "team": row.get("TEAM_ABBREVIATION"),
                        "position": None,  # Not available in this endpoint
                    }
                )

            return players
        except Exception as e:
            raise ProviderAPIError(f"nba_api error: {e}") from e

    def get_teams(self, **kwargs: Any) -> list[dict]:
        """
        Get all NBA teams.

        Returns:
            List of team dicts
        """
        try:
            teams_data = self.teams_module.get_teams()

            teams = []
            for team in teams_data:
                teams.append(
                    {
                        "id": team["id"],
                        "name": team["full_name"],
                        "abbreviation": team["abbreviation"],
                        "city": team["city"],
                        "conference": None,  # Not in static data
                        "division": None,
                    }
                )

            return teams
        except Exception as e:
            raise ProviderAPIError(f"nba_api error: {e}") from e

    def get_games(self, date: str, **kwargs: Any) -> list[dict]:
        """
        Get games for a specific date.

        Note: nba_api doesn't have a direct "games by date" endpoint.
        This is a simplified stub. For production, would need LeagueDashboard or similar.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            List of game dicts (stub implementation)
        """
        # Stub: nba_api doesn't have easy date-based game lookup
        # For real implementation, would use Scoreboard endpoint
        raise NotImplementedError(
            "get_games() not fully implemented for nba_api. "
            "Use BALLDONTLIE for game schedules."
        )

    def get_player_game_logs(
        self, player_id: str | int, season: str, **kwargs: Any
    ) -> list[dict]:
        """
        Get game logs for a player in a season.

        Args:
            player_id: NBA player ID
            season: Season string (e.g., "2024-25")

        Returns:
            List of game log dicts
        """
        try:
            game_log = self.PlayerGameLog(
                player_id=player_id, season=season
            ).get_data_frames()[0]

            logs = []
            for _, row in game_log.iterrows():
                logs.append(
                    {
                        "game_id": row["GAME_ID"],
                        "date": row["GAME_DATE"],
                        "opponent": row["MATCHUP"].split()[
                            -1
                        ],  # Extract opponent from "LAL @ BOS"
                        "points": row.get("PTS", 0),
                        "assists": row.get("AST", 0),
                        "rebounds": row.get("REB", 0),
                        "minutes": row.get("MIN", "0"),
                        "fgm": row.get("FGM", 0),
                        "fga": row.get("FGA", 0),
                        "fg3m": row.get("FG3M", 0),
                        "fg3a": row.get("FG3A", 0),
                        "ftm": row.get("FTM", 0),
                        "fta": row.get("FTA", 0),
                        "steals": row.get("STL", 0),
                        "blocks": row.get("BLK", 0),
                        "turnovers": row.get("TOV", 0),
                    }
                )

            return logs
        except Exception as e:
            raise ProviderAPIError(f"nba_api error: {e}") from e
