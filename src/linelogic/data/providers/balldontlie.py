"""
BALLDONTLIE API provider implementation.

Implements StatsProvider interface with:
- Tier gating (free vs. paid endpoints)
- Caching (via Cache class)
- Rate limiting (via RateLimiter)

See: https://www.balldontlie.io/home.html
"""

import logging
import time
from typing import Any

import requests

from linelogic.config.settings import settings
from linelogic.data.cache import Cache
from linelogic.data.providers.base import (
    PaidTierRequiredError,
    ProviderAPIError,
    StatsProvider,
)
from linelogic.data.rate_limit import RateLimiter

logger = logging.getLogger("linelogic.providers.balldontlie")


class BalldontlieProvider(StatsProvider):
    """
    BALLDONTLIE API provider.

    Free tier limitations:
    - 5 requests/minute
    - Players, teams, games endpoints only
    - No player stats, season averages, or injuries

    All-Star tier ($5/mo):
    - 30 requests/minute
    - Player stats, season averages, injuries

    MVP tier ($15/mo):
    - 60 requests/minute
    - Advanced stats, play-by-play
    """

    BASE_URL = "https://api.balldontlie.io/v1"

    def __init__(
        self,
        api_key: str | None = None,
        tier: str | None = None,
        rpm: int | None = None,
        cache: Cache | None = None,
        rate_limiter: RateLimiter | None = None,
    ):
        """
        Initialize BALLDONTLIE provider.

        Args:
            api_key: API key (optional for free tier)
            tier: Tier level ("free", "all-star", "mvp")
            rpm: Requests per minute limit
            cache: Cache instance (default: create new)
            rate_limiter: RateLimiter instance (default: create new)
        """
        self.api_key = api_key or settings.balldontlie_api_key
        self.tier = tier or settings.balldontlie_tier
        self.rpm = rpm or settings.balldontlie_rpm

        self.cache = cache or Cache(
            settings.cache_db_path, default_ttl=settings.cache_ttl_seconds
        )
        self.rate_limiter = rate_limiter or RateLimiter(self.rpm)

        # Resilience configuration
        self.request_timeout = 5
        self.max_retries = 2
        self.backoff_seconds = 1

        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

        self.session.headers.update({"User-Agent": settings.user_agent})

    def _request(self, endpoint: str, params: dict | None = None) -> dict:
        """
        Make HTTP request with caching and rate limiting.

        Args:
            endpoint: API endpoint (e.g., "/players")
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            ProviderAPIError: If API returns error
        """
        if params is None:
            params = {}

        # Check cache first
        cached = self.cache.get("balldontlie", endpoint, params)
        if cached is not None:
            return cached

        # Acquire rate limit token
        self.rate_limiter.acquire(blocking=True)

        url = f"{self.BASE_URL}{endpoint}"

        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                response = self.session.get(
                    url, params=params, timeout=self.request_timeout
                )
                elapsed = time.time() - start_time
                logger.info(
                    f"API request completed in {elapsed:.2f}s: {endpoint} (attempt {attempt + 1})"
                )

                if response.status_code != 200:
                    logger.error(f"API error {response.status_code}: {response.text}")
                    raise ProviderAPIError(
                        f"BALLDONTLIE API error: {response.status_code} {response.text}"
                    )

                data = response.json()
                break
            except Exception:  # noqa: BLE001 keep broad for HTTP/JSON errors
                if attempt == self.max_retries:
                    logger.error("Max retries exceeded")
                    raise
                wait_time = self.backoff_seconds * (attempt + 1)
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.max_retries + 1}), "
                    f"backoff {wait_time}s"
                )
                time.sleep(wait_time)

        # Cache response
        self.cache.set("balldontlie", endpoint, params, data)

        return data

    def get_players(self, **_kwargs: Any) -> list[dict]:
        """
        Get all NBA players.

        Available on FREE tier.

        Returns:
            List of player dicts
        """
        # BALLDONTLIE API uses pagination
        all_players = []
        page = 1
        per_page = 100

        while True:
            data = self._request("/players", {"page": page, "per_page": per_page})

            players = data.get("data", [])
            if not players:
                break

            # Normalize to internal schema
            for player in players:
                all_players.append(
                    {
                        "id": player["id"],
                        "first_name": player["first_name"],
                        "last_name": player["last_name"],
                        "team": (
                            player.get("team", {}).get("abbreviation")
                            if player.get("team")
                            else None
                        ),
                        "position": player.get("position"),
                    }
                )

            # Check if more pages
            meta = data.get("meta", {})
            if page >= meta.get("total_pages", 1):
                break

            page += 1

        return all_players

    def get_teams(self, **_kwargs: Any) -> list[dict]:
        """
        Get all NBA teams.

        Available on FREE tier.

        Returns:
            List of team dicts
        """
        data = self._request("/teams")

        teams = data.get("data", [])

        # Normalize to internal schema
        normalized = []
        for team in teams:
            normalized.append(
                {
                    "id": team["id"],
                    "name": team["name"],
                    "full_name": team.get("full_name", team["name"]),
                    "abbreviation": team["abbreviation"],
                    "city": team["city"],
                    "conference": team.get("conference"),
                    "division": team.get("division"),
                }
            )

        return normalized

    def get_current_teams(self) -> list[dict]:
        """
        Return only current NBA franchises (East/West conferences).

        Filters out historical teams by requiring a non-empty conference.

        Returns:
            List of team dicts with id, name, full_name, abbreviation, city, conference, division
        """
        teams = self.get_teams()
        return [t for t in teams if t.get("conference") in ("East", "West")]

    def get_team_games(self, team_id: int | str, season: int) -> list[dict]:
        """
        Get all games for a team in a given season.

        Args:
            team_id: Team ID (int)
            season: Season year (e.g., 2025)

        Returns:
            List of normalized game dicts (same shape as get_games)
        """
        params = {
            "team_ids[]": team_id,
            "seasons[]": season,
            "per_page": 100,
        }

        all_games: list[dict] = []
        page = 1
        while True:
            params["page"] = page
            data = self._request("/games", params)
            games = data.get("data", [])
            if not games:
                break

            for game in games:
                all_games.append(
                    {
                        "id": game["id"],
                        "date": game["date"],
                        "home_team": {
                            "id": game["home_team"]["id"],
                            "name": game["home_team"]["name"],
                            "abbreviation": game["home_team"]["abbreviation"],
                        },
                        "away_team": {
                            "id": game["visitor_team"]["id"],
                            "name": game["visitor_team"]["name"],
                            "abbreviation": game["visitor_team"]["abbreviation"],
                        },
                        "status": game["status"],
                        "home_score": game.get("home_team_score"),
                        "away_score": game.get("visitor_team_score"),
                    }
                )

            meta = data.get("meta", {})
            if page >= meta.get("total_pages", 1):
                break
            page += 1

        return all_games

    def get_team_season_game_stats(
        self, team_id: int | str, season: int
    ) -> dict[int, dict]:
        """
        Aggregate per-game team shooting stats (FG3A, FGA) across a season.

        Requires paid tier (stats endpoint).

        Args:
            team_id: Team ID (int)
            season: Season year (e.g., 2025)

        Returns:
            Dict of game_id -> { 'fg3a': int, 'fga': int }
        """
        if self.tier == "free":
            raise PaidTierRequiredError(
                provider="balldontlie",
                required_tier="all-star",
                method="get_team_season_game_stats",
            )

        params = {
            "team_ids[]": team_id,
            "seasons[]": season,
            "per_page": 100,
        }

        per_game: dict[int, dict] = {}
        page = 1
        while True:
            params["page"] = page
            data = self._request("/stats", params)
            stats = data.get("data", [])
            if not stats:
                break

            for s in stats:
                game_id = s["game"]["id"]
                fg3a = int(s.get("fg3a", 0) or 0)
                fga = int(s.get("fga", 0) or 0)
                g = per_game.setdefault(game_id, {"fg3a": 0, "fga": 0})
                g["fg3a"] += fg3a
                g["fga"] += fga

            meta = data.get("meta", {})
            if page >= meta.get("total_pages", 1):
                break
            page += 1

        return per_game

    def get_games(self, date: str, **_kwargs: Any) -> list[dict]:
        """
        Get games for a specific date.

        Available on FREE tier.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            List of game dicts
        """
        # BALLDONTLIE uses "dates[]" parameter
        params = {"dates[]": date}

        data = self._request("/games", params)

        games = data.get("data", [])

        # Normalize to internal schema
        normalized = []
        for game in games:
            normalized.append(
                {
                    "id": game["id"],
                    "date": game["date"],
                    "home_team": {
                        "id": game["home_team"]["id"],
                        "name": game["home_team"]["name"],
                        "abbreviation": game["home_team"]["abbreviation"],
                    },
                    "away_team": {
                        "id": game["visitor_team"]["id"],
                        "name": game["visitor_team"]["name"],
                        "abbreviation": game["visitor_team"]["abbreviation"],
                    },
                    "status": game["status"],
                    "home_score": game.get("home_team_score"),
                    "away_score": game.get("visitor_team_score"),
                }
            )

        return normalized

    def get_player_game_logs(
        self, player_id: str | int, season: str, **_kwargs: Any
    ) -> list[dict]:
        """
        Get game logs for a player in a season.

        REQUIRES ALL-STAR TIER OR HIGHER ($5/mo).

        Args:
            player_id: Player ID
            season: Season year (e.g., "2024")

        Returns:
            List of game log dicts

        Raises:
            PaidTierRequiredError: If tier is "free"
        """
        if self.tier == "free":
            raise PaidTierRequiredError(
                provider="balldontlie",
                required_tier="all-star",
                method="get_player_game_logs",
            )

        # Implementation for paid tiers
        params = {
            "player_ids[]": player_id,
            "seasons[]": season,
            "per_page": 100,
        }

        all_stats = []
        page = 1

        while True:
            params["page"] = page
            data = self._request("/stats", params)

            stats = data.get("data", [])
            if not stats:
                break

            # Normalize to internal schema
            for stat in stats:
                all_stats.append(
                    {
                        "game_id": stat["game"]["id"],
                        "date": stat["game"]["date"],
                        "opponent": (
                            stat["game"]["visitor_team"]["abbreviation"]
                            if stat["game"]["home_team"]["id"] == stat["team"]["id"]
                            else stat["game"]["home_team"]["abbreviation"]
                        ),
                        "points": stat.get("pts", 0),
                        "assists": stat.get("ast", 0),
                        "rebounds": stat.get("reb", 0),
                        "minutes": stat.get("min", "0"),
                        "fgm": stat.get("fgm", 0),
                        "fga": stat.get("fga", 0),
                        "fg3m": stat.get("fg3m", 0),
                        "fg3a": stat.get("fg3a", 0),
                        "ftm": stat.get("ftm", 0),
                        "fta": stat.get("fta", 0),
                        "steals": stat.get("stl", 0),
                        "blocks": stat.get("blk", 0),
                        "turnovers": stat.get("turnover", 0),
                    }
                )

            # Check if more pages
            meta = data.get("meta", {})
            if page >= meta.get("total_pages", 1):
                break

            page += 1

        return all_stats
