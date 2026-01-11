"""
LineLogic Dashboard (Enhanced)
Quantitative sports betting intelligence with precision UI/UX.
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
    page_title="LineLogic — Sports Betting Research Terminal",
    page_icon="📊",  # More professional than 🎯
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Professional Dark Theme Styling
st.markdown(
    """
<style>
    /* ===== GLOBAL RESETS ===== */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main container */
    .main > div {
        padding: 2rem 3rem;
        background: #0A1929;
    }
    
    /* ===== HIDE STREAMLIT BRANDING ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ===== CUSTOM HEADER ===== */
    .linelogic-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .linelogic-logo {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00D9FF, #0EA5E9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
    }
    
    .linelogic-tagline {
        color: #8B949E;
        font-size: 0.95rem;
        font-weight: 400;
        letter-spacing: 0.02em;
        margin-bottom: 2rem;
    }
    
    /* ===== METRIC CARDS ===== */
    [data-testid="stMetricValue"] {
        font-size: 2.25rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        color: #E6EDF3;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #8B949E;
        font-weight: 600;
    }
    
    /* Primary KPI Card */
    .primary-kpi {
        background: linear-gradient(135deg, #1A2332 0%, #243447 100%);
        border: 2px solid #00D9FF;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 217, 255, 0.15);
    }
    
    .primary-kpi-value {
        font-size: 3.5rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        color: #00D9FF;
        margin: 0.5rem 0;
    }
    
    .primary-kpi-label {
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #8B949E;
        font-weight: 600;
    }
    
    .primary-kpi-delta {
        font-size: 1.25rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .primary-kpi-submetrics {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-top: 1.5rem;
        padding-top: 1.5rem;
        border-top: 1px solid #30363d;
        font-size: 0.95rem;
    }
    
    /* ===== SECTION HEADERS ===== */
    .section-header {
        font-size: 1.125rem;
        font-weight: 700;
        color: #E6EDF3;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #30363d;
    }
    
    /* ===== TABLES ===== */
    [data-testid="stDataFrame"] {
        border: 1px solid #30363d;
        border-radius: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.875rem;
    }
    
    /* ===== BADGES ===== */
    .tier-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .tier-1 { background: #10B981; color: #000; }
    .tier-2 { background: #3B82F6; color: #fff; }
    .tier-3 { background: #F59E0B; color: #000; }
    .tier-4 { background: #6B7280; color: #fff; }
    
    /* ===== ALERTS ===== */
    .alert-box {
        background: linear-gradient(135deg, #1A2332, #243447);
        border-left: 4px solid #FF6B35;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        color: #E6EDF3;
    }
    
    .alert-box strong {
        color: #FF6B35;
    }
    
    /* ===== DIVIDERS ===== */
    hr {
        margin: 2.5rem 0;
        border: none;
        border-top: 1px solid #30363d;
    }
    
    /* ===== CHARTS ===== */
    .js-plotly-plot {
        border-radius: 8px;
        border: 1px solid #30363d;
    }
    
    /* ===== STATUS INDICATORS ===== */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.25rem 0.75rem;
        border-radius: 8px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .status-live {
        background: rgba(16, 185, 129, 0.2);
        color: #10B981;
        border: 1px solid #10B981;
    }
    
    .status-pending {
        background: rgba(99, 102, 241, 0.2);
        color: #6366F1;
        border: 1px solid #6366F1;
    }
    
    /* ===== FOOTER ===== */
    .dashboard-footer {
        margin-top: 3rem;
        padding-top: 2rem;
        border-top: 1px solid #30363d;
        color: #6E7681;
        font-size: 0.875rem;
    }
    
    /* ===== RESPONSIVE ===== */
    @media (max-width: 768px) {
        .main > div {
            padding: 1rem;
        }
        
        .primary-kpi-value {
            font-size: 2.5rem;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)


def get_db_path():
    """Locate database file - works locally and on Streamlit Cloud."""
    # Check if running on Streamlit Cloud
    if os.path.exists("/mount/src"):
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

    return ".linelogic/linelogic.db"


@st.cache_resource
def get_connection():
    """Get SQLite connection with error handling."""
    db_path = get_db_path()

    if not Path(db_path).exists():
        st.error(f"📂 Database not found at: `{db_path}`")
        st.info(
            "The database will be created after the first automated run. Check back after 9:00 UTC!"
        )
        st.stop()

    try:
        return sqlite3.connect(db_path, check_same_thread=False)
    except Exception as e:
        st.error(f"⚠️ Failed to connect to database: {e}")
        st.stop()


def get_metrics():
    """Fetch comprehensive metrics from database."""
    conn = get_connection()

    # Total recommendations
    total_picks = pd.read_sql_query(
        "SELECT COUNT(*) as count FROM recommendations", conn
    )["count"].iloc[0]

    # Settled picks
    settled = pd.read_sql_query("SELECT COUNT(*) as count FROM results", conn)[
        "count"
    ].iloc[0]

    # Win rate (last 30 days) with sample size
    win_stats = pd.read_sql_query(
        """
        SELECT 
            COUNT(*) as sample_size,
            SUM(outcome_win_bool) as wins,
            ROUND(SUM(outcome_win_bool) * 100.0 / COUNT(*), 2) as win_pct
        FROM results
        WHERE settled_at > datetime('now', '-30 days')
    """,
        conn,
    )

    sample_size = win_stats["sample_size"].iloc[0] if len(win_stats) > 0 else 0
    wins = win_stats["wins"].iloc[0] if len(win_stats) > 0 else 0
    losses = sample_size - wins if sample_size > 0 else 0
    win_pct = win_stats["win_pct"].iloc[0] if win_stats["win_pct"].iloc[0] else 0

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

    # ROI calculation
    total_staked = pd.read_sql_query(
        """
        SELECT SUM(stake_suggested) as total_staked
        FROM recommendations r
        JOIN results res ON r.id = res.recommendation_id
        WHERE res.settled_at > datetime('now', '-30 days')
    """,
        conn,
    )
    total_staked_value = (
        total_staked["total_staked"].iloc[0]
        if total_staked["total_staked"].iloc[0]
        else 1
    )
    roi = (pnl_value / total_staked_value * 100) if total_staked_value > 0 else 0

    # Avg edge (pending picks, last 7 days)
    avg_edge = pd.read_sql_query(
        """
        SELECT ROUND(AVG(edge) * 100, 2) as avg_edge
        FROM recommendations
        WHERE created_at > datetime('now', '-7 days')
    """,
        conn,
    )
    avg_edge_value = avg_edge["avg_edge"].iloc[0] if avg_edge["avg_edge"].iloc[0] else 0

    # Bankroll trajectory
    bankroll = pd.read_sql_query(
        """
        SELECT ROUND(bankroll_at_time, 2) as bankroll
        FROM recommendations
        ORDER BY created_at DESC
        LIMIT 1
    """,
        conn,
    )
    bankroll_value = bankroll["bankroll"].iloc[0] if len(bankroll) > 0 else 1000.00

    # Pending picks value
    pending_value = pd.read_sql_query(
        """
        SELECT COUNT(*) as count, COALESCE(SUM(stake_suggested), 0) as total_risk
        FROM recommendations r
        WHERE NOT EXISTS (SELECT 1 FROM results WHERE recommendation_id = r.id)
    """,
        conn,
    )
    pending_count = pending_value["count"].iloc[0] if len(pending_value) > 0 else 0
    pending_risk = pending_value["total_risk"].iloc[0] if len(pending_value) > 0 else 0

    return {
        "total_picks": total_picks,
        "settled": settled,
        "sample_size": sample_size,
        "wins": wins,
        "losses": losses,
        "win_pct": win_pct,
        "pnl": pnl_value,
        "roi": roi,
        "avg_edge": avg_edge_value,
        "bankroll": bankroll_value,
        "pending_count": pending_count,
        "pending_risk": pending_risk,
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

    return {
        "daily_pnl": daily_pnl,
        "cumulative_pnl": cumulative_pnl,
    }


def get_recent_picks(limit=15):
    """Fetch recent recommendations with enhanced display."""
    conn = get_connection()

    primary_query = f"""
        SELECT 
            r.created_at,
            r.market,
            r.selection,
            ROUND(r.model_prob * 100, 1) as model_prob_pct,
            ROUND(r.market_prob * 100, 1) as market_prob_pct,
            ROUND(r.edge * 100, 2) as edge_pct,
            r.confidence_tier,
            r.stake_suggested as stake,
            CASE
                WHEN res.outcome_win_bool = 1 THEN '✅ Win'
                WHEN res.outcome_win_bool = 0 THEN '❌ Loss'
                ELSE '⏳ Pending'
            END as result,
            COALESCE(ROUND(res.profit_loss, 2), 0) as pnl
        FROM recommendations r
        LEFT JOIN results res ON r.id = res.recommendation_id
        ORDER BY r.created_at DESC
        LIMIT {limit}
    """

    fallback_query = f"""
        SELECT 
            r.created_at,
            'ML' as market,
            r.selection,
            ROUND(r.model_prob * 100, 1) as model_prob_pct,
            ROUND(r.market_prob * 100, 1) as market_prob_pct,
            ROUND(r.edge * 100, 2) as edge_pct,
            r.confidence_tier,
            r.stake_suggested as stake,
            CASE
                WHEN res.outcome_win_bool = 1 THEN '✅ Win'
                WHEN res.outcome_win_bool = 0 THEN '❌ Loss'
                ELSE '⏳ Pending'
            END as result,
            COALESCE(ROUND(res.profit_loss, 2), 0) as pnl
        FROM recommendations r
        LEFT JOIN results res ON r.id = res.recommendation_id
        ORDER BY r.created_at DESC
        LIMIT {limit}
    """

    try:
        return pd.read_sql_query(primary_query, conn)
    except Exception:
        # Fallback for older databases without the `market` column; default to moneyline
        st.warning("Database missing `market` column; defaulting market to 'ML'.")
        return pd.read_sql_query(fallback_query, conn)


def format_delta(value, prefix="", suffix=""):
    """Format delta with color coding."""
    if value > 0:
        return f"🟢 {prefix}+{value:.2f}{suffix}"
    elif value < 0:
        return f"🔴 {prefix}{value:.2f}{suffix}"
    else:
        return f"⚪ {prefix}{value:.2f}{suffix}"


# ===== HEADER =====
st.markdown(
    """
    <div class="linelogic-header">
        <div class="linelogic-logo">📊 LINELOGIC</div>
    </div>
    <div class="linelogic-tagline">
        Quantitative Sports Betting Intelligence — Model-Driven Recommendations with CLV Tracking
    </div>
    """,
    unsafe_allow_html=True,
)

# ===== LOAD METRICS =====
try:
    metrics = get_metrics()
except Exception as e:
    st.error(f"⚠️ Error loading metrics: {e}")
    st.info(
        "Ensure the database has been populated by running the daily automated job."
    )
    st.stop()

# ===== PRIMARY KPI: BANKROLL =====
bankroll_change = metrics["pnl"]
bankroll_pct_change = (
    bankroll_change / 1000.0
) * 100  # Assuming starting bankroll of $1000

st.markdown(
    f"""
    <div class="primary-kpi">
        <div class="primary-kpi-label">💰 CURRENT BANKROLL</div>
        <div class="primary-kpi-value">${metrics['bankroll']:,.2f}</div>
        <div class="primary-kpi-delta">{format_delta(bankroll_change, "$", "")} ({bankroll_pct_change:+.1f}%) over 30 days</div>
        <div class="primary-kpi-submetrics">
            <span>P&L: <strong>${metrics['pnl']:,.2f}</strong></span>
            <span>|</span>
            <span>ROI: <strong>{metrics['roi']:.2f}%</strong></span>
            <span>|</span>
            <span>Win Rate: <strong>{metrics['win_pct']:.1f}%</strong></span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ===== PERFORMANCE METRICS =====
st.markdown(
    '<div class="section-header">📊 Performance Metrics (30 Days)</div>',
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Win Rate",
        f"{metrics['win_pct']:.1f}%",
        delta=f"{int(metrics['wins'])}W / {int(metrics['losses'])}L",
    )

with col2:
    market_comparison = metrics["win_pct"] - 50.0
    st.metric(
        "vs Market",
        f"{market_comparison:+.1f}pp",
        delta="Beating 50% baseline" if market_comparison > 0 else "Below baseline",
        delta_color="normal" if market_comparison > 0 else "inverse",
    )

with col3:
    st.metric(
        "Avg Edge",
        f"{metrics['avg_edge']:.2f}%",
        delta="Last 7 days",
    )

with col4:
    if metrics["sample_size"] < 50:
        sample_warning = f"⚠️ Small sample ({metrics['sample_size']})"
    elif metrics["sample_size"] < 100:
        sample_warning = f"📊 Building ({metrics['sample_size']})"
    else:
        sample_warning = f"✅ Valid ({metrics['sample_size']})"

    st.metric(
        "Sample Size",
        metrics["sample_size"],
        delta=sample_warning,
    )

# ===== ACTIVITY METRICS =====
col5, col6, col7 = st.columns(3)

with col5:
    st.metric(
        "Total Picks",
        f"{metrics['total_picks']:,}",
        delta=f"{metrics['settled']} settled",
    )

with col6:
    st.metric(
        "Pending",
        metrics["pending_count"],
        delta=f"${metrics['pending_risk']:.2f} at risk",
    )

with col7:
    # Show system status
    status_html = '<span class="status-indicator status-live">● LIVE</span>'
    st.markdown(f"**System Status**<br>{status_html}", unsafe_allow_html=True)

# ===== SMALL SAMPLE WARNING =====
if metrics["sample_size"] < 100:
    st.markdown(
        f"""
        <div class="alert-box">
            <strong>⚠️ Small Sample Warning:</strong> Only {metrics['sample_size']} settled picks in the last 30 days. 
            Statistical significance requires 100+ picks. Current metrics may not reflect true model performance.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ===== CHARTS SECTION =====
st.divider()
st.markdown(
    '<div class="section-header">📈 Performance Trends</div>', unsafe_allow_html=True
)

timeseries = get_time_series()

col_charts1, col_charts2 = st.columns(2)

# Cumulative P&L chart
with col_charts1:
    st.subheader("Cumulative P&L")
    if len(timeseries["cumulative_pnl"]) > 0:
        timeseries["cumulative_pnl"]["date"] = pd.to_datetime(
            timeseries["cumulative_pnl"]["date"]
        )

        fig = go.Figure()

        # Main line
        fig.add_trace(
            go.Scatter(
                x=timeseries["cumulative_pnl"]["date"],
                y=timeseries["cumulative_pnl"]["cumulative_pnl"],
                mode="lines+markers",
                name="Cumulative P&L",
                line=dict(color="#00D9FF", width=3),
                marker=dict(size=6, color="#00D9FF"),
                fill="tozeroy",
                fillcolor="rgba(0, 217, 255, 0.1)",
            )
        )

        # Zero line
        fig.add_hline(y=0, line_dash="dash", line_color="#6E7681", opacity=0.5)

        fig.update_layout(
            hovermode="x unified",
            plot_bgcolor="#0A1929",
            paper_bgcolor="#1A2332",
            font=dict(color="#E6EDF3"),
            xaxis_title="Date",
            yaxis_title="Cumulative P&L ($)",
            height=400,
            margin=dict(l=40, r=20, t=40, b=40),
            xaxis=dict(gridcolor="#30363d"),
            yaxis=dict(gridcolor="#30363d"),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No settled results yet. Check back after picks are settled.")

# Daily P&L chart
with col_charts2:
    st.subheader("Daily P&L")
    if len(timeseries["daily_pnl"]) > 0:
        timeseries["daily_pnl"]["date"] = pd.to_datetime(
            timeseries["daily_pnl"]["date"]
        )
        timeseries["daily_pnl"] = timeseries["daily_pnl"].sort_values("date")

        # Color bars by P&L
        colors = [
            "#10B981" if pnl >= 0 else "#EF4444"
            for pnl in timeseries["daily_pnl"]["pnl"]
        ]

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=timeseries["daily_pnl"]["date"],
                y=timeseries["daily_pnl"]["pnl"],
                marker_color=colors,
                name="Daily P&L",
            )
        )

        fig.update_layout(
            hovermode="x",
            plot_bgcolor="#0A1929",
            paper_bgcolor="#1A2332",
            font=dict(color="#E6EDF3"),
            xaxis_title="Date",
            yaxis_title="Daily P&L ($)",
            height=400,
            margin=dict(l=40, r=20, t=40, b=40),
            xaxis=dict(gridcolor="#30363d"),
            yaxis=dict(gridcolor="#30363d"),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No daily P&L data available yet.")

# ===== RECENT PICKS TABLE =====
st.divider()
st.markdown('<div class="section-header">📋 Recent Picks</div>', unsafe_allow_html=True)

recent = get_recent_picks(20)
if len(recent) > 0:
    recent_display = recent.copy()
    recent_display["created_at"] = pd.to_datetime(
        recent_display["created_at"]
    ).dt.strftime("%m/%d %H:%M")

    # Apply color coding
    def highlight_result(row):
        if "✅" in str(row["result"]):
            return ["background-color: rgba(16, 185, 129, 0.15)"] * len(row)
        elif "❌" in str(row["result"]):
            return ["background-color: rgba(239, 68, 68, 0.15)"] * len(row)
        else:
            return ["background-color: rgba(99, 102, 241, 0.1)"] * len(row)

    st.dataframe(
        recent_display.style.apply(highlight_result, axis=1),
        use_container_width=True,
        hide_index=True,
        column_config={
            "created_at": st.column_config.TextColumn("Date", width="small"),
            "market": st.column_config.TextColumn("Market", width="small"),
            "selection": st.column_config.TextColumn("📍 Pick", width="large"),
            "result": st.column_config.TextColumn("Result", width="small"),
            "model_prob_pct": st.column_config.NumberColumn(
                "Model%", format="%.1f%%", width="small"
            ),
            "market_prob_pct": st.column_config.NumberColumn(
                "Market%", format="%.1f%%", width="small"
            ),
            "edge_pct": st.column_config.NumberColumn(
                "Edge", format="%.2f%%", width="small"
            ),
            "confidence_tier": st.column_config.TextColumn("Tier", width="small"),
            "stake": st.column_config.NumberColumn(
                "Stake", format="$%.2f", width="small"
            ),
            "pnl": st.column_config.NumberColumn("P&L", format="$%.2f", width="small"),
        },
    )
else:
    st.info(
        "No picks recorded yet. Check back after the first automated daily run (9:00 UTC)!"
    )

# ===== FOOTER =====
st.markdown(
    f"""
    <div class="dashboard-footer">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>LineLogic</strong> — Quantitative Sports Betting Intelligence<br>
                Database: <code>{Path(get_db_path()).name}</code>
            </div>
            <div style="text-align: right;">
                Last Updated: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</strong><br>
                Automated Run: <strong>Daily @ 9:00 UTC</strong>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "💡 **Model:** LogisticRegression (L1, C=0.1) | **Test Accuracy:** 68.98% | **Features:** 13 L1-selected"
)
st.caption(
    "📊 **Data refreshes automatically after each GitHub Actions run** — No manual intervention required"
)
