"""
Provider protocol/interface for data sources.

Allows dependency injection and mocking while maintaining SOLID principles.
"""

from __future__ import annotations

from typing import Protocol, List, Dict


class GamesProvider(Protocol):
    """Protocol for fetching game data."""

    def get_games(self, date: str, **kwargs) -> List[Dict]:
        """
        Fetch games for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            List of game dictionaries
        """
        ...


class TeamsProvider(Protocol):
    """Protocol for fetching team data."""

    def get_teams(self, **kwargs) -> List[Dict]:
        """
        Fetch all teams.

        Returns:
            List of team dictionaries
        """
        ...

    def get_current_teams(self) -> List[Dict]:
        """
        Fetch current active teams (excludes historical).

        Returns:
            List of current team dictionaries
        """
        ...

    def get_team_games(self, team_id: int | str, season: int) -> List[Dict]:
        """
        Fetch all games for a team in a season.

        Args:
            team_id: Team identifier
            season: Season year

        Returns:
            List of game dictionaries
        """
        ...
