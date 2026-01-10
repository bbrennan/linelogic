"""
Tests for Elo rating system.
"""

import pytest
from linelogic.models.elo import EloRating
import tempfile
import json


def test_elo_initialization():
    """Test Elo system initializes with correct defaults."""
    elo = EloRating()
    assert elo.k_factor == 20.0
    assert elo.home_advantage == 100.0
    assert elo.initial_rating == 1500.0
    assert len(elo.ratings) == 0


def test_get_rating_creates_initial():
    """Test get_rating creates initial rating for new teams."""
    elo = EloRating()
    rating = elo.get_rating("Lakers")
    assert rating == 1500.0
    assert "Lakers" in elo.ratings


def test_predict_win_probability():
    """Test win probability prediction."""
    elo = EloRating()

    # Equal teams + home advantage
    prob = elo.predict_win_probability("Lakers", "Celtics")
    assert 0.6 < prob < 0.7  # Home team favored

    # Set ratings manually
    elo.ratings["Warriors"] = 1700
    elo.ratings["Wizards"] = 1300

    prob_warriors_home = elo.predict_win_probability("Warriors", "Wizards")
    assert prob_warriors_home > 0.85  # Strong favorite at home

    prob_wizards_home = elo.predict_win_probability("Wizards", "Warriors")
    assert prob_wizards_home < 0.35  # Underdog even at home


def test_update_ratings_home_win():
    """Test ratings update after home team wins."""
    elo = EloRating()

    # Both teams start at 1500
    home_before = elo.get_rating("Lakers")
    away_before = elo.get_rating("Celtics")

    # Lakers win at home 110-95
    new_home, new_away = elo.update_ratings("Lakers", "Celtics", 110, 95)

    # Home team should gain rating, away should lose
    assert new_home > home_before
    assert new_away < away_before

    # Ratings should be symmetric (zero-sum)
    assert abs((new_home - home_before) + (new_away - away_before)) < 0.01


def test_update_ratings_away_win():
    """Test ratings update after away team wins."""
    elo = EloRating()

    home_before = elo.get_rating("Lakers")
    away_before = elo.get_rating("Celtics")

    # Celtics win on road 105-98
    new_home, new_away = elo.update_ratings("Lakers", "Celtics", 98, 105)

    # Away team gains, home team loses
    assert new_away > away_before
    assert new_home < home_before

    # Changes should be symmetric (zero-sum)
    assert abs((new_away - away_before) + (new_home - home_before)) < 0.01


def test_margin_of_victory_impact():
    """Test that larger margins produce larger rating changes."""
    elo1 = EloRating()
    elo2 = EloRating()

    # Close game
    elo1.update_ratings("Lakers", "Celtics", 100, 98)
    close_change = elo1.get_rating("Lakers") - 1500

    # Blowout
    elo2.update_ratings("Lakers", "Celtics", 120, 90)
    blowout_change = elo2.get_rating("Lakers") - 1500

    # Blowout should produce larger rating change
    assert blowout_change > close_change


def test_save_and_load_ratings():
    """Test persisting and loading ratings from disk."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

    try:
        # Create Elo and update some ratings
        elo1 = EloRating(ratings_file=temp_file)
        elo1.update_ratings("Lakers", "Celtics", 110, 95)
        elo1.update_ratings("Warriors", "Nets", 115, 100)
        elo1.save_ratings()

        lakers_rating = elo1.get_rating("Lakers")
        warriors_rating = elo1.get_rating("Warriors")

        # Load ratings in new instance
        elo2 = EloRating(ratings_file=temp_file)

        assert elo2.get_rating("Lakers") == lakers_rating
        assert elo2.get_rating("Warriors") == warriors_rating
        assert len(elo2.ratings) == 4  # Lakers, Celtics, Warriors, Nets

    finally:
        import os

        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_reset_ratings():
    """Test resetting all ratings to initial."""
    elo = EloRating()
    elo.update_ratings("Lakers", "Celtics", 110, 95)

    assert len(elo.ratings) > 0

    elo.reset_ratings()
    assert len(elo.ratings) == 0


def test_get_all_ratings():
    """Test retrieving all current ratings."""
    elo = EloRating()
    elo.update_ratings("Lakers", "Celtics", 110, 95)
    elo.update_ratings("Warriors", "Nets", 115, 100)

    all_ratings = elo.get_all_ratings()

    assert len(all_ratings) == 4
    assert "Lakers" in all_ratings
    assert "Warriors" in all_ratings
    assert all_ratings["Lakers"] > 1500  # Won, should be above initial


def test_elo_converges_after_many_games():
    """Test that Elo ratings stabilize after sufficient games."""
    elo = EloRating()

    # Simulate a strong team beating a weak team repeatedly
    for _ in range(50):
        elo.update_ratings("Warriors", "Wizards", 115, 95)

    warriors_rating = elo.get_rating("Warriors")
    wizards_rating = elo.get_rating("Wizards")

    # Warriors should be significantly higher
    assert warriors_rating > 1700
    assert wizards_rating < 1300

    # Ratings should converge (changes get smaller)
    before = elo.get_rating("Warriors")
    elo.update_ratings("Warriors", "Wizards", 115, 95)
    after = elo.get_rating("Warriors")

    # Change should be small after many games
    assert abs(after - before) < 5
