# LineLogic: Lines, Markets, and Odds Architecture

## Overview

This document explains which lines LineLogic currently supports, where they come from, and how the system is designed to evolve toward multi-market betting.

---

## Current State: Paper POC (v0.1)

### Markets Supported

**Currently Active:**
- ✅ **MoneyLine (W/L)**: Home/Away team winner
  - Fetches actual opening lines from [TheOddsAPI](https://theOddsAPI.com)
  - Falls back to 50/50 stub if API unavailable or key not configured
  - Stores American odds in `odds_snapshots` table with source metadata

### Sources: Real Odds from Real Books

The POC is **not** betting on synthetic data. Instead:

1. **Games**: Fetched from [BALLDONTLIE API](https://balldontlie.io) (free tier, real NBA schedule)
2. **Odds**: Fetched from [TheOddsAPI](https://theOddsAPI.com) (aggregates real US sportsbooks):
   - DraftKings
   - FanDuel
   - BetMGM
   - Caesars
   - Other major US books
3. **Stored**: All odds captured at recommendation time in SQLite `odds_snapshots` table
   - Timestamp: `captured_at`
   - Source: Sportsbook name (e.g., "DraftKings")
   - Line: Implied probability
   - American odds: E.g., -110, +150
   - Decimal odds: E.g., 1.91, 2.50

### Safety: Paper-Only Enforcement

- **Mode=paper**: Hardcoded check prevents `recommend_date()` from executing in `mode=live`
- **No Real Money**: Paper recommendations written to SQLite; settlement uses stub 50/50 outcomes (not real results)
- **Audit Trail**: Every recommendation includes:
  - Model probability
  - Market probability (from actual opening line)
  - Edge (model - market)
  - Stake suggested (fractional Kelly with caps)
  - Sportsbook source and line captured

---

## Database Schema Support

The SQLite schema is **designed for multi-market support**:

### `recommendations` Table
```sql
CREATE TABLE recommendations (
    ...
    market TEXT NOT NULL,       -- "moneyline", "spread", "total", "prop_over_under"
    selection TEXT NOT NULL,   -- "Heat (Home)", "Spread -5.5", "Over 210.5", etc.
    ...
);
```

### `odds_snapshots` Table
```sql
CREATE TABLE odds_snapshots (
    recommendation_id INTEGER,
    source TEXT,              -- "TheOddsAPI" or sportsbook name
    captured_at TEXT,         -- Timestamp
    line REAL,                -- The specific line (e.g., -5.5 for spread)
    odds_american INTEGER,    -- American odds (e.g., -110, +150)
    odds_decimal REAL,        -- Decimal odds (e.g., 1.91)
    raw_payload_json TEXT,    -- Full API response
);
```

**This design supports:**
- Multiple markets per game (W/L, spread, total, props)
- Multiple sportsbooks per market (opening, closing, best bid/ask)
- Historical tracking of line movement
- Fair odds comparison across books

---

## Roadmap: From W/L to Full Market Coverage

### Phase 1 (Current): MoneyLine Only
- ✅ Fetch real opening MoneyLine odds from TheOddsAPI
- ✅ Store with sportsbook source
- ✅ Fall back to stub if API unavailable

### Phase 2 (v0.2): Spread + Total
Add support for:
- Spread lines (e.g., "Spread -5.5", "Spread +5.5")
- Total lines (e.g., "Over 210.5", "Under 210.5")
- Implementation: Extend `fetch_real_moneyline_odds()` to handle market_key="spreads" and "totals"

### Phase 3 (v0.3): Player Props
Add support for:
- Player Over/Under (PTS, AST, REB, etc.)
- Requires: Prop lines from sportsbooks (via TheOddsAPI "player_props" market)
- Challenge: Linking props to player IDs from BALLDONTLIE

### Phase 4 (v0.4): Live Betting
- Add closing odds integration (sportsbook API or manual feed)
- Compare opening vs. closing for line movement analysis
- Compute CLV (Closing Line Value) for performance attribution

### Phase 5 (v1.0): Multi-Book Arbitrage
- Simultaneously track best bid/ask across books
- Compute hedge opportunities
- Auto-recommend best book per bet

---

## Why Only W/L Right Now?

1. **MVP Principle**: Moneyline is simplest to model (binary outcome)
2. **Data Quality**: TheOddsAPI free tier covers MoneyLine reliably; spreads/totals less consistent
3. **Baseline Metrics**: Need ROI and CLV baseline before adding complexity
4. **Schema Ready**: `market` column in schema already planned for extensibility

---

## How to Enable Real Odds

### Setup TheOddsAPI Key

1. Create account: https://theOddsAPI.com/
2. Get free API key (500 req/month, ~16 per day)
3. Add to `.env`:
```bash
ODDS_API_KEY=your_key_here
```

### Running Paper Recommendations with Real Odds

```bash
LOG_LEVEL=DEBUG linelogic recommend-daily --date 2026-01-15
```

**Output includes:**
- Cache hits/misses for rates
- Provider latency (TheOddsAPI request time)
- Rate limit waits (if free tier throttled)
- Real sportsbook odds captured to database

### Checking Captured Odds

```sql
sqlite3 .linelogic/linelogic.db
SELECT 
    r.selection,
    r.market_prob,
    o.odds_american,
    o.source,
    o.captured_at
FROM recommendations r
JOIN odds_snapshots o ON r.id = o.recommendation_id
LIMIT 5;
```

---

## Fallback Behavior

If TheOddsAPI fails or key not set:

1. **Cache**: Check local cache for prior odds (cached for 24h)
2. **Stub**: Use fair 50/50 odds
3. **Outcome**: Recommendation still generated with edge vs. fair odds
4. **Logging**: Error logged at WARNING level; user can retry

---

## Future: Real Settlement

Currently settle uses **stub 50/50 outcomes**. To integrate real results:

1. **Sportsbook API**: Query ESPN/official results
2. **Manual Feed**: Ingest from CSV/webhook (results uploaded to S3, fetched by cron)
3. **Update schema**: Add actual game outcome to `results` table
4. **Compute CLV**: Compare model edge to closing line value

---

## Rate Limits & Quotas

| Provider | Tier | Limit | POC Budget |
|----------|------|-------|-----------|
| BALLDONTLIE | Free | 5 req/min | ✅ Used: ~1/min (games + health checks) |
| TheOddsAPI | Free | 500 req/month | ✅ Used: ~16/month (~1 per day) |

**Safe to run**: Daily `recommend-daily` + `settle-daily` plus manual testing without hitting quotas.

---

## Summary: Real Lines from Real Books

✅ **We ARE tracking actual lines** from real sportsbooks (DraftKings, FanDuel, BetMGM, Caesars via TheOddsAPI)

✅ **We are NOT betting real $** (MODE=paper enforcement)

✅ **Architecture supports multi-market expansion** (Spreads, Totals, Props, multi-book arbitrage)

✅ **All data auditable**: Every recommendation includes source, line, odds, and timestamp

Next step: Set `ODDS_API_KEY` in `.env` and run paper slates to accumulate real odds data for v2 model training.
