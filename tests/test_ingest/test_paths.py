from __future__ import annotations

from pathlib import Path

from linelogic.ingest.paths import DataPaths


def test_data_paths_layout(tmp_path: Path) -> None:
    repo_root = tmp_path
    paths = DataPaths.from_repo_root(repo_root)
    paths.ensure()

    assert paths.root == repo_root / "data"
    assert paths.bronze_root.exists()
    assert paths.runs_root.exists()

    run_dir = paths.bronze_run_dir(
        provider="oddsapi",
        sport="basketball_nba",
        date="2026-01-11",
        run_id="abc",
        endpoint="/sports/basketball_nba/odds",
    )
    # endpoint should be normalized (slashes removed)
    assert "sports_basketball_nba_odds" in run_dir.as_posix()
    assert "/sports/basketball_nba/odds" not in run_dir.as_posix()
