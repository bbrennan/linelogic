# Data Sources

## Overview

LineLogic requires **high-quality, timely, and legally compliant data** across multiple domains: sports stats, odds/lines, weather, injuries, news/social sentiment, and venue information. This document catalogs all target data sources with **legal compliance as the top priority**.

## Key Principles

1. **Legal compliance first**: Never violate ToS or risk legal action
2. **Swappable providers**: Never lock into one API
3. **Tier awareness**: Free vs. paid endpoints
4. **Caching**: Minimize API calls
5. **Rate limiting**: Respect provider limits
6. **Failure gracefully**: Degrade to fallback sources

---

## Sports Stats

### Primary: NBA

#### BALLDONTLIE (PRIMARY CHOICE)

**API:** https://www.balldontlie.io

**Legal Status:** ✅ Community-run, published terms allow free use with rate limits

**Tiers:**

- **Free**: 5 requests/minute, players/teams/games endpoints
- **All-Star ($5/mo)**: 30 req/min, player stats, season averages, injuries
- **MVP ($15/mo)**: 60 req/min, advanced stats, play-by-play

**Available on Free:**

- `/players` - All NBA players (name, team, position)
- `/teams` - All NBA teams
- `/games` - Game schedules, scores, status

**Paid tier required:**

- `/stats` - Player game logs ⭐ **NEEDED FOR M1**
- `/season_averages` - Season stats per player
- `/injuries` - Injury reports (future)

**Integration:**

- Implemented in `src/linelogic/data/providers/balldontlie.py`
- Tier gating: Raise `PaidTierRequiredError` for paid endpoints on free tier
- Cache: 24h TTL for players/teams, 1h for games
- Rate limit: 5 rpm on free, 30 rpm on All-Star

**Decision:**

- ✅ Use for M0 (free tier for scaffolding)
- ✅ Upgrade to All-Star ($5/mo) for M1 (modeling requires player stats)
- ✅ Legal and safe for betting/fantasy/commercial use

**Limitations:**

- Free tier lacks player game stats (critical for modeling)
- No advanced stats (usage, TS%, etc.) on any tier
- No play-by-play data

---

#### ❌ nba_api (DO NOT USE)

**Library:** https://github.com/swar/nba_api

**Legal Status:** ⚠️ **VIOLATES NBA.com TERMS OF SERVICE**

**NBA.com ToS Section 9 Prohibits:**

1. Using NBA statistics for "any gambling activity (including legal gambling)"
2. Using stats for "any fantasy game or other commercial product or service"
3. Creating "database … of comprehensive, regularly updated statistics … without … express prior consent"
4. Any use without prominent NBA.com attribution

**Why LineLogic Cannot Use nba_api:**

- ✗ Paper trading/backtesting constitutes gambling activity analysis
- ✗ Building a stats database violates comprehensive database restriction
- ✗ Commercial intent (even if non-profit) violates ToS
- ✗ Risk of legal action from NBA
- ✗ Risk of IP ban

**Pros (irrelevant given legal issues):**

- Free, unlimited (no API key)
- Rich data: advanced stats, play-by-play, tracking data
- Historical data back to 1996

**Cons:**

- **ILLEGAL FOR OUR USE CASE**
- No SLA, can break without notice
- Rate limiting unclear, IP ban risk
- NBA.com actively monitors and blocks unauthorized access

**Decision: REMOVE FROM LINELOGIC**

- ❌ Delete `src/linelogic/data/providers/nba_api_provider.py`
- ❌ Remove `USE_NBA_API` config flag
- ❌ Remove nba_api from `pyproject.toml` dependencies
- ❌ Update tests to remove nba_api references

**Replacement Strategy:**

1. Use BALLDONTLIE All-Star tier ($5/mo) for all NBA data needs
2. For historical backfills: Use open datasets (Kaggle, BigQuery) where licensed
3. For advanced stats: Wait for official NBA API or use licensed providers
4. Budget BALLDONTLIE All-Star from M1 onwards ($5/mo minimum)

---

#### TheSportsDB (Cross-Sport Fallback)

**API:** https://www.thesportsdb.com/

**Legal Status:** ✅ Community-curated, free for non-commercial use

**Coverage:**

- NBA, NFL, MLB, NHL schedules and basic stats
- ~1,000 requests/day on free tier
- Not official but terms allow dev/prototype use

**Use cases:**

- Multi-sport schedule aggregation
- Basic team/player lookups (non-critical)
- Fallback when primary providers unavailable

**Limitations:**

- Less granular than sport-specific APIs
- Community-maintained (gaps possible)
- Non-commercial license restriction (OK for POC, not for monetized product)

**Integration plan (M2):**

- `src/linelogic/data/providers/thesportsdb.py`
- Low priority, fallback only

---

#### NBA Official API (Future)

**Status:** Not yet available for third-party developers

**If/when available:**

- Will be primary source for all NBA data
- Likely paid tier ($50-500/mo estimated)
- Full compliance with NBA terms
- Update provider interface: `src/linelogic/data/providers/nba_official.py`

**Decision:** Monitor for availability, migrate immediately when launched

---

### Expansion: NFL

#### nflverse (Open Source)

**Source:** https://github.com/nflverse/nflverse-data

**Legal Status:** ✅ Open-source derived data, permissive licenses

**Available:**

- Historical play-by-play (CSV/parquet)
- Season stats, roster data
- Released via GitHub/S3
- Free redistribution allowed

**Use cases:**

- Historical modeling and backtesting (M2)
- POC without live data requirements
- Training data for prop models

**Limitations:**

- Not authorized by NFL for commercial/betting use
- Historical only (not real-time)
- Requires local download/processing
- Not suitable for live production

**Integration plan (M2):**

- `src/linelogic/data/providers/nflverse.py`
- One-time backfill, cache locally in SQLite
- Same StatsProvider interface as NBA

**Decision:** ✅ Use for M2 NFL expansion (historical only)

---

#### Unofficial NFL APIs

**Status:** ⚠️ **DO NOT USE**

- ESPN/NFL.com JSON endpoints: Violate site ToS, no scraping allowed
- Community wrappers: Same legal issues as underlying source
- No official free real-time NFL API exists

**Decision:** Use nflverse for historical, wait for licensed provider for live data

---

### Expansion: MLB

#### Retrosheet / Chadwick Bureau / Lahman DB

**Sources:**

- https://www.retrosheet.org/
- Chadwick Bureau datasets
- Lahman database (1871-present)

**Legal Status:** ✅ Explicitly free/open, redistribution allowed

**Available:**

- Historical box scores, play-by-play
- Complete MLB history (1871-present)
- Lahman database: batting, pitching, fielding stats

**Use cases:**

- MLB modeling and backtesting (M2)
- Training data for prop models
- POC for MLB expansion

**Integration plan (M2):**

- `src/linelogic/data/providers/retrosheet.py`
- Batch download, SQLite storage
- One-time backfill

**Decision:** ✅ Use for M2 MLB expansion (historical only)

---

#### MLB Stats API

**Endpoint:** https://statsapi.mlb.com

**Legal Status:** ⚠️ Public but undocumented, governed by MLB.com ToS

**Restrictions:**

- Must be non-commercial
- No betting/fantasy use without license
- MLB can block access at any time

**Use cases:**

- Light prototyping only
- Non-commercial research
- Fallback for missing data

**Decision:** ⚠️ Use cautiously for POC only, migrate to licensed provider for production

**Integration plan (M2):**

- `src/linelogic/data/providers/mlb_api.py`
- Behind feature flag, disabled by default
- Clear ToS disclaimer in code comments

---

### Expansion: NHL

#### NHL Stats API

**Endpoint:** https://statsapi.web.nhl.com

**Legal Status:** ⚠️ Public but undocumented, governed by NHL.com ToS

**Similar restrictions to MLB:**

- Personal/non-commercial POC acceptable
- Avoid commercial, betting, fantasy redistribution without license
- Risk of access blocking

**Integration plan (M2):**

- `src/linelogic/data/providers/nhl_api.py`
- Light use only for POC
- Migrate to licensed provider for production
- Behind feature flag, disabled by default

---

### Expansion: MMA / UFC

#### UFC Stats

**Source:** http://ufcstats.com/

**Legal Status:** ⚠️ **HIGH RISK**

**Restrictions:**

- UFC terms restrict commercial/betting/fantasy use
- No official API or license grant
- Light personal research acceptable
- May block scrapers aggressively

**Decision:** ❌ Defer UFC/MMA support until:

1. Official UFC API available, OR
2. Licensed provider identified (Sportradar, etc.), OR
3. Clear legal guidance obtained

**Integration:** Not planned for M0-M2

---

### Licensed Providers (Production - M3/M4)

For production use beyond POC/prototyping, LineLogic will need licensed data feeds.

#### Sportradar

- Official NFL, NBA, NHL, MLB data partner
- Real-time feeds, historical data
- Cost: $2,000-10,000/mo depending on coverage
- Full legal compliance for betting/fantasy use

#### Genius Sports

- Official NBA, EPL data partner
- Advanced analytics, live data
- Cost: $1,500-8,000/mo

#### Stats Perform (Opta)

- Multi-sport coverage (soccer, basketball, etc.)
- Cost: $1,000-5,000/mo

#### SportsDataIO

- Developer-friendly APIs
- NBA, NFL, MLB, NHL, CFB, CBB
- Cost: $500-2,000/mo
- Good mid-tier option

**Decision:** Defer to M3/M4 when:

1. Revenue justifies cost ($500-2,000/mo minimum)
2. Moving beyond paper trading to live recommendations
3. User base demands real-time data

---

## Odds & Lines

### The Odds API

**API:** https://the-odds-api.com/

**Legal Status:** ✅ Legitimate aggregator, clear ToS

**Tiers:**

- **Free**: 500 requests/month, limited markets
- **Basic ($20/mo)**: 10,000 requests/mo, all US sportsbooks
- **Pro ($50/mo)**: 50,000 requests/mo, international books

**Available:**

- Pre-game odds (spreads, moneylines, totals)
- Player props (points, assists, rebounds)
- Multiple sportsbooks (DraftKings, FanDuel, Caesars, etc.)
- Historical odds (limited on free)

**Integration plan (M1):**

- `src/linelogic/odds/providers/theoddsapi.py`
- Basic tier ($20/mo) for M1
- Cache aggressively (TTL: 15 min for pre-game, 5 min for props)

**Decision:** ✅ Primary odds source starting M1

---

### Manual Entry (M0)

For M0 POC, manually copy odds from DraftKings/FanDuel into SQLite for testing.

**Workflow:**

1. Open DraftKings player props page
2. Manually create CSV: `player_id,market,line,odds_over,odds_under`
3. Import to `odds_snapshots` table
4. Run backtesting with synthetic historical odds

**Decision:** ✅ Use for M0 (no API cost), migrate to The Odds API for M1

---

## Weather

### WeatherAPI

**API:** https://www.weatherapi.com/

**Legal Status:** ✅ Legitimate weather service

**Tiers:**

- **Free**: 1M requests/month, 3-day forecast
- **Pro ($4/mo)**: 5M requests/mo, 14-day forecast

**Use cases:**

- Outdoor sports (NFL, MLB, MLS)
- Not needed for NBA (indoor)

**Integration plan (M2):**

- `src/linelogic/weather/providers/weatherapi.py`
- Free tier sufficient for POC
- Cache: 6h TTL

**Decision:** ✅ Free tier for M2 NFL/MLB expansion

---

## Injuries

### ESPN Injury Reports (Cautious)

**Source:** ESPN.com injury pages

**Legal Status:** ⚠️ Public but ToS restricts scraping

**Use cases:**

- Manual checks for POC
- Not suitable for automated scraping

**Decision:** ⚠️ Manual only for M0/M1, migrate to licensed provider (Sportradar) for M2

---

### RotoWorld / NBC Sports

**Similar status:** Public but ToS-restricted

**Decision:** ⚠️ Manual only

---

## Social Sentiment (Future - M3)

### Twitter API

**API:** https://developer.twitter.com/

**Legal Status:** ✅ Official API

**Tiers:**

- **Free**: 10,000 tweets/month (v2)
- **Basic ($100/mo)**: 500,000 tweets/month
- **Pro ($5,000/mo)**: 2M tweets/month

**Use cases:**

- Player sentiment analysis
- Breaking news detection (injuries, trades)
- Momentum shifts

**Integration plan (M3):**

- `src/linelogic/social/providers/twitter.py`
- Basic tier ($100/mo) for M3
- Not critical for M0-M2

**Decision:** Defer to M3

---

### NewsAPI

**API:** https://newsapi.org/

**Legal Status:** ✅ Legitimate news aggregator

**Tiers:**

- **Free**: 100 requests/day, dev only
- **Paid ($50/mo)**: 50,000 requests/mo

**Use cases:**

- Sports news aggregation
- Injury news detection
- Trade/roster move detection

**Integration plan (M3):**

- `src/linelogic/news/providers/newsapi.py`
- Paid tier ($50/mo) for M3

**Decision:** Defer to M3

---

## Cost Estimates

### M0 (POC, Free Tier Only)

- BALLDONTLIE: **Free** (5 rpm limit, no player stats)
- ❌ ~~nba_api: Free (REMOVED - ToS violation)~~
- Weather: Not needed (NBA indoor)
- Odds: **Manual entry** (no API cost)

**Total: $0/month**

---

### M1 (Production MVP with Real Data)

- BALLDONTLIE All-Star: **$5/mo** (30 rpm, player game logs)
- The Odds API Basic: **$20/mo** (10,000 requests/mo)
- Weather: **Free** (not needed for NBA)

**Total: $25/month**

---

### M2 (Multi-Sport Expansion)

- BALLDONTLIE All-Star: **$5/mo**
- The Odds API Pro: **$50/mo** (50,000 requests/mo for multi-sport)
- WeatherAPI: **Free** (1M requests/mo)
- nflverse: **Free** (historical only)
- Retrosheet: **Free** (historical only)

**Total: $55/month**

---

### M3 (Full Production with Social)

- BALLDONTLIE MVP: **$15/mo** (60 rpm, advanced stats)
- The Odds API Pro: **$50/mo**
- WeatherAPI Pro: **$4/mo** (14-day forecast)
- NewsAPI: **$50/mo** (50k requests/mo)
- Twitter Basic: **$100/mo** (optional, 500k tweets)

**Total: $119-219/month** (depending on Twitter)

---

### M4 (Licensed Production Data)

- Sportradar Basic NBA + NFL: **$3,000/mo** (estimated)
- The Odds API Pro: **$50/mo**
- WeatherAPI Pro: **$4/mo**
- NewsAPI: **$50/mo**
- Twitter Basic: **$100/mo**

**Total: $3,204/month**

**Note:** M4 requires revenue to justify licensed feeds. Only pursue when:

1. User base demands real-time data quality
2. Revenue exceeds $10k/mo
3. Legal/compliance requires licensed sources

---

## Legal Compliance Summary

### ✅ APPROVED FOR USE

- **BALLDONTLIE** - Primary NBA source (free + paid tiers)
- **TheSportsDB** - Multi-sport fallback (non-commercial OK)
- **nflverse** - Historical NFL data (open source)
- **Retrosheet/Chadwick/Lahman** - Historical MLB data (open source)
- **The Odds API** - Odds aggregator (paid, legitimate)
- **WeatherAPI** - Weather service (free/paid)
- **Twitter API** - Social sentiment (official API)
- **NewsAPI** - News aggregator (paid, legitimate)

### ⚠️ USE WITH CAUTION (POC ONLY)

- **MLB Stats API** - Public but ToS-restricted, non-commercial only
- **NHL Stats API** - Public but ToS-restricted, non-commercial only
- **ESPN Injury Reports** - Manual checks only, no automated scraping

### ❌ DO NOT USE

- **nba_api** - Violates NBA.com ToS Section 9 (gambling/fantasy/database prohibitions)
- **Unofficial ESPN/NFL.com scrapers** - ToS violations
- **UFC Stats scrapers** - ToS violations, high IP ban risk
- **Any unofficial scraper without clear legal status**

---

## Action Items

### Immediate (Before M1)

1. ❌ Remove `src/linelogic/data/providers/nba_api_provider.py`
2. ❌ Remove `USE_NBA_API` from settings.py
3. ❌ Remove nba_api from pyproject.toml
4. ❌ Remove nba_api tests from test_providers.py
5. ✅ Update README to remove nba_api references
6. ✅ Add NBA.com attribution wherever NBA stats are displayed
7. ✅ Budget BALLDONTLIE All-Star ($5/mo) starting M1

### M1 (Modeling Phase)

1. Upgrade to BALLDONTLIE All-Star ($5/mo)
2. Integrate The Odds API Basic ($20/mo)
3. Implement odds caching and rate limiting
4. Build recommendation engine with compliant data sources

### M2 (Multi-Sport)

1. Integrate nflverse for NFL historical data
2. Integrate Retrosheet for MLB historical data
3. Add WeatherAPI for outdoor sports
4. Upgrade to The Odds API Pro ($50/mo)

### M3 (Social & News)

1. Add Twitter API Basic ($100/mo)
2. Add NewsAPI ($50/mo)
3. Implement sentiment analysis pipeline
4. Build injury/news detection

### M4 (Licensed Production)

1. Evaluate Sportradar, Genius Sports, Stats Perform
2. Budget $3,000-5,000/mo for licensed feeds
3. Only pursue when revenue justifies cost

---

## Conclusion

LineLogic will build on **legally compliant, sustainable data sources** from day one:

- **M0:** BALLDONTLIE free tier (no player stats, scaffolding only)
- **M1:** BALLDONTLIE All-Star ($5/mo) + The Odds API ($20/mo) = $25/mo
- **M2:** Add multi-sport open datasets (nflverse, Retrosheet) + The Odds API Pro = $55/mo
- **M3:** Add social/news APIs = $119-219/mo
- **M4:** Migrate to licensed feeds when revenue justifies = $3,000+/mo

**The nba_api library will NOT be used** due to clear violations of NBA.com ToS Section 9. All code and references will be removed before M1.
