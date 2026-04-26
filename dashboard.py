"""
pages/dashboard.py — RPG-style character sheet dashboard.
Shows level, XP bar, total hours, and domain-specific stats.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import sheets
from xp import domain_level_info, DOMAIN_LABELS, DOMAIN_ICONS, ALL_DOMAINS


# ── Data loading ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def load_daily() -> pd.DataFrame:
    records = sheets.read_all(sheets.TAB_DAILY)
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def total_minutes_per_domain(df: pd.DataFrame) -> dict[str, int]:
    totals: dict[str, int] = {}
    for domain in ALL_DOMAINS:
        col = f"{domain}_min"
        if col in df.columns:
            totals[domain] = int(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())
        else:
            totals[domain] = 0
    return totals


# ── UI helpers ─────────────────────────────────────────────────────────────────

def _xp_bar(level_info, key_suffix=""):
    pct = level_info.progress_pct / 100
    st.progress(pct, text=f"")


def _domain_card(domain: str, total_min: int):
    info   = domain_level_info(domain, total_min)
    icon   = DOMAIN_ICONS[domain]
    label  = DOMAIN_LABELS[domain]
    pct    = info.progress_pct

    bar_filled = int(pct / 5)   # out of 20 chars
    bar_str    = "█" * bar_filled + "░" * (20 - bar_filled)

    st.markdown(f"""
<div class="metric-card">
  <div style="display:flex;justify-content:space-between;align-items:baseline;">
    <span style="font-family:'Cinzel',serif;font-size:1rem;color:#C8A96E;">
      {icon} {label}
    </span>
    <span style="font-family:'Cinzel',serif;font-size:1.4rem;color:#e8d5b0;">
      LVL {info.level}
    </span>
  </div>
  <div style="font-family:monospace;color:#888;font-size:0.82rem;margin:4px 0;">
    {bar_str}  {pct:.0f}%
  </div>
  <div style="color:#aaa;font-size:0.85rem;">
    {info.total_hours} hrs total &nbsp;·&nbsp;
    {info.xp_this_level:.1f} / {info.xp_next_level:.1f} hrs to LVL {info.level + 1}
  </div>
</div>
""", unsafe_allow_html=True)


def _sparkline(df: pd.DataFrame, domain: str) -> go.Figure:
    col = f"{domain}_min"
    if col not in df.columns or df.empty:
        return None
    series = df.set_index("date")[col].apply(pd.to_numeric, errors="coerce").fillna(0).tail(30)
    fig = go.Figure(go.Scatter(
        x=series.index, y=series.values,
        mode="lines", fill="tozeroy",
        line=dict(color="#C8A96E", width=1.5),
        fillcolor="rgba(200,169,110,0.12)",
    ))
    fig.update_layout(
        height=80, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


# ── Main render ────────────────────────────────────────────────────────────────

def render():
    st.markdown("## ⚔️ Character Sheet")

    df = load_daily()

    if df.empty:
        st.info("No data yet. Complete your first Daily Entry to populate the dashboard.")
        return

    totals = total_minutes_per_domain(df)
    total_hours_all = sum(totals.values()) / 60

    # ── Top summary ────────────────────────────────────────────────────────────
    avg_sleep = pd.to_numeric(df.get("sleep_hours", pd.Series()), errors="coerce").mean()
    days_logged = df["date"].nunique() if "date" in df.columns else 0
    streak = _compute_streak(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("⏳ Total Hours Logged", f"{total_hours_all:.1f}")
    col2.metric("📅 Days Logged",        days_logged)
    col3.metric("🔥 Current Streak",     f"{streak}d")
    col4.metric("💤 Avg Sleep",          f"{avg_sleep:.1f} hrs" if not pd.isna(avg_sleep) else "—")

    st.markdown("---")
    st.markdown("### Domain Levels")

    # Two-column grid of domain cards
    left, right = st.columns(2)
    for i, domain in enumerate(ALL_DOMAINS):
        with (left if i % 2 == 0 else right):
            _domain_card(domain, totals[domain])

    st.markdown("---")

    # ── Radar chart ───────────────────────────────────────────────────────────
    st.markdown("### Attribute Overview")
    levels = [domain_level_info(d, totals[d]).level for d in ALL_DOMAINS]
    labels = [f"{DOMAIN_ICONS[d]} {DOMAIN_LABELS[d]}" for d in ALL_DOMAINS]

    fig_radar = go.Figure(go.Scatterpolar(
        r=levels + [levels[0]],
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor="rgba(200,169,110,0.15)",
        line=dict(color="#C8A96E", width=2),
        marker=dict(color="#C8A96E", size=5),
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="#111",
            radialaxis=dict(visible=True, color="#555", gridcolor="#2a2a2a"),
            angularaxis=dict(color="#aaa", gridcolor="#2a2a2a"),
        ),
        paper_bgcolor="#0F0F0F",
        font=dict(family="Crimson Text, serif", color="#E8E0D0"),
        height=420,
        margin=dict(l=60, r=60, t=30, b=30),
    )
    st.plotly_chart(fig_radar, width='stretch', key="radar_chart")

    # ── 30-day time heatmap ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Daily Time by Domain (last 30 days)")
    _render_heatmap(df)

    # ── Per-domain sparklines ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 30-Day Activity Sparklines")
    cols = st.columns(3)
    for i, domain in enumerate(ALL_DOMAINS):
        fig = _sparkline(df, domain)
        with cols[i % 3]:
            st.caption(f"{DOMAIN_ICONS[domain]} {DOMAIN_LABELS[domain]}")
            if fig:
                st.plotly_chart(fig, width='stretch', config={"displayModeBar": False}, key=f"sparkline_{i}_{domain}")

    # ── Chess-specific stats ───────────────────────────────────────────────────
    _domain_detail_section()


def _compute_streak(df: pd.DataFrame) -> int:
    if df.empty or "date" not in df.columns:
        return 0
    from datetime import date, timedelta
    dates = sorted(df["date"].dt.date.dropna().unique(), reverse=True)
    streak = 0
    expected = date.today()
    for d in dates:
        if d == expected or d == expected - pd.Timedelta(days=1):
            streak += 1
            expected = d - pd.Timedelta(days=1)
        else:
            break
    return streak


def _render_heatmap(df: pd.DataFrame):
    if df.empty:
        return
    min_cols = [f"{d}_min" for d in ALL_DOMAINS]
    available = [c for c in min_cols if c in df.columns]
    if not available:
        return

    plot_df = df[["date"] + available].tail(30).copy()
    plot_df = plot_df.set_index("date")
    for c in available:
        plot_df[c] = pd.to_numeric(plot_df[c], errors="coerce").fillna(0)
    plot_df.columns = [DOMAIN_LABELS.get(c.replace("_min", ""), c) for c in plot_df.columns]

    fig = go.Figure(go.Heatmap(
        z=plot_df.values.T,
        x=[str(d.date()) for d in plot_df.index],
        y=list(plot_df.columns),
        colorscale=[[0, "#111"], [0.01, "#2a1f0e"], [0.5, "#8B4513"], [1, "#C8A96E"]],
        showscale=True,
        hoverongaps=False,
    ))
    fig.update_layout(
        height=340,
        margin=dict(l=120, r=20, t=10, b=60),
        paper_bgcolor="#0F0F0F",
        plot_bgcolor="#0F0F0F",
        font=dict(family="Crimson Text, serif", color="#888"),
        xaxis=dict(tickangle=-45, tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=11)),
    )
    st.plotly_chart(fig, use_container_width=True, key="heatmap_chart")


def _domain_detail_section():
    """Show domain-specific metric history for Chess, Finance, etc."""
    st.markdown("---")
    st.markdown("### Domain Records")

    tab_labels = ["♟️ Chess", "🔬 Research", "🎵 Music", "🎨 Visual Arts",
                  "🌐 Languages", "🎭 Criticism", "📚 Autodidactic", "🌱 Garden", "🍳 Cooking", "🏋️ Fitness"]
    tab_keys   = [sheets.TAB_CHESS, sheets.TAB_FINANCE, sheets.TAB_RESEARCH, sheets.TAB_MUSIC,
                  sheets.TAB_ARTS, sheets.TAB_LANG, sheets.TAB_CRITIC, sheets.TAB_AUTODID,
                  sheets.TAB_GARDEN, sheets.TAB_COOKING, sheets.TAB_FITNESS]

    tabs = st.tabs(tab_labels)
    for tab, key in zip(tabs, tab_keys):
        with tab:
            records = sheets.read_all(key)
            if records:
                st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
            else:
                st.caption("No records yet.")
