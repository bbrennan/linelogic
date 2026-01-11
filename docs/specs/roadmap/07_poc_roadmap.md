# LineLogic POC Roadmap

## Objectives
- Ship a minimal end-to-end loop that produces paper recommendations for real slates and records outcomes.
- Validate data quality, latency, and rate-limit posture against BALDONTLIE.
- Enforce staking safety rails (fractional Kelly + caps) and keep audit trails.

## Phases
1) **Access & Config**
   - Set `.env` with `BALLDONTLIE` key/tier/rpm, `CACHE_DB_PATH`, `DATABASE_PATH`, `MODE=paper`, `LOG_LEVEL`.
   - Pin persistent cache path (not temp) and confirm rpm <= tier limit.
2) **Data Fetch & Health**
   - Health check: ping `/teams` with timeout/retries; log rpm usage and cache hits.
   - Add backoff on provider errors; surface failures in CLI `check`.
3) **Recommendation Loop (Paper)**
   - Daily job: fetch games for target date, ingest market odds (or placeholder), convert odds → implied prob → fair prob, compute edge + fractional Kelly stake, write to SQLite (`recommendations`, `odds_snapshots`).
   - Emit run summary (CSV/console/Slack).
4) **Settlement Loop**
   - After games settle, record results and compute ROI/Kelly growth; update CLV if closing lines are available.
5) **Monitoring & Safety**
   - Logging at INFO/ERROR; capture provider exceptions and rate-limit waits.
   - Hard caps: per-bet, per-day; honor `MODE=paper` to prevent live execution.

## Definition of Done (POC)
- `linelogic check` succeeds against real API with configured key.
- Paper recommendations written to SQLite with model/version/edge/stake metadata.
- Cache persistence verified across runs; rate limiting respected (no 429s in logs).
- Basic reports produced (CSV/console) and outcomes recorded for at least one slate.

## Stretch
- Add odds provider integration, Slack alerts, richer models, and dashboarding.

## Next Actions
- Wire cache to `settings.cache_db_path` and use configured TTL in provider.
- Add provider timeout + retry/backoff in `_request`.
- Add `mode` setting (paper/live) and surface in CLI `check` output.
- Build a minimal daily runner to generate paper recommendations and log to DB (stub model is fine to start).
