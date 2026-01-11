from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Dict, List

from linelogic.data.providers.balldontlie import BalldontlieProvider
from linelogic.data.validators import (
    validate_teams,
    validate_games,
    sanity_check_current_teams,
    sanity_check_games,
)


class IngestPipeline:
    """
    Fetch → Normalize → Validate → Persist manifest.

    Idempotent via content-hash manifest keys.
    """

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = Path(output_dir or ".linelogic/manifests")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api = BalldontlieProvider()

    def _make_manifest_key(self, name: str, payload: Dict) -> str:
        raw = json.dumps(payload, sort_keys=True).encode()
        return f"{name}-{hashlib.md5(raw).hexdigest()[:8]}"

    def ingest_daily_games(self, date_str: str) -> Path:
        # Fetch
        games_raw = self.api.get_games(date_str)
        # Validate
        games, errors = validate_games(
            [
                {
                    "id": g["id"],
                    "date": g["date"],
                    "home_team": g["home_team"],
                    "away_team": g["away_team"],
                    "status": g["status"],
                    "home_score": g.get("home_score"),
                    "away_score": g.get("away_score"),
                }
                for g in games_raw
            ]
        )
        errors += sanity_check_games(games)
        manifest = {
            "type": "daily-games",
            "date": date_str,
            "count": len(games),
            "errors": errors,
        }
        key = self._make_manifest_key("daily-games", manifest)
        path = self.output_dir / f"{key}.json"
        path.write_text(json.dumps(manifest, indent=2))
        return path

    def ingest_current_teams(self) -> Path:
        teams_raw = self.api.get_current_teams()
        teams, errors = validate_teams(teams_raw)
        errors += sanity_check_current_teams(teams)
        manifest = {
            "type": "current-teams",
            "count": len(teams),
            "errors": errors,
        }
        key = self._make_manifest_key("current-teams", manifest)
        path = self.output_dir / f"{key}.json"
        path.write_text(json.dumps(manifest, indent=2))
        return path
