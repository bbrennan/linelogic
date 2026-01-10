"""
Model evaluation metrics.

Implements:
- Brier score (calibration metric)
- Log loss (cross-entropy)
- Calibration analysis (bucketing)
- Closing Line Value (CLV)
"""

import math
from dataclasses import dataclass


def brier_score(predictions: list[float], outcomes: list[int]) -> float:
    """
    Calculate Brier score for probabilistic predictions.

    Brier score = (1/N) × Σ (predicted_prob - actual_outcome)²

    Lower is better. Perfect score = 0.0, worst = 1.0.

    Args:
        predictions: List of predicted probabilities (0.0 to 1.0)
        outcomes: List of actual outcomes (0 = loss, 1 = win)

    Returns:
        Brier score (0.0 to 1.0)

    Raises:
        ValueError: If lengths don't match or invalid values

    Examples:
        >>> predictions = [0.6, 0.6, 0.4]
        >>> outcomes = [1, 0, 0]
        >>> brier_score(predictions, outcomes)
        0.227

    Interpretation:
        <0.15: Excellent
        0.15-0.20: Good
        0.20-0.25: Acceptable
        >0.25: Poor
    """
    if len(predictions) != len(outcomes):
        raise ValueError(
            f"Length mismatch: {len(predictions)} predictions, {len(outcomes)} outcomes"
        )

    if not predictions:
        raise ValueError("Empty predictions list")

    for prob in predictions:
        if prob < 0 or prob > 1:
            raise ValueError(f"Prediction must be between 0 and 1, got {prob}")

    for outcome in outcomes:
        if outcome not in (0, 1):
            raise ValueError(f"Outcome must be 0 or 1, got {outcome}")

    squared_errors = [
        (pred - outcome) ** 2 for pred, outcome in zip(predictions, outcomes)
    ]
    return sum(squared_errors) / len(squared_errors)


def log_loss(predictions: list[float], outcomes: list[int]) -> float:
    """
    Calculate log loss (cross-entropy) for probabilistic predictions.

    Log loss = -(1/N) × Σ [y × log(p) + (1-y) × log(1-p)]

    Lower is better. Perfect score = 0.0.

    Args:
        predictions: List of predicted probabilities (0.0 to 1.0)
        outcomes: List of actual outcomes (0 = loss, 1 = win)

    Returns:
        Log loss (0.0 to ∞)

    Raises:
        ValueError: If lengths don't match or invalid values

    Examples:
        >>> predictions = [0.6, 0.6, 0.4]
        >>> outcomes = [1, 0, 0]
        >>> log_loss(predictions, outcomes)
        0.576

    Interpretation:
        <0.50: Excellent
        0.50-0.60: Good
        0.60-0.70: Acceptable
        >0.70: Poor

    Note:
        Log loss penalizes confident wrong predictions more than Brier score.
    """
    if len(predictions) != len(outcomes):
        raise ValueError(
            f"Length mismatch: {len(predictions)} predictions, {len(outcomes)} outcomes"
        )

    if not predictions:
        raise ValueError("Empty predictions list")

    for prob in predictions:
        if prob <= 0 or prob >= 1:
            raise ValueError(
                f"Prediction must be between 0 and 1 (exclusive), got {prob}"
            )

    for outcome in outcomes:
        if outcome not in (0, 1):
            raise ValueError(f"Outcome must be 0 or 1, got {outcome}")

    # Clip probabilities to avoid log(0)
    eps = 1e-15
    clipped_preds = [max(eps, min(1 - eps, p)) for p in predictions]

    log_losses = [
        -(y * math.log(p) + (1 - y) * math.log(1 - p))
        for p, y in zip(clipped_preds, outcomes)
    ]

    return sum(log_losses) / len(log_losses)


@dataclass
class CalibrationBucket:
    """
    Calibration bucket for a range of predicted probabilities.

    Attributes:
        min_prob: Minimum probability for this bucket (inclusive)
        max_prob: Maximum probability for this bucket (exclusive)
        avg_predicted: Average predicted probability in this bucket
        wins: Number of wins in this bucket
        total: Total number of predictions in this bucket
        empirical_win_rate: Actual win rate (wins / total)
    """

    min_prob: float
    max_prob: float
    avg_predicted: float
    wins: int
    total: int
    empirical_win_rate: float


def calibration_buckets(
    predictions: list[float],
    outcomes: list[int],
    n_buckets: int = 10,
) -> list[CalibrationBucket]:
    """
    Analyze calibration by grouping predictions into buckets.

    Perfect calibration: avg_predicted ≈ empirical_win_rate for all buckets.

    Args:
        predictions: List of predicted probabilities (0.0 to 1.0)
        outcomes: List of actual outcomes (0 = loss, 1 = win)
        n_buckets: Number of buckets (default: 10 for deciles)

    Returns:
        List of CalibrationBucket objects

    Examples:
        >>> predictions = [0.52, 0.53, 0.57, 0.58, 0.62, 0.63, 0.67, 0.68]
        >>> outcomes = [1, 0, 1, 1, 1, 0, 1, 1]
        >>> buckets = calibration_buckets(predictions, outcomes, n_buckets=3)
        >>> len(buckets)
        3
        >>> buckets[1].avg_predicted  # Middle bucket
        0.575

    Usage:
        Use this to create calibration plots (predicted vs. empirical).
        Points on the y=x line indicate good calibration.
    """
    if len(predictions) != len(outcomes):
        raise ValueError(
            f"Length mismatch: {len(predictions)} predictions, {len(outcomes)} outcomes"
        )

    if not predictions:
        return []

    # Define bucket edges
    bucket_edges = [i / n_buckets for i in range(n_buckets + 1)]

    buckets = []

    for i in range(n_buckets):
        min_prob = bucket_edges[i]
        max_prob = bucket_edges[i + 1]

        # Collect predictions in this bucket
        in_bucket = [
            (pred, outcome)
            for pred, outcome in zip(predictions, outcomes)
            if min_prob <= pred < max_prob or (i == n_buckets - 1 and pred == max_prob)
        ]

        if not in_bucket:
            continue

        preds_in_bucket = [p for p, _ in in_bucket]
        outcomes_in_bucket = [o for _, o in in_bucket]

        avg_predicted = sum(preds_in_bucket) / len(preds_in_bucket)
        wins = sum(outcomes_in_bucket)
        total = len(outcomes_in_bucket)
        empirical_win_rate = wins / total

        buckets.append(
            CalibrationBucket(
                min_prob=min_prob,
                max_prob=max_prob,
                avg_predicted=avg_predicted,
                wins=wins,
                total=total,
                empirical_win_rate=empirical_win_rate,
            )
        )

    return buckets


def clv(open_line_prob: float, close_line_prob: float, bet_side: str) -> float:
    """
    Calculate Closing Line Value (CLV).

    CLV measures whether you beat the closing line (sharp money).

    Args:
        open_line_prob: Implied probability when bet was placed
        close_line_prob: Implied probability at game start (closing line)
        bet_side: "over" or "under" (or "favorite" / "underdog")

    Returns:
        CLV as decimal (positive = beat closing line, negative = did not)

    Examples:
        >>> clv(0.476, 0.524, "over")  # We bet Over at +110, closed at -110
        0.048
        >>> clv(0.524, 0.476, "under")  # We bet Under at -110, closed at +110
        0.048
        >>> clv(0.50, 0.50, "over")  # No line movement
        0.0

    Interpretation:
        CLV > 0: You got better odds than closing line (good)
        CLV = 0: No line movement
        CLV < 0: Closing line was better than your odds (bad)

    Note:
        Positive CLV is a strong indicator of long-term profitability,
        even if short-term results are negative (variance).
    """
    if bet_side.lower() in ("over", "favorite", "yes"):
        # For "over" or "favorite", lower prob = better odds
        # If closing prob increased, we beat the close
        return close_line_prob - open_line_prob
    elif bet_side.lower() in ("under", "underdog", "no"):
        # For "under" or "underdog", higher prob = better odds
        # If closing prob decreased, we beat the close
        return open_line_prob - close_line_prob
    else:
        raise ValueError(
            f"Invalid bet_side: {bet_side}. Must be 'over', 'under', 'favorite', or 'underdog'."
        )
