from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Tuple

from pydantic import ValidationError

from .contracts import Team, Game, TeamSeasonStats


def validate_teams(raw: Iterable[dict]) -> Tuple[List[Team], List[str]]:
    teams: List[Team] = []
    errors: List[str] = []
    for t in raw:
        try:
            teams.append(Team(**t))
        except ValidationError as e:
            errors.append(f"Team validation error for id={t.get('id')}: {e}")
    return teams, errors


def validate_games(raw: Iterable[dict]) -> Tuple[List[Game], List[str]]:
    games: List[Game] = []
    errors: List[str] = []
    for g in raw:
        try:
            # Normalize date to datetime if a string
            if isinstance(g.get("date"), str):
                try:
                    g["date"] = datetime.fromisoformat(g["date"].replace("Z", ""))
                except Exception:
                    # Let pydantic handle parsing; will error if invalid
                    pass
            games.append(Game(**g))
        except ValidationError as e:
            errors.append(f"Game validation error for id={g.get('id')}: {e}")
    return games, errors


def validate_team_stats(raw: Iterable[dict]) -> Tuple[List[TeamSeasonStats], List[str]]:
    stats: List[TeamSeasonStats] = []
    errors: List[str] = []
    for s in raw:
        try:
            stats.append(TeamSeasonStats(**s))
        except ValidationError as e:
            errors.append(
                f"TeamSeasonStats validation error for team={s.get('team')}: {e}"
            )
    return stats, errors


def sanity_check_current_teams(teams: List[Team]) -> List[str]:
    errors: List[str] = []
    # Expect 30 current NBA teams (conference East/West present)
    current = [t for t in teams if (t.conference in ("East", "West"))]
    if len(current) != 30:
        errors.append(f"Expected 30 current teams, found {len(current)}")
    # Abbreviation uniqueness
    abbr = {t.abbreviation for t in current}
    if len(abbr) != len(current):
        errors.append("Duplicate abbreviations detected")
    return errors


def sanity_check_games(games: List[Game]) -> List[str]:
    errors: List[str] = []
    for g in games:
        if g.home_team.id == g.away_team.id:
            errors.append(f"Game {g.id} has identical home/away team ID")
        if g.home_score is not None and g.away_score is not None:
            if g.home_score < 0 or g.away_score < 0:
                errors.append(f"Game {g.id} has negative score")
    return errors
