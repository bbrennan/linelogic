from __future__ import annotations

from pathlib import Path

from linelogic.ingest.bronze_writer import BronzeWriter


def test_bronze_writer_writes_response_and_manifest(tmp_path: Path) -> None:
    base_dir = tmp_path / "endpoint"
    writer = BronzeWriter(base_dir)

    result = writer.write_json(
        payload={"ok": True, "items": [1, 2, 3]},
        manifest={"provider": "test", "endpoint": "foo"},
    )

    assert result.response_path.exists()
    assert result.manifest_path.exists()
    assert result.record_count is None

    manifest = result.manifest_path.read_text(encoding="utf-8")
    assert '"provider": "test"' in manifest
    assert '"endpoint": "foo"' in manifest
    assert "written_at_utc" in manifest
