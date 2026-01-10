# Data Learning Plan for POC

## Objectives
- Treat the POC as a data acquisition loop to learn feature importance and model design (GLM/XGBoost).
- Build a "LineLogic Index" (LLI) that tracks market efficiency, model edge, and realized outcomes over time.
- Collect enough labeled examples to support calibration, feature engineering, and hyperparameter search.

## What to Log Each Slate
- **Market context**: opening/closing odds (american/decimal), implied probs, vig-removed fair probs, sportsbook source, timestamp.
- **Game context**: teams, date/time, home/away, pace proxies (if available), injuries (stub now, integrate later).
- **Recommendation**: model probability, market probability, edge, stake (fractional Kelly), caps applied, mode (paper/live), model version/commit hash.
- **Outcome**: settled result, profit/loss, realized ROI, realized Kelly growth, CLV (closing prob minus open prob), time-to-settle.
- **Execution meta**: cache hits/misses, rate-limit waits, request latency, provider errors.

## Minimal Pipelines (Paper)
1) **Recommend loop (daily)**
   - Input: slate date, mode=paper.
   - Steps: fetch games (BALDONTLIE), generate placeholder probs (stub baseline), convert odds → implied → fair, compute edge/stake, write to SQLite (`recommendations`, `odds_snapshots`).
   - Output: CSV/console summary + log counts, avg edge, total stake.
2) **Settle loop (daily)**
   - Input: slate date.
   - Steps: fetch results (stub), update `results`, compute ROI/Kelly growth/CLV deltas, write back to DB.
   - Output: daily metrics rollup.

## LineLogic Index (LLI) – Early Definition
- Rolling metrics: avg edge, realized ROI, Kelly growth, CLV drift, hit rate, over/under-stake ratio vs. cap.
- Data quality: percent missing odds/results, provider latency, rate-limit events.
- Confidence: calibration buckets (Brier/log loss) and sample size per bucket.

## Data Quality & Safety Rails
- Respect rpm (free tier: 5 rpm) and use cache for repeat calls.
- Enforce per-bet/day caps and keep mode=paper until live is approved.
- Record errors and backoff events; no silent skips.

## Open Questions
- Which sportsbook odds feed to integrate next? (needed for real CLV)
- Injury/news ingestion priority? (simple flag vs. richer feed)
- Target sample size for first GLM/XGBoost fit? (e.g., 5–10k labeled props)

## Immediate Next Tasks
- Add recommend/settle CLI commands that write to SQLite and emit summaries (paper only).
- Persist cache/DB paths from `.env`; confirm free-tier rpm=5 in config.
- Add lightweight logging (INFO/ERROR) with request latency and cache hit rate.
- Add daily cron/script wrapper to run recommend then settle for the target date.
