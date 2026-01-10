"""
Base provider interface and custom exceptions.

All data providers must implement the StatsProvider ABC.
"""

from abc import ABC, abstractmethod
from typing import Any


class PaidTierRequiredError(Exception):
    """
    Raised when a method requires a paid tier but user is on free tier.

    Attributes:
        provider: Name of the provider (e.g., "balldontlie")
        required_tier: Minimum tier required (e.g., "all-star")
        method: Method name that was called
    """

    def __init__(self, provider: str, required_tier: str, method: str):
        self.provider = provider
        self.required_tier = required_tier
        self.method = method
        super().__init__(
            f"{provider} {method}() requires {required_tier} tier or higher. "
            "Visit https://www.balldontlie.io/pricing to upgrade."
        )


class ProviderAPIError(Exception):
    """Raised when provider API returns an error."""

    pass


class ProviderRateLimitError(Exception):
    """Raised when provider rate limit is exceeded."""

    pass


class StatsProvider(ABC):
    """
    Abstract base class for sports statistics providers.

    All providers must implement these methods to ensure swappability.
    """

    @abstractmethod
    def get_players(self, **kwargs: Any) -> list[dict]:
        """
        Get all players.

        Returns:
            List of player dicts with keys:
                - id: str or int
                - first_name: str
                - last_name: str
                - team: str or None
                - position: str or None
        """
        pass

    @abstractmethod
    def get_teams(self, **kwargs: Any) -> list[dict]:
        """
        Get all teams.

        Returns:
            List of team dicts with keys:
                - id: str or int
                - name: str
                - abbreviation: str
                - city: str
                - conference: str or None
                - division: str or None
        """
        pass

    @abstractmethod
    def get_games(self, date: str, **kwargs: Any) -> list[dict]:
        """
        Get games for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            List of game dicts with keys:
                - id: str or int
                - date: str (YYYY-MM-DD)
                - home_team: dict
                - away_team: dict
                - status: str ("scheduled", "in_progress", "final")
                - home_score: int or None
                - away_score: int or None
        """
        pass

    @abstractmethod
    def get_player_game_logs(
        self, player_id: str | int, season: str, **kwargs: Any
    ) -> list[dict]:
        """
        Get game logs for a player in a season.

        Args:
            player_id: Player ID
            season: Season year (e.g., "2024")

        Returns:
            List of game log dicts with keys:
                - game_id: str or int
                - date: str (YYYY-MM-DD)
                - opponent: str
                - points: int
                - assists: int
                - rebounds: int
                - minutes: int
                - ... (other stats as available)

        Raises:
            PaidTierRequiredError: If method requires paid tier

        Note:
            This method may not be available on free tiers.
        """
        pass
