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
import os


# Page config
st.set_page_config(
    page_title="LineLogic Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Enhanced Styling
st.markdown(
    """
<style>
    /* Main container */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.875rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom header */
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #3fb950, #58a6ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        color: #8b949e;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    
    /* Tables */
    [data-testid="stDataFrame"] {
        border: 1px solid #30363d;
        border-radius: 8px;
    }
    
    /* Dividers */
    hr {
        margin: 2rem 0;
        border-color: #30363d;
    }
</style>
""",
    unsafe_allow_html=True,
)


def get_db_path():
    """Locate database file - works locally and on Streamlit Cloud."""
    # Check if running on Streamlit Cloud
    if os.path.exists("/mount/src"):
        # Streamlit Cloud paths
        cloud_paths = [
            Path("/mount/src/linelogic/.linelogic/linelogic.db"),
            Path("/mount/src/linelogic/linelogic.db"),
        ]
        for p in cloud_paths:
            if p.exists():
                return str(p)

    # Local paths
    local_paths = [
        Path(".linelogic/linelogic.db"),
        Path("../.linelogic/linelogic.db"),
        Path(".") / ".linelogic" / "linelogic.db",
    ]
    for p in local_paths:
        if p.exists():
            return str(p)

    # Default fallback
    return ".linelogic/linelogic.db"


@st.cache_resource
def get_connection():
    """Get SQLite connection with error handling."""
    db_path = get_db_path()

    if not Path(db_path).exists():
        st.error(f"Database not found at: {db_path}")
        st.info(
            "The database will be created after the first daily run. Check back soon!"
        )
        st.stop()

    try:
        return sqlite3.connect(db_path, check_same_thread=False)
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        st.stop()


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
st.markdown(
    '<h1 class="main-header">🎯 LineLogic Dashboard</h1>', unsafe_allow_html=True
)
st.markdown(
    '<p class="sub-header">Real-time tracking of sports betting recommendations and performance analytics</p>',
    unsafe_allow_html=True,
)

# Metrics row
try:
    metrics = get_metrics()
except Exception as e:
    st.error(f"Error loading metrics: {e}")
    st.info("Ensure the database has been populated by running the daily job.")
    st.stop()

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric(
        "Total Picks",
        f"{metrics['total_picks']:,}",
        delta=f"{metrics['settled']} settled",
    )

with col2:
    win_pct = metrics["win_pct"]
    st.metric(
        "Win Rate (30d)",
        f"{win_pct:.1f}%",
        delta=f"{'↑' if win_pct > 50 else '↓'} vs 50%",
        delta_color="normal" if win_pct > 50 else "inverse",
    )

with col3:
    pnl = metrics["pnl"]
    st.metric(
        "P&L (30d)",
        f"${pnl:,.2f}",
        delta=f"{'Profit' if pnl >= 0 else 'Loss'}",
        delta_color="normal" if pnl >= 0 else "inverse",
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
    picks_remaining = metrics["total_picks"] - metrics["settled"]
    st.metric(
        "Pending",
        picks_remaining,
        delta="unsettled",
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
st.subheader("📋 Recent Picks")

recent = get_recent_picks(20)
if len(recent) > 0:
    # Format the dataframe for better display
    recent_display = recent.copy()
    recent_display["created_at"] = pd.to_datetime(
        recent_display["created_at"]
    ).dt.strftime("%Y-%m-%d %H:%M")

    # Color code results
    def highlight_result(row):
        if row["result"] == 1:
            return ["background-color: rgba(63, 185, 80, 0.1)"] * len(row)
        elif row["result"] == 0:
            return ["background-color: rgba(248, 81, 73, 0.1)"] * len(row)
        else:
            return [""] * len(row)

    st.dataframe(
        recent_display.style.apply(highlight_result, axis=1),
        use_container_width=True,
        hide_index=True,
        column_config={
            "created_at": "Date",
            "selection": "Team",
            "model_prob_pct": st.column_config.NumberColumn("Model %", format="%.1f%%"),
            "market_prob_pct": st.column_config.NumberColumn(
                "Market %", format="%.1f%%"
            ),
            "edge_pct": st.column_config.NumberColumn("Edge", format="%.2f%%"),
            "stake": st.column_config.NumberColumn("Stake", format="$%.2f"),
            "result": st.column_config.TextColumn("Result"),
            "pnl": st.column_config.TextColumn("P&L"),
        },
    )
else:
    st.info("No picks recorded yet. Check back after the first daily run!")

# Footer with system status
st.divider()
col_footer1, col_footer2, col_footer3 = st.columns(3)

with col_footer1:
    st.caption("🤖 **LineLogic** — Automated Sports Betting Analytics")

with col_footer2:
    st.caption(f"📊 Database: `{Path(get_db_path()).name}`")

with col_footer3:
    st.caption("📧 Daily reports sent to bbrennan83@gmail.com")

# Refresh indicator
st.caption(f"⏱️ Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
st.caption(
    "💡 Data updates automatically after each daily GitHub Actions run (9:00 UTC)"
)
