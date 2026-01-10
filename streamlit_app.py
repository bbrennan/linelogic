"""
LineLogic Dashboard
Real-time tracking of picks, results, and bankroll trajectory.
"""

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px


# Page config
st.set_page_config(
    page_title="LineLogic Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Styling
st.markdown(
    """
<style>
    .metric-card {
        background-color: #0e1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 20px;
        margin: 10px 0;
    }
    .positive { color: #3fb950; }
    .negative { color: #f85149; }
    .neutral { color: #8b949e; }
</style>
""",
    unsafe_allow_html=True,
)


def get_db_path():
    """Locate database file."""
    paths = [
        Path(".linelogic/linelogic.db"),
        Path("linelogic/.linelogic/linelogic.db"),
        Path(".") / ".linelogic" / "linelogic.db",
    ]
    for p in paths:
        if p.exists():
            return str(p)
    return ".linelogic/linelogic.db"


@st.cache_resource
def get_connection():
    """Get SQLite connection."""
    db_path = get_db_path()
    return sqlite3.connect(db_path)


def get_metrics():
    """Fetch key metrics from database."""
    conn = get_connection()

    # Total recommendations
    total_picks = pd.read_sql_query(
        "SELECT COUNT(*) as count FROM recommendations", conn
    )["count"].iloc[0]

    # Settled picks
    settled = pd.read_sql_query("SELECT COUNT(*) as count FROM results", conn)[
        "count"
    ].iloc[0]

    # Win rate (last 30 days)
    win_rate = pd.read_sql_query(
        """
        SELECT 
            ROUND(SUM(outcome_win_bool) * 100.0 / COUNT(*), 2) as win_pct
        FROM results
        WHERE settled_at > datetime('now', '-30 days')
    """,
        conn,
    )
    win_pct = win_rate["win_pct"].iloc[0] if win_rate["win_pct"].iloc[0] else 0

    # P&L (last 30 days)
    pnl = pd.read_sql_query(
        """
        SELECT ROUND(SUM(profit_loss), 2) as pnl
        FROM results
        WHERE settled_at > datetime('now', '-30 days')
    """,
        conn,
    )
    pnl_value = pnl["pnl"].iloc[0] if pnl["pnl"].iloc[0] else 0

    # Avg edge (pending)
    avg_edge = pd.read_sql_query(
        """
        SELECT ROUND(AVG(edge) * 100, 2) as avg_edge
        FROM recommendations
        WHERE created_at > datetime('now', '-7 days')
    """,
        conn,
    )
    avg_edge_value = avg_edge["avg_edge"].iloc[0] if avg_edge["avg_edge"].iloc[0] else 0

    # Bankroll trajectory (last pick)
    bankroll = pd.read_sql_query(
        """
        SELECT ROUND(bankroll_at_time, 2) as bankroll
        FROM recommendations
        ORDER BY created_at DESC
        LIMIT 1
    """,
        conn,
    )
    bankroll_value = bankroll["bankroll"].iloc[0] if len(bankroll) > 0 else 0

    return {
        "total_picks": total_picks,
        "settled": settled,
        "win_pct": win_pct,
        "pnl": pnl_value,
        "avg_edge": avg_edge_value,
        "bankroll": bankroll_value,
    }


def get_time_series():
    """Fetch time series data for charts."""
    conn = get_connection()

    # Daily P&L
    daily_pnl = pd.read_sql_query(
        """
        SELECT 
            DATE(settled_at) as date,
            COUNT(*) as picks,
            SUM(outcome_win_bool) as wins,
            ROUND(SUM(profit_loss), 2) as pnl
        FROM results
        GROUP BY DATE(settled_at)
        ORDER BY date DESC
        LIMIT 60
    """,
        conn,
    )

    # Cumulative P&L
    cumulative_pnl = pd.read_sql_query(
        """
        SELECT 
            DATE(settled_at) as date,
            ROUND(SUM(SUM(profit_loss)) OVER (ORDER BY DATE(settled_at)), 2) as cumulative_pnl
        FROM results
        GROUP BY DATE(settled_at)
        ORDER BY date
    """,
        conn,
    )

    # Picks per day
    picks_per_day = pd.read_sql_query(
        """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as count
        FROM recommendations
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 60
    """,
        conn,
    )

    return {
        "daily_pnl": daily_pnl,
        "cumulative_pnl": cumulative_pnl,
        "picks_per_day": picks_per_day,
    }


def get_recent_picks(limit=10):
    """Fetch recent recommendations."""
    conn = get_connection()

    return pd.read_sql_query(
        f"""
        SELECT 
            r.created_at,
            r.selection,
            ROUND(r.model_prob * 100, 1) as model_prob_pct,
            ROUND(r.market_prob * 100, 1) as market_prob_pct,
            ROUND(r.edge * 100, 2) as edge_pct,
            r.stake_suggested as stake,
            COALESCE(res.outcome_win_bool, 'Pending') as result,
            COALESCE(ROUND(res.profit_loss, 2), '-') as pnl
        FROM recommendations r
        LEFT JOIN results res ON r.id = res.recommendation_id
        ORDER BY r.created_at DESC
        LIMIT {limit}
    """,
        conn,
    )


def get_edge_distribution():
    """Fetch edge distribution."""
    conn = get_connection()

    return pd.read_sql_query(
        """
        SELECT 
            ROUND(edge * 100, 1) as edge_pct,
            COUNT(*) as count
        FROM recommendations
        WHERE created_at > datetime('now', '-30 days')
        GROUP BY ROUND(edge * 100, 1)
        ORDER BY edge_pct
    """,
        conn,
    )


# Main app
st.title("📊 LineLogic Dashboard")
st.caption("Real-time tracking of sports betting recommendations and results")

# Metrics row
metrics = get_metrics()

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric(
        "Total Picks",
        metrics["total_picks"],
        delta=f"Settled: {metrics['settled']}",
    )

with col2:
    st.metric(
        "Win Rate (30d)",
        f"{metrics['win_pct']:.1f}%",
        delta="Last 30 days",
    )

with col3:
    pnl_delta = "✓" if metrics["pnl"] >= 0 else "✗"
    st.metric(
        "P&L (30d)",
        f"${metrics['pnl']:,.2f}",
        delta=pnl_delta,
    )

with col4:
    st.metric(
        "Avg Edge",
        f"{metrics['avg_edge']:.2f}%",
        delta="Last 7 days",
    )

with col5:
    st.metric(
        "Bankroll",
        f"${metrics['bankroll']:,.2f}",
    )

with col6:
    total_settled = metrics["settled"]
    picks_remaining = metrics["total_picks"] - metrics["settled"]
    st.metric(
        "Unsettled",
        picks_remaining,
        delta=f"{picks_remaining} pending",
    )

# Charts section
st.divider()

timeseries = get_time_series()

col_charts1, col_charts2 = st.columns(2)

# Cumulative P&L chart
with col_charts1:
    st.subheader("Cumulative P&L")
    if len(timeseries["cumulative_pnl"]) > 0:
        timeseries["cumulative_pnl"]["date"] = pd.to_datetime(
            timeseries["cumulative_pnl"]["date"]
        )
        fig = px.line(
            timeseries["cumulative_pnl"],
            x="date",
            y="cumulative_pnl",
            title="",
            markers=True,
        )
        fig.update_traces(line=dict(color="#3fb950", width=3))
        fig.update_layout(
            hovermode="x unified",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Date",
            yaxis_title="Cumulative P&L ($)",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No settled results yet.")

# Picks per day chart
with col_charts2:
    st.subheader("Picks per Day")
    if len(timeseries["picks_per_day"]) > 0:
        timeseries["picks_per_day"]["date"] = pd.to_datetime(
            timeseries["picks_per_day"]["date"]
        )
        fig = px.bar(
            timeseries["picks_per_day"].sort_values("date"),
            x="date",
            y="count",
            title="",
            color_discrete_sequence=["#58a6ff"],
        )
        fig.update_layout(
            hovermode="x",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Date",
            yaxis_title="Number of Picks",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No picks yet.")

# Edge distribution
st.divider()
col_edge1, col_edge2 = st.columns([2, 1])

with col_edge1:
    st.subheader("Edge Distribution (Last 30 Days)")
    edge_dist = get_edge_distribution()
    if len(edge_dist) > 0:
        fig = px.bar(
            edge_dist,
            x="edge_pct",
            y="count",
            title="",
            color="count",
            color_continuous_scale="viridis",
        )
        fig.update_layout(
            hovermode="x",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Edge (%)",
            yaxis_title="Count",
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for edge distribution.")

# Recent picks table
st.divider()
st.subheader("Recent Picks")

recent = get_recent_picks(15)
if len(recent) > 0:
    st.dataframe(
        recent,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No picks recorded yet.")

# Footer
st.divider()
st.caption(
    "🤖 LineLogic — Automated sports betting analysis. Data updates after each daily run."
)
st.caption("Last updated: Daily summaries sent to bbrennan83@gmail.com")
