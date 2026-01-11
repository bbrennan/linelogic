from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BronzeWriteResult:
    response_path: Path
    manifest_path: Path
    record_count: int | None


class BronzeWriter:
    """Writes raw provider responses to the Bronze layer (append-only)."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write_json(
        self,
        *,
        payload: Any,
        manifest: dict[str, Any],
        filename_prefix: str = "response",
    ) -> BronzeWriteResult:
        self.base_dir.mkdir(parents=True, exist_ok=True)

        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()[:12]
        response_path = self.base_dir / f"{filename_prefix}_{digest}.json"
        manifest_path = self.base_dir / "manifest.json"

        # Append-only rule: never overwrite existing response JSON
        if not response_path.exists():
            response_path.write_bytes(raw)

        enriched_manifest = {
            **manifest,
            "written_at_utc": datetime.now(timezone.utc).isoformat(),
            "response_file": response_path.name,
        }

        # manifest.json is per endpoint/run folder; overwrite is fine
        manifest_path.write_text(
            json.dumps(enriched_manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        record_count: int | None = None
        if isinstance(payload, list):
            record_count = len(payload)

        return BronzeWriteResult(
            response_path=response_path,
            manifest_path=manifest_path,
            record_count=record_count,
        )
