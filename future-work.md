# LineLogic — NBA Game Winner Modeling (Doc + Implementation Plan)

**Last updated:** 2026-01-11  
**Owner:** LineLogic  
**Objective:** Produce **leakage-safe** pregame probabilities `P(home_win)` for NBA games, with clean evaluation (log loss / Brier / calibration), **paper-trading validation**, and a clear path to using **market odds as a benchmark/prior** plus roster/injury intelligence.

---

## 0) Why this doc exists

We already have a promising POC model (per your internal summary). This doc is the blueprint for making it **trustworthy, reproducible, and extensible**.

This doc will:
1. Define the **non-negotiable** data and modeling rules (leakage, as-of, time splits).
2. Establish the **benchmarks we must beat** (Elo-only, market baseline, market+model).
3. Propose **feature families** that matter (travel, pace-adjusted form, roster strength).
4. Describe a **Champion/Challenger** model strategy (Logistic as champion; calibrated GBDT as challenger).
5. Specify **data sources** and “snapshot” requirements.
6. Provide an **implementation plan** with milestones and acceptance criteria.

---

## 1) Principles (non-negotiable rules)

### 1.1 “As-of” semantics for every feature
For a game at datetime **D**, the model may only use information that was available **strictly before D**.

**Hard rule:** Every feature must have an explicit **AS_OF definition** and a reproducible build query/window.

### 1.2 Time-aware evaluation (no random splits for primary claims)
NBA is time-dependent (rosters, form, injuries, strategies, schedule density).  
Primary evaluation must use **forward-chaining** or season-forward splits.

**Hard rule:** All “headline performance” numbers must come from **out-of-time** evaluation.

### 1.3 Snapshotting external data is required (not optional)
Anything that changes over time (odds, injuries, lineup news, social signals) must be stored as a timestamped snapshot.

**Hard rule:** if we can’t prove what we knew at prediction time, we cannot trust the backtest.

### 1.4 Probability quality > accuracy
LineLogic is a probability engine. We optimize:
- **Log loss**
- **Brier score**
- **Calibration quality** (reliability buckets, ECE/MCE artifacts)
Accuracy is secondary.

---

## 2) Strong, opinionated review of the current POC model (what stays, what must change)

### 2.1 What’s strong
- You’re using **proper scoring rules** (log loss + Brier).
- You’re using sensible first-order signals: **team strength (Elo), rest, recent form**.
- You’re doing some collinearity controls and feature selection hygiene.

### 2.2 What’s risky (and must be resolved before trusting performance claims)
Your reported jump is plausible, but **suspiciously strong** unless the pipeline is airtight.

#### A) Leakage via season-level “advanced metrics”
If PER/BPM/WS48 (or similar) are end-of-season aggregates applied to early-season games, that is look-ahead leakage.

**Hard rule:** season-level metrics must be either:
- prior-season priors, or
- computed strictly from games with datetime `< D` for each game.

#### B) Leakage via lineup continuity / “starter” artifacts
Starter flags and minutes are often only finalized postgame. If your continuity uses realized starters/minutes that include game D, it will inflate performance.

**Hard rule:** continuity and minutes-share features must be based on games strictly before D.

#### C) Split strategy risk (“stratified” or random splitting)
Random splitting creates subtle look-ahead and “future team identity” leakage.

**Hard rule:** primary validation is time-based:
- train: seasons up to year N-1
- validate: season N (early segment)
- test: season N (late segment) or season N+1

### 2.3 Bottom line
The POC is a great prototype, but it must be elevated to **audit-grade** before we let the numbers drive product decisions.

---

## 3) Benchmarks we must beat (add this early and keep it forever)

This is the “truth table” that prevents self-delusion.

### 3.1 Benchmark A — Elo-only baseline
A clean Elo implementation is a required baseline.

- FiveThirtyEight Elo details:  
  https://fivethirtyeight.com/features/how-we-calculate-nba-elo-ratings/  
- 538 NBA forecast methodology:  
  https://fivethirtyeight.com/methodology/how-our-nba-predictions-work/

### 3.2 Benchmark B — Market implied probability (when odds are available)
The market aggregates injuries/news faster than most models. It is the strongest baseline.

- The Odds API: https://the-odds-api.com/  
- Betting markets overview: https://the-odds-api.com/sports-odds-data/betting-markets.html  
- v4 API guide: https://the-odds-api.com/liveapi/guides/v4/

### 3.3 Benchmark C — Market-as-prior blend
We should implement the blend early (paper mode is enough):

`p_final = α * p_market + (1-α) * p_model`

We tune α to improve out-of-time log loss and calibration.

### 3.4 Benchmark D — Elo + market + model residual
This is the likely “MVP best practice” path:
- Elo provides structural stability.
- Market provides aggregated real-time information.
- Model provides a residual edge and feature explanations.

---

## 4) Advanced survey: NBA game-winner modeling techniques (what we support)

### 4.1 Elo family (must-have baseline)
- Home-court adjustment
- MOV multiplier
- K factor tuning

Reference:
- https://fivethirtyeight.com/features/how-we-calculate-nba-elo-ratings/

### 4.2 SRS / points-differential power ratings
SRS provides a points-based team strength adjusted for strength-of-schedule.

References:
- https://www.sports-reference.com/blog/2015/03/srs-calculation-details/  
- https://www.basketball-reference.com/blog/indexba52.html?p=39  
- https://www.basketball-reference.com/about/glossary.html

### 4.3 Efficiency / Four-Factors style models (possession-based)
Better than raw point diff because pace confounds margin.

References:
- https://www.basketball-reference.com/about/factors.html  
- https://cleaningtheglass.com/stats/guide/league_four_factors  
- https://squared2020.com/2017/09/05/introduction-to-olivers-four-factors/

### 4.4 Player-impact driven models (high leverage, if data/license feasible)
Impact metrics are better predictive building blocks than PER/WS48.

References:
- EPM: https://dunksandthrees.com/about/epm  
- Team ratings aggregation: https://dunksandthrees.com/ratings  
- DARKO overview: https://www.nbastuffer.com/analytics101/darko-daily-plus-minus/  
- DARKO app: https://apanalytics.shinyapps.io/DARKO/

### 4.5 Model families (Champion/Challenger, not “switch and pray”)
**Champion (always on):** Regularized Logistic Regression  
**Challenger:** Calibrated Gradient Boosted Trees (XGBoost/LightGBM)

**Rule:** Challenger can only become champion if it wins **out-of-time** on:
- log loss
- Brier
- calibration artifacts
- stability across season segments

---

## 5) Probability calibration + uncertainty (make it first-class)

### 5.1 Required evaluation artifacts
Every model run produces:
- log loss + Brier (train/val/test)
- reliability buckets (e.g., 0.50–0.55, 0.55–0.60, …)
- ECE/MCE summary values (or an equivalent calibration summary)
- segment breakdown (home/away, rest tiers, favorites/dogs, early/late season)

### 5.2 “Uncertainty flags” (MVP-friendly)
In addition to a probability, output a small set of flags:
- `DATA_STALE` (any critical feed not fresh)
- `INJURY_UNCERTAIN` (key player status unknown at snapshot time)
- `LINEUP_UNCONFIRMED`
- `LOW_SIMILARITY_MATCHUPS` (optional later)

These flags are product gold: they preserve trust.

---

## 6) Indexes (ratings) we should support and how they’re built

### 6.1 EloIndex (winner-focused)
**Inputs:** game results, home/away, optional margin  
**Outputs:** `elo_home`, `elo_away`, `elo_diff`, `p_home_win_elo`

Reference:
- https://fivethirtyeight.com/features/how-we-calculate-nba-elo-ratings/

### 6.2 SRSLikeIndex (points-focused)
**Inputs:** points for/against, opponent schedule  
**Outputs:** team rating + SOS components

Reference:
- https://www.sports-reference.com/blog/2015/03/srs-calculation-details/

### 6.3 RollingEfficiencyIndex (net rating / pace)
**Inputs:** possessions estimates, points, box stats  
**Outputs:** rolling offense/defense/net rating + pace

References:
- https://www.basketball-reference.com/about/factors.html  
- https://cleaningtheglass.com/stats/guide/league_four_factors

### 6.4 RosterStrengthIndex (impact × minutes)
**Inputs:** player impact, expected minutes, injury status  
**Outputs:** `team_available_strength`, `strength_diff`, uncertainty flags

References:
- https://dunksandthrees.com/about/epm  
- https://dunksandthrees.com/ratings

---

## 7) Feature roadmap (what to add next, and how)

### 7.1 Feature Audit (mandatory)
Every feature must register:
- `feature_name`
- `source`
- `as_of_definition`
- `window`
- `leakage_risk_level`
- `unit_test_status`

**Definition of Done (DoD) for any new feature:**
- has a written AS_OF rule
- has an automated test that fails if it uses data with datetime `>= game_datetime`
- is computed in a reproducible build step

### 7.2 Travel + time zone + circadian disruption (high value, low dependency)
Open research examples:
- https://pmc.ncbi.nlm.nih.gov/articles/PMC8636381/  
- https://www.tandfonline.com/doi/abs/10.1080/07420528.2022.2113093  
- https://www.mdpi.com/2075-4663/6/3/89  

**Implementation notes**
- Map team home arenas to coordinates + time zone.
- Compute distance/time-zone shift since prior game.
- Add schedule density (3-in-4, 4-in-6, etc.) and interactions with travel.

### 7.3 Rolling per-possession form (replace raw point diff)
Replace “pt diff last 10” with:
- rolling net rating windows (5/10/20)
- rolling pace
- optionally exponential decay versions

### 7.4 Roster availability: move from “out count” → magnitude-based strength
Upgrade path:
1) MVP: minutes-share availability using last-7 games rotation weights
2) Next: impact × minutes if impact data is feasible
3) Later: injury report snapshots + uncertainty modeling

### 7.5 Market features (bring this earlier than “later phase”)
Once odds ingestion is available:
- implied probabilities
- vig removal (if needed)
- market priors + calibration
- CLV tracking in paper mode

---

## 8) Data sources (linked) + GOAT/OpenAPI acceleration

### 8.1 BALLDONTLIE (core sports data; GOAT subscription)
Docs hub:
- https://www.balldontlie.io/docs/  

NBA portal:
- https://nba.balldontlie.io/

OpenAPI specification (key for AI-assisted development):
- https://www.balldontlie.io/openapi.yml

Using the OpenAPI spec with AI:
- https://nba.balldontlie.io/  (see “Using the OpenAPI Specification with AI” section)

AI-assisted development guide:
- https://www.balldontlie.io/blog/ai-assisted-development/

Getting started guide:
- https://www.balldontlie.io/blog/getting-started/

Official Python SDK:
- https://pypi.org/project/balldontlie/

Official MCP server (agentic workflows):
- https://github.com/balldontlie-api/mcp

### 8.2 NBA.com endpoints (optional / feature-flagged)
Unreliable over time; keep behind feature flag:
- https://github.com/swar/nba_api  
- https://pypi.org/project/nba_api/

### 8.3 Odds / props providers (market baseline & CLV)
- The Odds API: https://the-odds-api.com/  
- Markets overview: https://the-odds-api.com/sports-odds-data/betting-markets.html  
- v4 guide: https://the-odds-api.com/liveapi/guides/v4/  
- Sportradar odds/props reference (enterprise-grade):  
  https://developer.sportradar.com/odds/reference/oc-player-props-overview

### 8.4 Weather (primarily NFL, but platform-wide)
- https://www.weather.gov/documentation/services-web-api  
- https://weather-gov.github.io/api/general-faqs

### 8.5 Social/news (MVP caution)
Treat as:
- “awareness/uncertainty” signals
- snapshot + timestamp required
- never used without strict as-of semantics

(We will document exact channels once chosen.)

---

## 9) Storage + snapshot contract (upgrade from “as-of semantics” to “audit-grade”)

### 9.1 Snapshot record fields (required)
For any external changing feed (odds, injuries, news, etc.):
- `observed_at` (timestamp when we fetched it)
- `source` and `source_version`
- `entity_id` (game_id/team_id/player_id)
- `raw_payload` (or stable hash + blob storage pointer)
- `parsed_fields` (structured columns)
- `valid_for_start` / `valid_for_end` (if applicable)

### 9.2 Prediction record fields (required)
Every prediction row should include:
- `model_version` (git SHA)
- `features_version` (pipeline version)
- `feature_as_of_ts` (cutoff)
- `prob_home_win`
- `uncertainty_flags` (array/string)

---

## 10) Proposed LineLogic architecture for NBA winner modeling

### 10.1 Modules
- `linelogic/nba/datasets/`
  - `GameDatasetBuilder` (leakage-safe, as-of dataset)
  - `FeatureAuditReport`
- `linelogic/nba/indexes/`
  - `EloIndexBuilder`
  - `SRSLikeIndexBuilder`
  - `RollingEfficiencyBuilder`
  - `RosterStrengthBuilder`
- `linelogic/nba/features/`
  - `RestScheduleFeatures`
  - `TravelTimezoneFeatures`
  - `FormFeatures` (rolling net rating / pace)
  - `MarketFeatures` (implied prob, vig, CLV hooks)  **(add this earlier)**
- `linelogic/models/`
  - `WinProbModel` interface
  - Champion: `LogisticWinModel`
  - Challenger: `GBDTWinModel` (calibrated)
  - `Calibrator` (Platt/isotonic)
- `linelogic/eval/`
  - time-split evaluation
  - log loss, Brier
  - calibration artifacts (buckets + ECE/MCE)
  - stability/segment reports
- `linelogic/storage/`
  - snapshots + model runs + predictions
  - reproducibility manifests

### 10.2 Data contract (POC storage; SQLite is fine)
Minimum tables:
- `games_raw` (schedule/results, with `pulled_at`)
- `snapshots_external` (odds/injuries/news snapshots; generic table or per-source)
- `features_game` (one row per game, with `feature_as_of_ts`)
- `indexes_team_daily` (Elo/SRS/efficiency, per team per date)
- `model_runs` (config + git SHA + versions)
- `predictions` (game_id, prob, timestamps, model_version)
- `paper_bets` (paper portfolio)  **(add early)**

---

## 11) Implementation plan (milestones)

### Milestone M0 — Leak-proof and reproducible
**Goal:** We trust evaluation numbers.

Deliverables:
1) Season-forward / forward-chaining split utilities
2) `FeatureAuditReport` + tests that fail on any `datetime >= game_datetime`
3) Rebuild any season-level advanced metrics to be as-of (or replace with priors)

Exit criteria:
- “Leakage test suite” passes
- Reproducible build from raw sources to dataset to predictions

---

### Milestone M1 — Benchmarks + paper validation loop (move this earlier)
**Goal:** Build the loop that makes LineLogic trustworthy.

Deliverables:
- Elo-only baseline
- (If odds available) market implied baseline
- paper portfolio schema + logging UX
- calibration artifacts produced automatically

Exit criteria:
- We can run “today’s slate” in paper mode and store predictions + snapshots + bets
- We can report calibration buckets and baseline comparisons

---

### Milestone M2 — Index backbone + travel + efficiency features
**Goal:** Strong interpretable signals with explainable shifts.

Deliverables:
- `EloIndexBuilder` (538-inspired)
- `RollingEfficiencyBuilder` (net rating / pace windows)
- `TravelTimezoneFeatures`

Exit criteria:
- Out-of-time improvement vs Elo-only
- Stable calibration; no weird probability spikes

---

### Milestone M3 — Roster strength and uncertainty modeling
**Goal:** Convert “injury info” into magnitude and confidence.

Deliverables:
- minutes-share availability MVP
- impact × minutes (if feasible)
- uncertainty flags for questionable/unknown data

Exit criteria:
- incremental improvement and better explanations (not just score)

---

### Milestone M4 — Market priors + CLV (if not already in M1)
**Goal:** Measure skill against the market, not just outcomes.

Deliverables:
- odds ingestion snapshots
- vig handling
- market prior blend
- CLV tracking in paper mode

Exit criteria:
- stable calibration + positive CLV trend (over a meaningful sample)

---

## 12) Detailed new feature specs (build notes)

### 12.1 TravelTimezoneFeatures
**Inputs:** team home arena coords + time zone, schedule w/ tipoff times  
**Outputs:** travel_km, tz_shift, eastward_flag, schedule density + interactions

Research:
- https://pmc.ncbi.nlm.nih.gov/articles/PMC8636381/
- https://www.tandfonline.com/doi/abs/10.1080/07420528.2022.2113093

### 12.2 RollingEfficiencyBuilder
Compute rolling:
- possessions estimate
- off/def/net rating
- pace
- windows: 5/10/20 + optional exponential decay

References:
- https://www.basketball-reference.com/about/factors.html
- https://cleaningtheglass.com/stats/guide/league_four_factors

### 12.3 RosterStrengthBuilder (MVP → upgraded)
**MVP:** last-7 games minutes shares, remove unavailable players, renormalize  
**Upgraded:** multiply minutes shares by impact metrics (EPM/DARKO), aggregate

References:
- https://dunksandthrees.com/about/epm
- https://dunksandthrees.com/ratings
- https://www.nbastuffer.com/analytics101/darko-daily-plus-minus/
- https://apanalytics.shinyapps.io/DARKO/

---

## 13) “Next 12 tasks” backlog (copy into issues)

1) Implement forward-chaining split utilities (season-forward + rolling-origin)
2) Implement Feature Audit registry + leakage unit tests
3) Convert any season-level advanced metric into as-of computation or priors
4) Implement EloIndexBuilder baseline
5) Add evaluation artifacts: log loss, Brier, calibration buckets, ECE/MCE summary
6) Create snapshot store schema (odds/injuries/news) with `observed_at`
7) Add paper portfolio schema + “log paper bet” workflow
8) Add travel/timezone feature builder
9) Add rolling efficiency features (net rating / pace windows)
10) Implement Champion logistic + Challenger calibrated GBDT scaffolding
11) Add market implied probability baseline (if odds ingested)
12) Build “model card” output for each model run (assumptions, limits, versions)

---

## 14) Appendix — What we keep vs change immediately

### Keep
- Log loss + Brier as primary metrics
- Elo + rest + recent form as baseline signals
- Feature pruning and regularization discipline

### Change immediately
- Enforce forward-chaining splits (no random stratified for headline results)
- Enforce snapshotting and as-of semantics for anything time-varying
- Replace coarse injury counts with magnitude-based roster strength (when feasible)
- Add market baselines and paper validation loop early

---

**Optional companion doc (recommended next):**
`docs/08_leakage_audit_checklist.md` — concrete unit tests, feature DoD checklist, and a dataset validator that fails the build when any as-of rule is violated.
