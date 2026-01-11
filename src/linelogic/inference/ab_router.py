"""A/B testing router for model serving."""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

ModelStage = Literal["staging", "production"]


@dataclass
class OutcomeLog:
    """Log entry for prediction outcome."""

    user_id: str
    model_stage: ModelStage
    prediction: float
    actual: bool | None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ABTestRouter:
    """
    Route prediction requests between staging and production models.

    Uses consistent hashing to ensure same user always gets same model variant.
    Logs outcomes for metric comparison (staging vs production).

    Example:
        router = ABTestRouter(staging_percentage=10.0)
        stage = router.route(user_id="game_123_home")  # "staging" or "production"
        model = mlflow.sklearn.load_model(f"models:/nba_win_predictor/{stage}")
        prediction = model.predict_proba(features)[0][1]
        router.log_outcome(user_id="game_123_home", prediction=prediction, actual=True)
    """

    def __init__(
        self,
        staging_percentage: float = 10.0,
        log_dir: Path | str = ".linelogic/ab_logs",
    ):
        """
        Initialize A/B test router.

        Args:
            staging_percentage: Percentage of traffic routed to staging (0-100)
            log_dir: Directory to store outcome logs for analysis
        """
        if not 0 <= staging_percentage <= 100:
            raise ValueError(
                f"staging_percentage must be 0-100, got {staging_percentage}"
            )

        self.staging_percentage = staging_percentage
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.outcomes: list[OutcomeLog] = []

        logger.info(
            f"ABTestRouter initialized: {staging_percentage}% staging, "
            f"{100 - staging_percentage}% production"
        )

    def route(self, user_id: str) -> ModelStage:
        """
        Route request to staging or production based on consistent hash.

        Uses MD5 hash of user_id to deterministically assign variant.
        Same user_id always gets same model stage (session affinity).

        Args:
            user_id: Unique identifier (e.g., "game_123_home", "user_abc")

        Returns:
            "staging" or "production"
        """
        # Hash user_id to [0, 100) range
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        bucket = hash_value % 100

        # Route to staging if bucket < staging_percentage
        stage: ModelStage = (
            "staging" if bucket < self.staging_percentage else "production"
        )
        logger.debug(f"Routed {user_id} to {stage} (bucket={bucket})")
        return stage

    def log_outcome(
        self,
        user_id: str,
        prediction: float,
        actual: bool | None = None,
    ) -> None:
        """
        Log prediction outcome for later analysis.

        Args:
            user_id: Same user_id passed to route()
            prediction: Model predicted probability [0, 1]
            actual: Actual outcome (True=home won, False=home lost, None=pending)
        """
        stage = self.route(user_id)  # Reconstruct stage from user_id
        outcome = OutcomeLog(
            user_id=user_id,
            model_stage=stage,
            prediction=prediction,
            actual=actual,
        )
        self.outcomes.append(outcome)

        # Write to daily log file
        log_file = self.log_dir / f"outcomes_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(outcome.__dict__) + "\n")

        logger.debug(f"Logged outcome: {user_id} → {stage} (pred={prediction:.3f})")

    def get_metrics(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[ModelStage, dict[str, float]]:
        """
        Compute metrics for staging vs production.

        Args:
            start_date: ISO date (YYYY-MM-DD), defaults to all time
            end_date: ISO date (YYYY-MM-DD), defaults to today

        Returns:
            {
                "staging": {"log_loss": 0.62, "accuracy": 0.58, "count": 100},
                "production": {"log_loss": 0.65, "accuracy": 0.55, "count": 900},
            }
        """
        from sklearn.metrics import accuracy_score, log_loss

        # Load outcomes from log files
        outcomes = self._load_outcomes(start_date, end_date)

        # Filter completed outcomes (actual is not None)
        completed = [o for o in outcomes if o.actual is not None]

        # Group by model stage
        staging_outcomes = [o for o in completed if o.model_stage == "staging"]
        production_outcomes = [o for o in completed if o.model_stage == "production"]

        metrics = {}
        for stage_name, stage_outcomes in [
            ("staging", staging_outcomes),
            ("production", production_outcomes),
        ]:
            if not stage_outcomes:
                metrics[stage_name] = {"log_loss": None, "accuracy": None, "count": 0}
                continue

            y_true = [int(o.actual) for o in stage_outcomes]  # Convert bool to int
            y_pred = [o.prediction for o in stage_outcomes]

            # sklearn log_loss requires labels parameter if only one class present
            try:
                loss = log_loss(y_true, y_pred, labels=[0, 1])
            except ValueError:
                loss = None

            metrics[stage_name] = {
                "log_loss": loss,
                "accuracy": accuracy_score(y_true, [int(p > 0.5) for p in y_pred]),
                "count": len(stage_outcomes),
            }

        return metrics

    def compare_variants(self) -> str:
        """
        Generate human-readable comparison report.

        Returns:
            Formatted string with staging vs production metrics
        """
        metrics = self.get_metrics()
        staging = metrics.get("staging", {})
        production = metrics.get("production", {})

        report = "A/B Test Results\n"
        report += "=" * 60 + "\n"
        report += f"Staging Percentage: {self.staging_percentage}%\n\n"

        report += "STAGING:\n"
        report += f"  Predictions: {staging.get('count', 0):,}\n"
        if staging.get("log_loss"):
            report += f"  Log Loss: {staging['log_loss']:.4f}\n"
            report += f"  Accuracy: {staging['accuracy']:.4f}\n"
        else:
            report += "  (No completed predictions)\n"

        report += "\nPRODUCTION:\n"
        report += f"  Predictions: {production.get('count', 0):,}\n"
        if production.get("log_loss"):
            report += f"  Log Loss: {production['log_loss']:.4f}\n"
            report += f"  Accuracy: {production['accuracy']:.4f}\n"
        else:
            report += "  (No completed predictions)\n"

        # Winner determination
        if staging.get("log_loss") and production.get("log_loss"):
            report += "\nWINNER: "
            if staging["log_loss"] < production["log_loss"]:
                improvement = (
                    (production["log_loss"] - staging["log_loss"])
                    / production["log_loss"]
                    * 100
                )
                report += f"STAGING (log_loss improved by {improvement:.1f}%)\n"
                report += "  → Recommend promoting staging to production\n"
            else:
                degradation = (
                    (staging["log_loss"] - production["log_loss"])
                    / production["log_loss"]
                    * 100
                )
                report += f"PRODUCTION (staging degraded by {degradation:.1f}%)\n"
                report += "  → Keep production, discard staging model\n"

        return report

    def _load_outcomes(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[OutcomeLog]:
        """Load outcomes from log files in date range."""
        outcomes = []
        for log_file in sorted(self.log_dir.glob("outcomes_*.jsonl")):
            # Parse date from filename
            date_str = log_file.stem.split("_")[1]  # outcomes_20260110.jsonl → 20260110
            file_date = datetime.strptime(date_str, "%Y%m%d").date()

            # Filter by date range
            if start_date and file_date < datetime.fromisoformat(start_date).date():
                continue
            if end_date and file_date > datetime.fromisoformat(end_date).date():
                continue

            # Load outcomes from file
            with open(log_file) as f:
                for line in f:
                    data = json.loads(line)
                    outcomes.append(
                        OutcomeLog(
                            user_id=data["user_id"],
                            model_stage=data["model_stage"],
                            prediction=data["prediction"],
                            actual=data.get("actual"),
                            timestamp=data["timestamp"],
                        )
                    )

        return outcomes
