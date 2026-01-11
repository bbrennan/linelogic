# Data Sources

## Overview

LineLogic requires **high-quality, timely data** across multiple domains: sports stats, odds/lines, weather, injuries, news/social sentiment, and venue information. This document catalogs all target data sources and integration strategies.

## Key Principles

1. **Swappable providers**: Never lock into one API
2. **Tier awareness**: Free vs. paid endpoints
3. **Caching**: Minimize API calls
4. **Rate limiting**: Respect provider limits
5. **Failure gracefully**: Degrade to fallback sources

---

## Sports Stats

### Primary: NBA

#### BALLDONTLIE (Free Tier)

**API:** https://www.balldontlie.io

**Tiers:**

- **Free**: 5 requests/minute, players/teams/games endpoints
- **All-Star ($5/mo)**: 30 req/min, player stats, season averages, injuries
- **MVP ($15/mo)**: 60 req/min, advanced stats, play-by-play

**Available on Free:**

- `/players` - All NBA players (name, team, position)
- `/teams` - All NBA teams
- `/games` - Game schedules, scores, status

**Paid tier required:**

- `/stats` - Player game logs
- `/season_averages` - Season stats per player
- `/injuries` - Injury reports (future)

**Integration:**

- Implemented in `src/linelogic/data/providers/balldontlie.py`
- Tier gating: Raise `PaidTierRequiredError` for paid endpoints on free tier
- Cache: 24h TTL for players/teams, 1h for games
- Rate limit: 5 rpm global

**Limitations:**

- Free tier lacks player game stats (critical for modeling)
- No advanced stats (usage, TS%, etc.) on any tier
- No play-by-play data

**Mitigation:**

- Use for POC scaffolding and basic game schedules
- Upgrade to All-Star ($5/mo) for M1 when modeling begins
- Use `nba_api` for backfill/research (see below)

---

#### nba_api (Unofficial)

**Library:** https://github.com/swar/nba_api

**Pros:**

- Free, unlimited (no API key)
- Rich data: advanced stats, play-by-play, tracking data
- Historical data back to 1996

**Cons:**

- **Unofficial scraper**: Violates NBA.com ToS (use at own risk)
- **No SLA**: Can break without notice
- **Rate limiting unclear**: Anecdotal reports of IP bans if too aggressive

**Available:**

- Player career stats
- Team stats
- Game logs (all historical)
- Advanced stats (usage, TS%, PER, etc.)
- Tracking data (shot charts, hustle stats)

**Integration:**

- Implemented in `src/linelogic/data/providers/nba_api_provider.py`
- Behind feature flag: `USE_NBA_API=false` by default
- Use sparingly: For backfills and historical analysis, NOT real-time
- Respect delays: Add 1-2 second delays between requests

**Recommended Use:**

- Historical backtesting (train models on 2022-2024 seasons)
- One-time backfills (download full season, cache locally)
- Fallback for missing BALLDONTLIE data

**NOT for:**

- Daily production use
- Real-time odds tracking
- High-frequency requests

---

#### Future: NBA Official API

**Status:** Not yet available for third-party developers.

**If/when available:**

- Replace `nba_api` for production
- Likely paid tier
- Update provider interface in `src/linelogic/data/providers/nba_official.py`

---

### NFL (M2+)

**Target Providers:**

1. **ESPN API** (unofficial)
   - Free, public endpoints
   - Game schedules, scores, basic stats
   - Similar risks to `nba_api`

2. **Pro Football Reference** (scraping)
   - Rich historical data
   - Requires rate-limited scraping (respect robots.txt)
   - Use as backfill only

3. **Sportradar** (paid)
   - Official NFL partner
   - Real-time stats, play-by-play
   - Expensive (~$1000+/year for basic tier)

**Recommendation:**

- Start with ESPN API (free, unofficial)
- Upgrade to Sportradar if POC proves profitable

---

### MLB (M2+)

**Target Providers:**

1. **MLB Stats API** (official, free-ish)
   - https://statsapi.mlb.com
   - Game schedules, scores, player stats
   - Undocumented but stable

2. **Statcast** (official, free)
   - https://baseballsavant.mlb.com
   - Advanced metrics (exit velocity, spin rate, xwOBA)
   - CSV downloads available

3. **Sportradar** (paid)
   - Real-time stats, pitch-by-pitch data

**Recommendation:**

- MLB Stats API + Statcast for M2
- Scraping-friendly, no rate limits observed

---

### MMA (M3+)

**Target Providers:**

1. **UFC Stats** (official, scraping)
   - http://ufcstats.com
   - Fight results, fighter stats
   - Must scrape HTML (no API)

2. **Tapology** (scraping)
   - Upcoming fight schedules
   - Fighter rankings
   - Must scrape HTML

3. **Manual tracking**
   - Google Sheets or Airtable
   - Track training camps, weight cuts, etc.

**Recommendation:**

- Manual scraping + database
- Low volume (few fights per week) makes manual feasible

---

## Odds and Lines

### Primary: The Odds API

**API:** https://the-odds-api.com

**Tiers:**

- **Free**: 500 requests/month
- **Basic ($20/mo)**: 10,000 requests/month
- **Pro ($50/mo)**: 50,000 requests/month

**Coverage:**

- 30+ sportsbooks (DraftKings, FanDuel, BetMGM, etc.)
- Moneylines, spreads, totals, player props
- Real-time odds updates
- Historical odds (limited on free tier)

**Integration:**

- Future: `src/linelogic/data/providers/odds_api_provider.py`
- Cache: 5-minute TTL for live odds
- Rate limit: Depends on tier (500 req/month = ~16/day)

**Limitations:**

- Free tier is insufficient for daily production
- Upgrade to Basic ($20/mo) recommended for M1

---

### Alternative: BetOnline / Pinnacle

**BetOnline:**

- No official API
- Scraping required (violates ToS)

**Pinnacle:**

- Official API for data feed (not betting)
- Best for "sharp" closing lines (use as benchmark)
- Requires approval + paid subscription

**Recommendation:**

- Use The Odds API for M0-M1
- Add Pinnacle closing lines for CLV evaluation (M2+)

---

## Weather

### WeatherAPI

**API:** https://www.weatherapi.com

**Tiers:**

- **Free**: 1M calls/month
- **Pro ($4/mo)**: 5M calls/month

**Coverage:**

- Current weather, forecasts (7 days)
- Historical weather (last 7 days on free)
- Wind speed/direction, humidity, temperature

**Use Cases:**

- NFL: Wind >15 mph affects passing
- MLB: Wind direction affects home runs, temperature affects ball flight
- NBA: N/A (indoor)

**Integration:**

- `src/linelogic/data/providers/weather_provider.py`
- Cache: 1h TTL for forecasts, 24h for historical

---

### Alternative: OpenWeather

**API:** https://openweathermap.org

**Tiers:**

- **Free**: 1000 calls/day
- **Startup ($40/mo)**: 100,000 calls/day

**Similar features to WeatherAPI.**

**Recommendation:**

- Start with WeatherAPI (free tier sufficient)

---

## Injuries

### ESPN Injury Report (Scraping)

**Source:** https://www.espn.com/nba/injuries

**Pros:**

- Free, public
- Updated frequently

**Cons:**

- Must scrape HTML
- No official API

**Integration:**

- `src/linelogic/data/providers/injury_scraper.py`
- Daily scraping (run once per day)
- Cache: 24h TTL

---

### Alternative: Rotoworld / Official Team Sources

**Rotoworld:**

- https://www.rotoworld.com
- Similar to ESPN

**Official Team Sources:**

- Twitter accounts, team websites
- Real-time updates (but unstructured)

**Recommendation:**

- ESPN scraping for M0-M1
- Add Twitter monitoring (future) for real-time alerts

---

## Social Media and News Sentiment

### Twitter API (X API)

**API:** https://developer.twitter.com

**Tiers:**

- **Free**: Read-only, 1500 tweets/month (severely limited)
- **Basic ($100/mo)**: 10,000 tweets/month, write access
- **Pro ($5000/mo)**: 1M tweets/month

**Use Cases:**

- Injury news (before official reports)
- Sentiment analysis (public betting bias)
- Line movement triggers (steam, reverse line movement)

**Challenges:**

- Free tier is insufficient
- Basic tier ($100/mo) expensive for POC
- NLP required to extract signal from noise

**Recommendation:**

- Defer to M2+
- Start with manual monitoring of key accounts (e.g., @ShamsCharania, @wojespn)

---

### News Aggregators

**NewsAPI:**

- https://newsapi.org
- **Free**: 100 requests/day
- Coverage: ESPN, CBS Sports, etc.

**Google News RSS:**

- Free, no API key
- Simple RSS feeds by keyword

**Recommendation:**

- NewsAPI for structured news (M2)
- RSS feeds for manual monitoring (M0)

---

## Scheduling and Venue Data

### NBA Schedules

**Source:** BALLDONTLIE `/games` endpoint

**Coverage:**

- Game schedules
- Start times
- Home/away teams
- Arena info (future)

**Integration:**

- Already in `BalldontlieProvider`

---

### Venue Effects

**Source:** Manual database

**Data:**

- Arena altitude (Denver = 5280 ft, affects cardio)
- Court dimensions (not standardized across venues)
- Travel distance (back-to-backs with cross-country flights)

**Integration:**

- Static JSON file: `src/linelogic/data/static/venues.json`
- Load at startup

---

## Backtesting and Historical Data

### Data Lake Strategy

**Problem:** Need 2+ years of data for training and backtesting.

**Solution:**

1. **One-time backfill:**
   - Use `nba_api` to download 2022-2024 seasons
   - Store in local SQLite or Parquet files
   - Never re-fetch (static historical data)

2. **Daily incremental:**
   - Fetch yesterday's games + results
   - Append to local database

3. **Caching:**
   - Cache all API responses (raw JSON) for audit trail

**Schema:**

```sql
CREATE TABLE games_history (
    game_id TEXT PRIMARY KEY,
    date TEXT,
    home_team TEXT,
    away_team TEXT,
    home_score INTEGER,
    away_score INTEGER,
    raw_json TEXT
);

CREATE TABLE player_stats_history (
    id INTEGER PRIMARY KEY,
    game_id TEXT,
    player_id TEXT,
    points INTEGER,
    assists INTEGER,
    rebounds INTEGER,
    -- ... all stats
    raw_json TEXT
);
```

---

## Data Pipeline Architecture

### Ingestion Flow

```
Provider (BALLDONTLIE, nba_api, etc.)
    ↓
Rate Limiter (5 rpm)
    ↓
Cache Layer (SQLite, 24h TTL)
    ↓
Normalized Internal Schema
    ↓
Feature Engineering
    ↓
Model Input
```

### Key Components

1. **Provider Interface** (`StatsProvider` ABC)
   - Swappable implementations
   - Normalized return types

2. **Cache** (`src/linelogic/data/cache.py`)
   - SQLite-backed
   - Key: provider + endpoint + params hash
   - TTL: Configurable per endpoint

3. **Rate Limiter** (`src/linelogic/data/rate_limit.py`)
   - Token bucket algorithm
   - Global + per-provider limits

4. **Tier Gating**
   - Raise `PaidTierRequiredError` for paid endpoints on free tier
   - Clear error messages: "This endpoint requires All-Star tier ($5/mo)"

---

## Data Quality and Monitoring

### Validation Checks

1. **Schema validation**: Pydantic models for all API responses
2. **Completeness**: Check for null/missing values
3. **Timeliness**: Flag stale data (e.g., game started but no score)
4. **Consistency**: Cross-check across providers (if available)

### Alerts (Future)

- Slack/email alerts for:
  - API downtime (>5 min)
  - Stale data (>1 hour)
  - Rate limit errors

---

## Cost Estimates

### M0 (POC, Free Tier Only)

- BALLDONTLIE: **Free** (5 rpm limit)
- nba_api: **Free** (unofficial)
- Weather: **Free** (WeatherAPI)
- Odds: **Future** (manual for M0)

**Total: $0/month**

---

### M1 (Production MVP)

- BALLDONTLIE All-Star: **$5/mo**
- The Odds API Basic: **$20/mo**
- WeatherAPI: **Free**
- nba_api: **Free** (backfill only)

**Total: $25/month**

---

### M2 (Full Production)

- BALLDONTLIE MVP: **$15/mo**
- The Odds API Pro: **$50/mo**
- WeatherAPI Pro: **$4/mo**
- NewsAPI: **$50/mo**
- Twitter Basic: **$100/mo** (optional)

**Total: $119-219/month**

---

### M3+ (Multi-Sport)

Add NFL/MLB providers:

- Sportradar (NFL): **$1000+/year**
- MLB Stats API: **Free**
- ESPN+ (data access): **$10/mo**

**Total: ~$200-300/month + $1000/year**

---

## Data Retention

### Recommendations

| Data Type | Retention | Storage |
|-----------|-----------|---------|
| Raw API responses | Forever (audit trail) | S3 / local files |
| Processed games | Forever (backtesting) | SQLite / Postgres |
| Player stats | Forever (modeling) | SQLite / Postgres |
| Odds snapshots | 1 year (CLV analysis) | SQLite / Postgres |
| Cache | 24-48 hours (TTL) | SQLite (auto-expire) |
| Logs | 30 days | Cloudwatch / local |

---

## Future Enhancements

### Advanced Tracking Data

- **SecondSpectrum** (NBA): Player tracking, speed, distance
- **Next Gen Stats** (NFL): Ball velocity, route depth
- **Statcast** (MLB): Exit velo, launch angle, spin rate

**Challenges:**

- Expensive (enterprise contracts)
- Complex data formats
- Requires domain expertise to extract signal

**Timeline:** M3+, after core models validated

---

### Automated Line Monitoring

**Goal:** Detect line movements in real-time.

**Architecture:**

- WebSocket connections to odds providers
- Stream odds updates to time-series DB (InfluxDB)
- Alerts for "steam moves" (sharp action)

**Timeline:** M2+

---

### Proprietary Data Sources

**Examples:**

- Injury reports from team insiders (paid subscriptions)
- Referee assignments and tendencies
- Travel schedules (jet lag effects)
- Player social media (mood, confidence)

**Timeline:** M3+, if ROI justifies cost

---

## Conclusion

Data is the **lifeblood** of LineLogic. Our strategy:

1. **M0**: Free tier (BALLDONTLIE + nba_api) for scaffolding
2. **M1**: Paid tier ($25/mo) for production modeling
3. **M2**: Multi-source ($120-220/mo) for robustness
4. **M3**: Multi-sport + advanced tracking (case-by-case)

All providers are **swappable** via the `StatsProvider` interface. Cache and rate limiting are **mandatory** at every layer.

---

**Next**: [Backtesting and Paper Trading](05_backtesting_and_paper_trading.md) | [Risks and Compliance](06_risks_and_compliance.md)
