# LineLogic

> **Math-driven sports prop analytics and decision support system**

LineLogic is a quantitative sports betting research platform focused on **NBA player props** (with extensibility to NFL, MLB, and MMA). It combines statistical modeling, odds analysis, and portfolio theory to identify +EV opportunities—purely for **paper trading and research** in this POC phase.

## What LineLogic Does

- ✅ Converts and normalizes odds across formats (American, Decimal, Implied Probability)
- ✅ Removes vig to estimate true/fair odds
- ✅ Calculates expected value and edge
- ✅ Implements Kelly Criterion and fractional Kelly for stake sizing
- ✅ Tracks recommendations, odds snapshots, and results in SQLite
- ✅ Provides evaluation metrics: Brier score, log loss, calibration, CLV
- ✅ Integrates swappable data providers with caching and rate limiting
- ✅ Supports BALLDONTLIE (free tier) and nba_api (research/backfill)

## What LineLogic Does NOT Do

- ❌ Auto-place bets (decision support only)
- ❌ Guarantee profits (all outputs are probabilistic estimates)
- ❌ Handle real money in POC phase (paper trading only)
- ❌ Provide financial or legal advice

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/linelogic.git
cd linelogic

# Set up development environment
make setup

# Activate virtual environment
source .venv/bin/activate

# Copy environment template
cp .env.example .env

# Edit .env to add API keys (optional for free tier)
```

### Running Tests

```bash
make test
make test-cov  # with coverage report
```

### CLI Usage

```bash
# Show help
linelogic --help

# System health check
linelogic check

# Generate recommendations for a date
linelogic recommend-daily --date 2026-01-15

# Settle yesterday's picks (run after games complete)
linelogic settle-daily --date 2026-01-14

# With email notifications (requires SENDGRID_API_KEY)
linelogic recommend-daily --date 2026-01-15 --email your.email@example.com
linelogic settle-daily --date 2026-01-14 --email your.email@example.com --no-email  # skip email

# View system logs
tail -50 .linelogic/daily_job.log
LOG_LEVEL=DEBUG linelogic recommend-daily --date 2026-01-15  # verbose logging
```

### Daily Automated Runs

LineLogic can run automatically every day without manual intervention:

- **Local (LaunchAgent)**: 9 AM daily on your Mac (laptop must be on)
  - [Setup Guide](docs/10_daily_scheduler.md)
  - Commands: `./scripts/linelogic-job.sh {start|stop|restart|status|logs|unload}`

- **Cloud (GitHub Actions)**: 9 AM UTC daily on GitHub servers (24/7, no laptop required)
  - [Setup Guide](docs/11_github_actions_scheduler.md)
  - Requires: BALLDONTLIE_API_KEY, ODDS_API_KEY secrets

- **Email Notifications**: Daily summaries with bankroll tracking and results
  - Requires: SendGrid free account (100 emails/day, sufficient for daily reports)
  - [Setup Guide](docs/12_email_setup.md)
  - Shows: Current bankroll, picks with edges, settlement outcomes and P&L

## Repository Structure

```
linelogic/
├── src/linelogic/          # Main package
│   ├── config/             # Settings, feature flags, API keys
│   ├── odds/               # Odds math, vig removal, EV calculations
│   ├── models/             # Statistical models and interfaces
│   ├── features/           # Feature engineering by sport
│   ├── eval/               # Metrics: Brier, log loss, calibration, CLV
│   ├── portfolio/          # Kelly criterion, stake sizing, exposure caps
│   ├── data/               # Provider architecture, caching, rate limiting
│   │   └── providers/      # BALLDONTLIE, nba_api, future providers
│   ├── storage/            # SQLite schema and repository layer
│   └── app/                # CLI and future Streamlit UI
├── tests/                  # Unit and integration tests
├── docs/                   # Comprehensive documentation
├── adr/                    # Architecture Decision Records
├── Makefile                # Development commands
├── pyproject.toml          # Project config and dependencies
└── .env.example            # Environment template
```

## Data Sources

### Sports Stats (Primary: NBA)

-**BALLDONTLIE** (free + paid tiers): ✅ Legal, compliant, primary NBA source
  - Free tier: 5 req/min, players/teams/games
  - All-Star ($5/mo): 30 req/min, player stats (required for M1)
  - Tier gating: paid endpoints raise `PaidTierRequiredError`
- **TheSportsDB**: Multi-sport fallback, non-commercial use OK
- **nflverse** (M2): Open-source NFL historical data
- **Retrosheet/Chadwick** (M2): Open-source MLB historical data

### Future Integrations

-Odds: The Odds API ($20/mo for M1)
- Weather: WeatherAPI (free, M2 for outdoor sports)
- Injuries: Manual checks (M0/M1), licensed feeds (M2+)
- Social/News: Twitter API, NewsAPI (M3)
- Licensed providers: Sportradar, Genius Sports (M4, $3k+/mo)

See [docs/04_data_sources.md](docs/04_data_sources.md) for details.
+
**⚠️ Legal Compliance:** nba_api removed due to NBA.com ToS violations. LineLogic uses only legally compliant data sources.

## Key Concepts

### Fair Odds and Vig

Sportsbooks embed a margin (vig) in their odds. LineLogic removes this to estimate the "true" probability and identify +EV opportunities.

### Expected Value (EV)

```
EV = (prob_win × payout) - (prob_loss × stake)
```

Positive EV = long-term profitable bet (on average).

### Kelly Criterion

Optimal stake sizing to maximize log wealth:

```
f* = (p × b - q) / b
```

Where `p` = win probability, `q` = 1 - p, `b` = payout ratio.

We use **fractional Kelly** (e.g., 0.25× Kelly) for risk management.

### Closing Line Value (CLV)

Did you beat the closing line? Measures whether your bet was placed at a better price than the final market price—a key long-term performance indicator.

## Development

### Code Quality

```bash
make format      # Format with ruff
make lint        # Lint with ruff
make type-check  # Type check with mypy
```

### Adding a New Provider

1. Implement `StatsProvider` ABC in [src/linelogic/data/providers/](src/linelogic/data/providers/)
2. Add tier gating and error handling
3. Use cache and rate limiter
4. Write mocked integration tests
5. Update [docs/04_data_sources.md](docs/04_data_sources.md)

### Running Pre-commit Hooks

```bash
pre-commit run --all-files
```

## Documentation

Comprehensive docs in `docs/`:

1. [Vision and Goals](docs/01_vision.md)
2. [Sports Strategy](docs/02_sports_strategy.md) (NBA, NFL, MLB, MMA)
3. [Math Foundations](docs/03_math_foundations.md) (odds, EV, Kelly, Sharpe)
4. [Data Sources](docs/04_data_sources.md) (providers, APIs, tiers)
5. [Backtesting and Paper Trading](docs/05_backtesting_and_paper_trading.md)
6. [Risks and Compliance](docs/06_risks_and_compliance.md)

Architecture decisions in `adr/`:

- [ADR 0001: Architecture](adr/0001_architecture.md)

## Roadmap

### M0 (Current - POC)

- ✅ Core math and odds utilities (vig removal, EV, Kelly sizing)
- ✅ Provider architecture with BALLDONTLIE + TheOddsAPI
- ✅ Real odds integration (9 sportsbooks)
- ✅ Storage layer and evaluation metrics
- ✅ CLI: recommend-daily, settle-daily commands
- ✅ Paper trading workflow (log picks, track results)
- ✅ Scheduled daily runs (LaunchAgent + GitHub Actions)
- ✅ Email notifications with bankroll tracking and settlement reports

### M1 (Next)

- [ ] Feature engineering for NBA player props
- [ ] Baseline statistical models (GLM, XGBoost on labeled picks)
- [ ] Calibration dashboard
- [ ] Backtest infrastructure

### M2 (Future)

- [ ] NFL/MLB props adapters
- [ ] Advanced models and ensemble methods
- [ ] Streamlit UI with live dashboard
- [ ] Multi-game correlation analysis
- [ ] Real money trading (with strict risk controls)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

See [SECURITY.md](SECURITY.md) for security policies and responsible disclosure.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Disclaimer

**LineLogic is for research and educational purposes only.** This is a proof-of-concept system for paper trading. All predictions are probabilistic estimates with inherent uncertainty. No guarantee of accuracy or profitability. Users are responsible for compliance with local laws. Not financial advice.

---

**Built with Python 3.11+ | Managed with uv | Tested with pytest**
