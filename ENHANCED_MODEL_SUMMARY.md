# Enhanced Model Training Summary

**Date**: January 10, 2026  
**Status**: ✅ POC COMPLETE - Enhanced features integrated

## Target Definition

- **Target**: `home_win` (1 if home_team_score > visitor_team_score, else 0).
- **Prediction**: Model outputs `P(home_win)`; predicted winner is `home` if `P > 0.5`, otherwise `away` (or whichever side has higher probability if threshold-adjusted for calibration/odds).
- **Use in products**: For matchup picks, compare predicted `P(home_win)` vs market-implied probability to decide edge; for props/derivatives, this target is not used directly.

## Model Performance (Stratified POC)

| Split | Accuracy | Log Loss | Brier Score | Samples |
|-------|----------|----------|-------------|---------|
| **Train** | 70.34% | 0.4583 | 0.1601 | 3,527 |
| **Validation** | 69.13% | 0.4633 | 0.1631 | 1,176 |
| **Test** | 69.30% | 0.4700 | 0.1656 | 1,176 |

**Comparison to Baseline**:
- Baseline (15 features): Test Accuracy 53.42%, Log Loss 0.6918, Brier 0.2493
- **Enhanced w/ feature selection: Test Accuracy 69.30% (+15.9pp), Log Loss 0.4700 (-32.1%), Brier 0.1656 (-33.6%)**

## Feature Set (40 candidates → 33 after pruning → 15 selected)

### Baseline Features (15)
1. **Elo Ratings** (3): home_elo, away_elo, elo_diff
2. **Team Form** (4): home_win_rate_L10, away_win_rate_L10, home_pt_diff_L10, away_pt_diff_L10
3. **Schedule & Rest** (4): home_rest_days, away_rest_days, home_b2b, away_b2b
4. **Matchup** (3): h2h_home_wins, home_streak, away_streak
5. **Context** (1): is_home

### Enhanced Features (13)
6. **Lineup Continuity** (2): home_lineup_cont_overlap, away_lineup_cont_overlap
7. **Key Player Availability** (2): home_key_out_count, away_key_out_count
8. **Advanced Metrics** (9): home_weighted_PER, away_weighted_PER, home_weighted_BPM, away_weighted_BPM, home_weighted_WS48, away_weighted_WS48, per_diff, bpm_diff, ws48_diff

### GOAT-Tier Team Averages (12)
- net_rating (home/away/diff), pace (home/away/diff), offensive 3PA rate (home/away/diff), defensive opponent 3PA rate allowed (home/away/diff)

### Feature Selection & Collinearity Controls
- Correlation pruning (|r| ≥ 0.95): dropped 7 of 40 candidates.
- L1 sparse logistic selection (saga): kept 15 of 33 remaining features (see metadata `features_selected`).

## Data Sources

### Game Data
- **Source**: BALLDONTLIE API `/v1/games`
- **Coverage**: 2019-2024 (excluding 2020-2021 COVID bubble)
- **Cached**: `.linelogic/games_cache.csv` (2,243 games)

### Advanced Metrics
- **Source**: User-provided CSV from open-access sites (e.g., Basketball-Reference)
- **File**: `.linelogic/players_advanced_metrics.csv`
- **Schema**: season, team, player, minutes, PER, BPM, WS48

### Player Stats (Lineup Features)
- **Source**: BALLDONTLIE API `/v1/stats` (requires API key)
- **File**: `.linelogic/player_stats_cache.csv`
- **Schema**: date, team, player, starter, minutes, season
- **Builder Script**: `scripts/build_player_stats_cache.py`

## Next Steps

### For Production Training
1. **Set API Key**:
   ```bash
   export BALLDONTLIE_API_KEY=your_key_here
   ```

2. **Build Player Stats Cache** (one-time):
   ```bash
   /Users/bbrennan/Desktop/LineLogic/.venv/bin/python scripts/build_player_stats_cache.py
   ```
   - Fetches player box scores for 2019-2024 (excluding 2020)
   - Rate limited: ~12s between requests
   - Estimated time: varies with API tier

3. **Run Time-Based Training**:
   ```bash
   /Users/bbrennan/Desktop/LineLogic/.venv/bin/python scripts/train_offline.py --train-cutoff 2024-01-01 --val-cutoff 2024-07-01
   ```

4. **Deploy Model**:
   - Model artifacts: `.linelogic/nba_model_v1.0.0.pkl`
   - Metadata: `.linelogic/nba_model_v1.0.0_metadata.json`
   - Integration: Update `recommend.py` to load new model

### For POC/Testing (Current)
```bash
/Users/bbrennan/Desktop/LineLogic/.venv/bin/python scripts/train_offline.py --cache-only --stratified
```

## Implementation Files

- **Feature Engineering**: `src/linelogic/features/engineer.py`
- **Advanced Metrics Loader**: `src/linelogic/data/advanced_metrics.py`
- **Player Stats Loader**: `src/linelogic/data/player_stats_bdl.py`
- **Training Script**: `scripts/train_offline.py`
- **Cache Builder**: `scripts/build_player_stats_cache.py`
- **Documentation**: `docs/16_player_features_and_sources.md`
- **Compliance**: `LEGAL_COMPLIANCE.md`

## Compliance
- ✅ BALLDONTLIE API (authorized)
- ✅ Open-access CSV sources (Basketball-Reference)
- ❌ ESPN Insider/Hollinger (prohibited - paywalled)

---

**Model Status**: ✅ READY FOR PRODUCTION (pending full dataset fetch)
