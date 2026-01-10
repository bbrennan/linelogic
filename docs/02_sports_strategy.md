# Sports Strategy

## Overview

LineLogic is designed to be **sport-agnostic** at the architecture level, but each sport requires tailored features, models, and market understanding. This document outlines our approach for NBA, NFL, MLB, and (future) MMA.

## Key Questions

### Does the Math Change by Sport?

**Core math (odds, EV, Kelly) is universal.** However:

- **Probability distributions differ**: NBA totals are roughly normal; NFL prop bets are discrete and skewed.
- **Variance and sample size**: NBA has 82 games; NFL has 17. More data = better estimates.
- **Market efficiency**: NBA mainlines are very sharp; niche player props less so. NFL has more public bias.
- **Feature engineering**: Completely different. NBA: pace, usage, matchups. NFL: weather, snap counts, game script.

### Should MMA Be Included?

**Yes, as a future adapter.** MMA has attractive properties:

- **Less efficient markets**: Smaller betting volumes = more exploitable inefficiencies
- **Fight-by-fight modeling**: Each event is independent (unlike team sports)
- **Rich features**: Fighter styles, reach, age, training camps, injuries

However, MMA requires specialized domain knowledge. Include in architecture (swappable provider interface), but defer implementation until NBA/NFL validated.

## Sport-Specific Strategies

### NBA (Primary Focus for M0-M1)

#### Why Start with NBA?

- **High volume**: 82-game season, multiple games per night
- **Rich data**: Advanced stats, play-by-play, tracking data (via nba_api)
- **Player props**: Large market with many bookmakers offering lines
- **Fast iteration**: Daily games = quick feedback loops

#### Target Markets (Priority Order)

1. **Player Points Over/Under** (MVP)
   - Most liquid prop market
   - Relatively predictable (compared to assists/rebounds)
   - Feature-rich: usage, pace, opponent defense, rest days

2. **Player Assists/Rebounds**
   - Similar to points but different distributions
   - Assists: Poisson-like (discrete, low-count)
   - Rebounds: Depends on pace, shot quality, positioning

3. **Player 3-Pointers Made**
   - Binary + count: Did they hit? How many?
   - Variance is high (hot/cold shooting)

4. **Same-Game Parlays (SGP)** (Future)
   - Correlated outcomes (e.g., LeBron points + Lakers win)
   - Books often misprice correlations
   - Requires dependency modeling

#### Key Features for NBA

**Player-Level:**
- Last 10 games: mean, std dev, trend
- Season averages: points, FGA, FTA, minutes
- Usage rate, TS%, PER
- Home/away splits
- Back-to-back games (rest)
- Injury history (DTD, minutes restrictions)

**Matchup:**
- Opponent defensive rating (overall and vs. position)
- Pace (possessions per 48 min)
- Referee tendencies (foul calls)

**Context:**
- Line movement (opening vs. current)
- Public betting % (if available)
- Weather: N/A for NBA (indoor)

#### Model Approaches

**Baseline (M0):**
- Simple over/under: player's recent avg ± 0.5 std dev → prob
- Compare to market implied prob → edge
- If edge > 5%, recommend

**Intermediate (M1):**
- Generalized Linear Model (GLM) with Poisson/Gaussian
- Features: player recent, opponent defense, pace, rest
- Calibrate on holdout set

**Advanced (M2+):**
- XGBoost/LightGBM with engineered features
- Ensemble: GLM + tree model + market signal
- Incorporate line movement and sharp money indicators

---

### NFL (M2+)

#### Why NFL is Different

- **Weekly games**: Only 17 regular-season games per team
- **Lower sample size**: Harder to train complex models
- **Public bias**: Heavy favorites and popular teams often overbet
- **Weather impact**: Critical for outdoor games (wind, rain, snow)
- **Injury uncertainty**: Players hide injuries; practice reports are noisy

#### Target Markets

1. **Player Passing Yards** (QB props)
   - Large market, high liquidity
   - Affected by: opponent pass defense, weather, game script

2. **Player Rushing Yards** (RB props)
   - Dependent on game script (leading teams run more)
   - Opponent run defense, O-line quality

3. **Player Receiving Yards** (WR/TE props)
   - Target share, QB quality, defensive coverage

4. **Touchdowns (Anytime TD scorer)**
   - Binary, low-probability events (harder to price)
   - Red-zone usage is key

#### Key Features for NFL

**Player-Level:**
- Season averages (YPG, TDs, targets/carries)
- Last 3 games (recent form)
- Snap count % (usage)
- Red-zone opportunities

**Matchup:**
- Opponent pass/rush defense rank (DVOA or EPA-based)
- Home/away
- Divisional game (more familiarity)

**Context:**
- Weather: wind >15 mph (affects passing), rain, snow
- Betting line: Point spread and total (game script proxy)
- Injuries: Key players (e.g., QB, O-line) in/out

**Game Script:**
- If team is favored by 7+, expect more rushing (clock management)
- If underdog, expect more passing (playing catch-up)

#### Model Approaches

**Baseline:**
- Player's season avg adjusted for opponent defense rank
- Weather adjustment (e.g., -10% passing yards if wind >15 mph)

**Intermediate:**
- GLM with game script features
- Separate models for rushing vs. passing

**Advanced:**
- Simulate game flow (possessions, score differential)
- Dynamic game script: predict when team will be ahead/behind
- Incorporate betting market signals (line movement, steam moves)

---

### MLB (M2+)

#### Why MLB is Different

- **162 games**: Most data of any sport
- **Pitcher-centric**: Starting pitcher drives most of the variance
- **Discrete outcomes**: Hits, strikeouts, home runs (not continuous like points)
- **Weather matters**: Wind (home runs), humidity, temperature
- **Platoon splits**: L/R matchups are critical

#### Target Markets

1. **Pitcher Strikeouts Over/Under**
   - Highly predictable (K/9 is stable)
   - Opponent team K% is a strong signal

2. **Batter Total Bases**
   - Continuous-ish (0, 1, 2, 3, 4+)
   - Depends on: batter vs. pitcher handedness, ballpark, weather

3. **Home Runs (Yes/No)**
   - Binary, low-probability
   - Ballpark factors (e.g., Coors Field in Denver)

4. **Team Totals (Over/Under)**
   - More efficient than player props
   - Pitcher + lineup + ballpark + weather

#### Key Features for MLB

**Pitcher:**
- K/9, BB/9, ERA, FIP, xFIP (expected FIP)
- Recent starts (last 3 games)
- Opponent team K%, wOBA vs. L/R pitchers

**Batter:**
- wOBA, ISO, K%, BB% (season and last 30 days)
- vs. L/R pitcher splits
- Ballpark factors (home/away)

**Context:**
- Weather: wind direction and speed, temperature
- Umpire: Strike zone tendencies (affects K rate)
- Lineup order (batters 1-4 get more PAs)

#### Model Approaches

**Baseline:**
- Pitcher's season K/9 vs. opponent team K%
- Linear adjustment for ballpark and weather

**Intermediate:**
- Poisson regression for discrete outcomes (strikeouts, hits)
- Batter vs. pitcher handedness matchups

**Advanced:**
- Simulate at-bats (Monte Carlo)
- Expected stats (xwOBA, xSLG) from Statcast data
- Ballpark + weather interaction effects

---

### MMA (Future)

#### Why MMA is Attractive

- **Smaller markets**: Less sharp, more exploitable
- **Fight-by-fight independence**: No "season" or "team" dynamics
- **Rich features**: Fighter styles, reach, age, training camps, weight cuts
- **Finish method props**: KO/TKO, submission, decision (higher variance = mispricing)

#### Target Markets

1. **Fight Winner (Moneyline)**
   - Basic, but MMA moneylines often have value vs. other sports

2. **Method of Victory**
   - KO/TKO, submission, decision
   - Style matchups matter (striker vs. grappler)

3. **Over/Under Rounds**
   - Finish rate vs. decision
   - Cardio, age, fight IQ

4. **Fighter Props**
   - Total strikes landed, takedowns, knockdowns

#### Key Features for MMA

**Fighter:**
- Record (W-L-D), finish rate (KO%, sub%)
- Reach, height, age
- Recent form (last 3 fights)
- Training camp (coach, gym, sparring partners)
- Weight cut history (fighters who struggle to make weight)

**Matchup:**
- Style matchup (striker vs. grappler, orthodox vs. southpaw)
- Reach advantage
- Age gap

**Context:**
- Main card vs. prelims (fighter motivation, skill level)
- Title fight (5 rounds vs. 3 rounds)
- Venue (altitude, cage size)

#### Model Approaches

**Baseline:**
- Elo-style ratings with style adjustments
- Finish rate vs. opponent's defense

**Intermediate:**
- Logistic regression for fight outcome
- Separate models for finish method

**Advanced:**
- Simulate round-by-round (Markov chain)
- Fighter aging curves
- Camp quality features (if data available)

#### Why Defer MMA to Later?

- **Smaller data sets**: Fewer fights per fighter
- **Domain expertise needed**: MMA requires deep sport knowledge
- **NBA/NFL validation first**: Prove the system works before expanding
- **Architecture supports it**: Provider interface is ready when we are

---

## Cross-Sport Insights

### Market Efficiency Spectrum

**Most Efficient (Hardest to Beat):**
1. NFL point spreads
2. NBA totals
3. MLB moneylines

**Least Efficient (Most Opportunity):**
1. Player props (all sports)
2. Same-game parlays
3. MMA finish method props
4. Low-volume leagues (WNBA, G League, international)

### Variance and Sample Size

| Sport | Games/Season | Data Richness | Sample Size Challenge |
|-------|--------------|---------------|----------------------|
| NBA   | 82           | High (tracking data) | Low |
| NFL   | 17           | Medium (snap counts) | High |
| MLB   | 162          | Very High (Statcast) | Low |
| MMA   | 2-4/year     | Low (manual tracking) | Very High |

**Implication**: NBA and MLB allow more robust models. NFL and MMA require simpler, more conservative approaches.

### Feature Engineering Themes

**Universal:**
- Recent form (last N games/fights)
- Opponent quality/defense
- Home/away or venue effects
- Rest/fatigue

**Sport-Specific:**
- NBA: Pace, usage, back-to-backs
- NFL: Weather, game script, snap counts
- MLB: Pitcher handedness, ballpark, umpire
- MMA: Reach, weight cut, finish rates

---

## Strategic Recommendations

### M0-M1: Focus on NBA

- Deepest data, fastest iteration
- Validate core system (math, storage, eval)
- Prove paper trading workflow

### M2: Expand to NFL

- Weekly cadence (less time-intensive than NBA)
- Public bias creates opportunities
- Weather and game script are fun challenges

### M3: Add MLB

- Summer sport (fills NBA/NFL off-season)
- Pitcher props are highly predictable
- Ballpark effects are well-documented

### M4+: Consider MMA

- Only after NBA/NFL models are profitable in paper trading
- Requires domain expert or partnership
- Start with simple Elo + finish rate models

---

## Conclusion

**The math is universal, but the features and intuition are sport-specific.** LineLogic's architecture supports multiple sports through:

- **Swappable providers**: Each sport has its own data adapters
- **Sport-specific feature modules**: `features/nba.py`, `features/nfl.py`, etc.
- **Shared evaluation**: Brier, CLV, ROI work across all sports

**Next steps:**

1. Build NBA vertical slice (M0-M1)
2. Document lessons learned in ADRs
3. Extend to NFL/MLB/MMA once NBA is validated

---

**Next**: [Math Foundations](03_math_foundations.md) | [Data Sources](04_data_sources.md)
