from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class RunContext:
    """Represents a single ingestion run (for manifests/metrics/logs)."""

    run_id: str
    date: str
    started_at_utc: str

    @classmethod
    def create(cls, *, now: datetime | None = None) -> "RunContext":
        now_dt = now or datetime.now(timezone.utc)
        date = now_dt.strftime("%Y-%m-%d")
        ts = now_dt.strftime("%Y%m%dT%H%M%SZ")
        rand = os.urandom(3).hex()
        return cls(
            run_id=f"{ts}-{rand}",
            date=date,
            started_at_utc=now_dt.isoformat(),
        )

    def write_run_config(
        self,
        run_dir: Path,
        config: Mapping[str, Any],
    ) -> Path:
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / "run_config.json"
        payload = json.dumps(config, indent=2, sort_keys=True)
        path.write_text(payload, encoding="utf-8")
        return path

    def write_run_summary(
        self,
        run_dir: Path,
        summary: Mapping[str, Any],
    ) -> Path:
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / "run_summary.json"
        payload = json.dumps(summary, indent=2, sort_keys=True)
        path.write_text(payload, encoding="utf-8")
        return path

    def write_metrics(
        self,
        run_dir: Path,
        metrics: Mapping[str, Any],
    ) -> Path:
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / "metrics.json"
        payload = json.dumps(metrics, indent=2, sort_keys=True)
        path.write_text(payload, encoding="utf-8")
        return path
