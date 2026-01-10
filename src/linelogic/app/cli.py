"""
LineLogic CLI.

Commands:
- check: System health check
- recommend: Generate recommendations (future)
- backtest: Run backtest (future)
- report: Generate performance report (future)
"""

import click

from linelogic.config.settings import settings
from linelogic.logging_config import logger  # noqa: F401 initializes logging
from linelogic.storage.sqlite import init_db


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """LineLogic: Math-driven sports prop analytics."""
    pass


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
        "  2. Generate recommendations: linelogic recommend --sport nba (coming soon)"
    )
    click.echo("  3. View docs: docs/")


@main.command("recommend-daily")
@click.option("--date", required=True, help="Date in YYYY-MM-DD format")
def recommend_daily(date: str) -> None:
    """
    Generate paper recommendations for a date.

    Fetches games, runs stub model, computes edge/stake, writes to SQLite.
    Mode must be 'paper' (controlled via .env MODE setting).
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
    except ValueError as exc:
        click.echo(f"❌ Error: {exc}")
    except Exception as exc:
        click.echo(f"❌ Unexpected error: {exc}")


@main.command("settle-daily")
@click.option("--date", required=True, help="Date in YYYY-MM-DD format")
def settle_daily(date: str) -> None:
    """
    Settle recommendations for a date (stub: ingest results, compute ROI/Kelly).

    This is a placeholder; integrate real sportsbook result feeds in v2+.
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
@click.option("--period", default="month", help="Report period (week, month, all)")
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
