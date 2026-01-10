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

# Run smoke test (future)
linelogic check

# Generate recommendations (future)
linelogic recommend --sport nba --date 2026-01-15
```

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

- **BALLDONTLIE** (free tier): Players, teams, games
  - Rate limit: 5 req/min
  - Tier gating: paid endpoints raise `PaidTierRequiredError`
- **nba_api** (optional): Behind `USE_NBA_API` flag for research/backfill
  - Unofficial scraper, use with caution

### Future Integrations

- Odds: The Odds API, BetOnline, Pinnacle
- Weather: WeatherAPI, OpenWeather
- Injuries: ESPN, CBS, team sources
- Social/News: Twitter API, news aggregators
- Scheduling: NBA API, ESPN

See [docs/04_data_sources.md](docs/04_data_sources.md) for details.

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

### M0 (Current)

- ✅ Core math and odds utilities
- ✅ Provider architecture with BALLDONTLIE + nba_api
- ✅ Storage layer and evaluation metrics
- 🚧 Basic CLI

### M1 (Next)

- [ ] Feature engineering for NBA player props
- [ ] Baseline statistical models (simple over/under)
- [ ] Paper trading workflow (log picks, track results)
- [ ] Calibration dashboard

### M2 (Future)

- [ ] NFL props adapter
- [ ] Advanced models (GLM, XGBoost)
- [ ] Streamlit UI
- [ ] Multi-game correlation analysis
- [ ] Automated daily reports

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
