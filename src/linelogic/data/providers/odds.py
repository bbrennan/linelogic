"""
TheOddsAPI provider for fetching sports odds from multiple sportsbooks.

Fetches opening/closing lines for games; free tier sufficient for POC.
See: https://theOddsAPI.com/
"""

from typing import Any

import requests

from linelogic.config.settings import settings
from linelogic.data.providers.base import ProviderAPIError, StatsProvider


class OddsProvider(StatsProvider):
    """Base class for odds providers."""

    pass


class TheOddsAPIProvider(OddsProvider):
    """
    TheOddsAPI provider for multi-sportsbook odds.

    Free tier:
    - 500 requests/month (~16/day)
    - Major US sportsbooks: DraftKings, FanDuel, BetMGM, Caesars, etc.
    - No rate limit per se, but quota is monthly.

    Usage:
        provider = TheOddsAPIProvider()
        odds = provider.get_game_odds(sport="basketball_nba", date="2026-01-15")
    """

    BASE_URL = "https://api.the-odds-api.com/v4"

    def __init__(self, api_key: str | None = None):
        """
        Initialize TheOddsAPI provider.

        Args:
            api_key: API key (optional; defaults to settings.odds_api_key)
        """
        self.api_key = api_key or settings.odds_api_key
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.user_agent})

    def _request(self, endpoint: str, params: dict | None = None) -> dict:
        """
        Make HTTP request to TheOddsAPI.

        Args:
            endpoint: API endpoint (e.g., "/sports/basketball_nba/events")
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            ProviderAPIError: If API returns error
        """
        if params is None:
            params = {}

        params["apiKey"] = self.api_key

        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=5)

            if response.status_code != 200:
                raise ProviderAPIError(
                    f"TheOddsAPI error: {response.status_code} {response.text}"
                )

            return response.json()
        except requests.RequestException as exc:
            raise ProviderAPIError(f"TheOddsAPI request error: {exc}") from exc

    def get_players(self, **_kwargs: Any) -> list[dict]:
        """Not implemented for odds provider."""
        raise NotImplementedError("OddsProvider does not support get_players")

    def get_teams(self, **_kwargs: Any) -> list[dict]:
        """Not implemented for odds provider."""
        raise NotImplementedError("OddsProvider does not support get_teams")

    def get_games(self, date: str, **_kwargs: Any) -> list[dict]:
        """Not implemented for odds provider."""
        raise NotImplementedError("OddsProvider does not support get_games")

    def get_player_game_logs(
        self, player_id: str | int, season: str, **_kwargs: Any
    ) -> list[dict]:
        """Not implemented for odds provider."""
        raise NotImplementedError("OddsProvider does not support get_player_game_logs")

    def get_game_odds(
        self, _sport: str = "basketball_nba", **kwargs: Any
    ) -> list[dict]:
        """
        Get odds for games in a sport.

        Args:
            _sport: Sport key (e.g., "basketball_nba")
            **kwargs: Additional params (e.g., regions, bookmakers, oddsFormat)

        Returns:
            List of game dicts with odds per sportsbook
        """
        params = {
            "markets": "h2h",  # Head-to-head (moneyline)
            "oddsFormat": "american",
            "regions": "us",  # US sportsbooks
        }
        params.update(kwargs)

        data = self._request("/sports/basketball_nba/odds", params)

        # API returns list directly; handle both list and dict responses
        events = data if isinstance(data, list) else data.get("events", [])

        normalized = []
        for event in events:
            bookmakers = event.get("bookmakers", [])
            normalized.append(
                {
                    "id": event.get("id"),
                    "home_team": event.get("home_team"),
                    "away_team": event.get("away_team"),
                    "commence_time": event.get("commence_time"),
                    "bookmakers": bookmakers,
                }
            )

        return normalized
