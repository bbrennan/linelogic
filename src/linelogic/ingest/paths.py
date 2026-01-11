from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataPaths:
    """Conventional local directory layout for ingestion data."""

    root: Path

    @classmethod
    def from_repo_root(cls, repo_root: Path) -> "DataPaths":
        return cls(root=repo_root / "data")

    def ensure(self) -> None:
        for path in [
            self.root,
            self.bronze_root,
            self.silver_root,
            self.gold_root,
            self.runs_root,
            self.checkpoints_root,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    @property
    def bronze_root(self) -> Path:
        return self.root / "bronze"

    @property
    def silver_root(self) -> Path:
        return self.root / "silver"

    @property
    def gold_root(self) -> Path:
        return self.root / "gold"

    @property
    def runs_root(self) -> Path:
        return self.root / "runs"

    @property
    def checkpoints_root(self) -> Path:
        return self.root / "checkpoints"

    def bronze_run_dir(
        self,
        provider: str,
        sport: str,
        date: str,
        run_id: str,
        endpoint: str,
    ) -> Path:
        # Note: endpoint may contain slashes, normalize to path-safe
        endpoint_safe = endpoint.strip("/").replace("/", "_")
        return (
            self.bronze_root
            / f"provider={provider}"
            / f"sport={sport}"
            / f"date={date}"
            / f"run_id={run_id}"
            / f"endpoint={endpoint_safe}"
        )

    def run_dir(self, date: str, run_id: str) -> Path:
        return self.runs_root / date / f"run_id={run_id}"

    def checkpoint_path(self, provider: str, sport_or_league: str) -> Path:
        return self.checkpoints_root / provider / f"{sport_or_league}.json"
