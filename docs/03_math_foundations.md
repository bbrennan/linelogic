# Math Foundations (Why and How)

This chapter is a graduate-level refresher on the probabilistic and decision-theoretic backbone of sports betting. We focus on **why** each quantity matters for beating markets, and **how** to compute and deploy it correctly. Assumed background: measure-theoretic probability intuition, basic statistics, and utility theory.

---

## 1. Odds, Prices, and Implied Probabilities

### 1.1 Odds as Prices
Odds are simply prices for binary payoffs. If a bet pays $b$ net on a $1$ stake when the event occurs and $-1$ otherwise, the fair price under risk-neutral measure is $p \cdot b - (1-p) = 0$, so the **no-arbitrage implied probability** is $p = 1/(b+1)$ in decimal odds. American odds are just a reparameterization of $b$.

### 1.2 Conversions (How)
Let $o_A$ be American odds and $o_D$ decimal odds.
- If $o_A > 0$, then payout ratio $b = o_A/100$, implied $p = 100/(o_A+100)$.
- If $o_A < 0$, then $b = 100/|o_A|$, implied $p = |o_A|/(|o_A|+100)$.
- Decimal odds: $p = 1/o_D$.

Edge cases: very large $|o_A|$ approach $p \to 0$ or $1$; ensure numeric stability. Implementation lives in `src/linelogic/odds/math.py` with tests for symmetry and round-trip consistency.

### 1.3 Why this matters
All downstream quantities (EV, Kelly, CLV) operate on probabilities, not odds. Any bias in conversion propagates linearly into staking errors and non-linear into log-utility. Getting the mapping correct is table stakes.

---

## 2. Vigorish, Overround, and Fair Lines

### 2.1 Why vig removal is necessary
Books quote **distorted probabilities** to embed margin. If we compare our model to raw book numbers, we will systematically overestimate value. Fair probabilities are the only defensible baseline for edge estimation.

### 2.2 Overround (What)
For a two-way market, let $p_1^{m}, p_2^{m}$ be market-implied probabilities from odds. The overround is $\omega = p_1^{m} + p_2^{m} - 1$, typically 0.02–0.10.

### 2.3 De-vig methods (How)
We need a mapping $T$ such that $p_i = T(p_i^{m})$ with $\sum p_i = 1$.
- **Proportional (used in M0/M1):** $p_i = p_i^{m} / \sum_j p_j^{m}$. Simple, stable, unbiased if vig is additive.
- **Shin (informed money model):** Introduces insider fraction $z$ and solves nonlinear system; better when limits are high and asymmetry exists.
- **Power / logit scaling:** $p_i \propto (p_i^{m})^{\alpha}$, tune $\alpha$ to historical hold distributions.

We default to proportional for robustness and clarity; Shin is a planned experiment when we have closing-line histories.

### 2.4 Sensitivity (Why)
Edge is linear in de-vig probabilities: a 1 pp error in $p$ becomes a 1 pp error in edge. Since Kelly stake is roughly linear near small edges, vig-removal accuracy directly controls bankroll volatility.

---

## 3. Expected Value and Edge

### 3.1 Expected value (EV)
For stake $s$, decimal odds $o$, model win probability $p$, loss prob $q=1-p$:
$$EV = s \big(p (o-1) - q\big).$$
Positive EV ($EV>0$) is a **necessary** condition for long-run growth.

### 3.2 Edge (Why)
Define **edge** as $\text{edge} = p - p_{\text{fair}}$. A model that only matches the fair price (edge = 0) will lose to vig; a positive edge indicates price improvement over the market. Edge is the sufficient statistic for both EV sign and Kelly sizing (see §4).

### 3.3 Estimation error (How to guard)
If $\hat p$ has standard error $\sigma_p$, then stake and EV inherit that uncertainty. We apply **minimum edge thresholds** (default 5 pp) so that $\text{edge} \gg \sigma_p$, reducing false positives from noise.

---

## 4. Kelly Criterion, Utility, and Risk Control

### 4.1 Why Kelly
Kelly maximizes expected log-wealth for IID bets. For a single bet with payout ratio $b$ and win prob $p$, the log-utility is $U(f) = p \log(1+fb) + q \log(1-f)$; first-order condition yields
$$f^{*} = \frac{pb - q}{b}.$$
This is optimal for growth but ignores estimation error and correlation.

### 4.2 Fractional Kelly (How)
We bet $f = \lambda f^{*}$ with $\lambda \in [0,1]$. Fractional Kelly trades growth for drawdown control; variance of log-returns scales roughly with $\lambda^2$ while growth scales roughly with $\lambda$. Empirically, $\lambda \in [0.25, 0.5]$ captures 50–75% of the growth with far smaller volatility. LineLogic defaults to $\lambda = 0.25$.

### 4.3 Correlation and meta-bets (Why)
Kelly assumes independence. Same-game or same-player bets are positively correlated; naive application overbets. We use heuristics to group correlated bets into a meta-bet and cap exposure (5% single, 10% game/player, 20% day). Future work: estimate correlation matrices and apply **Kelly with correlation** via quadratic form on log-utility Hessian.

### 4.4 Model error robustness
If true $p$ differs from estimated $\hat p$ by $\Delta$, the Kelly fraction error is roughly $\Delta/b$. Fractional Kelly reduces sensitivity linearly in $\lambda$; hence another reason to avoid full Kelly with noisy models.

---

## 5. Evaluation: Calibration, Sharpness, Price Beating

### 5.1 Brier Score (How and Why)
$$\text{Brier} = \frac{1}{N} \sum_{i=1}^{N} (\hat p_i - y_i)^2.$$
Measures **calibration** and **sharpness** jointly. Quadratic penalty is symmetric; good for bounded probabilities and interpretable decomposition (reliability, resolution, uncertainty). In betting, well-calibrated probabilities align staking with true risk; miscalibration inflates Kelly stakes.

### 5.2 Log Loss
$$\text{LogLoss} = -\frac{1}{N} \sum_{i=1}^{N} \big(y_i \log \hat p_i + (1-y_i) \log(1-\hat p_i)\big).$$
Asymmetric penalty: brutally punishes overconfident errors. Appropriate when we care about tail risk of bad probability estimates (we do, because of Kelly sensitivity).

### 5.3 Calibration plots (How)
Bucket $\hat p$ into bins, compute empirical win rate per bin, and compare to the 45° line. Deviations diagnose systemic bias (over/under-confidence). Adjust with Platt scaling / isotonic if needed.

### 5.4 Closing Line Value (CLV) (Why)
CLV checks if we **beat the market’s final consensus**, a forward-looking efficiency test. If $p_{\text{open}}$ is our implied prob from the wagered line and $p_{\text{close}}$ from closing:
$$\text{CLV} = p_{\text{close}} - p_{\text{open}}.$$
Persistent positive CLV implies informational or timing edge even before outcomes resolve. It is lower-variance than ROI for small samples.

### 5.5 ROI and Sharpe (Context)
ROI: $\text{ROI} = \text{Profit} / \text{Staked}$. Sharpe: $(\mu - r_f)/\sigma$. In betting, $r_f \approx 0$. Sharpe captures risk-adjusted performance; good models show Sharpe 0.5–1.5+. Beware short-sample Sharpe inflation.

---

## 6. Statistical Power and Significance

### 6.1 Binomial confidence (How)
For win rate $\hat p$ over $n$ bets, standard error $\sigma = \sqrt{\hat p(1-\hat p)/n}$. A 95% CI: $\hat p \pm 1.96\sigma$. To distinguish 52% from 50% at 95% power requires $n \approx 300$ bets.

### 6.2 Bayesian perspective (Why)
Using a Beta prior $\text{Beta}(\alpha,\beta)$ yields posterior $\text{Beta}(\alpha + k, \beta + n-k)$. Posterior intervals shrink extreme observed rates toward prior mean, mitigating small-sample overreaction. This is preferable when we continuously update models.

### 6.3 Multiple testing
Screening thousands of prop candidates introduces false positives. Mitigate by: (1) minimum edge thresholds, (2) shrinkage priors on player effects, (3) out-of-sample evaluation, (4) CLV as a process metric independent of win/loss noise.

---

## 7. Model Design for Betting

### 7.1 Baseline (M0)
Simple, low-variance estimators: recent mean ± half a standard deviation. Why: hard to overfit; serves as calibration anchor. We require edge > 5 pp to offset noise.

### 7.2 Generalized Linear Models (M1)
Use Poisson/negative binomial for counts (points, rebounds) or Gaussian for continuous rates with link functions. GLMs provide calibrated probabilities and interpretable coefficients (pace, usage, opponent defense). Regularize (L1/L2) to control variance.

### 7.3 Ensembles and Market Features (M2+)
Gradient-boosted trees capture nonlinear interactions (pace x matchup x rest). Add market signals (line moves, juice asymmetry) as priors; combine with GLM via stacking. Evaluate with walk-forward CV to respect temporal order.

### 7.4 Line movement as information
Reverse line moves, steam, and limits convey crowd information. Incorporate closing line as a posterior update: $p_{\text{final}} = w_{\text{model}} \hat p + (1-w_{\text{model}}) p_{\text{close}}$, with $w$ tuned on historical CLV.

---

## 8. Risk Controls and Execution

### 8.1 Exposure limits (How)
Hard caps (5% single, 10% game/player, 20% day) override Kelly to prevent tail events from compounding. These are deterministic constraints layered atop stochastic sizing.

### 8.2 Correlation handling (Future work)
Estimate pairwise or factor correlations across props (team pace, injury news, opponent defense). Solve for optimal stakes via mean-variance or Kelly-with-correlation approximations.

### 8.3 Latency and stale lines
Execution delay erodes edge. Track time-to-place-bet and line drift; require edges that survive expected slippage. If drift expected $d$ pp against us, require edge > threshold + $d$.

---

## 9. Putting It Together

The betting loop:
1. Convert odds → implied probabilities (correctly, including vig removal).
2. Produce calibrated model probabilities with honest uncertainty.
3. Compute edge = $p_{\text{model}} - p_{\text{fair}}$; discard below threshold.
4. Size stakes with fractional Kelly under exposure caps and correlation heuristics.
5. Track outcomes and **process metrics** (CLV, calibration) to validate edge before ROI converges.

Process discipline plus positive CLV is the only path to durable profitability. Every formula above links to a failure mode if misapplied; precision and humility are both required.

---

**Next**: [Data Sources](04_data_sources.md) | [Backtesting and Paper Trading](05_backtesting_and_paper_trading.md)
