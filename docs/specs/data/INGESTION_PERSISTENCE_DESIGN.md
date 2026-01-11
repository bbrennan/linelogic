# LineLogic Data Ingestion + Persistence Design (BALLDONTLIE + The Odds API)

**Last updated:** 2026-01-11  
**Owner:** LineLogic  
**Scope:** Software engineering + DevOps design for ingesting, normalizing, and persisting sports data from:

- **BALLDONTLIE** — schedules/results, teams/players, stats, injuries/lineups (varies by league/tier)
- **The Odds API** — pregame odds + historical odds snapshots

## Secrets policy
API keys are intentionally **not** stored in this repo. Configure locally via `.env`:

- `BALLDONTLIE_API_KEY=...`
- `ODDS_API_KEY=...`

See [.env.example](../../../.env.example).

---

## 0) Executive Summary

We will build a **provider-agnostic ingestion framework** with three storage layers:

- **Bronze (raw)**: Immutable API responses (JSON), partitioned by provider/sport/date/run.
- **Silver (normalized)**: Canonical, row-based tables in **Parquet** (SQLite/Postgres optional later).
- **Gold (feature-ready)**: Derived datasets (odds movement aggregates, consensus lines, “as-of” feature snapshots) for modeling and backtesting.

The pipeline supports:

1) **Historical backfill** (bounded, deterministic, resumable)
2) **Ongoing scheduled ingestion** (pregame snapshots)
3) **Optional near-real-time** windows (later, e.g. in-game contexts)

Odds are treated as **append-only time series snapshots**; movement/volatility features are computed in Gold.

---

## 1) Goals and Non-Goals

### Goals
- Multi-sport ingestion (NBA first; NFL/MLB next) with a single architecture.
- Reliable local persistence with strong reprocessing guarantees.
- Deterministic “as-of” datasets for leakage-safe modeling.
- Clear data contracts (schemas) for normalized tables.
- Observability: logs, metrics, run manifests, and failure recovery.
- DevOps-friendly: CLI + config-driven runs + cron/systemd + Docker option.

### Non-Goals (for now)
- No cloud object storage (S3/GCS) or warehouse (Snowflake/BigQuery).
- No full real-time streaming infra (Kafka, etc.).
- No in-game modeling pipeline; only design hooks.

---

## 2) Data Source Responsibilities

### 2.1 The Odds API (odds source of truth)
- Primary use: pregame markets
  - moneyline (`h2h`)
  - spreads
  - totals
- Historical: snapshot-style “odds at time T”
- Ongoing: scheduled snapshots at chosen times pregame

### 2.2 BALLDONTLIE (truth/labels/features)
- Primary use:
  - schedule + results (labels)
  - team/player stats (features)
  - injuries + lineups (features)
- Optional later:
  - play-by-play (in-game context)

---

## 3) High-Level Architecture

### 3.1 Components
- **Collector**: calls provider APIs, writes Bronze JSON, emits run metadata.
- **Normalizer**: transforms Bronze → Silver tables (Parquet).
- **Deriver**: computes Gold aggregates (odds movement, consensus, joins with results).
- **Orchestrator**: schedules and runs jobs, retries, checkpoints.
- **Registry**: canonical IDs + mapping between providers.

### 3.2 Data Flow

```
+------------------+          +------------------+
|  The Odds API    |          |   BALLDONTLIE     |
+---------+--------+          +---------+--------+
          |                             |
          v                             v
  (Collector: raw JSON)         (Collector: raw JSON)
          |                             |
          +-------------+---------------+
                        v
               Bronze (immutable)
                        |
                        v
             Normalizer (schemas)
                        |
                        v
           Silver (canonical parquet)
                        |
                        v
          Deriver (aggregates / joins)
                        |
                        v
           Gold (model-ready datasets)
```

---

## 4) Local Persistence Strategy

### 4.1 Storage layout
All data lives under a single project path: `./data/` (gitignored).

```
data/
  bronze/
    provider=oddsapi/
      sport=basketball_nba/
        date=YYYY-MM-DD/
          run_id=.../
            endpoint=.../
              response_0001.json
              response_0002.json
            manifest.json

    provider=balldontlie/
      league=nba/
        date=YYYY-MM-DD/
          run_id=.../
            endpoint=games/
              response_0001.json
            manifest.json

  silver/
    tables/
      odds_snapshot/
        sport=basketball_nba/
          season=2025/
            part-0000.parquet
      event/
      team/
      player/
      game_team_stats/
      game_player_stats/
      injuries/
      lineups/
      event_provider_map/
      team_provider_map/
      player_provider_map/

  gold/
    datasets/
      pregame_training_rows/
        sport=basketball_nba/
          season=2025/
            part-0000.parquet
      odds_movement_features/
      consensus_lines/
      clv_evaluation/

  runs/
    YYYY-MM-DD/
      run_id=.../
        run_config.json
        run_summary.json
        metrics.json
        logs.txt

  checkpoints/
    oddsapi/
      basketball_nba.json
    balldontlie/
      nba.json
```

### 4.2 File formats
- Bronze: JSON (+ small manifest)
- Silver/Gold: Parquet
- Run metadata: JSON
- Optional later: SQLite for small lookup tables (mapping overrides, etc.)

### 4.3 Immutability rules
- Bronze is append-only.
- Silver is append-only by partition (rebuildable by replaying Bronze).
- Gold is derived and recomputable.

---

## 5) Canonical IDs + Mapping (Non-Negotiable)

### 5.1 Canonical entity keys
- `canonical_event_id`
- `canonical_team_id`
- `canonical_player_id`

### 5.2 Mapping tables (Silver)
- `event_provider_map(provider, provider_event_id, canonical_event_id, match_confidence, created_at)`
- `team_provider_map(provider, provider_team_id, canonical_team_id, created_at)`
- `player_provider_map(provider, provider_player_id, canonical_player_id, created_at)`

### 5.3 Canonical event identity
For scheduled games:
- league
- home team canonical
- away team canonical
- start time (UTC)

`canonical_event_id = stable_hash(league, home_team, away_team, start_time_utc)`

### 5.4 Matching strategy
- First pass: exact match on start_time ± tolerance + normalized team names
- Fallback: league + date + fuzzy team match
- Store `match_confidence`; allow manual overrides in `mappings/overrides.yaml`

---

## 6) MVP Silver Tables (Phase 1)

### Events + labels (BALLDONTLIE)
- `event` (one row per game)
- `event_result` (final scores, winner)

### Odds time series (The Odds API)
- `odds_snapshot` (rows per event × snapshot_time × book × market × selection)

### Entities
- `team`
- `player`

### Recommended Phase 1+
- `injuries`
- `lineups`
- `game_team_stats`
- `game_player_stats`

---

## 7) Odds Snapshot Design (Core Table)

### 7.1 Append-only snapshot model
Every time we poll historical or current odds, we store a snapshot “as observed”.

### 7.2 Canonical schema: `odds_snapshot`
Required columns:

- `provider` (e.g., `oddsapi`)
- `sport` (e.g., `basketball_nba`, `americanfootball_nfl`, `baseball_mlb`)
- `canonical_event_id`
- `provider_event_id`
- `commence_time_utc`
- `snapshot_time_utc` (when observed)
- `is_live` (boolean)
- `bookmaker`
- `market` (enum: `h2h`, `spreads`, `totals`, …)
- `selection` (`home`, `away`, `over`, `under`, …)
- `price` (numeric; canonicalize to decimal)
- `point` (numeric; spread/total; null for h2h)
- `ingest_run_id`
- `ingested_at_utc`
- `record_hash` (for dedupe)
- `raw_ref` (path to bronze file)

### 7.3 Dedupe rules
- Intra-run: drop exact duplicates within a response
- Inter-run: dedupe exact repeats on `(event, snapshot_time, book, market, selection, price, point)`

We never collapse across different `snapshot_time_utc`.

---

## 8) Snapshot Strategy (Don’t Pull “Everything”)

### 8.1 Pregame snapshot schedule (Phase 1)
Default (configurable):
- `OPEN` (first-seen)
- `T-6h`
- `T-60m`
- `T-15m`
- `CLOSE` (last pregame snapshot)

If cost/complexity must be reduced:
- `OPEN`, `T-60m`, `CLOSE`

### 8.2 Historical backfill policy
1) Pull schedule from BALLDONTLIE (authoritative)
2) Compute target snapshot timestamps relative to `commence_time_utc`
3) Call The Odds API historical endpoint at those timestamps
4) Persist + normalize

### 8.3 Bookmaker scope
Use a fixed allowlist (configurable per sport), e.g.:
`["pinnacle", "draftkings", "fanduel", "betmgm"]`

### 8.4 Markets scope
Phase 1:
`["h2h", "spreads", "totals"]`

---

## 9) Gold Datasets (Model-Ready)

### 9.1 `odds_movement_features` (per event × market)
- open/close price/point
- deltas + volatility (std/range)
- late move (close − T-60)
- slope/trend + reversal flags

### 9.2 `consensus_lines` (per event × bucket)
- mean/median lines across books
- dispersion (IQR/std)

### 9.3 `pregame_training_rows` (Phase 1)
Leakage-safe joined dataset keyed by `(canonical_event_id, asof_bucket)`:
- labels (home_win, scores)
- odds consensus + movement features
- (optional) team form features

---

## 10) Orchestration + DevOps

### 10.1 Execution modes
- `ingest backfill` — historical ranges; resumable
- `ingest daily` — upcoming events + scheduled snapshots
- `derive gold` — build/rebuild gold from silver

### 10.2 Local scheduling
Pick one:
- cron (MVP)
- systemd timers
- Docker + cron

### 10.3 Rate limiting + retries
Provider clients enforce:
- token-bucket rate limiting
- exponential backoff on 429/5xx
- circuit breaker after N consecutive failures
- checkpointing per job

### 10.4 Run manifests
Each job writes:
- `run_config.json`, `run_summary.json`, `metrics.json`, `logs.txt`

---

## 11) Configuration + Secrets

### 11.1 Config file (YAML)
Proposed: `config/ingest.yaml` (committed; no secrets).

### 11.2 Secrets
Local-only in `.env` (never commit):
- `ODDS_API_KEY`
- `BALLDONTLIE_API_KEY`

---

## 12) Suggested Repo Structure (incremental, inside this repo)

Rather than creating a separate repo, we can add an ingestion package under `src/`:

```
src/linelogic/
  ingest/
    cli.py
    config.py
    providers/
    storage/
    normalize/
    derive/
    registry/
    orchestration/
config/
  ingest.yaml
```

---

## 13) MVP Validation

### Ingestion-time checks
- valid JSON
- required keys present
- snapshot_time recorded for all odds

### Silver validation checks
- canonical IDs not null
- commence_time parseable
- numeric bounds for price/point
- uniqueness post-dedupe

### Reconciliation checks
- % of events with ≥1 odds snapshot
- missingness by market/book
- outlier monitoring

---

## 14) Milestones

### Milestone A (MVP: Phase 1 ready)
- provider clients
- Bronze persistence + run manifests
- Silver: `event`, `event_result`, `odds_snapshot`
- canonical mapping for events/teams
- Gold: consensus + movement + minimal training rows

### Milestone B (Phase 1+)
- injuries + lineups
- team form (rolling)
- CLV evaluation dataset + reporting

### Milestone C (multi-sport hardening)
- NFL/MLB schedule/results coverage
- per-sport config tuning
- stress tests for large backfills
