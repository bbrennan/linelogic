#!/usr/bin/env python3
"""
A/B Testing Template: Track Model Predictions vs Actual Outcomes

This script provides a framework for validating model confidence tiers in production.
Run this weekly or monthly to assess model calibration by segment.

Usage:
    python scripts/validate_predictions.py --predictions docs/status/predictions_log.csv
    python scripts/validate_predictions.py --predictions docs/status/predictions_log.csv --by-tier
    python scripts/validate_predictions.py --predictions docs/status/predictions_log.csv --by-team --week 2026-W02
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


class PredictionValidator:
    """Validates predictions vs actual outcomes and computes calibration metrics."""

    def __init__(self, predictions_csv, verbose=False):
        """
        Args:
            predictions_csv (str): Path to predictions log CSV
            verbose (bool): Print detailed output
        """
        self.verbose = verbose
        self.pred_path = Path(predictions_csv)

        if not self.pred_path.exists():
            raise FileNotFoundError(
                f"Predictions log not found: {self.pred_path}\n"
                f"Create one using: python scripts/infer_daily.py --output predictions_YYYY-MM-DD.csv"
            )

        # Load predictions
        self.df = pd.read_csv(self.pred_path)
        self.df["date"] = pd.to_datetime(self.df["date"])

        # Ensure required columns
        required_cols = [
            "date",
            "home_team",
            "away_team",
            "pred_home_win_prob",
            "confidence_tier",
            "actual_home_win",
        ]
        missing = [c for c in required_cols if c not in self.df.columns]
        if missing:
            raise ValueError(f"Missing columns in predictions log: {missing}")

        # Parse confidence tiers
        self.df["tier"] = self.df["confidence_tier"].str.extract(r"(TIER \d)")[0]

        if self.verbose:
            print(f"✓ Loaded {len(self.df)} predictions from {self.pred_path}")
            print(
                f"  Date range: {self.df['date'].min().date()} to {self.df['date'].max().date()}"
            )
            print(f"  Tiers: {sorted(self.df['tier'].unique())}")

    def compute_calibration(self):
        """Compute overall calibration metrics."""
        self.df["pred_binary"] = (self.df["pred_home_win_prob"] >= 0.5).astype(int)
        self.df["pred_correct"] = (
            self.df["pred_binary"] == self.df["actual_home_win"]
        ).astype(int)

        metrics = {
            "total_predictions": len(self.df),
            "accuracy": self.df["pred_correct"].mean(),
            "log_loss": self._compute_logloss(),
            "brier_score": self._compute_brier(),
            "baseline_home_win_rate": self.df["actual_home_win"].mean(),
        }

        return metrics

    def _compute_logloss(self):
        """Compute log loss."""
        eps = 1e-15
        y = self.df["actual_home_win"]
        p = np.clip(self.df["pred_home_win_prob"], eps, 1 - eps)
        return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))

    def _compute_brier(self):
        """Compute Brier score."""
        y = self.df["actual_home_win"]
        p = self.df["pred_home_win_prob"]
        return np.mean((p - y) ** 2)

    def calibration_by_tier(self):
        """Compute calibration metrics by confidence tier."""
        results = []

        for tier in sorted(self.df["tier"].dropna().unique()):
            tier_df = self.df[self.df["tier"] == tier]
            if len(tier_df) == 0:
                continue

            tier_df_copy = tier_df.copy()
            tier_df_copy["pred_binary"] = (
                tier_df_copy["pred_home_win_prob"] >= 0.5
            ).astype(int)
            tier_df_copy["pred_correct"] = (
                tier_df_copy["pred_binary"] == tier_df_copy["actual_home_win"]
            ).astype(int)

            metrics = {
                "tier": tier,
                "n_games": len(tier_df),
                "accuracy": tier_df_copy["pred_correct"].mean(),
                "actual_home_win_rate": tier_df_copy["actual_home_win"].mean(),
                "avg_pred_prob": tier_df_copy["pred_home_win_prob"].mean(),
                "log_loss": self._compute_logloss_subset(tier_df),
                "brier_score": self._compute_brier_subset(tier_df),
            }
            results.append(metrics)

        return pd.DataFrame(results)

    def _compute_logloss_subset(self, subset_df):
        """Compute log loss for subset."""
        eps = 1e-15
        y = subset_df["actual_home_win"]
        p = np.clip(subset_df["pred_home_win_prob"], eps, 1 - eps)
        return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))

    def _compute_brier_subset(self, subset_df):
        """Compute Brier score for subset."""
        y = subset_df["actual_home_win"]
        p = subset_df["pred_home_win_prob"]
        return np.mean((p - y) ** 2)

    def calibration_by_team(self):
        """Compute calibration metrics by home team."""
        results = []

        for team in sorted(self.df["home_team"].unique()):
            team_df = self.df[self.df["home_team"] == team]
            if len(team_df) < 5:  # Skip teams with <5 games
                continue

            team_df_copy = team_df.copy()
            team_df_copy["pred_binary"] = (
                team_df_copy["pred_home_win_prob"] >= 0.5
            ).astype(int)
            team_df_copy["pred_correct"] = (
                team_df_copy["pred_binary"] == team_df_copy["actual_home_win"]
            ).astype(int)

            metrics = {
                "home_team": team,
                "n_games": len(team_df),
                "actual_win_rate": team_df_copy["actual_home_win"].mean(),
                "accuracy": team_df_copy["pred_correct"].mean(),
                "avg_pred_prob": team_df_copy["pred_home_win_prob"].mean(),
            }
            results.append(metrics)

        return pd.DataFrame(results).sort_values("actual_win_rate", ascending=False)

    def calibration_by_prediction_bucket(self):
        """Compute calibration by prediction probability bucket."""
        # Create probability buckets
        bins = [0, 0.45, 0.50, 0.55, 0.60, 1.0]
        labels = ["<45%", "45-50%", "50-55%", "55-60%", ">60%"]

        self.df["pred_bucket"] = pd.cut(
            self.df["pred_home_win_prob"], bins=bins, labels=labels, include_lowest=True
        )

        results = []

        for bucket in labels:
            bucket_df = self.df[self.df["pred_bucket"] == bucket]
            if len(bucket_df) == 0:
                continue

            bucket_df_copy = bucket_df.copy()
            bucket_df_copy["pred_binary"] = (
                bucket_df_copy["pred_home_win_prob"] >= 0.5
            ).astype(int)
            bucket_df_copy["pred_correct"] = (
                bucket_df_copy["pred_binary"] == bucket_df_copy["actual_home_win"]
            ).astype(int)

            metrics = {
                "pred_bucket": bucket,
                "n_games": len(bucket_df),
                "avg_pred_prob": bucket_df["pred_home_win_prob"].mean(),
                "actual_home_win_rate": bucket_df["actual_home_win"].mean(),
                "accuracy": bucket_df_copy["pred_correct"].mean(),
                "calibration_error": abs(
                    bucket_df["pred_home_win_prob"].mean()
                    - bucket_df["actual_home_win"].mean()
                ),
            }
            results.append(metrics)

        return pd.DataFrame(results)

    def false_positives_negatives(self):
        """Identify high-confidence errors."""
        self.df["pred_binary"] = (self.df["pred_home_win_prob"] >= 0.5).astype(int)
        self.df["pred_correct"] = (
            self.df["pred_binary"] == self.df["actual_home_win"]
        ).astype(int)

        # High-confidence errors (>0.65 prob, got it wrong)
        high_conf_errors = self.df[
            (
                (self.df["pred_home_win_prob"] > 0.65)
                | (self.df["pred_home_win_prob"] < 0.35)
            )
            & (~self.df["pred_correct"])
        ][
            [
                "date",
                "home_team",
                "away_team",
                "pred_home_win_prob",
                "actual_home_win",
                "confidence_tier",
            ]
        ].sort_values(
            "pred_home_win_prob", key=abs, ascending=False
        )

        return high_conf_errors

    def print_report(self, by_tier=False, by_team=False, by_bucket=False):
        """Print formatted validation report."""
        print("\n" + "=" * 80)
        print("MODEL VALIDATION REPORT")
        print("=" * 80)

        # Overall metrics
        metrics = self.compute_calibration()
        print(f"\nOVERALL METRICS ({metrics['total_predictions']} games):")
        print(f"  Accuracy:                {metrics['accuracy']:.2%}")
        print(f"  Log Loss:                {metrics['log_loss']:.4f}")
        print(f"  Brier Score:             {metrics['brier_score']:.4f}")
        print(f"  Baseline Home Win Rate:  {metrics['baseline_home_win_rate']:.2%}")

        # By tier
        if by_tier:
            print("\n" + "-" * 80)
            print("ACCURACY BY CONFIDENCE TIER:")
            print("-" * 80)

            tier_df = self.calibration_by_tier()
            for _, row in tier_df.iterrows():
                status = "✓" if row["accuracy"] >= 0.68 else "⚠"
                print(
                    f"{status} {row['tier']:15} | Accuracy: {row['accuracy']:6.2%} | "
                    f"n={row['n_games']:3} | Avg Pred: {row['avg_pred_prob']:5.2%} | "
                    f"Actual Win Rate: {row['actual_home_win_rate']:.2%}"
                )

            # Calibration error by tier
            tier_df["calibration_error"] = abs(
                tier_df["avg_pred_prob"] - tier_df["actual_home_win_rate"]
            )
            print(f"\n  Expected accuracy by tier:")
            print(f"    TIER 1: ≥70%")
            print(f"    TIER 2: 68-70%")
            print(f"    TIER 3: 65-68%")
            print(f"    TIER 4: <50% (expected weakness)")

        # By team
        if by_team:
            print("\n" + "-" * 80)
            print("ACCURACY BY HOME TEAM (Top/Bottom 5):")
            print("-" * 80)

            team_df = self.calibration_by_team()
            print("\nTop 5 (Highest actual win rate):")
            for _, row in team_df.head(5).iterrows():
                print(
                    f"  {row['home_team']:3} | Actual: {row['actual_win_rate']:5.1%} | "
                    f"Predicted: {row['avg_pred_prob']:5.1%} | Accuracy: {row['accuracy']:5.1%} (n={row['n_games']:.0f})"
                )

            print("\nBottom 5 (Lowest actual win rate):")
            for _, row in team_df.tail(5).iterrows():
                print(
                    f"  {row['home_team']:3} | Actual: {row['actual_win_rate']:5.1%} | "
                    f"Predicted: {row['avg_pred_prob']:5.1%} | Accuracy: {row['accuracy']:5.1%} (n={row['n_games']:.0f})"
                )

        # By prediction bucket
        if by_bucket:
            print("\n" + "-" * 80)
            print("CALIBRATION BY PREDICTION PROBABILITY BUCKET:")
            print("-" * 80)

            bucket_df = self.calibration_by_prediction_bucket()
            for _, row in bucket_df.iterrows():
                error_marker = "✓" if row["calibration_error"] < 0.05 else "⚠"
                print(
                    f"{error_marker} {row['pred_bucket']:10} | "
                    f"Avg Pred: {row['avg_pred_prob']:5.2%} | "
                    f"Actual: {row['actual_home_win_rate']:5.2%} | "
                    f"Calibration Error: {row['calibration_error']:5.2%} | "
                    f"Accuracy: {row['accuracy']:.2%} (n={row['n_games']:.0f})"
                )

        # High-confidence errors
        print("\n" + "-" * 80)
        print("HIGH-CONFIDENCE ERRORS (>65% or <35% confidence, but got it wrong):")
        print("-" * 80)

        errors = self.false_positives_negatives()
        if len(errors) == 0:
            print("  None! All high-confidence predictions were correct.")
        else:
            for _, row in errors.head(10).iterrows():
                print(
                    f"  {row['date'].date()} | {row['home_team']} vs {row['away_team']:3} | "
                    f"Pred: {row['pred_home_win_prob']:.1%} | "
                    f"Actual: {'Home W' if row['actual_home_win'] else 'Away W':7} | "
                    f"{row['confidence_tier']}"
                )

        print("\n" + "=" * 80)

    def export_report(self, output_json=None, output_csv=None):
        """Export results to JSON and/or CSV."""
        report = {
            "date_generated": datetime.now().isoformat(),
            "n_predictions": len(self.df),
            "date_range": {
                "min": self.df["date"].min().isoformat(),
                "max": self.df["date"].max().isoformat(),
            },
            "overall_metrics": self.compute_calibration(),
            "by_tier": self.calibration_by_tier().to_dict(orient="records"),
            "by_team": self.calibration_by_team().to_dict(orient="records"),
            "by_bucket": self.calibration_by_prediction_bucket().to_dict(
                orient="records"
            ),
        }

        if output_json:
            with open(output_json, "w") as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n✓ Report exported to {output_json}")

        if output_csv:
            # Export tier-level metrics as CSV
            tier_df = self.calibration_by_tier()
            tier_df.to_csv(output_csv, index=False)
            print(f"✓ Tier metrics exported to {output_csv}")

        return report


def main():
    parser = argparse.ArgumentParser(
        description="Validate predictions vs actual outcomes by segment"
    )
    parser.add_argument(
        "--predictions",
        type=str,
        required=True,
        help="Path to predictions_log.csv",
    )
    parser.add_argument(
        "--by-tier",
        action="store_true",
        help="Show breakdown by confidence tier",
    )
    parser.add_argument(
        "--by-team",
        action="store_true",
        help="Show breakdown by home team",
    )
    parser.add_argument(
        "--by-bucket",
        action="store_true",
        help="Show calibration by probability bucket",
    )
    parser.add_argument(
        "--export-json",
        type=str,
        default=None,
        help="Export full report to JSON",
    )
    parser.add_argument(
        "--export-csv",
        type=str,
        default=None,
        help="Export tier metrics to CSV",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    try:
        validator = PredictionValidator(args.predictions, verbose=args.verbose)

        # Show all breakdowns by default
        show_all = not (args.by_tier or args.by_team or args.by_bucket)

        validator.print_report(
            by_tier=(args.by_tier or show_all),
            by_team=(args.by_team or show_all),
            by_bucket=(args.by_bucket or show_all),
        )

        if args.export_json or args.export_csv:
            validator.export_report(
                output_json=args.export_json, output_csv=args.export_csv
            )

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
