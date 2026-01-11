#!/usr/bin/env python3
"""
Offline NBA Model Training Script with Professional Logging

Features:
- Trains on 2019-2024 data (excludes 2020-2021 COVID bubble)
- Professional structured logging for progress tracking
- Robust error handling and recovery
- Cursor-based pagination (fixes infinite loop bug)
- Synthetic data fallback when API unavailable

Usage:
    python train_offline_v2.py                  # Default: fetch + train (2019-2024, excludes COVID)
    python train_offline_v2.py --cache-only     # Load from cached data
    python train_offline_v2.py --data-cache FILE # Use specific cache file
"""

import argparse
import json
import logging
import os
import pickle
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import mlflow
import mlflow.sklearn

# Load environment variables from .env file
load_dotenv()

# Configure robust professional logging to STDOUT
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],  # Force output to stdout
)
logger = logging.getLogger(__name__)
logger.propagate = True  # Ensure all messages propagate

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import synthetic data generator
sys.path.insert(0, str(Path(__file__).parent))
try:
    from generate_synthetic_games import generate_synthetic_games
except ImportError:
    generate_synthetic_games = None

from linelogic.features.engineer import FeatureEngineer
from linelogic.data.advanced_metrics import load_team_advanced_metrics
from linelogic.data.player_stats_bdl import load_player_stats_cache
from linelogic.data.team_season_avgs import load_team_season_avgs
from linelogic.data.odds_cache import load_odds_cache
from linelogic.data.player_injuries_cache import load_player_injuries_cache
from linelogic.eval.metrics import (
    calibration_errors as ll_calibration_errors,
    calibration_table as ll_calibration_table,
)


def fetch_historical_games(
    start_season=2019, end_season=2024, api_key=None, allow_synthetic: bool = True
):
    """Fetch historical NBA games from BALLDONTLIE API or use synthetic data.

    Excludes 2020-2021 season (COVID bubble) as it's statistically anomalous.
    Uses cursor-based pagination for reliable data fetching.
    """
    # Filter out COVID bubble year
    seasons_to_fetch = [s for s in range(start_season, end_season + 1) if s != 2020]

    logger.info(
        f"Fetching games from {len(seasons_to_fetch)} seasons: {seasons_to_fetch}"
    )
    logger.info("(Excluding 2020-2021 COVID bubble season)")

    all_games = []
    base_url = "https://api.balldontlie.io/v1/games"

    headers = {}
    if api_key:
        headers["Authorization"] = api_key
        logger.debug(f"Using API key: {api_key[:10]}...")
    else:
        logger.warning("No API key provided; will use synthetic data fallback")

    request_count = 0
    last_request_time = time.time()

    for season in seasons_to_fetch:
        logger.info(f"Fetching {season}-{season + 1} season...")
        cursor = None
        season_complete = False
        rate_limited = False
        request_attempt = 0
        max_attempts = 50  # Safety limit to prevent infinite loops
        season_games = 0

        while (
            not season_complete and not rate_limited and request_attempt < max_attempts
        ):
            params = {
                "seasons[]": season,
                "per_page": 100,
            }
            if cursor:
                params["cursor"] = cursor

            try:
                # Rate limiting: 5 req/min = 1 request every 12 seconds
                elapsed = time.time() - last_request_time
                if elapsed < 12:
                    sleep_time = 12 - elapsed
                    logger.info(f"  Waiting for rate limit... ({sleep_time:.1f}s)")
                    sys.stdout.flush()
                    time.sleep(sleep_time)

                logger.info(
                    f"  → API request #{request_count + 1} (attempt {request_attempt}/{max_attempts})"
                )
                sys.stdout.flush()

                resp = requests.get(
                    base_url,
                    params=params,
                    headers=headers,
                    timeout=5,  # Reduced timeout from 10s
                )
                last_request_time = time.time()
                request_count += 1
                request_attempt += 1

                logger.info(f"  ✓ Response received (status {resp.status_code})")
                sys.stdout.flush()

                # Check for rate limiting
                if resp.status_code == 429:
                    logger.warning(
                        "Rate limited (429). Switching to synthetic data fallback"
                    )
                    rate_limited = True
                    break

                resp.raise_for_status()
                data = resp.json()
                logger.info(f"  ✓ Parsed JSON response")
                sys.stdout.flush()

                games = data.get("data", [])
                if not games:
                    logger.info(f"  → No more games for {season}-{season + 1}")
                    season_complete = True
                    break

                logger.info(f"  ✓ Received {len(games)} games, processing...")
                sys.stdout.flush()

                # Process games
                for game in games:
                    if game.get("status") == "Final":
                        all_games.append(
                            {
                                "date": game["date"].split("T")[0],
                                "home_team": game["home_team"]["full_name"],
                                "away_team": game["visitor_team"]["full_name"],
                                "home_score": game["home_team_score"],
                                "away_score": game["visitor_team_score"],
                                "home_win": (
                                    1
                                    if game["home_team_score"]
                                    > game["visitor_team_score"]
                                    else 0
                                ),
                            }
                        )
                        season_games += 1

                logger.info(
                    f"  ✓ Added {season_games} completed games (total: {len(all_games):,})"
                )
                sys.stdout.flush()

                # Get next cursor for pagination
                meta = data.get("meta", {})
                cursor = meta.get("next_cursor")
                if not cursor:
                    logger.info(
                        f"✓ {season}-{season + 1}: {season_games} completed games"
                    )
                    season_complete = True

            except requests.exceptions.Timeout:
                logger.error(
                    f"API timeout for {season}-{season + 1}. Moving to next..."
                )
                season_complete = True
            except requests.exceptions.RequestException as e:
                logger.error(f"API Error for {season}-{season + 1}: {e}")
                season_complete = True
            except Exception as e:
                logger.error(f"Unexpected error for {season}-{season + 1}: {e}")
                season_complete = True

        if request_attempt >= max_attempts:
            logger.warning(
                f"Max attempts ({max_attempts}) reached for {season}. Moving to next..."
            )

    logger.info(
        f"\nFetched {len(all_games)} games from BALLDONTLIE API (via {request_count} requests)"
    )

    # If API failed or insufficient data
    if len(all_games) < 1500:
        msg = (
            f"Insufficient data ({len(all_games)} games). Synthetic fallback disabled."
            if not allow_synthetic
            else f"Insufficient data ({len(all_games)} games). Supplementing with synthetic data..."
        )
        logger.warning(msg)
        if not allow_synthetic:
            sys.exit(1)
        if generate_synthetic_games:
            logger.info("Generating synthetic games...")
            synthetic_games = generate_synthetic_games()
            all_games.extend(synthetic_games)
            logger.info(
                f"Combined dataset: {len(all_games)} total games ({len(synthetic_games)} synthetic)"
            )
        else:
            logger.error("Cannot generate synthetic data")
            sys.exit(1)

    df = pd.DataFrame(all_games)
    df["date"] = pd.to_datetime(df["date"])
    # Drop unplayed or zero-score games (protect home_win baseline)
    before_drop = len(df)
    df = df[(df["home_score"] > 0) & (df["away_score"] > 0)]
    dropped = before_drop - len(df)
    if dropped > 0:
        logger.info(f"Dropped {dropped} games with zero scores before training/cache.")

    # Drop 2023 season (BALD api returned zeros); keep 2024-2025 for now
    before_year_drop = len(df)
    df = df[df["date"].dt.year != 2023]
    if len(df) != before_year_drop:
        logger.info(f"Dropped {before_year_drop - len(df)} games from 2023 season.")

    df = df.sort_values("date").reset_index(drop=True)

    logger.info(f"\nDataset Summary:")
    logger.info(f"  Total games: {len(df):,}")
    logger.info(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    logger.info(f"  Home win rate: {df['home_win'].mean():.2%}")
    logger.info(f"  Unique home teams: {df['home_team'].nunique()}\n")

    return df


def cache_data(df, cache_path):
    """Cache games DataFrame for offline reuse."""
    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache_path, index=False)
    size_mb = cache_path.stat().st_size / 1024 / 1024
    logger.info(f"Cached {len(df):,} games to {cache_path} ({size_mb:.2f} MB)")


def load_cached_data(cache_path):
    """Load cached games DataFrame."""
    logger.info(f"Loading cached data from {cache_path}...")
    df = pd.read_csv(cache_path)
    df["date"] = pd.to_datetime(df["date"])
    before_drop = len(df)
    df = df[(df["home_score"] > 0) & (df["away_score"] > 0)]
    dropped = before_drop - len(df)
    if dropped > 0:
        logger.info(f"Dropped {dropped} cached games with zero scores before training.")
    before_year_drop = len(df)
    df = df[df["date"].dt.year != 2023]
    if len(df) != before_year_drop:
        logger.info(
            f"Dropped {before_year_drop - len(df)} cached games from 2023 season."
        )
    logger.info(
        f"Loaded {len(df):,} games (date range: {df['date'].min().date()} to {df['date'].max().date()})\n"
    )
    return df


def split_data(features_df, train_cutoff: pd.Timestamp, val_cutoff: pd.Timestamp):
    """Split data by time (train/val/test)."""

    train = features_df[features_df["date"] < train_cutoff]
    val = features_df[
        (features_df["date"] >= train_cutoff) & (features_df["date"] < val_cutoff)
    ]
    test = features_df[features_df["date"] >= val_cutoff]

    logger.info(f"Data Split (Time-based):")
    logger.info(f"  Train: {len(train):,} samples (before {train_cutoff.date()})")
    logger.info(
        f"  Validation: {len(val):,} samples ({train_cutoff.date()} to {val_cutoff.date()})"
    )
    logger.info(f"  Test: {len(test):,} samples (after {val_cutoff.date()})\n")

    if len(val) == 0 or len(test) == 0:
        logger.error(
            f"Insufficient data for validation/test splits. Validation: {len(val)}, Test: {len(test)}"
        )
        sys.exit(1)

    return train, val, test


def evaluate_split(model, X, y, scaler, split_name):
    """Evaluate model on a split."""
    X_scaled = scaler.transform(X)

    y_pred_proba = model.predict_proba(X_scaled)[:, 1]
    y_pred = (y_pred_proba > 0.5).astype(int)

    metrics = {
        "log_loss": log_loss(y, y_pred_proba, labels=[0, 1]),
        "brier_score": brier_score_loss(y, y_pred_proba),
        "accuracy": accuracy_score(y, y_pred),
        "n_samples": len(y),
    }

    logger.debug(
        f"{split_name}: Accuracy={metrics['accuracy']:.2%}, LogLoss={metrics['log_loss']:.4f}, Brier={metrics['brier_score']:.4f}"
    )

    return metrics, y_pred_proba


def _bucket_rest(days: float) -> str:
    if days <= 0:
        return "0 (B2B)"
    if days == 1:
        return "1"
    if days <= 3:
        return "2-3"
    return "4+"


def log_segment_metrics(df: pd.DataFrame, proba_col: str = "pred_proba") -> None:
    """Log basic segmentation metrics on the test split."""
    segments = {
        "season": df["date"].dt.year,
        "rest_bucket": df["home_rest_days"].apply(_bucket_rest),
        "home_team": df["home_team"],
    }

    for name, series in segments.items():
        seg_df = df.copy()
        seg_df[name] = series
        logger.info(f"\nSegment performance by {name}:")
        for level, g in seg_df.groupby(name):
            n = len(g)
            if n < 30:
                continue
            acc = (g["home_win"] == (g[proba_col] > 0.5).astype(int)).mean()
            ll = log_loss(g["home_win"], g[proba_col], labels=[0, 1])
            logger.info(f"  {level}: n={n}, acc={acc:.3f}, logloss={ll:.3f}")


def _elo_expected_prob(
    home_elo: float,
    away_elo: float,
    home_advantage: float = 100.0,
) -> float:
    """Elo expected score for home team with home-court advantage."""
    home_adj = home_elo + home_advantage
    return float(1.0 / (1.0 + 10 ** ((away_elo - home_adj) / 400.0)))


def _logit(p: np.ndarray) -> np.ndarray:
    eps = 1e-15
    p = np.clip(p, eps, 1 - eps)
    return np.log(p / (1 - p))


def _inv_logit(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def _baseline_metrics(y_true: np.ndarray, proba: np.ndarray) -> dict:
    y_true = np.asarray(y_true).astype(int)
    proba = np.asarray(proba).astype(float)
    pred = (proba > 0.5).astype(int)
    return {
        "log_loss": float(log_loss(y_true, proba, labels=[0, 1])),
        "brier_score": float(brier_score_loss(y_true, proba)),
        "accuracy": float(accuracy_score(y_true, pred)),
        "n_samples": int(len(y_true)),
    }


def _fit_market_blend_weight(
    y_val: np.ndarray,
    model_proba_val: np.ndarray,
    market_proba_val: np.ndarray,
    w_grid: np.ndarray | None = None,
) -> float:
    """Fit a logit-space blend weight between model and market on validation."""
    if w_grid is None:
        w_grid = np.linspace(0.0, 1.0, 21)

    y_val = np.asarray(y_val).astype(int)
    model_proba_val = np.asarray(model_proba_val).astype(float)
    market_proba_val = np.asarray(market_proba_val).astype(float)

    best_w = 1.0
    best_loss = float("inf")
    m_logit = _logit(model_proba_val)
    k_logit = _logit(market_proba_val)
    for w in w_grid:
        blended = _inv_logit(w * m_logit + (1.0 - w) * k_logit)
        loss = float(log_loss(y_val, blended, labels=[0, 1]))
        if loss < best_loss:
            best_loss = loss
            best_w = float(w)
    return best_w


def stratified_split(features_df, train_ratio=0.6, val_ratio=0.2, random_state=42):
    """Stratified split into train/val/test ignoring time for POC.

    Returns (train_df, val_df, test_df)
    """
    y = features_df["home_win"].astype(int)
    idx = features_df.index
    train_idx, temp_idx = train_test_split(
        idx, test_size=(1 - train_ratio), stratify=y, random_state=random_state
    )
    temp_y = y.loc[temp_idx]
    val_size = val_ratio / (1 - train_ratio)
    val_idx, test_idx = train_test_split(
        temp_idx, test_size=(1 - val_size), stratify=temp_y, random_state=random_state
    )
    return (
        features_df.loc[train_idx],
        features_df.loc[val_idx],
        features_df.loc[test_idx],
    )


def prune_correlated_features(
    df: pd.DataFrame, cols: list[str], threshold: float = 0.95
) -> list[str]:
    """Greedily drop features with absolute pairwise correlation above threshold."""
    if not cols:
        return cols
    corr = df[cols].corr().abs()
    to_drop = set()
    for i, col in enumerate(cols):
        if col in to_drop:
            continue
        for other in cols[i + 1 :]:
            if other in to_drop:
                continue
            if corr.loc[col, other] >= threshold:
                to_drop.add(other)
    kept = [c for c in cols if c not in to_drop]
    logger.info(
        f"Correlation pruning: dropped {len(to_drop)} of {len(cols)} features (threshold {threshold})"
    )
    return kept


def l1_feature_select(
    X_train_scaled: np.ndarray,
    y_train: pd.Series,
    X_val_scaled: np.ndarray,
    y_val: pd.Series,
    feature_names: list[str],
    c_grid: list[float] | None = None,
) -> list[str]:
    """Select features using L1-penalized logistic regression."""
    if c_grid is None:
        c_grid = [0.01, 0.1, 1.0]

    best_loss = float("inf")
    best_mask = None
    best_c = None
    for c in c_grid:
        model = LogisticRegression(
            penalty="l1", solver="saga", C=c, max_iter=1000, random_state=42
        )
        model.fit(X_train_scaled, y_train)
        val_pred = model.predict_proba(X_val_scaled)[:, 1]
        if pd.Series(y_val).nunique() < 2:
            continue
        loss = log_loss(y_val, val_pred, labels=[0, 1])
        if loss < best_loss:
            best_loss = loss
            best_mask = (np.abs(model.coef_) > 1e-4).flatten()
            best_c = c

    if best_mask is None or best_mask.sum() == 0:
        logger.warning("L1 selection kept 0 features; falling back to all candidates.")
        return feature_names

    selected = [f for f, keep in zip(feature_names, best_mask) if keep]
    logger.info(
        f"L1 feature selection: kept {len(selected)}/{len(feature_names)} features (best C={best_c}, val_loss={best_loss:.4f})"
    )
    return selected


def save_model(
    model,
    scaler,
    train_metrics,
    val_metrics,
    test_metrics,
    train_pred_proba: np.ndarray,
    val_pred_proba: np.ndarray,
    test_pred_proba: np.ndarray,
    output_dir,
    selected_features: list[str] | None = None,
    pruned_features: list[str] | None = None,
    best_c: float | None = None,
    train_df: pd.DataFrame | None = None,
    val_df: pd.DataFrame | None = None,
    test_df: pd.DataFrame | None = None,
):
    """Save model and metadata with MLflow experiment tracking."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics_dir = output_dir / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)

    # Start MLflow run
    mlflow.set_experiment("nba_win_prediction")

    with mlflow.start_run(run_name=f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        # Log hyperparameters
        mlflow.log_param("model_type", "LogisticRegression")
        mlflow.log_param("C", float(model.C) if best_c is None else best_c)
        mlflow.log_param("max_iter", model.max_iter)
        mlflow.log_param("solver", model.solver)
        mlflow.log_param(
            "n_features_selected", len(selected_features) if selected_features else 0
        )
        mlflow.log_param(
            "n_features_pruned", len(pruned_features) if pruned_features else 0
        )

        # Log dataset sizes
        if train_df is not None:
            mlflow.log_param("train_size", len(train_df))
        if val_df is not None:
            mlflow.log_param("val_size", len(val_df))
        if test_df is not None:
            mlflow.log_param("test_size", len(test_df))

        # Log training data window
        mlflow.log_param("training_data", "2019-2024 (excluding 2020-2021 COVID)")
        mlflow.log_param(
            "data_min_date",
            train_df["date"].min().isoformat() if train_df is not None else "N/A",
        )
        mlflow.log_param(
            "data_max_date",
            train_df["date"].max().isoformat() if train_df is not None else "N/A",
        )

        # Log metrics for all splits
        for split_name, metrics in [
            ("train", train_metrics),
            ("val", val_metrics),
            ("test", test_metrics),
        ]:
            mlflow.log_metric(f"{split_name}_log_loss", metrics["log_loss"])
            mlflow.log_metric(f"{split_name}_brier_score", metrics["brier_score"])
            mlflow.log_metric(f"{split_name}_accuracy", metrics["accuracy"])

        # Calibration artifacts (required by future-work.md)
        calibration_summary: dict[str, dict] = {}
        for split_name, split_df, split_proba in [
            ("train", train_df, train_pred_proba),
            ("val", val_df, val_pred_proba),
            ("test", test_df, test_pred_proba),
        ]:
            if split_df is None:
                continue
            y_split = split_df["home_win"].astype(int).to_numpy()
            proba = np.asarray(split_proba).astype(float)

            ece, mce = ll_calibration_errors(
                proba.tolist(), y_split.tolist(), n_buckets=10
            )
            mlflow.log_metric(f"{split_name}_ece", ece)
            mlflow.log_metric(f"{split_name}_mce", mce)

            table = ll_calibration_table(proba.tolist(), y_split.tolist(), n_buckets=10)
            table_path = metrics_dir / f"reliability_{split_name}.json"
            with open(table_path, "w") as f:
                json.dump(table, f, indent=2)
            mlflow.log_artifact(str(table_path), "metrics")

            calibration_summary[split_name] = {
                "ece": float(ece),
                "mce": float(mce),
                "reliability_buckets_artifact": str(table_path.name),
            }

        # Benchmarks (required by future-work.md)
        baseline_summary: dict[str, dict] = {}
        if train_df is not None and test_df is not None:
            train_home_rate = float(train_df["home_win"].mean())
            y_test = test_df["home_win"].astype(int).to_numpy()
            p_const = np.full_like(y_test, fill_value=train_home_rate, dtype=float)
            baseline_summary["constant_home_rate"] = {
                "train_home_rate": train_home_rate,
                "test": _baseline_metrics(y_test, p_const),
            }
            mlflow.log_metric(
                "baseline_constant_test_log_loss",
                baseline_summary["constant_home_rate"]["test"]["log_loss"],
            )

            p_elo = test_df.apply(
                lambda r: _elo_expected_prob(
                    float(r["home_elo"]), float(r["away_elo"])
                ),
                axis=1,
            ).to_numpy(dtype=float)
            baseline_summary["elo_only"] = {"test": _baseline_metrics(y_test, p_elo)}
            mlflow.log_metric(
                "baseline_elo_test_log_loss",
                baseline_summary["elo_only"]["test"]["log_loss"],
            )

            # Market baselines only on rows with market data
            if "implied_home_prob" in test_df.columns:
                market_mask_test = test_df["implied_home_prob"].astype(float) > 0
                if market_mask_test.any():
                    y_mkt = y_test[market_mask_test.to_numpy()]
                    p_mkt = (
                        test_df.loc[market_mask_test, "implied_home_prob"]
                        .astype(float)
                        .to_numpy()
                    )
                    baseline_summary["market_only"] = {
                        "test": _baseline_metrics(y_mkt, p_mkt)
                    }
                    mlflow.log_metric(
                        "baseline_market_test_log_loss",
                        baseline_summary["market_only"]["test"]["log_loss"],
                    )

                    # Market-as-prior blend (fit on validation subset with market)
                    if val_df is not None and "implied_home_prob" in val_df.columns:
                        market_mask_val = val_df["implied_home_prob"].astype(float) > 0
                        if market_mask_val.any():
                            y_val = (
                                val_df.loc[market_mask_val, "home_win"]
                                .astype(int)
                                .to_numpy()
                            )
                            p_model_val = np.asarray(val_pred_proba, dtype=float)[
                                market_mask_val.to_numpy()
                            ]
                            p_market_val = (
                                val_df.loc[market_mask_val, "implied_home_prob"]
                                .astype(float)
                                .to_numpy()
                            )
                            best_w = _fit_market_blend_weight(
                                y_val=y_val,
                                model_proba_val=p_model_val,
                                market_proba_val=p_market_val,
                            )

                            p_model_test = np.asarray(test_pred_proba, dtype=float)[
                                market_mask_test.to_numpy()
                            ]
                            p_blend = _inv_logit(
                                best_w * _logit(p_model_test)
                                + (1.0 - best_w) * _logit(p_mkt)
                            )
                            baseline_summary["market_prior_blend"] = {
                                "best_weight_model_logit": float(best_w),
                                "test": _baseline_metrics(y_mkt, p_blend),
                            }
                            mlflow.log_metric(
                                "baseline_market_blend_test_log_loss",
                                baseline_summary["market_prior_blend"]["test"][
                                    "log_loss"
                                ],
                            )

        # Segment summary artifact (test split)
        segment_summary: dict[str, dict] = {}
        if test_df is not None:
            seg_df = test_df.copy()
            seg_df["pred_proba"] = np.asarray(test_pred_proba, dtype=float)
            seg_df["rest_bucket"] = seg_df["home_rest_days"].apply(_bucket_rest)
            if "implied_home_prob" in seg_df.columns:
                seg_df["market_favorite"] = np.where(
                    seg_df["implied_home_prob"].astype(float) > 0,
                    np.where(
                        seg_df["implied_home_prob"].astype(float) >= 0.5, "fav", "dog"
                    ),
                    "unknown",
                )
            seg_df["month"] = seg_df["date"].dt.month

            def _season_phase(month: int) -> str:
                # Simple NBA-season-ish buckets (calendar-based; good enough for POC)
                if month in (10, 11):
                    return "early"
                if month in (12, 1):
                    return "mid"
                if month in (2, 3, 4):
                    return "late"
                return "other"

            seg_df["season_phase"] = seg_df["month"].astype(int).apply(_season_phase)

            def summarize(group: pd.DataFrame) -> dict:
                y = group["home_win"].astype(int).to_numpy()
                p = group["pred_proba"].astype(float).to_numpy()
                return _baseline_metrics(y, p)

            for key in ["season", "rest_bucket", "market_favorite", "season_phase"]:
                if key not in seg_df.columns:
                    continue
                out: dict[str, dict] = {}
                for level, g in seg_df.groupby(key):
                    if len(g) < 30:
                        continue
                    out[str(level)] = summarize(g)
                if out:
                    segment_summary[key] = out

            segment_path = metrics_dir / "segment_summary_test.json"
            with open(segment_path, "w") as f:
                json.dump(segment_summary, f, indent=2)
            mlflow.log_artifact(str(segment_path), "metrics")

        evaluation_summary = {
            "splits": {
                "train": train_metrics,
                "val": val_metrics,
                "test": test_metrics,
            },
            "calibration": calibration_summary,
            "baselines": baseline_summary,
            "segments_test": segment_summary,
        }
        evaluation_path = metrics_dir / "evaluation_summary.json"
        with open(evaluation_path, "w") as f:
            json.dump(evaluation_summary, f, indent=2)
        mlflow.log_artifact(str(evaluation_path), "metrics")

        # Save model locally first
        model_path = output_dir / "nba_model_v1.0.0.pkl"
        with open(model_path, "wb") as f:
            pickle.dump({"model": model, "scaler": scaler}, f)
        logger.info(
            f"Saved model to {model_path} ({model_path.stat().st_size / 1024:.1f} KB)"
        )

        # Log model to MLflow
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name="nba_win_predictor",
        )

        # Log model artifact
        mlflow.log_artifact(str(model_path), "model_artifacts")

        metadata = {
            "version": "v1.0.0_20260110",
            "created_at": datetime.now().isoformat(),
            "model_type": "LogisticRegression",
            "training_data": "2019-2024 (excluding 2020-2021 COVID bubble)",
            "features_all": [
                "home_elo",
                "away_elo",
                "elo_diff",
                "is_home",
                "home_win_rate_L10",
                "away_win_rate_L10",
                "home_pt_diff_L10",
                "away_pt_diff_L10",
                "home_rest_days",
                "away_rest_days",
                "home_b2b",
                "away_b2b",
                "h2h_home_wins",
                "home_streak",
                "away_streak",
                "home_lineup_cont_overlap",
                "away_lineup_cont_overlap",
                "home_key_out_count",
                "away_key_out_count",
                "home_injured_count",
                "away_injured_count",
                "home_injured_minutes_lost",
                "away_injured_minutes_lost",
                "home_weighted_PER",
                "away_weighted_PER",
                "home_weighted_BPM",
                "away_weighted_BPM",
                "home_weighted_WS48",
                "away_weighted_WS48",
                "per_diff",
                "bpm_diff",
                "ws48_diff",
                "home_net_rating",
                "away_net_rating",
                "net_rating_diff",
                "home_pace",
                "away_pace",
                "pace_diff",
                "home_off_3pa_rate",
                "away_off_3pa_rate",
                "off_3pa_rate_diff",
                "home_def_opp_3pa_rate",
                "away_def_opp_3pa_rate",
                "def_opp_3pa_rate_diff",
                "implied_home_prob",
                "spread_home",
                "total",
            ],
            "features_pruned_corr": pruned_features or [],
            "features_selected": selected_features or [],
            "train_metrics": train_metrics,
            "val_metrics": val_metrics,
            "test_metrics": test_metrics,
            "calibration": calibration_summary,
            "baselines": baseline_summary,
            "hyperparameters": {
                "C": float(model.C),
                "max_iter": model.max_iter,
                "solver": model.solver,
            },
        }
        metadata_path = output_dir / "nba_model_v1.0.0_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")

        # Log metadata as artifact
        mlflow.log_artifact(str(metadata_path), "model_artifacts")

        # Log feature lists as artifacts
        if selected_features:
            features_path = output_dir / "selected_features.json"
            with open(features_path, "w") as f:
                json.dump(selected_features, f, indent=2)
            mlflow.log_artifact(str(features_path), "features")

        logger.info(f"✓ MLflow run logged: {mlflow.active_run().info.run_id}")
        logger.info(
            f"✓ View at: http://localhost:5000/#/experiments/{mlflow.active_run().info.experiment_id}\n"
        )


def print_results(
    train_metrics, val_metrics, test_metrics, features_df, train_df, val_df, test_df
):
    """Log comprehensive training results."""
    logger.info("=" * 80)
    logger.info("MODEL TRAINING COMPLETE")
    logger.info("=" * 80)

    logger.info(f"\nDataset Summary:")
    logger.info(f"  Total games: {len(features_df):,}")
    logger.info(
        f"  Train: {len(train_df):,} | Val: {len(val_df):,} | Test: {len(test_df):,}"
    )

    logger.info(f"\nPerformance Metrics:")
    logger.info(
        f"  {'Split':<12} | {'Log Loss':>10} | {'Brier':>8} | {'Accuracy':>10} | {'Samples':>8}"
    )
    logger.info(f"  {'-'*60}")

    for split, metrics in [
        ("Train", train_metrics),
        ("Validation", val_metrics),
        ("Test", test_metrics),
    ]:
        logger.info(
            f"  {split:<12} | {metrics['log_loss']:>10.4f} | "
            f"{metrics['brier_score']:>8.4f} | {metrics['accuracy']:>10.2%} | {metrics['n_samples']:>8}"
        )

    logger.info(f"\n✅ Model ready for deployment!")


def main():
    logger.info("=" * 80)
    logger.info("NBA Win Probability Model Training Script")
    logger.info("Data: 2019-2024 (excludes 2020-2021 COVID bubble)")
    logger.info("=" * 80 + "\n")

    parser = argparse.ArgumentParser(
        description="Train NBA win probability model offline with robust logging"
    )
    parser.add_argument(
        "--cache-only", action="store_true", help="Load from cached data"
    )
    parser.add_argument(
        "--data-cache", default=".linelogic/games_cache.csv", help="Cache file path"
    )
    parser.add_argument(
        "--output-dir", default=".linelogic", help="Model output directory"
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("BALLDONTLIE_API_KEY"),
        help="BALLDONTLIE API key",
    )
    parser.add_argument(
        "--start-season", type=int, default=2019, help="Start season (default: 2019)"
    )
    parser.add_argument(
        "--end-season", type=int, default=2024, help="End season (default: 2024)"
    )
    parser.add_argument(
        "--train-cutoff",
        type=str,
        default="2024-01-01",
        help="Train/val split cutoff date (YYYY-MM-DD). Default: 2024-01-01",
    )
    parser.add_argument(
        "--val-cutoff",
        type=str,
        default="2024-07-01",
        help="Val/test split cutoff date (YYYY-MM-DD). Default: 2024-07-01",
    )
    parser.add_argument(
        "--stratified",
        action="store_true",
        help="Use stratified (class-balanced) split for POC (ignores time).",
    )
    parser.add_argument(
        "--no-synthetic",
        action="store_true",
        help="Disallow synthetic data fallback; fail if data insufficient or single-class.",
    )

    args = parser.parse_args()

    # Load or fetch data
    cache_path = Path(args.data_cache)
    if args.cache_only and cache_path.exists():
        games_df = load_cached_data(cache_path)
    elif not args.cache_only:
        games_df = fetch_historical_games(
            args.start_season,
            args.end_season,
            args.api_key,
            allow_synthetic=not args.no_synthetic,
        )
        cache_data(games_df, cache_path)
    else:
        logger.error(f"Cache not found at {cache_path} and --cache-only specified")
        sys.exit(1)

    # Ensure dataset has both classes; if not, supplement with synthetic games for POC
    if games_df["home_win"].nunique() < 2:
        logger.warning("Dataset contains a single class for home_win.")
        if args.no_synthetic:
            logger.error(
                "Synthetic fallback disabled (--no-synthetic). Please fetch full data from BALLDONTLIE."
            )
            sys.exit(1)
        if generate_synthetic_games:
            logger.info("Supplementing with synthetic games for POC...")
            synthetic_games = pd.DataFrame(generate_synthetic_games())
            synthetic_games["date"] = pd.to_datetime(synthetic_games["date"])
            games_df = pd.concat([games_df, synthetic_games], ignore_index=True)
            games_df = games_df.sort_values("date").reset_index(drop=True)
            logger.info(f"✓ After supplementation: {len(games_df):,} total games.")
        else:
            logger.error(
                "Synthetic generator unavailable; cannot proceed with single-class dataset."
            )
            sys.exit(1)

    # Engineer features
    logger.info("Engineering features...")
    # Load optional player-derived advanced metrics (minutes-weighted PER/BPM/WS48)
    logger.info("Loading team advanced metrics (optional)...")
    adv_df = load_team_advanced_metrics()
    if adv_df.empty:
        logger.info(
            "No advanced metrics available; proceeding without player-derived features."
        )
    else:
        logger.info(f"✓ Advanced metrics loaded: {len(adv_df)} team-season rows\n")

    logger.info("Loading player stats cache (optional)...")
    player_stats_df = load_player_stats_cache()
    if player_stats_df.empty:
        logger.info("No player stats cache available; lineup features will be neutral.")
    else:
        logger.info(f"✓ Player stats loaded: {len(player_stats_df)} rows\n")

    logger.info("Loading team season averages (advanced) via GOAT tier (optional)...")
    seasons = [s for s in range(args.start_season, args.end_season + 1) if s != 2020]
    team_avgs_df = load_team_season_avgs(
        api_key=args.api_key, seasons=seasons, season_type="regular"
    )
    if team_avgs_df.empty:
        logger.info("No team season averages available; net/pace/3PA features neutral.")
    else:
        logger.info(
            f"✓ Team season averages loaded: {len(team_avgs_df)} rows across {team_avgs_df['season'].nunique()} seasons\n"
        )

    logger.info("Loading odds cache (optional)...")
    odds_df = load_odds_cache()
    if odds_df.empty:
        logger.info("No odds cache available; odds features neutral.")
    else:
        logger.info(f"✓ Odds cache loaded: {len(odds_df)} rows\n")

    logger.info("Loading player injuries cache (optional)...")
    injuries_df = load_player_injuries_cache()
    if injuries_df.empty:
        logger.info("No injuries cache available; injury features neutral.")
    else:
        logger.info(f"✓ Injuries cache loaded: {len(injuries_df)} rows\n")

    engineer = FeatureEngineer(
        advanced_metrics_df=adv_df,
        player_stats_df=player_stats_df,
        team_avgs_df=team_avgs_df,
        injuries_df=injuries_df,
        odds_df=odds_df,
    )
    features_df = engineer.engineer_features(games_df)
    logger.info(f"✓ {len(features_df):,} feature sets engineered\n")

    # Split data
    if args.stratified:
        logger.info("Using stratified class-balanced split for POC...")
        train_df, val_df, test_df = stratified_split(features_df)
        logger.info("Data Split (Stratified):")
        logger.info(f"  Train: {len(train_df):,} samples")
        logger.info(f"  Validation: {len(val_df):,} samples")
        logger.info(f"  Test: {len(test_df):,} samples\n")
    else:
        # Time-based split cutoffs
        train_cutoff = pd.Timestamp(args.train_cutoff)
        val_cutoff = pd.Timestamp(args.val_cutoff)

        # Attempt initial split
        train_df, val_df, test_df = split_data(features_df, train_cutoff, val_cutoff)

        # If invalid split due to limited cached data, auto-adjust for POC
        def has_two_classes(y):
            return len(pd.Series(y).unique()) >= 2

        attempts = 0
        while attempts < 6 and (
            (len(val_df) == 0 or len(test_df) == 0)
            or not has_two_classes(train_df["home_win"])
        ):
            logger.warning(
                "Adjusting split for POC due to insufficient validation/test or single-class train."
            )
            train_cutoff = train_cutoff + pd.Timedelta(days=30)
            val_cutoff = train_cutoff + pd.Timedelta(days=180)
            attempts += 1
            logger.info(
                f"→ New cutoffs: train<{train_cutoff.date()}, val<{val_cutoff.date()} (attempt {attempts})"
            )
            train_df, val_df, test_df = split_data(
                features_df, train_cutoff, val_cutoff
            )

    # Prepare features
    feature_cols = [
        "home_elo",
        "away_elo",
        "elo_diff",
        "is_home",
        "home_win_rate_L10",
        "away_win_rate_L10",
        "home_pt_diff_L10",
        "away_pt_diff_L10",
        "home_rest_days",
        "away_rest_days",
        "home_b2b",
        "away_b2b",
        "h2h_home_wins",
        "home_streak",
        "away_streak",
        # Lineup & availability features (if stats available; zeros otherwise)
        "home_lineup_cont_overlap",
        "away_lineup_cont_overlap",
        "home_key_out_count",
        "away_key_out_count",
        # Injuries (if available; zeros otherwise)
        "home_injured_count",
        "away_injured_count",
        "home_injured_minutes_lost",
        "away_injured_minutes_lost",
        # Player-derived team advanced metrics (if available; zeros otherwise)
        "home_weighted_PER",
        "away_weighted_PER",
        "home_weighted_BPM",
        "away_weighted_BPM",
        "home_weighted_WS48",
        "away_weighted_WS48",
        "per_diff",
        "bpm_diff",
        "ws48_diff",
        # Team season averages (GOAT tier, if available; zeros otherwise)
        "home_net_rating",
        "away_net_rating",
        "net_rating_diff",
        "home_pace",
        "away_pace",
        "pace_diff",
        "home_off_3pa_rate",
        "away_off_3pa_rate",
        "off_3pa_rate_diff",
        "home_def_opp_3pa_rate",
        "away_def_opp_3pa_rate",
        "def_opp_3pa_rate_diff",
        # Odds / market priors (if available; zeros otherwise)
        "implied_home_prob",
        "spread_home",
        "total",
    ]

    # Correlation pruning to reduce multicollinearity
    pruned_feature_cols = prune_correlated_features(train_df, feature_cols, 0.95)

    X_train = train_df[pruned_feature_cols].fillna(0)
    y_train = train_df["home_win"]
    X_val = val_df[pruned_feature_cols].fillna(0)
    y_val = val_df["home_win"]
    X_test = test_df[pruned_feature_cols].fillna(0)
    y_test = test_df["home_win"]

    # Scale features
    logger.info("Scaling features (for L1 selection)...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    # L1 feature selection (sparse) on pruned set
    selected_feature_cols = l1_feature_select(
        X_train_scaled, y_train, X_val_scaled, y_val, pruned_feature_cols
    )

    # Restrict to selected features
    X_train_sel = train_df[selected_feature_cols].fillna(0)
    X_val_sel = val_df[selected_feature_cols].fillna(0)
    X_test_sel = test_df[selected_feature_cols].fillna(0)

    logger.info("Scaling features (selected set)...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_sel)
    X_val_scaled = scaler.transform(X_val_sel)
    X_test_scaled = scaler.transform(X_test_sel)

    # Hyperparameter search on selected features
    logger.info("Hyperparameter search...\n")
    best_c = None
    best_val_loss = float("inf")
    best_model = None

    for c in [0.001, 0.01, 0.1, 1.0, 10.0]:
        model = LogisticRegression(C=c, max_iter=1000, random_state=42, solver="lbfgs")
        model.fit(X_train_scaled, y_train)

        y_val_pred_proba = model.predict_proba(X_val_scaled)[:, 1]
        if pd.Series(y_val).nunique() < 2:
            val_loss = float("inf")
        else:
            val_loss = log_loss(y_val, y_val_pred_proba, labels=[0, 1])

        status = "🏆 BEST" if val_loss < best_val_loss else "      "
        logger.info(f"  {status} | C={c:6.3f} → Val Loss: {val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_c = c
            best_model = model

    logger.info(
        f"\n✓ Best hyperparameter: C={best_c} (val_loss: {best_val_loss:.4f})\n"
    )

    # Evaluate on all splits
    logger.info("Evaluating model...")
    train_metrics, train_proba = evaluate_split(
        best_model, X_train_sel, y_train, scaler, "Train"
    )
    val_metrics, val_proba = evaluate_split(
        best_model, X_val_sel, y_val, scaler, "Validation"
    )
    test_metrics, test_proba = evaluate_split(
        best_model, X_test_sel, y_test, scaler, "Test"
    )
    logger.info("")

    # Save artifacts
    logger.info("Saving model artifacts...")
    save_model(
        best_model,
        scaler,
        train_metrics,
        val_metrics,
        test_metrics,
        train_proba,
        val_proba,
        test_proba,
        args.output_dir,
        selected_features=selected_feature_cols,
        pruned_features=pruned_feature_cols,
        best_c=best_c,
        train_df=train_df,
        val_df=val_df,
        test_df=test_df,
    )

    # Print results
    print_results(
        train_metrics, val_metrics, test_metrics, features_df, train_df, val_df, test_df
    )

    # Segmentation analysis on test split
    test_df_with_pred = test_df.copy()
    test_df_with_pred["pred_proba"] = test_proba
    log_segment_metrics(test_df_with_pred)


if __name__ == "__main__":
    main()
