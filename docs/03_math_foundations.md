# Math Foundations

## Overview

LineLogic is built on **quantitative sports betting theory**, combining probability, expected value, portfolio optimization, and evaluation metrics. This document provides the mathematical foundation for all models and recommendations.

## Odds Formats and Conversions

### American Odds

Standard in US sportsbooks:

- **Positive (+150)**: Amount you win on a $100 bet
- **Negative (-150)**: Amount you must bet to win $100

### Decimal Odds

Common in Europe and Australia:

- **Decimal (2.50)**: Total return per $1 bet (includes stake)

### Implied Probability

Convert odds to probability:

**From American:**

```
If odds > 0:
    implied_prob = 100 / (odds + 100)

If odds < 0:
    implied_prob = -odds / (-odds + 100)
```

**From Decimal:**

```
implied_prob = 1 / decimal_odds
```

**Implementation:**

See `src/linelogic/odds/math.py` for full functions with edge case handling.

### Examples

| American | Decimal | Implied Prob | Payout on $100 |
|----------|---------|--------------|----------------|
| +150     | 2.50    | 40.0%        | $150           |
| -150     | 1.67    | 60.0%        | $66.67         |
| +100     | 2.00    | 50.0%        | $100           |
| -200     | 1.50    | 66.7%        | $50            |

---

## Vigorish (Vig) and Fair Odds

### The Problem

Sportsbooks embed a margin (vig) in their odds. For a fair two-way market:

```
P(A) + P(B) = 1.00
```

But bookmaker odds sum to **>1.00** (overround):

```
P_market(A) + P_market(B) = 1.05 to 1.10
```

This 5-10% is the vig.

### Removing Vig

**Proportional Method (Simple):**

```
fair_prob(A) = market_prob(A) / (market_prob(A) + market_prob(B))
fair_prob(B) = market_prob(B) / (market_prob(A) + market_prob(B))
```

**Example:**

- Over 25.5 points: -110 (52.4% implied)
- Under 25.5 points: -110 (52.4% implied)
- Sum: 104.8% (4.8% vig)

Fair odds:

```
P(Over) = 52.4% / 104.8% = 50.0%
P(Under) = 52.4% / 104.8% = 50.0%
```

**Alternative Methods:**

- **Margin proportional to odds**: Allocate vig inversely to implied prob
- **Shin method**: Assumes informed insiders, requires numerical optimization
- **Power method**: Raise each prob to power, then normalize

For LineLogic M0, we use **proportional (simple)**. Document alternatives in code for future experimentation.

---

## Expected Value (EV)

### Definition

Expected value is the **long-run average** profit/loss per bet:

```
EV = (prob_win × payout) - (prob_loss × stake)
```

Or equivalently:

```
EV = (prob_win × (odds + stake)) - stake
EV = stake × (prob_win × odds - prob_loss)
```

### Positive EV (+EV)

A bet with **EV > 0** is profitable in the long run. This is the **only** sustainable reason to bet.

### Example

**Bet:**

- Player Over 25.5 points
- Odds: +110 (2.10 decimal)
- Our model: P(Over) = 55%
- Market implied: P(Over) = 47.6%

**Calculation:**

```
Stake = $100
Payout = $110
prob_win = 0.55
prob_loss = 0.45

EV = (0.55 × $110) - (0.45 × $100)
EV = $60.50 - $45.00
EV = $15.50 per $100 bet (15.5% ROI)
```

**Interpretation:** If we make this bet 1000 times, we expect to win $15,500 on $100,000 wagered.

---

## Edge

### Definition

**Edge** is the difference between our model's probability and the market's fair probability:

```
edge = prob_model - prob_market_fair
```

**Example:**

- Our model: 55%
- Market (vig-removed): 48%
- Edge: 55% - 48% = **7%**

### Minimum Edge Threshold

Due to estimation error, we require a **minimum edge** before betting:

- **Conservative**: 5% edge
- **Moderate**: 3% edge
- **Aggressive**: 1% edge

LineLogic defaults to **5%** for POC to avoid false positives.

---

## Kelly Criterion

### Purpose

Kelly Criterion determines the **optimal stake size** to maximize long-term log wealth.

### Formula

For a two-outcome bet:

```
f* = (p × b - q) / b
```

Where:

- `f*` = fraction of bankroll to bet
- `p` = probability of winning
- `q` = 1 - p (probability of losing)
- `b` = payout ratio (e.g., +150 odds → b = 1.5)

### Example

**Bet:**

- P(win) = 55%
- Odds: +110 (b = 1.1)
- Bankroll: $10,000

```
f* = (0.55 × 1.1 - 0.45) / 1.1
f* = (0.605 - 0.45) / 1.1
f* = 0.155 / 1.1
f* = 0.141 (14.1%)

Optimal bet = 0.141 × $10,000 = $1,410
```

### Kelly Dangers

**Full Kelly is aggressive** and can lead to large drawdowns. Issues:

1. **Estimation error**: If our 55% is actually 52%, we overbet
2. **Bankroll volatility**: 14% of bankroll per bet is risky
3. **Correlated bets**: Multiple bets on same game/team compound risk

### Fractional Kelly (Recommended)

Bet a **fraction** of the Kelly amount:

```
stake = f* × fraction × bankroll
```

**Common fractions:**

- **1/4 Kelly (0.25)**: Conservative, reduces volatility by ~75%
- **1/2 Kelly (0.50)**: Moderate, reduces volatility by ~50%
- **1/3 Kelly (0.33)**: Balanced

LineLogic defaults to **1/4 Kelly** for POC.

**Adjusted example:**

```
1/4 Kelly = 0.141 × 0.25 = 0.035 (3.5%)
Bet = 0.035 × $10,000 = $350
```

---

## Portfolio Considerations

### Exposure Caps

Even with fractional Kelly, we limit **aggregate exposure** to avoid concentration risk:

**Rules:**

1. **Per-bet cap**: Max 5% of bankroll per single bet (overrides Kelly)
2. **Per-game cap**: Max 10% of bankroll across all bets on one game
3. **Per-day cap**: Max 20% of bankroll across all bets on one day
4. **Per-player cap**: Max 10% of bankroll on same player across markets

### Correlation Heuristics

**Problem:** Same-game bets are correlated. If LeBron scores 30+, Lakers are likely winning. Betting both is not diversification.

**Heuristic rules:**

- Flag bets on same game
- Flag bets on same team
- Flag bets on same player (different markets)
- **Conservative approach**: Treat correlated bets as one "meta-bet" and apply Kelly to the combined payoff

**Future work:** Build correlation matrices from historical data to quantify dependencies.

---

## Evaluation Metrics

### Brier Score

**Purpose:** Measure probabilistic calibration.

**Formula:**

```
Brier = (1/N) × Σ (predicted_prob - actual_outcome)^2
```

Where `actual_outcome` is 0 (loss) or 1 (win).

**Range:** 0 (perfect) to 1 (worst)

**Good score:**

- <0.15: Excellent
- 0.15-0.20: Good
- 0.20-0.25: Acceptable
- \>0.25: Poor

**Example:**

```
Bet 1: Predicted 60%, outcome = win (1) → (0.6 - 1)^2 = 0.16
Bet 2: Predicted 60%, outcome = loss (0) → (0.6 - 0)^2 = 0.36
Bet 3: Predicted 40%, outcome = loss (0) → (0.4 - 0)^2 = 0.16

Brier = (0.16 + 0.36 + 0.16) / 3 = 0.227
```

### Log Loss (Cross-Entropy)

**Purpose:** Penalize confident wrong predictions more heavily than Brier.

**Formula:**

```
LogLoss = -(1/N) × Σ [y × log(p) + (1-y) × log(1-p)]
```

Where `y` is actual outcome (0 or 1), `p` is predicted probability.

**Range:** 0 (perfect) to ∞ (worst)

**Good score:**

- <0.50: Excellent
- 0.50-0.60: Good
- 0.60-0.70: Acceptable
- \>0.70: Poor

### Calibration

**Purpose:** Are our 60% predictions actually winning 60% of the time?

**Method:**

1. Bucket predictions (e.g., 50-55%, 55-60%, 60-65%)
2. Calculate average predicted prob and empirical win rate per bucket
3. Plot predicted vs. actual
4. Perfect calibration: points lie on y=x line

**Example:**

| Bucket | Avg Predicted | Wins | Total | Empirical Win Rate |
|--------|---------------|------|-------|--------------------|
| 50-55% | 52.5%         | 10   | 20    | 50.0%              |
| 55-60% | 57.5%         | 12   | 20    | 60.0%              |
| 60-65% | 62.5%         | 11   | 20    | 55.0%              |

Interpretation: Model is slightly overconfident in 60-65% bucket.

### Closing Line Value (CLV)

**Purpose:** Did we beat the closing line?

**Definition:**

- **Opening line**: Odds when we place bet
- **Closing line**: Odds just before game starts
- **CLV**: Positive if our odds were better than closing

**Formula:**

```
CLV = implied_prob_close - implied_prob_open
```

If CLV > 0, we got a better price than the sharp closing line.

**Example:**

- We bet Over 25.5 at +110 (implied 47.6%)
- Closing line: Over 25.5 at -110 (implied 52.4%)
- CLV = 52.4% - 47.6% = **+4.8%**

We beat the closing line by 4.8 percentage points.

**Why it matters:**

- Closing line is the "wisdom of the crowd" (sharpest bettors)
- Positive CLV → long-term indicator of skill
- Negative CLV → losing strategy even if short-term lucky

---

## ROI and Sharpe Ratio

### Return on Investment (ROI)

```
ROI = (Total Profit) / (Total Staked)
```

**Example:**

- Wagered: $10,000
- Profit: $1,200
- ROI = 1,200 / 10,000 = **12%**

**Good ROI in sports betting:**

- 3-5%: Professional
- 5-10%: Elite
- \>10%: Exceptional (or lucky/short sample)

### Sharpe Ratio

**Purpose:** Risk-adjusted returns.

**Formula:**

```
Sharpe = (Mean Return - Risk-Free Rate) / Std Dev of Returns
```

**Interpretation:**

- Sharpe > 1.0: Good
- Sharpe > 2.0: Excellent
- Sharpe > 3.0: World-class (or overfitting)

Sports betting Sharpe ratios are typically **0.5 to 1.5** for good strategies.

---

## Hypothesis Testing and Statistical Significance

### The Problem

With small samples, luck dominates. A 55% win rate over 100 bets could easily be 50% in reality.

### Confidence Intervals

For a binomial (win/loss):

```
Standard Error = sqrt( p × (1-p) / n )
95% CI = p ± 1.96 × SE
```

**Example:**

- 55 wins out of 100 bets (55% win rate)
- SE = sqrt(0.55 × 0.45 / 100) = 0.0497
- 95% CI = 55% ± 9.7% = **45.3% to 64.7%**

**Interpretation:** We cannot confidently say this is >50%.

**Rule of thumb:** Need **300+ bets** to distinguish 52% from 50% with statistical significance.

---

## Avoiding Common Pitfalls

### 1. Leakage

**Problem:** Using future information to predict past.

**Example:** Betting on a player prop using post-game injury reports.

**Prevention:**

- Strict train/test split by date
- Only use data available **before** bet placement

### 2. Overfitting

**Problem:** Model fits noise in training data, fails on new data.

**Prevention:**

- Simple models first (linear, GLM)
- Holdout validation (never touch until final evaluation)
- Cross-validation on time series (walk-forward)
- Regularization (L1/L2 for GLM, early stopping for trees)

### 3. Survivorship Bias

**Problem:** Only analyzing winners (e.g., profitable bettors who keep records).

**Prevention:**

- Track **all** bets, not just winners
- Include deleted/abandoned strategies

### 4. Recency Bias

**Problem:** Overweighting recent performance ("hot hand" fallacy).

**Prevention:**

- Use season-long averages with recency weighting (exponential moving average)
- Bayesian priors to shrink extreme recent samples

### 5. Small Sample Fallacy

**Problem:** Drawing conclusions from <100 bets.

**Prevention:**

- Require **300+ bets** for statistical claims
- Report confidence intervals
- Focus on **process** (CLV, calibration) over short-term results

---

## Model Hierarchy

### Baseline (M0)

**Goal:** Simple, interpretable, hard to overfit.

**Approach:**

- Player's recent avg (last 10 games) ± 0.5 std dev
- Compare to market line
- If edge > 5%, bet

**Evaluation:**

- Brier score
- CLV
- ROI

### Intermediate (M1)

**Goal:** Incorporate matchup and context.

**Approach:**

- Generalized Linear Model (Poisson for counts, Gaussian for continuous)
- Features: player recent, opponent defense, pace, rest days
- Train on 2 seasons, validate on 1 season

**Evaluation:**

- Brier, log loss, calibration plots
- Feature importance
- Out-of-sample performance

### Advanced (M2+)

**Goal:** Ensemble, adaptive, market-aware.

**Approach:**

- XGBoost/LightGBM with 50+ features
- Ensemble: GLM + tree + market signal
- Adaptive weighting based on recent performance
- Incorporate line movement (steam, reverse line movement)

**Evaluation:**

- Walk-forward cross-validation
- CLV >2% on 500+ bets
- Sharpe ratio >1.0

---

## Conclusion

The math of sports betting is **probabilistic, not deterministic**. We aim to:

1. **Estimate probabilities** better than the market
2. **Size bets** optimally (Kelly + exposure caps)
3. **Evaluate performance** rigorously (Brier, CLV, ROI)
4. **Avoid overconfidence** (wide CIs, process over results)

Good process + positive CLV → long-term profitability (on average).

---

**Next**: [Data Sources](04_data_sources.md) | [Backtesting and Paper Trading](05_backtesting_and_paper_trading.md)
