# Modeling Strategy

## Overview

LineLogic uses a hybrid modeling approach that combines historical NBA data with live market odds to generate profitable betting recommendations. This document outlines our feature engineering, model architecture, training strategy, and evaluation framework.

---

## Approach: Hybrid Historical + Live Learning

### Phase 1: Historical Model (Weeks 1-2)
- **Data Source**: BALLDONTLIE API (2022-2024 seasons)
- **Goal**: Build baseline win probability model
- **Output**: Replace 52% stub with data-driven probabilities

### Phase 2: Live Calibration (Weeks 3-8)
- **Data Source**: Daily recommendations + TheOddsAPI odds + game results
- **Goal**: Calibrate model against real market behavior
- **Output**: Refined probabilities accounting for market inefficiencies

### Phase 3: Continuous Learning (Ongoing)
- **Data Source**: Growing database of picks, odds, and results
- **Goal**: Adapt to evolving market conditions and team dynamics
- **Output**: Self-improving model via weekly retraining

---

## Model Architecture

### Initial Model: Logistic Regression (Baseline)
Simple, interpretable, fast to train, easy to debug.

**Why start here:**
- Establishes baseline performance
- Fast iteration on feature engineering
- Transparent coefficients for auditing
- Low risk of overfitting with limited data

### Future Models (Post-Phase 2):
- **Gradient Boosted Trees** (XGBoost/LightGBM) for non-linear patterns
- **Neural Networks** for complex feature interactions
- **Ensemble Methods** combining multiple model types

---

## Target Variable

### Primary Target: Win Probability
```
P(Team Wins) ∈ [0, 1]
```

**Binary outcome:**
- `1` = Team won
- `0` = Team lost

**Rationale:**
- Moneyline bets are win/loss binary
- Probabilities map directly to implied odds
- Edge = Model Prob - Market Prob

---

## Feature Engineering

### Core Features (Phase 1)

#### 1. Team Strength Metrics
- **Elo Rating** (custom implementation)
  - Starting Elo: 1500
  - K-factor: 20 (adjusts based on margin of victory)
  - Rolling window: season-to-date
- **Win Rate** (last 10, 20 games)
- **Point Differential** (last 10 games)
- **Offensive/Defensive Efficiency** (points per 100 possessions)

#### 2. Situational Features
- **Home Court Advantage** (binary: 1 = home, 0 = away)
- **Rest Days** (0 = back-to-back, 1 = one day rest, 2+ = full rest)
- **Travel Distance** (miles between cities, proxy via lat/lon)
- **Season Progress** (games played / 82)

#### 3. Head-to-Head
- **Season H2H Record** (wins in current season matchup)
- **Last Meeting Result** (win/loss, margin)
- **Historical H2H Win Rate** (last 3 seasons)

#### 4. Recent Form
- **Streak** (current win/loss streak length)
- **Last 5 Games Result** (W-L record)
- **Recent Point Differential Trend** (improving/declining)

#### 5. Schedule Factors
- **Back-to-Back** (binary: playing 2nd game in 2 days)
- **3-in-4 Nights** (fatigue indicator)
- **Post-West-Coast Trip** (home team after road trip)

### Advanced Features (Phase 2+)

#### 6. Market-Derived Features
- **Opening Line Movement** (odds shift from open to close)
- **Sharp Money Indicator** (reverse line movement)
- **Public Betting %** (if available from external sources)
- **Historical Line Value** (team's ATS performance at similar lines)

#### 7. Injury & Roster
- **Key Player Availability** (starter out/in)
- **Minutes Restriction** (player returning from injury)
- **Lineup Change Impact** (new rotation)

#### 8. Opponent-Adjusted Metrics
- **Opponent-Adjusted Offensive Rating** (vs. league avg defense)
- **Pace Matchup** (fast vs. slow team)
- **Style Mismatch** (3PT% vs. opponent 3PT defense)

---

## Feature Importance & Selection

### Method
- **Recursive Feature Elimination** (scikit-learn RFE)
- **Mutual Information Scores**
- **SHAP Values** (for tree models)

### Criteria
- Drop features with <0.01 importance score
- Retain features with p < 0.05 in logistic regression
- Monitor multicollinearity (VIF < 5)

---

## Training Strategy

### Data Split
```
Train:      2022-01-01 to 2023-12-31  (~2,500 games)
Validation: 2024-01-01 to 2024-06-30  (~1,250 games)
Test:       2024-10-01 to 2025-04-30  (live season)
```

**Why time-based split:**
- Avoid data leakage (no future information)
- Simulates real-world deployment
- Tests model on new season dynamics

### Cross-Validation
- **Time Series CV** (5 folds, expanding window)
- Each fold: train on past, test on future
- Prevents look-ahead bias

### Hyperparameter Tuning
- **Grid Search** for logistic regression (C, penalty)
- **Bayesian Optimization** for tree models (max_depth, learning_rate)
- Optimize for **log loss** (calibration) not just accuracy

---

## Evaluation Metrics

### Primary Metrics

#### 1. Log Loss (Cross-Entropy)
```
LogLoss = -Σ [y * log(p) + (1-y) * log(1-p)]
```
**Why:** Penalizes confident incorrect predictions; rewards calibration.

**Target:** < 0.60 (better than random guessing)

#### 2. Brier Score
```
Brier = Σ (p - y)² / N
```
**Why:** Measures probability accuracy; lower is better.

**Target:** < 0.20

#### 3. ROI (Return on Investment)
```
ROI = (Profit / Total Staked) * 100
```
**Why:** Real-world profitability measure.

**Target:** > 5% sustained over 100+ bets

### Secondary Metrics

#### 4. Accuracy
```
Accuracy = Correct Predictions / Total Predictions
```
**Target:** > 55% (breakeven with -110 odds ≈ 52.4%)

#### 5. Calibration Curve
- Bins: [0-10%, 10-20%, ..., 90-100%]
- Plot: Predicted Prob vs. Actual Win Rate
- **Target:** Predictions aligned with reality (diagonal line)

#### 6. Sharpe Ratio (Risk-Adjusted Return)
```
Sharpe = (Mean Return - Risk-Free Rate) / Std Dev of Returns
```
**Target:** > 1.0 (good), > 2.0 (excellent)

#### 7. Max Drawdown
```
MaxDrawdown = Peak Bankroll - Trough Bankroll
```
**Target:** < 20% of starting bankroll

---

## Edge Detection & Bet Selection

### Edge Calculation
```
Edge = Model Probability - Market Implied Probability
```

**Market Implied Probability:**
```
For American odds:
  If odds > 0:  Prob = 100 / (odds + 100)
  If odds < 0:  Prob = |odds| / (|odds| + 100)
```

### Bet Filtering Criteria
```python
def should_bet(model_prob, market_prob, edge_threshold=0.02):
    edge = model_prob - market_prob
    return edge >= edge_threshold
```

**Thresholds:**
- **Minimum Edge:** 2% (adjustable based on performance)
- **Model Confidence:** Model Prob > 52% (avoid coin flips)
- **Sample Size:** Skip first 10 games (warm-up period for Elo)

---

## Kelly Criterion Staking

### Formula
```
Kelly % = (Edge * Model Prob) / (Market Prob * (1 - Market Prob))
```

### Fractional Kelly (Risk Management)
```
Stake = Bankroll * (Kelly % * Fraction)
```

**Fraction:** 25% (Quarter Kelly) to reduce variance

**Constraints:**
- Min Stake: $1
- Max Stake: 5% of bankroll (cap risk)

---

## Model Versioning & Tracking

### Schema (Already in DB)
```sql
CREATE TABLE model_versions (
    version TEXT PRIMARY KEY,
    created_at TEXT,
    git_sha TEXT,
    config_json TEXT
)
```

**Config JSON includes:**
- Feature list
- Hyperparameters
- Training date range
- Evaluation metrics
- Data sources

### Version Naming
```
v{major}.{minor}.{patch}_{YYYYMMDD}
```
Example: `v1.0.0_20260110` (initial logistic regression)

---

## Retraining Schedule

### Phase 1: Weekly
- Every Monday after weekly-summary
- Use all historical + past week's live data
- Compare performance to previous version

### Phase 2: Bi-Weekly
- Once model stabilizes (after 8 weeks)
- Retrain only if new data shows drift

### Phase 3: Monthly
- Mature model (6+ months of data)
- Focus on feature engineering and new data sources

### Trigger Conditions (Retrain Immediately If:)
- ROI drops below 0% for 2 consecutive weeks
- Brier score increases >10% from baseline
- Market conditions change (new season, playoffs)

---

## Backtesting Framework

### Walk-Forward Backtesting
1. Train on data up to date `t`
2. Predict on games from `t` to `t+7 days`
3. Record predictions, odds, outcomes
4. Slide window forward 7 days
5. Repeat for entire test period

### Performance Simulation
```python
def backtest(model, historical_games, starting_bankroll=1000):
    bankroll = starting_bankroll
    for game in historical_games:
        model_prob = model.predict_proba(game.features)
        market_prob = game.implied_probability
        edge = model_prob - market_prob
        
        if edge >= 0.02:
            kelly = calculate_kelly(model_prob, market_prob)
            stake = bankroll * kelly * 0.25  # Fractional Kelly
            outcome = game.result  # 1 = win, 0 = loss
            pnl = calculate_pnl(stake, game.odds, outcome)
            bankroll += pnl
    
    return bankroll, roi, sharpe, max_drawdown
```

---

## Risk Management

### Bankroll Protection
- **Starting Bankroll:** $1,000 (adjustable)
- **Max Daily Risk:** 10% of bankroll
- **Stop-Loss:** Pause betting if bankroll drops 30%
- **Profit-Taking:** Lock gains quarterly, reset bankroll

### Bet Sizing Limits
- **Min Bet:** $1 (avoid micro-stakes)
- **Max Bet:** 5% of bankroll (cap Kelly outliers)
- **Max Simultaneous Bets:** 10 per day (diversification)

### Model Confidence Thresholds
- **High Confidence:** Edge ≥ 5% → Increase stake to 1.5x
- **Low Confidence:** Edge < 3% → Reduce stake to 0.5x
- **No Bet Zone:** Edge < 2% → Skip

---

## Success Criteria

### Phase 1 (Weeks 1-2)
- ✅ Model trains without errors
- ✅ Backtest ROI > 0% on 2023-2024 season
- ✅ Calibration curve shows reasonable alignment
- ✅ Log Loss < 0.65

### Phase 2 (Weeks 3-8)
- ✅ Live ROI > 2% over 50+ bets
- ✅ Sharpe Ratio > 0.5
- ✅ Win Rate > 52%
- ✅ Max Drawdown < 25%

### Phase 3 (Months 3-6)
- ✅ Sustained ROI > 5% over 200+ bets
- ✅ Sharpe Ratio > 1.0
- ✅ Profitable across multiple books
- ✅ Model generalizes to playoffs

---

## Next Steps

1. **Implement Elo Rating System** (custom, team-level)
2. **Build Feature Pipeline** (transform raw BALLDONTLIE data)
3. **Train Baseline Logistic Regression**
4. **Backtest on 2023-2024 Season**
5. **Replace Stub Model in `recommend-daily`**
6. **Deploy v1.0.0 Model**
7. **Monitor Live Performance** (daily emails + dashboard)
8. **Iterate on Features** (add market signals in Phase 2)

---

## Tools & Libraries

### Data & Feature Engineering
- `pandas`, `numpy` (data manipulation)
- `scikit-learn` (feature scaling, encoding)

### Modeling
- `scikit-learn` (logistic regression, cross-validation)
- `xgboost`, `lightgbm` (future gradient boosting)

### Evaluation
- `scikit-learn.metrics` (log_loss, brier_score)
- `matplotlib`, `plotly` (calibration curves, ROI charts)

### Experiment Tracking
- JSON config files (stored in `model_versions` table)
- Git SHA for reproducibility

---

## References

- [Kelly Criterion](https://en.wikipedia.org/wiki/Kelly_criterion)
- [Elo Rating System](https://en.wikipedia.org/wiki/Elo_rating_system)
- [Log Loss Explained](https://en.wikipedia.org/wiki/Cross_entropy)
- [Brier Score](https://en.wikipedia.org/wiki/Brier_score)
- [Sharpe Ratio](https://en.wikipedia.org/wiki/Sharpe_ratio)

---

**Last Updated:** 2026-01-10  
**Status:** Phase 1 - Ready to Implement
