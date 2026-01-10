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
    click.echo(f"✅ Config loaded")
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


@main.command()
@click.option("--sport", default="nba", help="Sport (nba, nfl, mlb)")
@click.option("--date", help="Date in YYYY-MM-DD format (default: today)")
def recommend(sport: str, date: str | None) -> None:
    """
    Generate recommendations for a date.

    NOT YET IMPLEMENTED (M1).
    """
    click.echo(f"🚧 recommend command coming in M1")
    click.echo(f"   Sport: {sport}")
    click.echo(f"   Date: {date or 'today'}")
    click.echo("\n   Stay tuned!")


@main.command()
@click.option("--start-date", required=True, help="Start date YYYY-MM-DD")
@click.option("--end-date", required=True, help="End date YYYY-MM-DD")
def backtest(start_date: str, end_date: str) -> None:
    """
    Run backtest on historical data.

    NOT YET IMPLEMENTED (M1).
    """
    click.echo(f"🚧 backtest command coming in M1")
    click.echo(f"   Period: {start_date} to {end_date}")
    click.echo("\n   Stay tuned!")


@main.command()
@click.option("--period", default="month", help="Report period (week, month, all)")
def report(period: str) -> None:
    """
    Generate performance report.

    NOT YET IMPLEMENTED (M1).
    """
    click.echo(f"🚧 report command coming in M1")
    click.echo(f"   Period: {period}")
    click.echo("\n   Stay tuned!")


if __name__ == "__main__":
    main()
