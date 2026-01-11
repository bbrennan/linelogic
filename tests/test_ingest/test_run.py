from __future__ import annotations

from pathlib import Path

from linelogic.ingest.run import RunContext


def test_run_context_writes_files(tmp_path: Path) -> None:
    run = RunContext.create()
    run_dir = tmp_path / "runs" / run.date / f"run_id={run.run_id}"

    cfg = run.write_run_config(run_dir, {"a": 1})
    summary = run.write_run_summary(run_dir, {"b": 2})
    metrics = run.write_metrics(run_dir, {"c": 3})

    assert cfg.exists()
    assert summary.exists()
    assert metrics.exists()
