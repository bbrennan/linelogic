# Vision and Goals

## Mission Statement

LineLogic is a **quantitative sports prop analytics platform** that combines rigorous statistical methods, portfolio theory, and modern software engineering to provide **probabilistic decision support** for sports betting research.

We are building a tool for **sharp, data-driven analysis**—not a get-rich-quick auto-betting system.

## Core Principles

### 1. Math First, Hype Never

- All predictions are **probabilistic estimates** with quantified uncertainty
- No "guaranteed winners" or "lock" language
- Focus on long-term edge, not short-term results
- Transparent about limitations and risks

### 2. Reproducibility and Rigor

- Version-controlled models and experiments
- Documented assumptions and data sources
- Backtests that avoid leakage and overfitting
- Peer-reviewable methodology

### 3. Decision Support, Not Automation

- LineLogic recommends; humans decide
- Paper trading POC to validate models
- Clear separation: research vs. production vs. real money
- User retains full control and responsibility

### 4. Modularity and Extensibility

- **Swappable data providers**: Don't lock into one API
- **Sport-agnostic architecture**: NBA first, but designed for NFL/MLB/MMA
- **Model registry**: Baseline → advanced → ensemble pipelines
- **Open to experimentation**: Researchers can plug in custom features/models

## What Success Looks Like

### Short-term (M0-M1)

- ✅ Clean, runnable codebase with comprehensive tests
- ✅ Core math validated: odds conversions, vig removal, Kelly criterion
- ✅ Data providers integrated with caching and rate limiting
- ✅ Storage layer tracks recommendations, odds, and results
- ✅ Evaluation framework measures calibration and CLV

### Medium-term (M2-M3)

- 🎯 Positive CLV in paper trading over 3+ months
- 🎯 Well-calibrated models (Brier score < 0.20 for 2-way markets)
- 🎯 Streamlit dashboard for daily recommendations
- 🎯 NFL and MLB adapters functional
- 🎯 Advanced models (GLM, XGBoost) outperform baseline

### Long-term (M4+)

- 🚀 Production-grade system with monitoring and alerting
- 🚀 Multi-sport, multi-market portfolio optimization
- 🚀 Real-time odds tracking and line movement alerts
- 🚀 Community of researchers contributing features/models
- 🚀 Potential commercial SaaS (if POC proves viable)

## Non-Goals

### What We Are NOT Building

- ❌ **Fully automated betting bot**: Humans must review and approve bets
- ❌ **Black-box system**: All logic is transparent and auditable
- ❌ **Consumer gambling app**: This is a researcher/analyst tool
- ❌ **High-frequency trading system**: Sports markets are slower; we optimize for correctness over speed
- ❌ **Get-rich-quick scheme**: Focus is on long-term, sustainable edge

## Target Users

### Primary: Quantitative Researchers

- Sports analytics enthusiasts
- Data scientists interested in sports betting
- Engineers building betting tools
- Academic researchers studying prediction markets

### Secondary: Sharp Bettors (Future)

- Professional or semi-professional sports bettors
- Betting syndicates looking for alpha
- Individuals who understand EV, CLV, and portfolio theory

### NOT for: Casual Bettors

- LineLogic requires statistical literacy
- Designed for those who understand uncertainty and bankroll management
- Not a "pick'em" service or tipster platform

## Strategic Priorities

### 1. Correctness Over Speed

- Thoroughly tested math and models
- Conservative assumptions (e.g., fractional Kelly by default)
- Prioritize avoiding big mistakes over chasing every edge

### 2. Transparency Over Complexity

- Simple, interpretable models first
- Document why we make picks
- Clear reporting of uncertainty and confidence intervals

### 3. Flexibility Over Optimization

- Start with SQL + Python; scale later if needed
- Swappable providers > vendor lock-in
- Iterate quickly; don't over-engineer early

### 4. Compliance and Ethics

- Paper trading only in POC
- No underage gambling, no prohibited jurisdictions
- Responsible gambling messaging
- Open-source core (with optional paid tiers for production features)

## Risks and Challenges

### Technical Risks

- **Data quality**: Free APIs may have missing/stale data
- **API stability**: Unofficial endpoints can break
- **Overfitting**: Must rigorously validate out-of-sample
- **Latency**: Odds move fast; stale data = bad picks

### Business Risks

- **Model doesn't work**: EV may not translate to real profits
- **Market efficiency**: Sharp lines are hard to beat
- **Regulatory**: Gambling laws vary; compliance is complex
- **Competition**: Other sharps may arbitrage away edge

### Mitigation Strategies

- Start with paper trading to validate before risking capital
- Use multiple data sources to cross-check
- Implement strict backtesting discipline (no peeking)
- Focus on less efficient markets (props vs. totals/spreads)
- Build in monitoring and alerting for model drift

## Success Metrics

### Model Performance

- **Calibration**: Brier score, calibration plots
- **Discrimination**: Log loss, ROC-AUC (where applicable)
- **CLV**: % of bets that beat closing line
- **ROI**: Return on investment (paper trading)
- **Sharpe ratio**: Risk-adjusted returns

### Engineering Quality

- **Test coverage**: >80%
- **Type safety**: mypy strict mode passing
- **Documentation**: Every module has README
- **Uptime**: 99%+ for data fetching (with retries)

### User Experience

- **Time to first recommendation**: <5 minutes after setup
- **Recommendation clarity**: Clear rationale + uncertainty
- **Dashboard responsiveness**: <2s load time
- **Error messages**: Actionable, not cryptic

## Timeline

### Phase 1: Foundation (Weeks 1-2)

- ✅ Repo setup, docs, scaffolding
- ✅ Core math and portfolio utilities
- ✅ Provider architecture with BALLDONTLIE
- ✅ Storage and evaluation framework

### Phase 2: NBA MVP (Weeks 3-4)

- 🚧 Feature engineering for player props
- 🚧 Baseline model (simple over/under)
- 🚧 Paper trading workflow
- 🚧 CLI + basic dashboard

### Phase 3: Validation (Weeks 5-8)

- 📅 Collect 4+ weeks of paper trading data
- 📅 Evaluate calibration and CLV
- 📅 Iterate on features and models
- 📅 Document learnings in ADRs

### Phase 4: Expansion (Weeks 9-12)

- 📅 NFL props adapter
- 📅 Advanced models (GLM, XGBoost)
- 📅 Multi-game portfolio optimization
- 📅 Streamlit dashboard polish

## Philosophy

> "The goal of a quantitative system is not to be perfect, but to be **better than the alternative** (guessing) and **measurably improvable** over time."

We embrace:

- **Bayesian thinking**: Update beliefs with new data
- **Ensembles over single models**: Diversify model risk
- **Small edges compounded**: 52% win rate beats 50% long-term
- **Process over results**: Good process with bad luck > bad process with good luck

## Call to Action

If you believe in:

- Math-driven decision making
- Transparent, reproducible research
- Long-term thinking over short-term gambling
- Building tools that respect users' intelligence

...then LineLogic is for you. Let's build something rigorous and useful.

---

**Next**: [Sports Strategy](02_sports_strategy.md) | [Math Foundations](03_math_foundations.md)
