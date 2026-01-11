"""
Weekly summary and trend analysis for LineLogic.

Generates comprehensive reports with:
- Results summary (W-L, ROI, P&L trends)
- Edge analysis and distribution
- Team/selection patterns
- Bankroll trajectory
- Statistical insights (sample size, confidence intervals)
- Hypotheses for future feature engineering
- Correlation analysis (time of day, teams, odds patterns)
"""

from datetime import datetime, timedelta
import statistics
from typing import Optional

from linelogic.config.settings import settings
from linelogic.storage.sqlite import get_connection


class WeeklySummaryGenerator:
    """Generate comprehensive weekly analysis reports."""

    def __init__(self):
        """Initialize weekly summary generator."""
        self.conn = get_connection(settings.database_path)

    def get_week_stats(self, end_date_str: str) -> dict:
        """
        Get weekly statistics for trend analysis.

        Args:
            end_date_str: End date in YYYY-MM-DD format (typically today)

        Returns:
            Dictionary with comprehensive weekly metrics
        """
        # Calculate week boundaries (Monday-Sunday)
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        start_date = end_date - timedelta(days=6)  # 7 days including end_date
        start_date_str = start_date.strftime("%Y-%m-%d")

        cursor = self.conn.cursor()

        # Get recommendations for the week
        cursor.execute(
            """
            SELECT 
                r.id,
                r.selection,
                r.model_prob,
                r.edge,
                r.stake_suggested,
                r.created_at,
                res.outcome_win_bool,
                res.profit_loss,
                res.settled_at,
                os.odds_american
            FROM recommendations r
            LEFT JOIN results res ON r.id = res.recommendation_id
            LEFT JOIN odds_snapshots os ON r.id = os.recommendation_id
            WHERE DATE(r.created_at) >= ? AND DATE(r.created_at) <= ?
            ORDER BY r.created_at
        """,
            (start_date_str, end_date_str),
        )

        picks = cursor.fetchall()

        # Get settled results
        cursor.execute(
            """
            SELECT outcome_win_bool, profit_loss FROM results
            WHERE DATE(settled_at) >= ? AND DATE(settled_at) <= ?
        """,
            (start_date_str, end_date_str),
        )

        settled_results = cursor.fetchall()

        # Calculate statistics
        stats = {
            "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date_str}",
            "total_picks": len(picks),
            "settled_picks": len(settled_results),
            "picks_by_day": self._picks_by_day(picks),
            "edge_stats": self._calculate_edge_stats(picks),
            "results_stats": self._calculate_results_stats(settled_results),
            "team_analysis": self._analyze_teams(picks),
            "odds_patterns": self._analyze_odds_patterns(picks),
            "bankroll_trajectory": self._get_bankroll_trajectory(
                start_date_str, end_date_str
            ),
            "confidence_metrics": self._calculate_confidence_metrics(settled_results),
        }

        return stats

    def _picks_by_day(self, picks: list) -> dict:
        """Analyze picks by day of week."""
        by_day = {}
        for pick in picks:
            if pick[5]:  # created_at
                day = datetime.fromisoformat(pick[5]).strftime("%A")
                by_day[day] = by_day.get(day, 0) + 1
        return by_day

    def _calculate_edge_stats(self, picks: list) -> dict:
        """Calculate edge distribution statistics."""
        edges = [pick[3] * 100 for pick in picks if pick[3] is not None]

        if not edges:
            return {
                "avg_edge": 0,
                "min_edge": 0,
                "max_edge": 0,
                "median_edge": 0,
                "stdev": 0,
                "distribution": {},
            }

        # Create edge distribution buckets
        distribution = {}
        for edge in edges:
            bucket = f"{int(edge // 1.0)}%-{int(edge // 1.0) + 1}%"
            distribution[bucket] = distribution.get(bucket, 0) + 1

        return {
            "avg_edge": statistics.mean(edges),
            "min_edge": min(edges),
            "max_edge": max(edges),
            "median_edge": statistics.median(edges),
            "stdev": statistics.stdev(edges) if len(edges) > 1 else 0,
            "distribution": distribution,
        }

    def _calculate_results_stats(self, results: list) -> dict:
        """Calculate win/loss statistics."""
        if not results:
            return {
                "total_settled": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "roi": 0,
                "avg_pnl_per_pick": 0,
                "longest_streak": "",
                "streak_type": "",
            }

        wins = sum(1 for r in results if r[0])  # outcome_win_bool
        losses = len(results) - wins
        total_pnl = sum(r[1] for r in results if r[1] is not None)

        # Calculate streak
        streak, streak_type = self._calculate_streak(results)

        return {
            "total_settled": len(results),
            "wins": wins,
            "losses": losses,
            "win_rate": wins / len(results) if results else 0,
            "total_pnl": total_pnl,
            "roi": (
                (total_pnl / (len(results) * 5)) * 100 if results else 0
            ),  # Assuming $5 avg stake
            "avg_pnl_per_pick": total_pnl / len(results) if results else 0,
            "longest_streak": streak,
            "streak_type": streak_type,
        }

    def _calculate_streak(self, results: list) -> tuple:
        """Calculate longest win or loss streak."""
        if not results:
            return "", ""

        current_streak = 1
        longest_streak = 1
        streak_type = "W" if results[0][0] else "L"
        longest_type = streak_type

        for i in range(1, len(results)):
            if (results[i][0] and results[i - 1][0]) or (
                not results[i][0] and not results[i - 1][0]
            ):
                current_streak += 1
            else:
                if current_streak > longest_streak:
                    longest_streak = current_streak
                    longest_type = "W" if results[i - 1][0] else "L"
                current_streak = 1

        return f"{longest_streak} {longest_type}", longest_type

    def _analyze_teams(self, picks: list) -> dict:
        """Analyze performance by team."""
        team_stats = {}

        for pick in picks:
            team = pick[1]  # selection
            edge = pick[3]  # edge
            outcome = pick[6]  # outcome_win_bool
            pnl = pick[7]  # profit_loss

            if team not in team_stats:
                team_stats[team] = {"picks": 0, "edges": [], "wins": 0, "pnl": 0}

            team_stats[team]["picks"] += 1
            if edge:
                team_stats[team]["edges"].append(edge * 100)
            if outcome:
                team_stats[team]["wins"] += 1
            if pnl:
                team_stats[team]["pnl"] += pnl

        # Calculate win rates and avg edges
        for team in team_stats:
            stats = team_stats[team]
            stats["win_rate"] = stats["wins"] / stats["picks"] if stats["picks"] else 0
            stats["avg_edge"] = statistics.mean(stats["edges"]) if stats["edges"] else 0

        # Sort by pick count
        return dict(
            sorted(team_stats.items(), key=lambda x: x[1]["picks"], reverse=True)
        )

    def _analyze_odds_patterns(self, picks: list) -> dict:
        """Analyze odds patterns and correlations."""
        odds_data = []

        for pick in picks:
            if pick[9]:  # american_odds
                odds = pick[9]
                edge = pick[3] * 100 if pick[3] else 0
                odds_data.append({"odds": odds, "edge": edge})

        if not odds_data:
            return {"pattern": "Insufficient data"}

        # Correlate odds with edge
        negative_odds = [d for d in odds_data if d["odds"] < 0]
        positive_odds = [d for d in odds_data if d["odds"] > 0]

        return {
            "favorite_analysis": {
                "count": len(negative_odds),
                "avg_edge": (
                    statistics.mean([d["edge"] for d in negative_odds])
                    if negative_odds
                    else 0
                ),
            },
            "underdog_analysis": {
                "count": len(positive_odds),
                "avg_edge": (
                    statistics.mean([d["edge"] for d in positive_odds])
                    if positive_odds
                    else 0
                ),
            },
            "pattern": (
                "Higher edges on underdogs"
                if (
                    positive_odds
                    and negative_odds
                    and statistics.mean([d["edge"] for d in positive_odds])
                    > statistics.mean([d["edge"] for d in negative_odds])
                )
                else (
                    "Higher edges on favorites"
                    if (negative_odds and positive_odds)
                    else "No pattern"
                )
            ),
        }

    def _get_bankroll_trajectory(self, start_date_str: str, end_date_str: str) -> list:
        """Get daily bankroll values for the week."""
        cursor = self.conn.cursor()

        bankroll_start = 1000.0

        cursor.execute(
            """
            SELECT DATE(settled_at) as date, SUM(profit_loss) as daily_pnl
            FROM results
            WHERE DATE(settled_at) >= ? AND DATE(settled_at) <= ?
            GROUP BY DATE(settled_at)
            ORDER BY date
        """,
            (start_date_str, end_date_str),
        )

        daily_results = cursor.fetchall()

        trajectory = []
        cumulative_pnl = 0

        start = datetime.strptime(start_date_str, "%Y-%m-%d")
        end = datetime.strptime(end_date_str, "%Y-%m-%d")
        current = start

        while current <= end:
            date_str = current.strftime("%Y-%m-%d")

            # Find daily PnL
            daily_pnl = 0
            for result in daily_results:
                if result[0] == date_str:
                    daily_pnl = result[1] or 0
                    break

            cumulative_pnl += daily_pnl
            bankroll = bankroll_start + cumulative_pnl

            trajectory.append(
                {"date": date_str, "daily_pnl": daily_pnl, "bankroll": bankroll}
            )

            current += timedelta(days=1)

        return trajectory

    def _calculate_confidence_metrics(self, results: list) -> dict:
        """Calculate statistical confidence metrics."""
        if len(results) < 2:
            return {
                "sample_size": len(results),
                "confidence_level": 0,
                "margin_of_error": 0,
                "status": "Insufficient data (need 30+ picks)",
            }

        wins = sum(1 for r in results if r[0])
        n = len(results)
        p = wins / n

        # Standard error for proportion
        se = (p * (1 - p) / n) ** 0.5

        # 95% confidence interval
        margin_of_error = 1.96 * se

        return {
            "sample_size": n,
            "win_rate": p,
            "confidence_level": 0.95,
            "margin_of_error": margin_of_error * 100,
            "ci_low": (p - margin_of_error) * 100,
            "ci_high": (p + margin_of_error) * 100,
            "status": f"{n} picks - {'Statistical significance reached' if n >= 30 else 'Continue accumulating'}",
        }

    def generate_html_weekly_report(self, end_date_str: str) -> str:
        """
        Generate comprehensive HTML weekly report.

        Args:
            end_date_str: End date in YYYY-MM-DD format

        Returns:
            HTML email content
        """
        stats = self.get_week_stats(end_date_str)

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; color: #333; }}
                .container {{ max-width: 1000px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #27ae60; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; margin-bottom: 15px; }}
                .metric {{ 
                    display: inline-block; 
                    background-color: #ecf0f1; 
                    padding: 15px 20px; 
                    margin: 10px 15px 10px 0;
                    border-radius: 5px;
                    min-width: 150px;
                }}
                .metric-label {{ color: #7f8c8d; font-size: 12px; font-weight: bold; text-transform: uppercase; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                .positive {{ color: #27ae60; }}
                .negative {{ color: #e74c3c; }}
                .neutral {{ color: #f39c12; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background-color: #34495e; color: white; padding: 12px; text-align: left; }}
                td {{ border-bottom: 1px solid #ecf0f1; padding: 10px; }}
                tr:hover {{ background-color: #f9f9f9; }}
                .insight-box {{
                    background-color: #e8f4f8;
                    border-left: 4px solid #3498db;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 4px;
                }}
                .chart {{ margin: 20px 0; }}
                .bar {{ 
                    display: inline-block; 
                    background-color: #3498db; 
                    height: 20px; 
                    margin: 5px 0;
                }}
            }}
            </style>
        </head>
        <body>
        <div class="container">
            <h1>📊 LineLogic Weekly Analysis Report</h1>
            <p>Period: <strong>{stats['period']}</strong></p>
            
            {self._metrics_html(stats)}
            
            {self._results_section_html(stats)}
            
            {self._edge_analysis_html(stats)}
            
            {self._team_analysis_html(stats)}
            
            {self._odds_patterns_html(stats)}
            
            {self._bankroll_trajectory_html(stats)}
            
            {self._insights_and_hypotheses_html(stats)}
            
            {self._confidence_metrics_html(stats)}
            
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ecf0f1; color: #7f8c8d; font-size: 12px;">
                <p>📈 LineLogic POC - Week {datetime.strptime(stats['period'].split(' to ')[0], '%Y-%m-%d').isocalendar()[1]}</p>
                <p>This report is automatically generated weekly for feature engineering insights.</p>
            </div>
        </div>
        </body>
        </html>
        """

        return html

    def _metrics_html(self, stats: dict) -> str:
        """Generate metrics cards HTML."""
        results = stats["results_stats"]
        edge = stats["edge_stats"]

        return f"""
        <h2>Key Metrics</h2>
        <div>
            <div class="metric">
                <div class="metric-label">Total Picks</div>
                <div class="metric-value">{stats['total_picks']}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Settled</div>
                <div class="metric-value">{results['total_settled']}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Win Rate</div>
                <div class="metric-value {'positive' if results['win_rate'] > 0.5 else 'negative'}">{results['win_rate']:.1%}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg Edge</div>
                <div class="metric-value neutral">{edge['avg_edge']:.2f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total P&L</div>
                <div class="metric-value {'positive' if results['total_pnl'] >= 0 else 'negative'}">${results['total_pnl']:+.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">ROI</div>
                <div class="metric-value {'positive' if results['roi'] >= 0 else 'negative'}">{results['roi']:+.1f}%</div>
            </div>
        </div>
        """

    def _results_section_html(self, stats: dict) -> str:
        """Generate results summary HTML."""
        results = stats["results_stats"]
        return f"""
        <h2>Results Summary</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Wins / Losses</td>
                <td><span class="positive">{results['wins']} W</span> / <span class="negative">{results['losses']} L</span></td>
            </tr>
            <tr>
                <td>Win Rate</td>
                <td>{results['win_rate']:.1%}</td>
            </tr>
            <tr>
                <td>Total P&L</td>
                <td class="{'positive' if results['total_pnl'] >= 0 else 'negative'}">${results['total_pnl']:+.2f}</td>
            </tr>
            <tr>
                <td>Avg P&L per Pick</td>
                <td class="{'positive' if results['avg_pnl_per_pick'] >= 0 else 'negative'}">${results['avg_pnl_per_pick']:+.2f}</td>
            </tr>
            <tr>
                <td>ROI</td>
                <td class="{'positive' if results['roi'] >= 0 else 'negative'}">{results['roi']:+.1f}%</td>
            </tr>
            <tr>
                <td>Longest Streak</td>
                <td>{results['longest_streak']}</td>
            </tr>
        </table>
        """

    def _edge_analysis_html(self, stats: dict) -> str:
        """Generate edge distribution analysis HTML."""
        edge = stats["edge_stats"]

        dist_rows = "".join(
            [
                f"<tr><td>{bucket}</td><td>{count}</td></tr>"
                for bucket, count in sorted(edge["distribution"].items())
            ]
        )

        return f"""
        <h2>Edge Distribution</h2>
        <p><strong>Average Edge:</strong> {edge['avg_edge']:.2f}% | <strong>Range:</strong> {edge['min_edge']:.2f}% to {edge['max_edge']:.2f}% | <strong>Median:</strong> {edge['median_edge']:.2f}%</p>
        <table>
            <tr>
                <th>Edge Range</th>
                <th>Count</th>
            </tr>
            {dist_rows}
        </table>
        <div class="insight-box">
            <strong>💡 Insight:</strong> Your edge distribution shows concentration. Consider if certain edge levels perform better (0-1% vs 2-3% vs 3%+).
        </div>
        """

    def _team_analysis_html(self, stats: dict) -> str:
        """Generate team analysis HTML."""
        teams = stats["team_analysis"]

        team_rows = "".join(
            [
                f"""
            <tr>
                <td>{team}</td>
                <td>{data['picks']}</td>
                <td>{data['wins']}-{data['picks']-data['wins']}</td>
                <td class="{'positive' if data['win_rate'] >= 0.5 else 'negative'}">{data['win_rate']:.1%}</td>
                <td>${data['pnl']:+.2f}</td>
                <td>{data['avg_edge']:.2f}%</td>
            </tr>
            """
                for team, data in list(teams.items())[:10]  # Top 10 teams
            ]
        )

        return f"""
        <h2>Team Analysis (Top 10)</h2>
        <table>
            <tr>
                <th>Team</th>
                <th>Picks</th>
                <th>W-L</th>
                <th>Win %</th>
                <th>P&L</th>
                <th>Avg Edge</th>
            </tr>
            {team_rows}
        </table>
        <div class="insight-box">
            <strong>🎯 Finding:</strong> Do certain teams show better/worse win rates? This could indicate systematic biases in model or market opportunities.
        </div>
        """

    def _odds_patterns_html(self, stats: dict) -> str:
        """Generate odds patterns analysis HTML."""
        patterns = stats["odds_patterns"]

        if "pattern" in patterns and patterns["pattern"] == "Insufficient data":
            return "<h2>Odds Patterns</h2><p>Not enough odds data collected yet.</p>"

        fav = patterns.get("favorite_analysis", {})
        ud = patterns.get("underdog_analysis", {})

        return f"""
        <h2>Odds Patterns Analysis</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Count</th>
                <th>Avg Edge</th>
            </tr>
            <tr>
                <td>Favorites (odds < -110)</td>
                <td>{fav.get('count', 0)}</td>
                <td>{fav.get('avg_edge', 0):.2f}%</td>
            </tr>
            <tr>
                <td>Underdogs (odds > +110)</td>
                <td>{ud.get('count', 0)}</td>
                <td>{ud.get('avg_edge', 0):.2f}%</td>
            </tr>
        </table>
        <div class="insight-box">
            <strong>📍 Pattern Detected:</strong> {patterns.get('pattern', 'No clear pattern')}
            <br>This could guide feature engineering focus (e.g., "favorites outperform" → add home-team strength feature).
        </div>
        """

    def _bankroll_trajectory_html(self, stats: dict) -> str:
        """Generate bankroll trajectory HTML."""
        trajectory = stats["bankroll_trajectory"]

        traj_rows = "".join(
            [
                f"""
            <tr>
                <td>{t['date']}</td>
                <td class="{'positive' if t['daily_pnl'] >= 0 else 'negative'}">${t['daily_pnl']:+.2f}</td>
                <td>${t['bankroll']:.2f}</td>
            </tr>
            """
                for t in trajectory
            ]
        )

        final_bankroll = trajectory[-1]["bankroll"] if trajectory else 1000
        total_pnl = final_bankroll - 1000

        return f"""
        <h2>Bankroll Trajectory</h2>
        <table>
            <tr>
                <th>Date</th>
                <th>Daily P&L</th>
                <th>Bankroll</th>
            </tr>
            {traj_rows}
        </table>
        <p><strong>Starting:</strong> $1,000.00 | <strong>Current:</strong> ${final_bankroll:.2f} | <strong>Total P&L:</strong> <span class="{'positive' if total_pnl >= 0 else 'negative'}">${total_pnl:+.2f}</span></p>
        """

    def _insights_and_hypotheses_html(self, stats: dict) -> str:
        """Generate insights and hypotheses for future work."""
        results = stats["results_stats"]
        teams = stats["team_analysis"]
        edge = stats["edge_stats"]

        hypotheses = []

        # Hypothesis 1: Edge levels
        if edge["max_edge"] > 3:
            hypotheses.append(
                "✓ Model generates edges up to {:.1f}%. Next: Validate if higher edges correlate with better W%".format(
                    edge["max_edge"]
                )
            )

        # Hypothesis 2: Team variance
        if len(teams) > 3:
            team_wr = [t[1]["win_rate"] for t in list(teams.items())[:5]]
            if max(team_wr) - min(team_wr) > 0.3:
                hypotheses.append(
                    "✓ Team win rates vary significantly ({}% to {}%). Feature: Team strength/form could improve predictions".format(
                        int(min(team_wr) * 100), int(max(team_wr) * 100)
                    )
                )

        # Hypothesis 3: Sample size
        if results["total_settled"] >= 10:
            hypotheses.append(
                f"✓ {results['total_settled']} settled picks accumulated. Can start analyzing correlations and refining model."
            )
        else:
            hypotheses.append(
                f"⏳ {results['total_settled']} settled picks. Target: 30+ for statistical significance. Continue for {30-results['total_settled']} more days."
            )

        # Hypothesis 4: Win rate
        if results["win_rate"] > 0.5:
            hypotheses.append(
                f"✓ Win rate {results['win_rate']:.1%} > 50% baseline. Validate edge calculation methodology."
            )
        elif results["total_settled"] > 20:
            hypotheses.append(
                f"⚠️ Win rate {results['win_rate']:.1%} < 50% with {results['total_settled']} picks. Debug: Edge calculation or model issues?"
            )

        hypothesis_html = "".join([f"<li>{h}</li>" for h in hypotheses])

        return f"""
        <h2>Insights & Hypotheses for Feature Engineering</h2>
        <ul style="line-height: 1.8;">
            {hypothesis_html}
        </ul>
        
        <div class="insight-box">
            <strong>🚀 Next Steps:</strong>
            <ul>
                <li>Collect data for 30+ more days (target: 100-150 total picks)</li>
                <li>Analyze team strength, home/away splits, opponent strength</li>
                <li>Feature engineering: Form, injuries, line movement, steam</li>
                <li>Train v2 GLM/XGBoost model with engineered features</li>
                <li>Validate improvements in holdout test set</li>
            </ul>
        </div>
        """

    def _confidence_metrics_html(self, stats: dict) -> str:
        """Generate statistical confidence metrics HTML."""
        conf = stats["confidence_metrics"]

        return f"""
        <h2>Statistical Significance</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Sample Size (picks settled)</td>
                <td>{conf['sample_size']}</td>
            </tr>
            <tr>
                <td>Win Rate</td>
                <td>{conf.get('win_rate', 0):.1%}</td>
            </tr>
            <tr>
                <td>95% Confidence Interval</td>
                <td>{conf.get('ci_low', 0):.1f}% to {conf.get('ci_high', 0):.1f}%</td>
            </tr>
            <tr>
                <td>Margin of Error</td>
                <td>±{conf.get('margin_of_error', 0):.1f}%</td>
            </tr>
            <tr>
                <td>Status</td>
                <td><strong>{conf['status']}</strong></td>
            </tr>
        </table>
        <div class="insight-box">
            <strong>📊 What This Means:</strong> With {conf['sample_size']} picks, we can be 95% confident in the win rate range. More picks = tighter confidence interval = better validation.
        </div>
        """

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
