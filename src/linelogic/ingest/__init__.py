"""Data ingestion and persistence utilities.

This package provides local lake-style persistence under `data/`:
- Bronze: raw provider responses (JSON)
- Runs: manifests + metrics per execution

Silver/Gold layers are intentionally incremental and will be added as
normalizers/derivers mature.
"""

from __future__ import annotations

__all__ = [
    "BronzeWriter",
    "DataPaths",
    "RunContext",
]

from .bronze_writer import BronzeWriter
from .paths import DataPaths
from .run import RunContext
