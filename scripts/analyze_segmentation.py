#!/usr/bin/env python3
"""
Deep segmentation analysis for model trustworthiness.
Identifies which scenarios the model should be trusted vs cautious.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load data
cache_path = Path(".linelogic/games_cache.csv")
df = pd.read_csv(cache_path)
df["date"] = pd.to_datetime(df["date"])
df = df[(df["home_score"] > 0) & (df["away_score"] > 0)]
df = df[df["date"].dt.year != 2023].sort_values("date")

print("=" * 80)
print("DEEP SEGMENTATION ANALYSIS - MODEL TRUSTWORTHINESS")
print("=" * 80)
print(
    f"\nDataset: {len(df)} games, {df['date'].min().date()} to {df['date'].max().date()}"
)
print(f"Baseline home win rate: {df['home_win'].mean():.2%}\n")

# Estimate rest days
df["rest_days"] = df.groupby("home_team")["date"].diff().dt.days.fillna(3)


def bucket_rest(days):
    if days <= 0:
        return "B2B"
    if days == 1:
        return "1-day"
    if days <= 3:
        return "2-3 days"
    return "4+ days"


df["rest_bucket"] = df["rest_days"].apply(bucket_rest)

print("\n" + "=" * 80)
print("1. BY SEASON")
print("=" * 80)
season_stats = (
    df.groupby(df["date"].dt.year).agg({"home_win": ["count", "mean", "std"]}).round(3)
)
season_stats.columns = ["n", "home_wr", "std"]
for yr, row in season_stats.iterrows():
    print(
        f"  {int(yr)}: n={int(row['n']):3d}, home_wr={row['home_wr']:6.1%}, std={row['std']:.3f}"
    )

print("\n" + "=" * 80)
print("2. BY REST BUCKET")
print("=" * 80)
rest_order = ["B2B", "1-day", "2-3 days", "4+ days"]
rest_stats = df.groupby("rest_bucket").agg({"home_win": ["count", "mean"]}).round(3)
rest_stats.columns = ["n", "home_wr"]
for bucket in rest_order:
    if bucket in rest_stats.index:
        row = rest_stats.loc[bucket]
        print(f"  {bucket:8s}: n={int(row['n']):3d}, home_wr={row['home_wr']:6.1%}")

print("\n" + "=" * 80)
print("3. BY HOME TEAM (n >= 30)")
print("=" * 80)
team_stats = df.groupby("home_team").agg({"home_win": ["count", "mean"]}).round(3)
team_stats.columns = ["n", "home_wr"]
team_stats = team_stats[team_stats["n"] >= 30].sort_values("home_wr", ascending=False)
for team, row in team_stats.iterrows():
    conf = "HIGH" if 0.48 <= row["home_wr"] <= 0.60 else "CAUTION"
    print(f"  {team:20s}: n={int(row['n']):3d}, home_wr={row['home_wr']:6.1%} [{conf}]")

print("\n" + "=" * 80)
print("4. BY SEASON + REST COMBO")
print("=" * 80)
combo_stats = (
    df.groupby([df["date"].dt.year, "rest_bucket"])
    .agg({"home_win": ["count", "mean"]})
    .round(3)
)
combo_stats.columns = ["n", "home_wr"]
combo_stats = combo_stats[combo_stats["n"] >= 10]
for (yr, bucket), row in combo_stats.iterrows():
    print(
        f"  {int(yr)} + {bucket:8s}: n={int(row['n']):3d}, home_wr={row['home_wr']:6.1%}"
    )

print("\n" + "=" * 80)
print("5. CONFIDENCE TIERS (by home_win deviation from 54%)")
print("=" * 80)
baseline = df["home_win"].mean()
print(f"\nBaseline home_wr: {baseline:.2%}\n")

print("TIER 1 (HIGH CONFIDENCE): home_wr within 2% of baseline (52-56%)")
print("  → Use model predictions with confidence")
print("  → Trust probability estimates\n")

print("TIER 2 (MEDIUM-HIGH): home_wr 50-52% or 56-58%")
print("  → Use model but apply 1.5x uncertainty buffer")
print("  → Lean on model as tiebreaker\n")

print("TIER 3 (MEDIUM): home_wr 48-50% or 58-60%")
print("  → Use model with caution")
print("  → Combine with external factors\n")

print("TIER 4 (LOW): home_wr < 48% or > 60%")
print("  → Investigate scenario separately")
print("  → May have small sample size or anomaly")
print("  → Do not rely solely on model\n")

# Categorize segments
print("=" * 80)
print("6. SCENARIO CLASSIFICATION")
print("=" * 80)

tier1_segments = []
tier2_segments = []
tier3_segments = []
tier4_segments = []

for (yr, bucket), row in combo_stats.iterrows():
    wr = row["home_wr"]
    if 0.52 <= wr <= 0.56:
        tier1_segments.append(
            f"  {int(yr)} {bucket:8s}: {row['home_wr']:.1%} (n={int(row['n'])})"
        )
    elif 0.50 <= wr < 0.52 or 0.56 < wr <= 0.58:
        tier2_segments.append(
            f"  {int(yr)} {bucket:8s}: {row['home_wr']:.1%} (n={int(row['n'])})"
        )
    elif 0.48 <= wr < 0.50 or 0.58 < wr <= 0.60:
        tier3_segments.append(
            f"  {int(yr)} {bucket:8s}: {row['home_wr']:.1%} (n={int(row['n'])})"
        )
    else:
        tier4_segments.append(
            f"  {int(yr)} {bucket:8s}: {row['home_wr']:.1%} (n={int(row['n'])})"
        )

if tier1_segments:
    print(f"\nTIER 1 ({len(tier1_segments)} segments - HIGH CONFIDENCE):")
    for seg in tier1_segments:
        print(seg)

if tier2_segments:
    print(f"\nTIER 2 ({len(tier2_segments)} segments - MEDIUM-HIGH):")
    for seg in tier2_segments:
        print(seg)

if tier3_segments:
    print(f"\nTIER 3 ({len(tier3_segments)} segments - MEDIUM):")
    for seg in tier3_segments:
        print(seg)

if tier4_segments:
    print(f"\nTIER 4 ({len(tier4_segments)} segments - LOW/CAUTION):")
    for seg in tier4_segments:
        print(seg)

print("\n" + "=" * 80)
print("7. DEPLOYMENT RECOMMENDATIONS")
print("=" * 80)
print(
    """
✓ USE MODEL WITH CONFIDENCE:
  • 2024-2025 regular season games
  • Any rest scenario (B2B to 4+ days)
  • Standard home team matchups

⚠ USE WITH CAUTION:
  • Edge cases: very high/low home_wr teams
  • Rare rest + season combinations
  • Back-to-back scenarios (slight model weakness if detected)

✗ DO NOT RELY SOLELY ON MODEL:
  • Playoff or tournament games (different dynamics)
  • COVID/injury-impacted games
  • Games with unusual lineups (if available)
  • Major team trades/roster changes

OPERATIONAL:
  • Log all predictions with confidence (probability output)
  • Track accuracy by segment (see above tiers)
  • Retrain monthly with new 2025-2026 data
  • Validate model on live games before betting
"""
)

print("=" * 80)
