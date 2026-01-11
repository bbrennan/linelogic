# ADR 0001: Architecture

**Status:** Accepted

**Date:** 2026-01-10

**Context:**

LineLogic is a sports prop analytics platform that must:

1. Support multiple sports (NBA, NFL, MLB, MMA)
2. Integrate multiple data providers (free and paid tiers)
3. Implement mathematical models (odds, EV, Kelly criterion)
4. Track recommendations and results for evaluation
5. Remain modular and testable
6. Allow easy experimentation with new models and features

**Decision:**

We adopt a **layered, provider-abstraction architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                     Application Layer                    │
│                  (CLI, Streamlit UI)                     │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                      Service Layer                       │
│         (Recommendation Engine, Backtesting)             │
└─────────────────────────────────────────────────────────┘
                            │
┌──────────────┬──────────────┬──────────────┬────────────┐
│   Models     │  Features    │  Evaluation  │ Portfolio  │
│  (Predict)   │  (Extract)   │  (Metrics)   │  (Size)    │
└──────────────┴──────────────┴──────────────┴────────────┘
                            │
┌──────────────────────────────┬──────────────────────────┐
│       Data Layer             │     Storage Layer        │
│  (Providers, Cache, Rate)    │   (SQLite, Repo)         │
└──────────────────────────────┴──────────────────────────┘
```

## Architecture Layers

### 1. Data Layer

**Responsibilities:**

- Fetch data from external APIs (sports stats, odds, weather)
- Cache responses to minimize API calls
- Rate limit to respect provider constraints
- Normalize data to internal schema

**Key Components:**

- **Provider Interface** (`StatsProvider` ABC)
  - Methods: `get_players()`, `get_teams()`, `get_games()`, `get_player_game_logs()`
  - Return types: Typed dicts or Pydantic models
  - Implementations: `BalldontlieProvider`, `NbaApiProvider`, etc.

- **Cache** (`src/linelogic/data/cache.py`)
  - SQLite-backed key-value store
  - Key: `{provider}:{endpoint}:{params_hash}`
  - Value: JSON response + timestamp + TTL

- **Rate Limiter** (`src/linelogic/data/rate_limit.py`)
  - Token bucket algorithm
  - Global and per-provider limits
  - Blocks or delays requests when limit reached

**Design Principles:**

- **Swappable providers**: Easy to add/remove providers via interface
- **Fail gracefully**: Raise clear exceptions for paid-tier endpoints
- **Idempotent**: Cache ensures same query returns same result within TTL

---

### 2. Storage Layer

**Responsibilities:**

- Persist recommendations, odds, results, model versions
- Provide repository pattern for queries
- Migrations for schema changes

**Key Components:**

- **Database** (`src/linelogic/storage/sqlite.py`)
  - `init_db()`: Create tables if not exist
  - Tables: `recommendations`, `odds_snapshots`, `results`, `model_versions`

- **Repositories** (future: `src/linelogic/storage/repositories/`)
  - `RecommendationRepo`: CRUD for recommendations
  - `ResultsRepo`: Match results to recommendations
  - `OddsRepo`: Track line movement

**Design Principles:**

- **Timestamp everything**: All rows have `created_at` or `captured_at`
- **Audit trail**: Store raw JSON payloads for debugging
- **Versioning**: Track model version for every recommendation

---

### 3. Math and Utilities

**Responsibilities:**

- Odds conversions (American, Decimal, Implied Prob)
- Vig removal
- Expected value and edge calculations
- Kelly criterion and portfolio sizing
- Evaluation metrics (Brier, CLV, calibration)

**Key Components:**

- **Odds** (`src/linelogic/odds/math.py`)
  - Pure functions (no side effects)
  - Comprehensive unit tests

- **Portfolio** (`src/linelogic/portfolio/`)
  - Kelly fraction calculation
  - Exposure caps (per bet, per game, per day)
  - Correlation heuristics (rule-based for M0)

- **Evaluation** (`src/linelogic/eval/`)
  - Brier score, log loss, calibration
  - CLV calculation
  - Reporting utilities

**Design Principles:**

- **Pure functions**: Easy to test and reason about
- **Type-safe**: All functions have type hints
- **Well-documented**: Docstrings with examples

---

### 4. Models and Features

**Responsibilities:**

- Feature engineering (player recent, opponent, context)
- Model training and prediction
- Model versioning and registry

**Key Components:**

- **Features** (`src/linelogic/features/`)
  - Sport-specific feature builders
  - `nba.py`: NBA player props features
  - `nfl.py`, `mlb.py`, `mma.py` (future)

- **Models** (`src/linelogic/models/`)
  - `BaseModel` interface: `predict(features) -> probability`
  - `BaselineModel`: Simple average + std dev
  - `GLMModel`: Generalized Linear Model (future)
  - `EnsembleModel`: Combine multiple models (future)

**Design Principles:**

- **Model registry**: Track versions, configs, performance
- **Serializable**: Save/load models for reproducibility
- **Sport-agnostic interface**: Same API across sports

---

### 5. Service Layer

**Responsibilities:**

- Orchestrate end-to-end workflows
- Generate recommendations
- Run backtests
- Evaluate performance

**Key Components:**

- **Recommendation Engine** (`src/linelogic/services/recommend.py` - future)
  - Fetch games for date
  - Generate features
  - Run model
  - Compare to market
  - Apply portfolio rules
  - Log recommendation

- **Backtester** (`src/linelogic/services/backtest.py` - future)
  - Load historical data
  - Walk-forward validation
  - Generate report

**Design Principles:**

- **Stateless**: No shared mutable state
- **Testable**: Mock data layer, test logic
- **Configurable**: Inject dependencies (providers, models, storage)

---

### 6. Application Layer

**Responsibilities:**

- User interface (CLI, web app)
- Input validation
- Output formatting

**Key Components:**

- **CLI** (`src/linelogic/app/cli.py`)
  - Commands: `check`, `recommend`, `backtest`, `report`
  - Uses Click library

- **Streamlit** (`app/app.py`)
  - Dashboard: Bankroll, P&L, calibration plots
  - Recommendation viewer
  - Manual bet logger

**Design Principles:**

- **Thin layer**: Business logic in services, not UI
- **User-friendly**: Clear error messages, helpful prompts

---

## Key Design Decisions

### Decision 1: SQLite for Storage

**Alternatives:**

- PostgreSQL (more scalable)
- MongoDB (document store)
- CSV files (simplest)

**Rationale:**

- SQLite is **file-based** (no server setup)
- **ACID-compliant** (data integrity)
- **Fast enough** for M0-M2 (millions of rows)
- **Easy backup** (copy .db file)
- Can migrate to Postgres if scale requires (same SQL interface)

**Trade-offs:**

- Not suitable for high concurrency (fine for single-user POC)
- No replication (fine for local-first approach)

---

### Decision 2: Provider Abstraction

**Alternatives:**

- Hardcode BALLDONTLIE calls throughout codebase
- Use a generic HTTP client (requests) everywhere

**Rationale:**

- **Swappable providers** = no vendor lock-in
- **Testable**: Mock provider in tests
- **Graceful degradation**: Try provider A, fallback to B
- **Tier gating**: Clear errors when free tier insufficient

**Trade-offs:**

- Extra boilerplate (abstract class + implementations)
- Slightly more complex (worth it for flexibility)

---

### Decision 3: Cache + Rate Limiting

**Alternatives:**

- No caching (always hit API)
- No rate limiting (risk IP bans)

**Rationale:**

- **Caching reduces API costs** (especially on paid tiers)
- **Rate limiting prevents bans** (respectful to providers)
- **Faster responses** (cache hits are instant)

**Implementation:**

- SQLite-backed cache (simple, persistent)
- Token bucket rate limiter (industry standard)

**Trade-offs:**

- Stale data risk (mitigated by TTL)
- Extra complexity (worth it for reliability)

---

### Decision 4: Fractional Kelly (0.25) Default

**Alternatives:**

- Full Kelly (maximize growth)
- Fixed stake (e.g., always $100)
- Proportional betting (e.g., 2% of bankroll)

**Rationale:**

- **Full Kelly is too aggressive** (high variance, large drawdowns)
- **Fractional Kelly (0.25) balances growth and risk**
- **Fixed stakes ignore bankroll size** (inefficient)
- **Proportional betting ignores edge** (bet same on 51% and 60%)

**Trade-offs:**

- Slower bankroll growth than full Kelly
- More conservative (acceptable for POC)

---

### Decision 5: Paper Trading in POC

**Alternatives:**

- Real money from day 1
- Simulation only (no live tracking)

**Rationale:**

- **Validate model before risking capital**
- **Learn operational workflow** (data → model → bet → result)
- **Build confidence** (prove to yourself it works)

**Trade-offs:**

- Delayed gratification (no real profits yet)
- Execution risk not tested (paper trading is easier than real)

---

## Data Flow Example: Generating a Recommendation

**User action:** `linelogic recommend --sport nba --date 2026-01-15`

**Flow:**

1. **CLI** parses command, calls `RecommendationService.generate()`
2. **Service** fetches games for date from `BalldontlieProvider`
3. **Provider** checks cache → cache miss → HTTP request → store in cache → return games
4. **Service** loops through games, fetches player stats
5. **Provider** checks cache → cache hit → return from cache (no HTTP)
6. **Feature Builder** generates features (player recent, opponent defense, etc.)
7. **Model** predicts probability for each prop (e.g., "LeBron Over 25.5" → 60%)
8. **Odds Module** converts market line to implied prob, removes vig → 50%
9. **Edge** = 60% - 50% = 10% (above threshold)
10. **Portfolio** calculates Kelly stake, applies exposure caps
11. **Storage** logs recommendation to `recommendations` table
12. **CLI** displays recommendation to user

---

## Testing Strategy

### Unit Tests

- All math functions (odds, Kelly, Brier, etc.)
- Cache hit/miss/expire logic
- Rate limiter token bucket behavior
- Feature builders (given input, expect output)

### Integration Tests

- Provider mocking (use `responses` library)
- Cache + rate limiter integration
- End-to-end: Data → features → model → recommendation

### Backtest Tests

- Reproduce known backtest result
- Test walk-forward cross-validation
- Test leakage detection (should fail if future data used)

---

## Configuration Management

**Environment variables** (`.env`):

```
BALLDONTLIE_API_KEY=<key>
BALLDONTLIE_TIER=free
BALLDONTLIE_RPM=5
USE_NBA_API=false
CACHE_TTL_SECONDS=86400
DATABASE_PATH=.linelogic/linelogic.db
```

**Pydantic Settings** (`src/linelogic/config/settings.py`):

- Load from `.env`
- Validate types and required fields
- Provide defaults

**Feature Flags:**

- `USE_NBA_API`: Enable/disable nba_api provider
- `ENABLE_TWITTER`: Enable/disable Twitter sentiment (future)

---

## Deployment (Future)

**M0 (Local):**

- Run on developer's laptop
- SQLite file stored in `.linelogic/`

**M1 (VPS):**

- Deploy to DigitalOcean or AWS EC2
- Daily cron job for backfills
- Streamlit app on port 8501

**M2 (Managed):**

- RDS for PostgreSQL (migrate from SQLite)
- S3 for raw API responses
- ECS/Fargate for services
- CloudWatch for monitoring

---

## Security Considerations

1. **API Keys**: Stored in `.env`, never committed
2. **SQLite file**: Contains no PII, but treat as sensitive
3. **Logs**: Sanitize logs (no API keys, no personal data)
4. **Backups**: Encrypt backups if uploaded to cloud

---

## Scalability Considerations

**M0-M1:**

- Single-user, local-first
- SQLite sufficient (handle millions of rows)

**M2:**

- Multi-user or high concurrency
- Migrate to PostgreSQL
- Consider Redis for caching (faster than SQLite cache)

**M3:**

- Distributed system (multiple services)
- Microservices for data, models, API
- Kubernetes for orchestration (if needed)

---

## Consequences

**Positive:**

- ✅ Clean separation of concerns (easy to reason about)
- ✅ Testable (mock providers, test logic independently)
- ✅ Extensible (add sports, providers, models without refactoring)
- ✅ Maintainable (clear boundaries, minimal coupling)

**Negative:**

- ⚠️ More boilerplate (abstractions add code)
- ⚠️ Over-engineering risk (YAGNI for features we don't need yet)

**Mitigation:**

- Start simple (baseline models, basic features)
- Add complexity only when justified
- Document decisions in ADRs (like this one)

---

## Future Decisions

- **ADR 0002**: Model Selection (GLM vs. XGBoost vs. Ensemble)
- **ADR 0003**: Feature Store (if we build one)
- **ADR 0004**: Real-Time Odds Tracking (WebSocket vs. Polling)
- **ADR 0005**: Multi-Sport Correlation Modeling

---

**Authors:** LineLogic Core Team

**Reviewed by:** (future: add reviewers)

**Status:** Accepted
