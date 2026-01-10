# Backtesting and Paper Trading

## Overview

**Backtesting** validates models on historical data. **Paper trading** validates models on live games without risking real money. Both are **mandatory** before any real-money deployment.

This document outlines LineLogic's approach to rigorous, leak-free validation.

---

## Key Principles

### 1. No Leakage

**Leakage** = using information that wouldn't be available at bet placement time.

**Common leakage sources:**

- Using post-game injury reports to predict game outcomes
- Training on data that includes the target variable (circular reference)
- Peeking at closing lines before bet placement
- Using future games to inform past predictions

**Prevention:**

- Strict temporal ordering: only use data **before** bet timestamp
- Train/test split by date, not random shuffle
- Snapshot all data with timestamps

---

### 2. Out-of-Sample Testing

**Problem:** Models can overfit to training data and fail on new data.

**Solution:**

1. **Train set**: 2022-2023 seasons
2. **Validation set**: 2023-2024 season (for hyperparameter tuning)
3. **Test set**: 2024-2025 season (never touched until final evaluation)

**Walk-forward validation:**

- Train on N months, predict next month
- Slide window forward, retrain
- Simulates production deployment (models retrain periodically)

---

### 3. Realistic Assumptions

Backtests must reflect **real-world constraints**:

- **Odds availability**: Not all lines are available at all times
- **Line movement**: Odds change; you may not get your desired price
- **Stake limits**: Books limit sharp bettors
- **Fees**: Credit card fees, withdrawal fees (typically 2-5%)
- **Slippage**: Odds move between decision and execution

**Conservative approach:**

- Assume worst available odds (worst of 3 sportsbooks)
- Assume 2% fee on deposits/withdrawals
- Assume stake limits (max $1000 per bet for props)

---

## Backtest Architecture

### Data Requirements

1. **Historical games** (2022-2025)
   - Scores, player stats, dates
   - Source: `nba_api` (one-time backfill)

2. **Historical odds** (if available)
   - Opening and closing lines
   - Source: The Odds API (paid feature) or scraping

3. **Historical injuries**
   - Questionable/out players
   - Source: ESPN scraping (manual backfill)

4. **Historical weather** (NFL/MLB only)
   - Game-time conditions
   - Source: WeatherAPI historical (paid)

### Backtest Workflow

```
For each game in test set:
    1. Snapshot available data at T-24h (day before game)
    2. Generate features
    3. Run model → predicted probability
    4. Compare to market line (if available)
    5. Calculate edge
    6. If edge > threshold:
        a. Log recommendation
        b. Calculate stake (fractional Kelly)
        c. Apply exposure caps
    7. After game settles:
        a. Record outcome (win/loss)
        b. Calculate profit/loss
        c. Update bankroll
```

### Evaluation Metrics

**Per-backtest run:**

- **Total bets**: N
- **Win rate**: W / N
- **ROI**: Total profit / Total staked
- **Sharpe ratio**: Mean return / Std dev of returns
- **Max drawdown**: Largest peak-to-trough bankroll decline
- **Brier score**: Calibration metric
- **CLV** (if closing lines available): % of bets beating close

**Report format:**

```
=== Backtest Results: 2024-25 Season ===
Total bets:        237
Win rate:          53.2%
ROI:               6.8%
Total staked:      $47,400
Total profit:      $3,223
Max drawdown:      -$1,890 (4.0%)
Brier score:       0.192
CLV (avg):         +2.1%
Sharpe ratio:      1.23
```

---

## Avoiding Overfitting

### Problem: Curve Fitting

**Bad:** Model fits noise in training data, fails on test data.

**Example:**

- Train model with 50+ features on 1000 games
- Perfect fit on training set (100% accuracy)
- Test set: 48% accuracy (worse than coin flip)

### Solutions

#### 1. Simple Models First

Start with interpretable, low-complexity models:

- **Linear regression** (OLS)
- **Generalized Linear Models** (Poisson, logistic)
- **Decision trees** (max depth 3-5)

Only increase complexity if simple models fail.

---

#### 2. Regularization

**L1 (Lasso):** Shrinks weak features to zero (feature selection)

**L2 (Ridge):** Penalizes large coefficients (smoothing)

**Elastic Net:** Combines L1 + L2

**XGBoost/LightGBM:** Built-in regularization via:

- `max_depth` (tree depth)
- `min_child_weight` (min samples per leaf)
- `lambda` (L2 penalty)
- `alpha` (L1 penalty)

---

#### 3. Cross-Validation

**Time-series CV (walk-forward):**

```
Fold 1: Train 2022-23 | Test Oct 2023
Fold 2: Train 2022-Oct 2023 | Test Nov 2023
Fold 3: Train 2022-Nov 2023 | Test Dec 2023
...
```

**Do NOT use random K-fold** (introduces leakage).

---

#### 4. Holdout Test Set

**Critical:** Never touch test set until final evaluation.

- Train on 2022-2023
- Validate on 2023-2024 (tune hyperparameters)
- **Test on 2024-2025 ONCE** (final evaluation)

If test performance is poor, **do not retrain on test set**. Start over with new hypothesis.

---

#### 5. Feature Engineering Discipline

**Bad features:**

- Derived from target (e.g., "player scored 30+ in this game")
- Too specific (e.g., "Tuesday night games in January vs. Western Conference")
- Data-mined (e.g., "if temperature is 67°F and wind is 8 mph, bet Over")

**Good features:**

- Historical averages (last 10 games, season-long)
- Opponent strength (defensive rating, pace)
- Context (home/away, rest days, injury status)

**Rule:** Every feature must have a **causal story**. "Why would this predict outcome?"

---

## Paper Trading

### What is Paper Trading?

**Simulated betting** with live games but no real money.

**Purpose:**

- Validate model on current season (not historical)
- Test execution workflow (data → model → recommendation → tracking)
- Build confidence before real money

---

### Paper Trading Workflow

#### Daily Routine

**Morning:**

1. Fetch today's games from BALLDONTLIE
2. Fetch current player stats and injury reports
3. Generate features for all player props
4. Run model → predictions
5. Compare to market lines (manual check on DraftKings/FanDuel)
6. Generate recommendations (edge > 5%)
7. Log to database (recommendations table)

**Evening (after games):**

1. Fetch game results
2. Fetch player stats (points, assists, rebounds)
3. Match results to recommendations
4. Update results table (win/loss, actual value)
5. Calculate P&L
6. Update bankroll
7. Generate daily report

---

### Paper Trading Schema

**recommendations table:**

```sql
CREATE TABLE recommendations (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    sport TEXT,
    game_id TEXT,
    market TEXT,  -- e.g., "player_points_over_under"
    selection TEXT,  -- e.g., "LeBron James Over 25.5"
    model_prob REAL,  -- our predicted probability
    market_prob REAL,  -- market implied probability (vig-removed)
    edge REAL,  -- model_prob - market_prob
    stake_suggested REAL,  -- fractional Kelly stake
    kelly_fraction REAL,  -- e.g., 0.25
    bankroll_at_time REAL,
    notes TEXT,
    model_version TEXT
);
```

**odds_snapshots table:**

```sql
CREATE TABLE odds_snapshots (
    id INTEGER PRIMARY KEY,
    recommendation_id INTEGER,
    source TEXT,  -- e.g., "DraftKings", "FanDuel"
    captured_at TEXT,
    line REAL,  -- e.g., 25.5
    odds_american INTEGER,  -- e.g., -110
    odds_decimal REAL,  -- e.g., 1.91
    raw_payload_json TEXT,
    FOREIGN KEY (recommendation_id) REFERENCES recommendations(id)
);
```

**results table:**

```sql
CREATE TABLE results (
    id INTEGER PRIMARY KEY,
    recommendation_id INTEGER,
    settled_at TEXT,
    outcome_win_bool INTEGER,  -- 1 = win, 0 = loss
    outcome_value_numeric REAL,  -- e.g., LeBron scored 28 (Over 25.5)
    profit_loss REAL,  -- stake × (odds - 1) or -stake
    raw_payload_json TEXT,
    FOREIGN KEY (recommendation_id) REFERENCES recommendations(id)
);
```

---

### Example Paper Trade

**Date:** 2026-01-15

**Game:** Lakers vs. Celtics

**Prop:** LeBron James Over 25.5 Points

**Model prediction:**

- P(Over) = 60%
- Market line: -110 (52.4% implied)
- Fair market (vig removed): 50%
- Edge: 60% - 50% = **10%**

**Kelly sizing:**

- Odds: +90 (1.9 decimal, b = 0.9)
- p = 0.60, q = 0.40
- Kelly = (0.60 × 0.9 - 0.40) / 0.9 = 0.144 (14.4%)
- Fractional Kelly (0.25): 0.144 × 0.25 = 0.036 (3.6%)
- Bankroll: $1,000
- Stake: $36

**Log recommendation:**

```sql
INSERT INTO recommendations (created_at, sport, game_id, market, selection, model_prob, market_prob, edge, stake_suggested, kelly_fraction, bankroll_at_time, model_version)
VALUES ('2026-01-15 10:00:00', 'NBA', 'LAL_BOS_20260115', 'player_points_over_under', 'LeBron James Over 25.5', 0.60, 0.50, 0.10, 36.00, 0.25, 1000.00, 'baseline_v1');
```

**Capture odds:**

```sql
INSERT INTO odds_snapshots (recommendation_id, source, captured_at, line, odds_american, odds_decimal)
VALUES (1, 'DraftKings', '2026-01-15 10:00:00', 25.5, -110, 1.91);
```

**After game (LeBron scores 28 points):**

```sql
INSERT INTO results (recommendation_id, settled_at, outcome_win_bool, outcome_value_numeric, profit_loss)
VALUES (1, '2026-01-15 22:30:00', 1, 28.0, 32.76);  -- $36 × (1.91 - 1) = $32.76 profit
```

**Update bankroll:**

```
$1,000 + $32.76 = $1,032.76
```

---

### Paper Trading Evaluation (Weekly)

**Metrics to track:**

- **Weekly ROI**: (Profit this week) / (Staked this week)
- **Cumulative ROI**: (Total profit) / (Total staked)
- **Win rate**: Wins / Total bets
- **Brier score**: Updated weekly
- **CLV**: If closing lines tracked

**Dashboard (future Streamlit app):**

- Line chart: Bankroll over time
- Bar chart: Weekly P&L
- Calibration plot: Predicted vs. actual by bucket
- Table: Top 10 wins and losses (learn from mistakes)

---

## Simulation vs. Reality

### Limitations of Paper Trading

**Paper trading is NOT the same as real betting:**

1. **No execution risk**: You always "get" the line you want
2. **No stake limits**: Real books cap sharp bettors
3. **No emotional impact**: Losing fake money doesn't hurt
4. **No market impact**: Your bets don't move lines

### Bridging the Gap

**Conservative adjustments:**

- Assume you get **2nd-best odds** (not best)
- Assume **10% of recommended bets are unavailable** (lines pulled)
- Track **line movement**: Did odds worsen by bet time?

**Emotional preparation:**

- Treat paper trading seriously (set aside time daily)
- Track every bet (no cherry-picking)
- Accept losses as learning opportunities

---

## Transition to Real Money (Future)

### Readiness Checklist

**Do NOT bet real money until:**

- ✅ **300+ paper trades** (statistical significance)
- ✅ **Positive ROI** over 3+ months
- ✅ **Positive CLV** (if closing lines tracked)
- ✅ **Well-calibrated** (Brier <0.20)
- ✅ **Max drawdown <20%** (risk tolerance)
- ✅ **Workflow is automated** (no manual errors)
- ✅ **Bankroll is disposable** (can afford to lose 100%)

### Real Money Strategy

**Start small:**

- Initial bankroll: $1,000-$5,000 (not life savings)
- Fractional Kelly: 0.25 or lower (0.1 for very conservative)
- Max bet: $50 (override Kelly if it suggests more)
- Track **everything** (same schema as paper trading)

**Scale gradually:**

- After 100 bets: If ROI >3%, increase bankroll by 20%
- After 300 bets: If ROI >5%, increase to full Kelly 0.25
- After 500 bets: Consider increasing fractional Kelly to 0.33

**Stop-loss:**

- If drawdown >30%, **pause all betting**
- Re-evaluate model, check for data issues
- Resume only after fixes validated in paper trading

---

## Backtest Pitfalls and Solutions

### Pitfall 1: Survivor Bias

**Problem:** Only analyzing bets that were placed (ignoring rejected bets).

**Solution:** Log **all** model outputs, not just recommendations.

---

### Pitfall 2: Data Snooping

**Problem:** Peeking at test set, retraining, peeking again.

**Solution:** Lock test set. Only look once.

---

### Pitfall 3: Ignoring Correlations

**Problem:** Betting 5 props on same game, treating as independent.

**Solution:** Track per-game exposure. Use conservative caps.

---

### Pitfall 4: Recency Bias

**Problem:** Overweighting recent losses (model works, just unlucky).

**Solution:** Track CLV. If CLV is positive but ROI is negative, it's likely variance.

---

### Pitfall 5: Overfitting to Market Inefficiencies

**Problem:** Model learns to exploit specific sportsbook quirks that don't generalize.

**Example:** FanDuel always overprices Lakers props → model only bets Lakers.

**Solution:** Test on multiple books. Avoid single-book backtests.

---

## Reporting Template

### Monthly Backtest/Paper Trading Report

```
=== LineLogic Performance Report: January 2026 ===

SUMMARY
-------
Total bets:       48
Win rate:         54.2% (26 wins, 22 losses)
ROI:              7.3%
Total staked:     $960
Total profit:     $70.10
Bankroll (start): $1,000
Bankroll (end):   $1,070.10
Max drawdown:     -$42 (4.2%)

CALIBRATION
-----------
Brier score:      0.183 (good)
Log loss:         0.541 (good)

Calibration by bucket:
| Bucket   | Avg Pred | Wins | Total | Empirical |
|----------|----------|------|-------|-----------|
| 50-55%   | 52.5%    | 5    | 10    | 50.0%     |
| 55-60%   | 57.5%    | 7    | 12    | 58.3%     |
| 60-65%   | 62.5%    | 8    | 14    | 57.1%     |
| 65-70%   | 67.5%    | 6    | 8     | 75.0%     |

Interpretation: Slightly overconfident in 60-65% bucket. Overall well-calibrated.

CLOSING LINE VALUE (if available)
----------------------------------
CLV (avg):        +1.8%
Bets beating close: 58.3% (28/48)

WEEKLY BREAKDOWN
----------------
| Week | Bets | Wins | ROI   | P&L    |
|------|------|------|-------|--------|
| W1   | 12   | 7    | 8.5%  | +$204  |
| W2   | 11   | 6    | 3.2%  | +$71   |
| W3   | 13   | 6    | -2.1% | -$54   |
| W4   | 12   | 7    | 19.8% | +$480  |

TOP WINS
--------
1. LeBron Over 25.5 pts (+$380, 60% → 28 pts)
2. Tatum Over 6.5 asts (+$290, 58% → 9 asts)
3. Curry Over 4.5 3PM (+$250, 62% → 6 3PM)

TOP LOSSES
----------
1. Durant Over 27.5 pts (-$360, 65% → 22 pts)
2. Embiid Over 10.5 rebs (-$320, 60% → 8 rebs)
3. Harden Over 8.5 asts (-$310, 58% → 6 asts)

LESSONS LEARNED
---------------
- Model performed well in weeks with normal variance
- Week 3 suffered from injury surprises (need better injury data)
- Top losses: All involved players with recent injury history (missed in features)
- Next steps: Add "games since injury" feature

RECOMMENDATIONS
---------------
- Continue paper trading for 2+ more months (need 300+ bets)
- Improve injury tracking (scrape ESPN daily, not weekly)
- Consider adding "recent trend" feature (last 3 games vs. last 10)
```

---

## Conclusion

**Backtesting and paper trading are non-negotiable.** They are the only way to validate that LineLogic's models work without risking real money.

**Best practices:**

1. **Leak-free backtests** (temporal ordering, realistic assumptions)
2. **Out-of-sample testing** (never touch test set until final eval)
3. **Avoid overfitting** (simple models, regularization, cross-validation)
4. **Rigorous paper trading** (daily routine, full logging, weekly reports)
5. **Transition to real money only after 300+ successful paper trades**

---

**Next**: [Risks and Compliance](06_risks_and_compliance.md) | [Architecture](../adr/0001_architecture.md)
