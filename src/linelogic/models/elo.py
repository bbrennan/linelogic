"""
Elo Rating System for NBA Teams

Implements a dynamic team strength rating system that:
- Starts all teams at 1500
- Adjusts ratings after each game based on outcome and margin
- Accounts for home court advantage
- Persists ratings across seasons
"""

from typing import Dict, Optional, Tuple
import math
import json
from pathlib import Path


class EloRating:
    """
    Elo rating system for NBA teams.

    Attributes:
        k_factor: Sensitivity to new results (default: 20)
        home_advantage: Points added to home team rating (default: 100)
        initial_rating: Starting rating for new teams (default: 1500)
        margin_multiplier: Scale factor for margin of victory adjustment (default: 1.0)
    """

    def __init__(
        self,
        k_factor: float = 20.0,
        home_advantage: float = 100.0,
        initial_rating: float = 1500.0,
        margin_multiplier: float = 1.0,
        ratings_file: Optional[str] = None,
    ):
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.initial_rating = initial_rating
        self.margin_multiplier = margin_multiplier
        self.ratings: Dict[str, float] = {}
        self.ratings_file = ratings_file or ".linelogic/elo_ratings.json"

        # Load existing ratings if available
        self._load_ratings()

    def get_rating(self, team: str) -> float:
        """Get current Elo rating for a team."""
        if team not in self.ratings:
            self.ratings[team] = self.initial_rating
        return self.ratings[team]

    def _expected_score(self, rating_a: float, rating_b: float) -> float:
        """
        Calculate expected score for team A vs team B.

        Returns probability in [0, 1] that team A wins.
        """
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def _margin_multiplier_factor(
        self, margin: int, winning_elo: float, losing_elo: float
    ) -> float:
        """
        Adjust K-factor based on margin of victory.

        Closer games have less impact; blowouts have more impact.
        Upset wins (low Elo beats high Elo) get bonus multiplier.
        """
        # Base margin factor: log scale
        if margin <= 0:
            return 1.0

        margin_factor = math.log(margin + 1) * self.margin_multiplier

        # Autocorrelation adjustment: penalize blowouts by favorites
        elo_diff = winning_elo - losing_elo
        if elo_diff > 0:
            # Favorite won - less credit for blowout
            margin_factor *= 2.2 / ((elo_diff * 0.001) + 2.2)

        return margin_factor

    def update_ratings(
        self,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
    ) -> Tuple[float, float]:
        """
        Update Elo ratings after a game.

        Args:
            home_team: Name of home team
            away_team: Name of away team
            home_score: Points scored by home team
            away_score: Points scored by away team

        Returns:
            Tuple of (new_home_rating, new_away_rating)
        """
        # Get current ratings
        home_rating = self.get_rating(home_team)
        away_rating = self.get_rating(away_team)

        # Apply home court advantage to expected score calculation
        home_rating_adj = home_rating + self.home_advantage
        expected_home = self._expected_score(home_rating_adj, away_rating)
        expected_away = 1 - expected_home

        # Actual outcome (1 = win, 0 = loss)
        actual_home = 1.0 if home_score > away_score else 0.0
        actual_away = 1 - actual_home

        # Margin of victory
        margin = abs(home_score - away_score)

        # Determine winner/loser Elo for margin adjustment
        if home_score > away_score:
            winning_elo = home_rating
            losing_elo = away_rating
        else:
            winning_elo = away_rating
            losing_elo = home_rating

        margin_mult = self._margin_multiplier_factor(margin, winning_elo, losing_elo)

        # Update ratings
        k_adjusted = self.k_factor * margin_mult
        home_change = k_adjusted * (actual_home - expected_home)
        away_change = k_adjusted * (actual_away - expected_away)

        new_home_rating = home_rating + home_change
        new_away_rating = away_rating + away_change

        # Store updated ratings
        self.ratings[home_team] = new_home_rating
        self.ratings[away_team] = new_away_rating

        return new_home_rating, new_away_rating

    def predict_win_probability(
        self,
        home_team: str,
        away_team: str,
    ) -> float:
        """
        Predict probability that home team wins.

        Returns value in [0, 1].
        """
        home_rating = self.get_rating(home_team)
        away_rating = self.get_rating(away_team)

        # Apply home court advantage
        home_rating_adj = home_rating + self.home_advantage

        return self._expected_score(home_rating_adj, away_rating)

    def get_all_ratings(self) -> Dict[str, float]:
        """Get current ratings for all teams."""
        return dict(self.ratings)

    def reset_ratings(self) -> None:
        """Reset all teams to initial rating."""
        self.ratings = {}

    def _load_ratings(self) -> None:
        """Load ratings from disk if file exists."""
        path = Path(self.ratings_file)
        if path.exists():
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    self.ratings = data.get("ratings", {})
            except Exception:
                # If load fails, start fresh
                self.ratings = {}

    def save_ratings(self) -> None:
        """Persist current ratings to disk."""
        path = Path(self.ratings_file)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "ratings": self.ratings,
            "k_factor": self.k_factor,
            "home_advantage": self.home_advantage,
            "initial_rating": self.initial_rating,
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def __repr__(self) -> str:
        return f"EloRating(teams={len(self.ratings)}, k={self.k_factor}, home_adv={self.home_advantage})"
