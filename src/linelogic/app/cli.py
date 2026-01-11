"""
LineLogic CLI.

Commands:
- check: System health check
- recommend: Generate recommendations (future)
- backtest: Run backtest (future)
- report: Generate performance report (future)
"""

import os

import click

from linelogic.config.settings import settings
from linelogic.logging_config import logger  # noqa: F401 initializes logging
from linelogic.storage.sqlite import init_db


DEFAULT_TO_EMAIL = os.getenv("TO_EMAIL", "")


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """LineLogic: Math-driven sports prop analytics."""
    pass


@main.group()
def ingest() -> None:
    """Ingest and persist raw provider data (local)."""
    pass


@ingest.command("daily")
@click.option("--sport", default="basketball_nba", show_default=True)
@click.option("--date", "date_str", required=True, help="Date in YYYY-MM-DD")
@click.option(
    "--data-dir",
    default="./data",
    show_default=True,
    help="Root directory for bronze/silver/gold storage",
)
def ingest_daily(sport: str, date_str: str, data_dir: str) -> None:
    """Ingest daily BDL games and (optionally) an Odds API snapshot."""

    from pathlib import Path

    from linelogic.config.settings import settings
    from linelogic.data.providers.balldontlie import BalldontlieProvider
    from linelogic.data.providers.odds import TheOddsAPIProvider
    from linelogic.ingest.bronze_writer import BronzeWriter
    from linelogic.ingest.paths import DataPaths
    from linelogic.ingest.run import RunContext

    paths = DataPaths(root=Path(data_dir))
    paths.ensure()

    run = RunContext.create()
    run_dir = paths.run_dir(run.date, run.run_id)

    run.write_run_config(
        run_dir,
        {
            "command": "ingest daily",
            "sport": sport,
            "date": date_str,
            "data_dir": str(Path(data_dir).resolve()),
        },
    )

    metrics: dict[str, int] = {
        "bronze_writes": 0,
        "oddsapi_calls": 0,
        "balldontlie_calls": 0,
    }

    # BALLDONTLIE: daily games
    bdl = BalldontlieProvider()
    games = bdl.get_games(date_str)
    metrics["balldontlie_calls"] += 1
    bdl_endpoint_dir = paths.bronze_run_dir(
        provider="balldontlie",
        sport=sport,
        date=date_str,
        run_id=run.run_id,
        endpoint="games",
    )
    bdl_result = BronzeWriter(bdl_endpoint_dir).write_json(
        payload=games,
        manifest={
            "provider": "balldontlie",
            "endpoint": "games",
            "sport": sport,
            "date": date_str,
            "run_id": run.run_id,
        },
    )
    metrics["bronze_writes"] += 1
    click.echo(f"✅ BDL games written: {bdl_result.response_path}")

    # The Odds API: current odds snapshot (skip if no key)
    if settings.odds_api_key:
        odds = TheOddsAPIProvider()
        odds_data = odds.get_game_odds(
            _sport=sport,
            markets="h2h,spreads,totals",
        )
        metrics["oddsapi_calls"] += 1
        odds_endpoint_dir = paths.bronze_run_dir(
            provider="oddsapi",
            sport=sport,
            date=date_str,
            run_id=run.run_id,
            endpoint=f"sports/{sport}/odds",
        )
        odds_result = BronzeWriter(odds_endpoint_dir).write_json(
            payload=odds_data,
            manifest={
                "provider": "oddsapi",
                "endpoint": f"sports/{sport}/odds",
                "sport": sport,
                "date": date_str,
                "run_id": run.run_id,
            },
        )
        metrics["bronze_writes"] += 1
        click.echo(f"✅ Odds snapshot written: {odds_result.response_path}")
    else:
        click.echo("⚠️  ODDS_API_KEY not set; skipping odds ingestion")

    run.write_run_summary(
        run_dir,
        {
            "status": "ok",
            "sport": sport,
            "date": date_str,
        },
    )
    run.write_metrics(run_dir, metrics)
    click.echo(f"🧾 Run manifest written under: {run_dir}")


@main.command()
def check() -> None:
    """
    Run system health check.

    Verifies:
    - Database initialization
    - Configuration loading
    - Provider availability
    """
    click.echo("🏀 LineLogic System Check")
    click.echo("=" * 50)

    # Check database
    try:
        init_db(settings.database_path)
        click.echo(f"✅ Database initialized: {settings.database_path}")
    except Exception as e:
        click.echo(f"❌ Database error: {e}")
        return

    # Check configuration
    click.echo("✅ Config loaded")
    click.echo(f"   - Mode: {settings.mode}")
    click.echo(f"   - BALLDONTLIE tier: {settings.balldontlie_tier}")
    click.echo(f"   - Rate limit: {settings.balldontlie_rpm} rpm")
    click.echo(f"   - Cache TTL: {settings.cache_ttl_seconds}s")

    # Check providers
    try:
        from linelogic.data.providers.balldontlie import BalldontlieProvider

        provider = BalldontlieProvider()
        click.echo("✅ BALLDONTLIE provider initialized")

        # Test basic request (teams - should work on free tier)
        teams = provider.get_teams()
        click.echo(f"✅ BALLDONTLIE API working ({len(teams)} teams fetched)")
    except Exception as e:
        click.echo(f"⚠️  BALLDONTLIE provider error: {e}")

    click.echo("=" * 50)
    click.echo("✅ System check complete!")
    click.echo("\nNext steps:")
    click.echo("  1. Run tests: make test")
    click.echo(
        "  2. Generate recommendations: linelogic recommend --sport nba "
        "(coming soon)"
    )
    click.echo("  3. View docs: docs/")


@main.command("recommend-daily")
@click.option("--date", required=True, help="Date in YYYY-MM-DD format")
@click.option(
    "--email",
    default=DEFAULT_TO_EMAIL,
    help="Email to send summary to (default: TO_EMAIL env var)",
)
@click.option("--no-email", is_flag=True, help="Skip email sending")
def recommend_daily(date: str, email: str, no_email: bool) -> None:
    """
    Generate paper recommendations for a date.

    Fetches games, runs stub model, computes edge/stake, writes to SQLite.
    Mode must be 'paper' (controlled via .env MODE setting).
    Optionally sends HTML email summary with bankroll and picks.
    """
    try:
        from linelogic.app.recommend import RecommendationEngine

        engine = RecommendationEngine()
        result = engine.recommend_date(date)

        click.echo(f"📊 Recommendations for {date}:")
        click.echo(f"   Count: {result['count']}")
        click.echo(f"   Total Staked: ${result['total_staked']:.2f}")
        click.echo(f"   Avg Edge: {result['avg_edge']:.2%}")

        if result["recommendations"]:
            click.echo("\n   Picks:")
            for rec in result["recommendations"]:
                click.echo(
                    f"     • {rec['selection']}: "
                    f"model={rec['model_prob']:.1%}, edge={rec['edge']:.2%}, "
                    f"stake=${rec['stake']:.0f}"
                )
        else:
            click.echo("   No picks generated (no +edge bets found)")

        click.echo("\n✅ Recommendations saved to database")

        # Send email summary if requested
        if not no_email and email and result["count"] > 0:
            try:
                from linelogic.eval.summary import SummaryGenerator
                from linelogic.email_router import get_email_sender

                summary_gen = SummaryGenerator()
                html_email, _ = summary_gen.generate_html_summary(
                    date,
                    date,
                )
                summary_gen.close()

                sender = get_email_sender()
                if sender.send_email(
                    to_email=email,
                    subject=f"LineLogic Daily Picks - {date}",
                    html_content=html_email,
                ):
                    click.echo(f"📧 Summary emailed to {email}")
                else:
                    click.echo("⚠️  Email send failed")
            except ValueError as exc:
                click.echo(f"⚠️  Email skipped: {exc}")
            except Exception as exc:
                click.echo(f"⚠️  Email error: {exc}")
        elif not no_email and not email:
            click.echo("⚠️  Email skipped: set TO_EMAIL or pass --email")

    except ValueError as exc:
        click.echo(f"❌ Error: {exc}")
    except Exception as exc:
        click.echo(f"❌ Unexpected error: {exc}")


@main.command("settle-daily")
@click.option("--date", required=True, help="Date in YYYY-MM-DD format")
@click.option(
    "--email",
    default=DEFAULT_TO_EMAIL,
    help="Email to send summary to (default: TO_EMAIL env var)",
)
@click.option("--no-email", is_flag=True, help="Skip email sending")
def settle_daily(date: str, email: str, no_email: bool) -> None:
    """
    Settle recommendations for a date.

    Stub: ingest results, compute ROI/Kelly.

    This is a placeholder; integrate real sportsbook result feeds in v2+.
    Optionally sends HTML email summary with settlement results and bankroll.
    """
    try:
        from linelogic.app.settle import SettlementEngine

        engine = SettlementEngine()
        result = engine.stub_settle_results(date)

        click.echo(f"📈 Settlement for {date}:")
        click.echo(f"   Settled: {result['settled_count']}")
        click.echo(f"   Total P&L: ${result['total_pnl']:.2f}")
        click.echo(f"   ROI: {result['roi_percent']:.2%}")

        click.echo("\n✅ Results saved to database")

        # Send email summary if requested
        if not no_email and email and result["settled_count"] > 0:
            try:
                from linelogic.eval.summary import SummaryGenerator
                from linelogic.email_router import get_email_sender
                from datetime import datetime, timedelta

                yesterday = (
                    datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)
                ).strftime("%Y-%m-%d")

                summary_gen = SummaryGenerator()
                _, html_email = summary_gen.generate_html_summary(
                    date,
                    yesterday,
                )
                summary_gen.close()

                sender = get_email_sender()
                if sender.send_email(
                    to_email=email,
                    subject=f"LineLogic Settlement Report - {yesterday}",
                    html_content=html_email,
                ):
                    click.echo(f"📧 Summary emailed to {email}")
                else:
                    click.echo("⚠️  Email send failed")
            except ValueError as exc:
                click.echo(f"⚠️  Email skipped: {exc}")
            except Exception as exc:
                click.echo(f"⚠️  Email error: {exc}")
        elif not no_email and not email:
            click.echo("⚠️  Email skipped: set TO_EMAIL or pass --email")
    except Exception as exc:
        click.echo(f"❌ Error: {exc}")


@main.command()
@click.option("--sport", default="nba", help="Sport (nba, nfl, mlb)")
@click.option("--date", help="Date in YYYY-MM-DD format (default: today)")
def recommend(sport: str, date: str | None) -> None:
    """
    Generate recommendations for a date.

    DEPRECATED: Use 'recommend-daily' instead.
    """
    click.echo("🚧 Use 'linelogic recommend-daily --date YYYY-MM-DD' instead")
    click.echo(f"   Sport: {sport}")
    click.echo(f"   Date: {date or 'today'}")


@main.command("weekly-summary")
@click.option(
    "--date",
    required=True,
    help="End date in YYYY-MM-DD format (typically today)",
)
@click.option(
    "--email",
    default=DEFAULT_TO_EMAIL,
    help="Email to send summary to (default: TO_EMAIL env var)",
)
@click.option("--no-email", is_flag=True, help="Skip email sending")
def weekly_summary(date: str, email: str, no_email: bool) -> None:
    """
    Generate comprehensive weekly analysis report.

    Analyzes:
    - Results trends (W-L, ROI, P&L trajectory)
    - Edge distribution and statistics
    - Team performance patterns
    - Odds correlations
    - Bankroll growth
    - Confidence metrics and statistical significance
    - Hypotheses for feature engineering
    """
    try:
        from linelogic.eval.weekly_summary import WeeklySummaryGenerator

        gen = WeeklySummaryGenerator()
        html_report = gen.generate_html_weekly_report(date)
        gen.close()

        click.echo(f"📊 Weekly Analysis Report for {date}")
        click.echo("=" * 50)

        # Parse dates for display
        from datetime import datetime, timedelta

        end_date = datetime.strptime(date, "%Y-%m-%d")
        start_date = end_date - timedelta(days=6)

        click.echo(f"Period: {start_date.strftime('%Y-%m-%d')} to {date}")
        click.echo("✅ Report generated")

        # Send email if requested
        if not no_email and email:
            try:
                from linelogic.email_router import get_email_sender

                sender = get_email_sender()
                subject = (
                    "LineLogic Weekly Analysis - Week of "
                    f"{start_date.strftime('%Y-%m-%d')}"
                )
                if sender.send_email(
                    to_email=email,
                    subject=subject,
                    html_content=html_report,
                ):
                    click.echo(f"📧 Report emailed to {email}")
                else:
                    click.echo("⚠️  Email send failed")
            except ValueError as exc:
                click.echo(f"⚠️  Email skipped: {exc}")
            except Exception as exc:
                click.echo(f"⚠️  Email error: {exc}")
        elif not no_email and not email:
            click.echo("⚠️  Email skipped: set TO_EMAIL or pass --email")

        click.echo("=" * 50)
        click.echo("\nKey sections in email:")
        click.echo("  • Results summary (W-L, ROI, P&L)")
        click.echo("  • Edge distribution analysis")
        click.echo("  • Team performance breakdown")
        click.echo("  • Odds patterns and correlations")
        click.echo("  • Bankroll trajectory")
        click.echo("  • Hypotheses for feature engineering")
        click.echo("  • Statistical confidence metrics")

    except Exception as exc:
        click.echo(f"❌ Error: {exc}")


@main.command()
@click.option("--start-date", required=True, help="Start date YYYY-MM-DD")
@click.option("--end-date", required=True, help="End date YYYY-MM-DD")
def backtest(start_date: str, end_date: str) -> None:
    """
    Run backtest on historical data.

    NOT YET IMPLEMENTED (M1).
    """
    click.echo("🚧 backtest command coming in M1")
    click.echo(f"   Period: {start_date} to {end_date}")
    click.echo("\n   Stay tuned!")


@main.command()
@click.option(
    "--period",
    default="month",
    help="Report period (week, month, all)",
)
def report(period: str) -> None:
    """
    Generate performance report.

    NOT YET IMPLEMENTED (M1).
    """
    click.echo("🚧 report command coming in M1")
    click.echo(f"   Period: {period}")
    click.echo("\n   Stay tuned!")


if __name__ == "__main__":
    main()
