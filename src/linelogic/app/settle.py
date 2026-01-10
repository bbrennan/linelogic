"""
Settlement engine: ingest results and compute ROI/Kelly growth metrics.
"""

import datetime

from linelogic.config.settings import settings
from linelogic.storage.sqlite import get_connection, init_db


class SettlementEngine:
    """
    Settle recommendations: ingest results and update ROI/Kelly metrics.
    """

    def __init__(self):
        """Initialize engine with DB."""
        init_db(settings.database_path)

    def stub_settle_results(self, date_str: str) -> dict:
        """
        Stub: mark all recommendations as settled with random outcomes.

        In v2+, integrate with sportsbook APIs or manual result feeds.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Dict with counts: settled, total_pnl, roi
        """
        conn = get_connection(settings.database_path)
        cursor = conn.cursor()

        # Get unsettled recommendations for the date
        cursor.execute(
            """
            SELECT id, stake_suggested FROM recommendations
            WHERE created_at LIKE ?
            AND id NOT IN (SELECT recommendation_id FROM results)
            """,
            (f"{date_str}%",),
        )

        rows = cursor.fetchall()

        total_pnl = 0.0
        settled_count = 0

        for rec_id, stake in rows:
            # Stub: 50/50 outcome, stub return
            outcome_win = 0  # lose for now
            profit = 0.0 if outcome_win == 0 else stake

            cursor.execute(
                """
                INSERT INTO results
                (recommendation_id, settled_at, outcome_win_bool, profit_loss)
                VALUES (?, ?, ?, ?)
                """,
                (
                    rec_id,
                    datetime.datetime.now().isoformat(),
                    outcome_win,
                    profit,
                ),
            )
            settled_count += 1
            total_pnl += profit

        conn.commit()

        total_staked = sum(stake for _, stake in rows)
        roi = (total_pnl / total_staked * 100) if total_staked > 0 else 0.0

        conn.close()

        return {
            "date": date_str,
            "settled_count": settled_count,
            "total_pnl": total_pnl,
            "roi_percent": roi,
        }
