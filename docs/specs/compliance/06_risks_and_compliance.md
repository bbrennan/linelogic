# Risks and Compliance

## Disclaimer

**LineLogic is a research and education tool for paper trading and decision support. It is NOT a gambling service, financial advisor, or get-rich-quick scheme.**

All predictions are **probabilistic estimates** with inherent uncertainty. Past performance does not guarantee future results. Users are solely responsible for their own betting decisions and compliance with applicable laws.

---

## Key Risks

### 1. Model Risk

**Description:** The model may be incorrect, miscalibrated, or overfit.

**Impact:**

- Negative ROI (losing money)
- False confidence (thinking model works when it doesn't)
- Ruin (losing entire bankroll)

**Mitigation:**

- **Rigorous backtesting** (300+ bets, out-of-sample)
- **Calibration monitoring** (Brier score, calibration plots)
- **CLV tracking** (are we beating closing lines?)
- **Fractional Kelly** (0.25 or lower)
- **Exposure caps** (max 5% per bet, 10% per game, 20% per day)
- **Regular re-evaluation** (monthly reports, model versioning)

**Acceptance:**

- **Paper trading only in POC** (no real money risk)
- Start with simple models (less overfitting risk)

---

### 2. Data Risk

**Description:** Data may be missing, stale, incorrect, or biased.

**Examples:**

- Injury reports delayed (player ruled out after we bet)
- API downtime (can't fetch odds in time)
- Incorrect stats (API bug, manual entry error)
- Selection bias (only profitable bettors share results)

**Impact:**

- Bad predictions (garbage in, garbage out)
- Missed opportunities (can't fetch odds)
- Execution errors (stale data)

**Mitigation:**

- **Multiple data sources** (BALLDONTLIE + nba_api + manual checks)
- **Data validation** (schema checks, null checks, consistency checks)
- **Timestamp everything** (audit trail for debugging)
- **Caching with TTL** (don't rely on real-time fetches)
- **Manual spot checks** (verify injury reports on ESPN/Twitter)

**Acceptance:**

- Free-tier APIs have limitations (expected)
- Unofficial APIs can break (nba_api risk)
- Budget for paid tiers if POC succeeds

---

### 3. Execution Risk

**Description:** Unable to place bet at desired odds or stake.

**Examples:**

- Line moves between decision and execution (slippage)
- Sportsbook pulls line (high-profile injury news)
- Stake limits (book caps sharp bettors at $100)
- Account restrictions (flagged as sharp, limited to $10 bets)

**Impact:**

- Lower ROI (worse odds than backtested)
- Missed opportunities (can't get full stake down)
- Frustration (backtests work, but can't execute)

**Mitigation:**

- **Paper trading first** (learn execution challenges)
- **Assume 2nd-best odds** in backtests (conservative)
- **Multiple sportsbooks** (if one limits you, use another)
- **Accept 10% unavailability** (some bets won't be placeable)

**Acceptance:**

- **POC is paper trading only** (no execution risk yet)
- Real money requires operational complexity (future problem)

---

### 4. Market Efficiency Risk

**Description:** Sports betting markets are increasingly efficient. Edges may be small or non-existent.

**Impact:**

- Model works in backtests but fails live (markets have improved)
- Competition from other sharps (they bet before you)
- Sportsbooks adjust quickly (closing lines sharpen)

**Mitigation:**

- **Focus on less efficient markets** (player props > totals/spreads)
- **Niche sports/leagues** (WNBA, G League, international)
- **Fast execution** (bet early before lines sharpen)
- **CLV as leading indicator** (if CLV is positive, model has edge)

**Acceptance:**

- May not be profitable long-term (especially at scale)
- View as research project, not guaranteed income

---

### 5. Bankroll Risk (Ruin)

**Description:** Even with an edge, variance can deplete bankroll.

**Example:**

- True win rate: 55% (profitable)
- Bad luck: 10 losses in a row
- Bankroll: -30% (psychological stress, forced to stop)

**Impact:**

- Emotional distress (tilt, revenge betting)
- Forced exit (bankroll too low to continue)
- Family/relationship strain (if betting with shared money)

**Mitigation:**

- **Fractional Kelly** (0.25 or lower)
- **Exposure caps** (per bet, per game, per day)
- **Only bet disposable income** (money you can afford to lose 100%)
- **Stop-loss rules** (pause if drawdown >30%)
- **Emotional discipline** (no tilt, stick to system)

**Acceptance:**

- **POC is paper trading** (no real financial risk)
- **Real money requires strict bankroll management** (non-negotiable)

---

### 6. Legal and Regulatory Risk

**Description:** Sports betting laws vary by jurisdiction. Operating illegally has serious consequences.

**Examples:**

- Betting in prohibited states (e.g., Utah, Hawaii)
- Underage gambling (under 21 in most US states)
- Unlicensed operation (acting as bookmaker)
- Tax evasion (not reporting winnings)

**Impact:**

- Criminal charges (fines, jail time)
- Civil penalties (IRS back taxes, interest)
- Account seizure (sportsbooks close accounts)

**Mitigation:**

- **Know your local laws** (consult lawyer if unsure)
- **Age verification** (LineLogic does not verify; user responsibility)
- **Tax compliance** (report all winnings, deduct losses)
- **No bookmaking** (LineLogic is decision support, not a betting service)

**Acceptance:**

- **Users are responsible for legal compliance** (not LineLogic)
- **No liability** (MIT license, no warranty)

---

### 7. Operational Risk

**Description:** System failures, bugs, human errors.

**Examples:**

- Bug in Kelly calculation (overbet by 10x)
- Database corruption (lose all historical data)
- Forgot to log bet (can't track performance)
- Manual entry error (bet wrong side)

**Impact:**

- Financial loss (wrong bet size or side)
- Invalid backtest (data missing)
- Lost learning (can't debug what went wrong)

**Mitigation:**

- **Comprehensive testing** (unit tests, integration tests)
- **Type safety** (mypy strict mode)
- **Code review** (pre-commit hooks, manual review)
- **Backups** (daily SQLite backups, S3 archival)
- **Logging** (audit trail for debugging)
- **Manual checks** (review recommendations before "placing")

**Acceptance:**

- Bugs are inevitable (catch early via testing)
- Paper trading catches bugs before real money

---

### 8. Psychological Risk

**Description:** Betting (even paper trading) can be addictive and stressful.

**Symptoms:**

- Obsessively checking scores/odds
- Emotional highs/lows tied to wins/losses
- Neglecting work, relationships, health
- Chasing losses (increasing bets to recover)

**Impact:**

- Mental health decline (anxiety, depression)
- Problem gambling behavior
- Financial ruin (if progresses to real money)

**Mitigation:**

- **Set time limits** (e.g., 1 hour per day for LineLogic)
- **Take breaks** (skip days if stressed)
- **Focus on process, not results** (CLV > short-term P&L)
- **Seek help if needed** (National Council on Problem Gambling: 1-800-522-4700)

**Acceptance:**

- Betting is not for everyone (know your limits)
- LineLogic is a tool, not a lifestyle

---

## Compliance and Responsible Use

### Age Restrictions

**Requirement:** Must be 21+ in most US states (18+ in some international jurisdictions).

**LineLogic's role:**

- **No age verification** (user's responsibility)
- Disclaimer in README and docs

---

### Jurisdictional Restrictions

**Legal sports betting** (as of Jan 2026):

- **Permitted**: 30+ US states (NY, NJ, PA, IL, MI, CO, AZ, etc.)
- **Prohibited**: UT, HI, and some others
- **International**: Varies widely (UK is legal, China is banned)

**LineLogic's role:**

- **No geo-blocking** (open-source tool)
- Users responsible for compliance
- Recommend consulting local attorney

---

### Tax Compliance

**US Tax Rules:**

- Gambling winnings are **taxable income** (reported on Form W-2G if >$600)
- Losses are **deductible** (up to amount of winnings, if you itemize)
- Professional gamblers may deduct losses as business expense

**LineLogic's role:**

- **Provide tracking** (detailed P&L reports)
- Users responsible for filing taxes
- Recommend consulting CPA

---

### Responsible Gambling

**Best practices:**

- Only bet with **disposable income** (not rent, groceries, savings)
- Set **hard limits** (daily, weekly, lifetime)
- Never **chase losses** (tilt is expensive)
- Take **breaks** (skip a week if stressed)
- **Self-exclude** if needed (most books offer self-exclusion programs)

**Resources:**

- National Council on Problem Gambling: [ncpgambling.org](https://www.ncpgambling.org)
- Gamblers Anonymous: [gamblersanonymous.org](https://www.gamblersanonymous.org)
- Self-exclusion programs: Available on DraftKings, FanDuel, BetMGM, etc.

---

### Prohibited Use Cases

**LineLogic must NOT be used for:**

- ❌ **Underage gambling** (under 21 or local minimum age)
- ❌ **Operating as a bookmaker** (taking bets from others)
- ❌ **Match fixing or insider trading** (using non-public info to cheat)
- ❌ **Money laundering** (betting to clean illegal funds)
- ❌ **Automated betting bots** (without user review and approval)
- ❌ **Violating sportsbook ToS** (multi-accounting, bonus abuse, etc.)

---

## Ethical Considerations

### Transparency

**Commitment:**

- All models and methodology are **open-source** (or well-documented if proprietary)
- No black-box predictions (users should understand reasoning)
- Clear reporting of uncertainty (confidence intervals, calibration)

---

### Honesty

**Commitment:**

- No "guaranteed winners" language
- No cherry-picking results (report all bets)
- No misleading marketing (LineLogic is research, not a service)

---

### User Empowerment

**Commitment:**

- LineLogic recommends; **user decides**
- Provide education (docs, math explanations)
- Encourage critical thinking (question the model)

---

## Security and Privacy

### Data Handling

**User data:**

- LineLogic stores **only what's necessary** (bets, results, bankroll)
- No personal info (name, address, SSN) collected
- Local storage by default (SQLite on user's machine)

**API keys:**

- Stored in `.env` file (never committed to git)
- User responsible for securing keys

**Future (if hosted service):**

- Encrypt sensitive data (AES-256)
- Use secure hosting (AWS, GCP with SOC 2 compliance)
- GDPR compliance for EU users

---

### Open Source Risks

**Risks:**

- Code is public (competitors can copy)
- Security vulnerabilities may be discovered by bad actors

**Mitigation:**

- Responsible disclosure policy (SECURITY.md)
- Community review (more eyes = fewer bugs)
- Regular dependency updates (security patches)

---

## Liability Disclaimer

**MIT License Summary:**

> "THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT."

**What this means:**

- **No guarantees** (model may fail, bugs may exist)
- **No liability** (contributors not responsible for your losses)
- **Use at your own risk** (you accept all consequences)

---

## Monitoring and Incident Response

### Detection

**Monitor for:**

- Model drift (calibration degrades over time)
- Data anomalies (missing stats, stale odds)
- Execution errors (wrong bet side, size)

**Tools:**

- Daily automated reports (email/Slack)
- Alerts for >5 consecutive losses (possible bug)
- Weekly calibration checks

---

### Response

**If model fails:**

1. **Pause all betting** (paper or real)
2. **Investigate** (data issue? model drift? bad luck?)
3. **Document in ADR** (what went wrong, why, how to prevent)
4. **Fix and validate** (re-backtest, paper trade again)
5. **Resume cautiously** (reduce stakes initially)

---

## Future Enhancements

### Advanced Risk Management

- **Correlation modeling** (don't overbet correlated props)
- **Hedging strategies** (middle opportunities, arbitrage)
- **Dynamic Kelly** (adjust fraction based on confidence/volatility)

### Regulatory Compliance

- **KYC/AML** (if hosting as service)
- **Licensing** (if accepting payments)
- **Data residency** (GDPR, CCPA compliance)

### Security Hardening

- **2FA for admin access**
- **Encrypted backups**
- **Penetration testing**

---

## Conclusion

Sports betting carries **inherent risks**:

- **Model risk** (predictions may be wrong)
- **Data risk** (garbage in, garbage out)
- **Execution risk** (can't always get your price)
- **Bankroll risk** (variance can deplete funds)
- **Legal risk** (know your local laws)
- **Psychological risk** (addiction, stress)

**LineLogic mitigates risks through:**

- Paper trading POC (no real money initially)
- Rigorous backtesting and validation
- Fractional Kelly and exposure caps
- Transparent, auditable methodology
- Clear disclaimers and responsible gambling resources

**Users are responsible for:**

- Legal compliance (age, jurisdiction, taxes)
- Bankroll management (only bet disposable income)
- Emotional discipline (no tilt, no chasing)
- Ethical use (no match fixing, money laundering, etc.)

**Remember:** Good process > short-term results. Focus on CLV, calibration, and learning—not quick profits.

---

**Next**: [Architecture](../adr/0001_architecture.md) | [README](../README.md)
