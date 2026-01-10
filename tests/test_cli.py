"""
CLI smoke tests.
"""

import sys
import types

from click.testing import CliRunner

from linelogic.app import cli


def test_cli_check_monkeypatched(monkeypatch, tmp_path):
    runner = CliRunner()

    # Point database to temp path to avoid touching real files
    monkeypatch.setattr(cli.settings, "database_path", str(tmp_path / "db.sqlite"))

    # Stub provider to avoid HTTP by replacing module import
    class FakeProvider:
        def __init__(self):
            self.called = True

        def get_teams(self):
            return []

    fake_module = types.SimpleNamespace(BalldontlieProvider=FakeProvider)
    monkeypatch.setitem(
        sys.modules, "linelogic.data.providers.balldontlie", fake_module
    )

    result = runner.invoke(cli.main, ["check"])

    assert result.exit_code == 0
    assert "System Check" in result.output or "System check" in result.output


def test_cli_check_db_error(monkeypatch, tmp_path):
    runner = CliRunner()

    monkeypatch.setattr(cli.settings, "database_path", str(tmp_path / "db.sqlite"))
    monkeypatch.setattr(
        cli, "init_db", lambda _path: (_ for _ in ()).throw(RuntimeError("db down"))
    )

    result = runner.invoke(cli.main, ["check"])

    assert result.exit_code == 0
    assert "Database error" in result.output


def test_cli_check_provider_error(monkeypatch, tmp_path):
    runner = CliRunner()

    monkeypatch.setattr(cli.settings, "database_path", str(tmp_path / "db.sqlite"))
    monkeypatch.setattr(cli, "init_db", lambda _path: None)

    class BadProvider:
        def __init__(self):
            self.called = True

        def get_teams(self):
            raise RuntimeError("api down")

    fake_module = types.SimpleNamespace(BalldontlieProvider=BadProvider)
    monkeypatch.setitem(
        sys.modules, "linelogic.data.providers.balldontlie", fake_module
    )

    result = runner.invoke(cli.main, ["check"])

    assert result.exit_code == 0
    assert "provider error" in result.output.lower()
    assert "api down" in result.output


def test_cli_placeholder_commands():
    runner = CliRunner()

    res_recommend = runner.invoke(cli.main, ["recommend", "--sport", "nba"])
    res_backtest = runner.invoke(
        cli.main, ["backtest", "--start-date", "2024-01-01", "--end-date", "2024-01-31"]
    )
    res_report = runner.invoke(cli.main, ["report", "--period", "week"])

    assert res_recommend.exit_code == 0
    assert res_backtest.exit_code == 0
    assert res_report.exit_code == 0
    # recommend command now points to recommend-daily, so check for that instead of "coming"
    assert "recommend-daily" in res_recommend.output.lower()
    assert "coming" in res_backtest.output.lower()
    assert "coming" in res_report.output.lower()
