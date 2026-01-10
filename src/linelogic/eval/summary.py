"""
Email summary generation for LineLogic daily jobs.

Generates HTML email with:
- Current bankroll/pot
- Today's recommendations
- Yesterday's settlement results
"""

import datetime
from pathlib import Path

from linelogic.config.settings import settings
from linelogic.storage.sqlite import get_connection


class SummaryGenerator:
    """Generate email summaries for daily jobs."""

    def __init__(self, bankroll_start: float = 1000.0):
        """
        Initialize summary generator.

        Args:
            bankroll_start: Starting bankroll for POC ($1,000)
        """
        self.bankroll_start = bankroll_start
        self.conn = get_connection(settings.database_path)

    def get_current_bankroll(self) -> float:
        """
        Calculate current bankroll from P&L.

        Returns:
            Current bankroll (starting - losses + wins)
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(profit_loss), 0) FROM results")
        total_pnl = cursor.fetchone()[0]
        return self.bankroll_start + total_pnl

    def get_todays_picks(self, date_str: str) -> list:
        """
        Get today's recommendations.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            List of picks with details
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 
                selection, model_prob, market_prob, edge, 
                stake_suggested, odds_american
            FROM recommendations r
            LEFT JOIN odds_snapshots o ON r.id = o.recommendation_id
            WHERE DATE(r.created_at) = ?
            ORDER BY edge DESC
            """,
            (date_str,),
        )
        return cursor.fetchall()

    def get_yesterdays_results(self, date_str: str) -> tuple:
        """
        Get yesterday's settled picks and P&L.

        Args:
            date_str: Yesterday's date in YYYY-MM-DD format

        Returns:
            Tuple of (picks_list, total_pnl, roi_pct)
        """
        cursor = self.conn.cursor()

        # Get settled picks from yesterday
        cursor.execute(
            """
            SELECT 
                r.selection, r.stake_suggested, 
                res.outcome_win_bool, res.profit_loss
            FROM recommendations r
            LEFT JOIN results res ON r.id = res.recommendation_id
            WHERE DATE(r.created_at) = ?
            ORDER BY res.id DESC
            """,
            (date_str,),
        )
        picks = cursor.fetchall()

        # Get P&L summary for yesterday
        cursor.execute(
            """
            SELECT 
                COUNT(*) as count,
                SUM(res.profit_loss) as total_pnl
            FROM recommendations r
            LEFT JOIN results res ON r.id = res.recommendation_id
            WHERE DATE(r.created_at) = ? AND res.id IS NOT NULL
            """,
            (date_str,),
        )
        result = cursor.fetchone()
        count, total_pnl = result if result else (0, 0)
        total_pnl = total_pnl or 0.0

        # Calculate ROI on yesterday's stakes
        yesterday_stakes = 0.0
        if picks:
            yesterday_stakes = sum(p[1] for p in picks)

        roi_pct = (total_pnl / yesterday_stakes * 100) if yesterday_stakes > 0 else 0.0

        return picks, total_pnl, roi_pct

    def generate_html_summary(self, date_str: str, yesterday_str: str) -> tuple:
        """
        Generate HTML email summaries.

        Args:
            date_str: Today's date (YYYY-MM-DD)
            yesterday_str: Yesterday's date (YYYY-MM-DD)

        Returns:
            Tuple of (html_recommend_email, html_settle_email)
        """
        current_bankroll = self.get_current_bankroll()
        todays_picks = self.get_todays_picks(date_str)
        yesterdays_picks, yesterday_pnl, yesterday_roi = self.get_yesterdays_results(
            yesterday_str
        )

        # Recommend email
        recommend_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5;">
        <div style="max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px;">
            <h1 style="color: #2c3e50;">📊 LineLogic Daily Recommendations - {date_str}</h1>
            
            <div style="background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h2 style="color: #27ae60; margin-top: 0;">Current Bankroll</h2>
                <p style="font-size: 24px; color: #27ae60; margin: 10px 0;">
                    ${current_bankroll:,.2f}
                </p>
                <p style="color: #7f8c8d; margin: 0;">
                    Starting: ${self.bankroll_start:,.2f} | 
                    P&L: ${current_bankroll - self.bankroll_start:+,.2f}
                </p>
            </div>
            
            <h3 style="color: #2c3e50;">Today's Picks ({len(todays_picks)} recommendations)</h3>
            
            {self._picks_table_html(todays_picks)}
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ecf0f1; color: #7f8c8d; font-size: 12px;">
                <p>This is an automated summary from LineLogic POC.</p>
                <p>Paper mode: No real money wagered.</p>
            </div>
        </div>
        </body>
        </html>
        """

        # Settle email
        settle_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5;">
        <div style="max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px;">
            <h1 style="color: #2c3e50;">📈 LineLogic Settlement Report - {yesterday_str}</h1>
            
            <div style="background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h2 style="color: #27ae60; margin-top: 0;">Yesterday's Results</h2>
                <p style="font-size: 18px; color: {'#27ae60' if yesterday_pnl >= 0 else '#e74c3c'}; margin: 10px 0;">
                    P&L: ${yesterday_pnl:+,.2f}
                </p>
                <p style="font-size: 16px; color: {'#27ae60' if yesterday_roi >= 0 else '#e74c3c'}; margin: 10px 0;">
                    ROI: {yesterday_roi:+.2f}%
                </p>
                <p style="color: #7f8c8d; margin: 0;">
                    Current Bankroll: ${current_bankroll:,.2f}
                </p>
            </div>
            
            <h3 style="color: #2c3e50;">Settled Picks ({len(yesterdays_picks)} picks)</h3>
            
            {self._results_table_html(yesterdays_picks)}
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ecf0f1; color: #7f8c8d; font-size: 12px;">
                <p>This is an automated summary from LineLogic POC.</p>
                <p>Paper mode: No real money wagered.</p>
            </div>
        </div>
        </body>
        </html>
        """

        return recommend_html, settle_html

    def _picks_table_html(self, picks: list) -> str:
        """Generate HTML table for picks."""
        if not picks:
            return "<p style='color: #7f8c8d;'>No picks for this date.</p>"

        rows = ""
        for selection, model_prob, market_prob, edge, stake, odds in picks:
            edge_pct = edge * 100 if edge else 0
            rows += f"""
            <tr style="border-bottom: 1px solid #ecf0f1;">
                <td style="padding: 10px;">{selection}</td>
                <td style="padding: 10px; text-align: center;">{model_prob*100:.1f}%</td>
                <td style="padding: 10px; text-align: center;">{market_prob*100:.1f}%</td>
                <td style="padding: 10px; text-align: center; color: {'#27ae60' if edge_pct >= 2 else '#e67e22'};"><strong>{edge_pct:.2f}%</strong></td>
                <td style="padding: 10px; text-align: right;">${stake:.2f}</td>
            </tr>
            """

        return f"""
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <thead style="background-color: #34495e; color: white;">
                <tr>
                    <th style="padding: 10px; text-align: left;">Pick</th>
                    <th style="padding: 10px;">Model %</th>
                    <th style="padding: 10px;">Market %</th>
                    <th style="padding: 10px;">Edge</th>
                    <th style="padding: 10px;">Stake</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """

    def _results_table_html(self, picks: list) -> str:
        """Generate HTML table for results."""
        if not picks:
            return "<p style='color: #7f8c8d;'>No settled picks yet.</p>"

        rows = ""
        for selection, stake, outcome, pnl in picks:
            outcome_text = (
                "✅ WIN"
                if outcome
                else "❌ LOSS" if outcome is not None else "⏳ PENDING"
            )
            pnl_color = (
                "#27ae60"
                if pnl and pnl > 0
                else "#e74c3c" if pnl and pnl < 0 else "#7f8c8d"
            )
            pnl_text = f"${pnl:+,.2f}" if pnl is not None else "N/A"
            rows += f"""
            <tr style="border-bottom: 1px solid #ecf0f1;">
                <td style="padding: 10px;">{selection}</td>
                <td style="padding: 10px; text-align: right;">${stake:.2f}</td>
                <td style="padding: 10px; text-align: center;">{outcome_text}</td>
                <td style="padding: 10px; text-align: right; color: {pnl_color};"><strong>{pnl_text}</strong></td>
            </tr>
            """

        return f"""
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <thead style="background-color: #34495e; color: white;">
                <tr>
                    <th style="padding: 10px; text-align: left;">Pick</th>
                    <th style="padding: 10px;">Stake</th>
                    <th style="padding: 10px;">Result</th>
                    <th style="padding: 10px;">P&L</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
