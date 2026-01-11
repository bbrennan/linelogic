# LineLogic — NBA Game Winner Modeling (Doc + Implementation Plan)

**Last updated:** 2026-01-10  
**Owner:** LineLogic  
**Objective:** Produce **leakage-safe** pregame probabilities `P(home_win)` for NBA games, with clean evaluation (log loss / Brier / calibration) and a clear path to adding market priors and roster/injury intelligence.

---

## 0) Why this doc exists

We already have a promising POC model (per your summary). This doc:

1. **Surveys proven modeling techniques** for NBA game-winner prediction.
2. Gives a **strong, opinionated review** of the current model (what’s solid vs what’s risky).
3. Defines a **leakage-safe data contract** (“as-of” feature semantics).
4. Proposes **new feature families** with explicit build steps.
5. Lists **all target data sources** (sports + injuries + odds + travel/timezone + weather + social/news), with links to the most credible references.
6. Provides an **implementation plan** (modules, classes, and milestones).

---

## 1) Strong, opinionated review of the current POC model

### 1.1 What’s strong
- You’re using **proper scoring rules** (log loss + Brier). That’s the correct evaluation framework for probability models.
- Your feature set is directionally correct: **team strength (Elo), rest, recent form**, and some roster intelligence.
- Feature selection + collinearity pruning is good hygiene.

### 1.2 What’s concerning (and must be resolved before we trust the numbers)
Your reported lift from ~53% to ~69% accuracy with log loss ~0.47 is *possible*, but **it’s “too good” unless the pipeline is extremely clean**. In my experience, this level of jump often indicates one or more of:

#### A) Leakage through season-level “advanced metrics”
If your CSV contains **end-of-season PER/BPM/WS48** and you’re applying it to games earlier in the same season, that is look-ahead leakage. Basketball-Reference style season aggregates are descriptive; unless you build them as-of date, you’re using future information.

**Hard rule:** any season-level metric used in a pregame model must be either:
- prior-season-based (a prior), or
- computed strictly from games **before** the game date.

#### B) Leakage through lineup continuity / “starter” artifacts
Lineup continuity is useful, but dangerous. If “starter” flags or minutes reflect postgame outcomes (or include the current game), your model will look fantastic for the wrong reason.

**Hard rule:** lineup/continuity features must be computed using **only games before tipoff**.

#### C) Split strategy risk
Your summary says “stratified POC.” If this means random stratified splitting, it can cause subtle leakage (e.g., team identity effects learned from later-season games influence earlier-season predictions). NBA is time-dependent; you want time-aware validation.

**Hard rule:** primary validation is **time-based**, ideally:
- train: seasons up to year N-1
- validate: season N (early)
- test: season N (late) or season N+1

### 1.3 Bottom line
Your current model is a great *prototype*, but before we celebrate the scores we must make it **compliance-grade leakage-safe**. Expect performance to drop after the audit. That’s okay; trustworthy > flashy.

---

## 2) Advanced survey: NBA game winner modeling techniques

This section outlines the techniques we’ll support (or at least benchmark against), ordered by practical value.

### 2.1 Market baseline (later phase, but the ultimate benchmark)
If you have access to **moneyline/spread**, the market is generally the strongest single predictor because it aggregates injuries, rest, matchup, and public/pro info.

- A standard strategy is to treat the market probability as a **prior** and model a small residual.
- This is not “defeatist”; it’s realistic. The bar is beating a sharp baseline.

References / starting points:
- The Odds API (odds + markets docs): https://the-odds-api.com/  
- Betting markets & player props markets overview: https://the-odds-api.com/sports-odds-data/betting-markets.html  
- v4 API guide (oddsFormat, endpoints): https://the-odds-api.com/liveapi/guides/v4/

### 2.2 Elo family (must-have baseline)
Elo remains one of the best **simple, robust** NBA win models when implemented correctly (home advantage + margin of victory multiplier).

FiveThirtyEight’s NBA Elo details include a margin-of-victory multiplier formula:
- https://fivethirtyeight.com/features/how-we-calculate-nba-elo-ratings/

Related methodology overview:
- https://fivethirtyeight.com/methodology/how-our-nba-predictions-work/

### 2.3 SRS / points-differential power ratings
SRS (Simple Rating System) is a team rating in points above/below average that incorporates strength of schedule.

- Sports-Reference “SRS calculation details”: https://www.sports-reference.com/blog/2015/03/srs-calculation-details/
- Basketball-Reference blog SRS page: https://www.basketball-reference.com/blog/indexba52.html?p=39
- Glossary entry: https://www.basketball-reference.com/about/glossary.html

### 2.4 Efficiency / Four-Factors style models (possession-based)
A strong modeling path is:
1) estimate possessions (pace)
2) estimate offense/defense efficiency (per 100 poss)
3) derive expected margin
4) map margin to win probability

Four Factors references:
- Basketball-Reference Four Factors page: https://www.basketball-reference.com/about/factors.html  
- Cleaning the Glass Four Factors guide: https://cleaningtheglass.com/stats/guide/league_four_factors  
- Background: https://squared2020.com/2017/09/05/introduction-to-olivers-four-factors/

### 2.5 Player-impact driven models (high leverage)
These are typically superior to PER/WS48 for win prediction because they estimate **impact on point differential**.

EPM (Estimated Plus-Minus):
- EPM methodology: https://dunksandthrees.com/about/epm  
- Team EPM explanation (minutes-weighted aggregation): https://dunksandthrees.com/ratings  
- EPM page (predictive framing): https://dunksandthrees.com/epm

DARKO / DPM:
- Explanation page (DARKO acronym + predictive intent): https://www.nbastuffer.com/analytics101/darko-daily-plus-minus/  
- DARKO app: https://apanalytics.shinyapps.io/DARKO/

### 2.6 Bayesian / state-space models (optional, “math first”)
Team strength evolves over time. A state-space model (random walk on latent team strength with updates from outcomes/margins + covariates like travel/rest/injuries) tends to improve calibration and stabilize early season predictions.

We won’t implement this first, but we’ll design the system so it can be added.

---

## 3) “Indexes” (ratings) we should support and how they’re built

### 3.1 EloIndex (winner-focused)
**Inputs:** game results (winner), optional margin of victory, home/away  
**Output:** `elo_home`, `elo_away`, `elo_diff`, `p_home_win_elo`

**Build:**
- Initialize team ratings (e.g., 1500).
- Home advantage offset.
- Expected win probability = logistic function of elo diff.
- Update = K × MOV multiplier × (actual - expected).

Reference:
- https://fivethirtyeight.com/features/how-we-calculate-nba-elo-ratings/

### 3.2 SRSLikeIndex (points-focused)
**Inputs:** points for/against, opponent schedule  
**Output:** points-above/below-average rating and SOS components.

Reference:
- https://www.sports-reference.com/blog/2015/03/srs-calculation-details/

### 3.3 Rolling efficiency indexes (net rating / pace / four factors)
**Inputs:** box score totals (FG, 3P, FT, TOV, ORB, possessions estimates)  
**Output:** rolling off/def/net ratings, pace, and four factor components.

References:
- https://www.basketball-reference.com/about/factors.html
- https://cleaningtheglass.com/stats/guide/league_four_factors

### 3.4 RosterStrengthIndex (minutes-weighted player impact)
**Inputs:** player impact (EPM/DARKO/etc), expected minutes, injury status  
**Output:** `team_available_strength`, `strength_diff`, plus uncertainty flags.

EPM shows a canonical “team rating = sum(player impact × predicted minutes)” concept:
- https://dunksandthrees.com/about/epm
- https://dunksandthrees.com/ratings

---

## 4) Feature roadmap (what to add next, and how)

### 4.1 Non-negotiable: “As-of” feature semantics
Every feature must be computed as-of pregame. Concretely:
- A game at date D can only use data from games with date < D.
- External data must be stored as **timestamped snapshots** (injuries, odds).

We will implement a **Feature Audit** that records:
- `feature_name`
- `source`
- `as_of_definition`
- `window`
- `leakage_risk_level`
- `unit_test` coverage status

### 4.2 Travel + time zone + circadian disruption (high-value, cheap)
This is a top “mathy” add because it’s:
- easy to compute deterministically
- supported by published research
- not subject to sports data licensing headaches

Open research examples:
- Travel distance/direction impacts on B2B (open access): https://pmc.ncbi.nlm.nih.gov/articles/PMC8636381/
- Circadian change & travel distance associations (journal page): https://www.tandfonline.com/doi/abs/10.1080/07420528.2022.2113093
- General background on air travel/circadian misalignment in elite sports: https://www.mdpi.com/2075-4663/6/3/89

**Implementation notes**
- Map each team to home arena coordinates + time zone.
- For each team’s prior game, compute distance traveled and time zone shift.
- Create schedule density features (3-in-4, 4-in-6, etc.) plus travel interactions.

### 4.3 Rolling per-possession form (better than raw point diff)
Replace raw “pt diff last 10” with:
- rolling net rating (last 5/10/20)
- rolling pace
- rolling four-factor components where possible

This reduces pace confounding and makes form more stable/interpretable.

### 4.4 Roster availability: move from “out count” → impact-weighted strength
Current `home_key_out_count` is too coarse.

Upgrade path:
1) MVP: minutes-weighted “starter-level” availability using last-7-games minutes share.
2) Next: incorporate impact metrics (EPM / DARKO / RAPM-like) and injury knowledge.

Supporting references:
- EPM aggregation explanation: https://dunksandthrees.com/about/epm
- DARKO explanation: https://www.nbastuffer.com/analytics101/darko-daily-plus-minus/
- RAPM resource (optional): https://www.nbarapm.com/

### 4.5 Market prior (later phase, but architect now)
Once odds are ingested, implement a market-prior blend:

`p_final = α * p_market + (1-α) * p_model`

Also compute CLV in paper mode.

Data sources:
- The Odds API: https://the-odds-api.com/
- Markets: https://the-odds-api.com/sports-odds-data/betting-markets.html
- v4 guide: https://the-odds-api.com/liveapi/guides/v4/

---

## 5) Recommended data sources (linked)

### 5.1 Core sports data (NBA/NFL/MLB/MMA coverage)
BALLDONTLIE docs hub:
- https://www.balldontlie.io/docs/

NBA API portal:
- https://nba.balldontlie.io/

Rate limiting example (shows tiered RPM):
- https://cs.balldontlie.io/  (see “Rate Limiting” section)

BALLDONTLIE tiers summary (official GitHub MCP server):
- https://github.com/balldontlie-api/mcp

### 5.2 NBA.com endpoints (research/backfill only)
`nba_api` (unofficial):
- https://github.com/swar/nba_api

**Policy:** keep behind a feature flag; never make it the only dependency.

### 5.3 Odds / props providers (later phase)
- The Odds API: https://the-odds-api.com/
- The Odds API markets: https://the-odds-api.com/sports-odds-data/betting-markets.html
- Sportradar player props overview (enterprise-grade reference): https://developer.sportradar.com/odds/reference/oc-player-props-overview

### 5.4 Weather (primarily NFL, but platform-wide)
US National Weather Service API:
- Overview: https://www.weather.gov/documentation/services-web-api  
- FAQ portal: https://weather-gov.github.io/api/general-faqs

**Note:** NWS requires a descriptive User-Agent header; treat it as a requirement.

### 5.5 Social/news (MVP caution)
These can easily become noisy or misleading. In MVP, treat them as:
- “awareness/uncertainty” signals
- **not** as primary predictive drivers
- always snapshot timestamps and avoid hindsight labeling

(We’ll document these sources once we decide the exact channels.)

---

## 6) Proposed LineLogic architecture for NBA winner modeling

### 6.1 Modules
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
- `linelogic/models/`
  - `WinProbModel` interface
  - baseline `LogisticWinModel`
  - optional `GBDTWinModel`
- `linelogic/eval/`
  - log loss, Brier, calibration buckets
  - time-split evaluation
- `linelogic/storage/`
  - snapshots + model versions

### 6.2 Data contract (tables / artifacts)
Store everything with timestamps and source metadata.

Minimum tables (SQLite for POC):
- `games_raw` (ingested schedule/results, with `pulled_at`)
- `features_game` (one row per game, with `feature_as_of_ts`)
- `indexes_team_daily` (team ratings per date)
- `model_runs` (config + git sha + model version)
- `predictions` (game_id, predicted prob, timestamp, model_version)

---

## 7) Implementation plan (milestones)

### Milestone M0 — Make the pipeline provably leakage-safe
**Goal:** We trust the evaluation numbers.

Deliverables:
1) Implement **time-based splits** (season-forward or rolling-origin).
2) Add `FeatureAuditReport` and a test suite that fails if any feature uses future data.
3) Rebuild any season-level metrics to be **as-of date**.

Exit criteria:
- Unit tests prove no “date >= game_date” data is used.
- Performance may drop; we accept that.

### Milestone M1 — Index backbone: Elo + rolling efficiency + travel
**Goal:** Strong interpretable baseline with explainable shifts.

Deliverables:
- `EloIndexBuilder` with 538-style MOV multiplier
- `RollingEfficiencyBuilder` (net rating, pace)
- `TravelTimezoneFeatures`
- Evaluation report: log loss, Brier, calibration plot data

Exit criteria:
- Elo-only baseline runs end-to-end and produces sane probabilities.
- Added features improve log loss out-of-sample.

### Milestone M2 — Roster strength (impact × minutes)
**Goal:** Convert injuries/availability into magnitude, not counts.

Deliverables:
- `RosterStrengthBuilder` using minutes-based rotation estimates
- Optional impact metric ingestion (EPM/DARKO) if feasible from licensing/data availability
- “uncertainty flags” for questionable/unknown availability

Exit criteria:
- Measurable gain in calibration and/or log loss.

### Milestone M3 — Market prior + CLV (paper mode)
**Goal:** Treat the market as the strongest baseline; measure skill via CLV.

Deliverables:
- Odds ingestion (timestamped)
- Vig removal + implied probability baseline
- Market-prior blend + calibration
- CLV tracking in paper mode

Exit criteria:
- Stable calibration and positive CLV trend over a meaningful sample.

---

## 8) Detailed new feature specs (build notes)

### 8.1 TravelTimezoneFeatures
**Inputs:**
- team home city coordinates + timezone
- game schedule with tipoff times and locations

**Outputs:**
- `home_travel_km`, `away_travel_km` (since last game)
- `home_tz_shift`, `away_tz_shift`
- `home_eastward_shift_flag`, `away_eastward_shift_flag`
- interactions with B2B / 3-in-4

Research:
- https://pmc.ncbi.nlm.nih.gov/articles/PMC8636381/
- https://www.tandfonline.com/doi/abs/10.1080/07420528.2022.2113093

### 8.2 EloIndexBuilder
Use FiveThirtyEight’s published MOV multiplier as a reference implementation:
- https://fivethirtyeight.com/features/how-we-calculate-nba-elo-ratings/

Deliver:
- daily team ratings
- `p_home_win_elo`

### 8.3 RollingEfficiencyBuilder
Compute rolling:
- possessions estimate
- off/def/net rating
- pace

Then build:
- last 5/10/20 windows
- exponentially-weighted variants (optional)

Four factors reference pages:
- https://www.basketball-reference.com/about/factors.html
- https://cleaningtheglass.com/stats/guide/league_four_factors

### 8.4 RosterStrengthBuilder (M2)
**MVP version:**
- Use last-7 games minutes share as expected rotation weights
- If player is out, remove their share and renormalize

**Upgraded version:**
- Multiply expected minutes shares by player impact metrics (EPM/DARKO)
- Aggregate to team strength

References:
- https://dunksandthrees.com/about/epm
- https://dunksandthrees.com/ratings
- https://www.nbastuffer.com/analytics101/darko-daily-plus-minus/
- https://apanalytics.shinyapps.io/DARKO/

---

## 9) “Next 10 tasks” backlog (copy into issues)

1. Implement time-based train/val/test split utilities (season-forward + rolling-origin)
2. Implement `FeatureAuditReport` (metadata + leakage checks)
3. Rebuild advanced metrics as-of date OR replace with prior-season priors
4. Implement `EloIndexBuilder` (538-style MOV multiplier)
5. Implement rolling efficiency features (net rating/pace windows)
6. Implement travel/timezone feature builder
7. Add calibration buckets + reliability reporting artifacts
8. Add model card doc (assumptions, failure modes, monitoring metrics)
9. Implement roster strength MVP (minutes-share availability)
10. Decide odds ingestion provider and design the schema for timestamped odds snapshots

---

## 10) Appendix — POC context (what we keep, what we change)

### Keep
- Log loss + Brier as primary metrics
- Regularization + collinearity pruning (good practice)
- Elo + rest + recent form as a baseline feature family

### Change immediately
- Enforce “as-of” and time-based splits
- Remove or rebuild any feature that can’t be proven pregame-known
- Replace coarse injury counts with magnitude-based roster strength (when possible)

---

**If you want, I can also generate a second markdown file:**
`docs/08_leakage_audit_checklist.md` with concrete unit tests (e.g., “no feature window end >= game_date”) and an automated dataset validator.
