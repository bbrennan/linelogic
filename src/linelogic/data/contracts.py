from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class Team(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: int = Field(..., ge=1)
    name: str
    full_name: str
    abbreviation: str = Field(..., min_length=2, max_length=4)
    city: str
    conference: Optional[str] = Field(default=None)
    division: Optional[str] = Field(default=None)


class TeamRef(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: int = Field(..., ge=1)
    name: str
    abbreviation: str = Field(..., min_length=2, max_length=4)


class Game(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., ge=1)
    date: datetime
    home_team: TeamRef
    away_team: TeamRef
    status: str
    home_score: Optional[int] = Field(default=None, ge=0)
    away_score: Optional[int] = Field(default=None, ge=0)


class TeamSeasonStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    season: int = Field(..., ge=1900)
    team: str
    win_pct: float = Field(..., ge=0.0, le=1.0)
    net_rating: float
    pace: float = Field(..., gt=0)
    off_rating: float
    def_rating: float
    off_3pa_rate: float = Field(..., ge=0.0, le=1.0)
    def_opp_3pa_rate: float = Field(..., ge=0.0, le=1.0)
