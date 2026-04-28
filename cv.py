"""
pages/cv.py — Arthur Fairfax · Curriculum Vitae
Reads from the CV Google Sheet tab and renders an RPG-style achievement ledger.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import sheets

# ── Constants ──────────────────────────────────────────────────────────────────

DOMAIN_COLORS = {
    "Knowledge":   "#C8A96E",   # gold
    "Cultural":    "#9E7BB5",   # violet
    "Industrial":  "#5E9E8A",   # teal
    "Autopoietic": "#C06060",   # crimson
}

DOMAIN_ICONS = {
    "Knowledge":   "🔬",
    "Cultural":    "🎨",
    "Industrial":  "⚙️",
    "Autopoietic": "🌱",
}

TYPE_ICONS = {
    "Publication":  "📄",
    "Poster":       "📌",
    "Presentation": "🎤",
    "Grant":        "💰",
    "Visual Art":   "🖼️",
    "Program":      "💻",
    "Job & Career": "🏛️",
    "Language":     "🗣️",
    "Fitness":      "🏃",
}

STATUS_STYLE = {
    "Completed":   ("✅", "#3a6b3a"),
    "In Progress": ("🔄", "#6b5c2a"),
    "Planned":     ("📋", "#2a3f6b"),
}


# ── Data loading ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def load_cv() -> pd.DataFrame:
    records = sheets.read_all(sheets.TAB_CV)
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df.columns = df.columns.str.strip()

    # Normalise Status
    if "Status" in df.columns:
        df["Status"] = df["Status"].str.strip()

    # Parse date — take the first 7 chars (YYYY-MM) or 4 (YYYY), coerce ranges
    if "Date Acquired" in df.columns:
        df["Date Acquired"] = df["Date Acquired"].astype(str).str.strip()
        df["Date Sort"] = pd.to_datetime(
            df["Date Acquired"].str[:7], format="%Y-%m", errors="coerce"
        ).fillna(
            pd.to_datetime(df["Date Acquired"].str[:4], format="%Y", errors="coerce")
        )

    if "Impact Score" in df.columns:
        df["Impact Score"] = pd.to_numeric(df["Impact Score"], errors="coerce").fillna(1)

    return df


# ── UI helpers ─────────────────────────────────────────────────────────────────

def _impact_pips(score: float) -> str:
    filled = int(score)
    return "◆" * filled + "◇" * (5 - filled)


def _achievement_card(row: pd.Series):
    domain  = str(row.get("Production Domain", "")).strip()
    ptype   = str(row.get("Production Type", "")).strip()
    title   = str(row.get("Title", "")).strip()
    desc    = str(row.get("Description", "")).strip()
    date    = str(row.get("Date Acquired", "")).strip()
    link    = str(row.get("Link", "")).strip()
    score   = float(row.get("Impact Score", 1))
    status  = str(row.get("Status", "Completed")).strip()
    collabs = str(row.get("Collaborators", "")).strip()

    color        = DOMAIN_COLORS.get(domain, "#888")
    d_icon       = DOMAIN_ICONS.get(domain, "•")
    t_icon       = TYPE_ICONS.get(ptype, "•")
    s_icon, s_bg = STATUS_STYLE.get(status, ("•", "#333"))
    pips         = _impact_pips(score)

    link_html = (
        f'<a href="{link}" target="_blank" style="color:{color};font-size:0.75rem;'
        f'text-decoration:none;letter-spacing:0.05em;">↗ VIEW</a>'
        if link and link not in ("", "nan") else ""
    )

    collab_html = (
        f'<div style="color:#666;font-size:0.72rem;margin-top:4px;font-style:italic;">'
        f'with {collabs}</div>'
        if collabs and collabs not in ("", "nan") else ""
    )

    st.markdown(f"""
<div style="
    border:1px solid #222;
    border-left:3px solid {color};
    background:linear-gradient(135deg,#111 0%,#141414 100%);
    border-radius:4px;
    padding:14px 16px;
    margin-bottom:10px;
    position:relative;
">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">
    <div style="flex:1;">
      <div style="font-family:'Cinzel',serif;font-size:0.92rem;color:#E8E0D0;
                  line-height:1.3;margin-bottom:4px;">
        {t_icon} {title}
      </div>
      <div style="color:#888;font-size:0.78rem;margin-bottom:6px;">{desc[:180]}{"…" if len(desc)>180 else ""}</div>
      {collab_html}
    </div>
    <div style="text-align:right;white-space:nowrap;flex-shrink:0;">
      <div style="color:{color};font-size:0.7rem;letter-spacing:0.08em;font-family:'Cinzel',serif;">
        {d_icon} {domain}
      </div>
      <div style="color:#555;font-size:0.68rem;">{ptype}</div>
      <div style="color:#C8A96E;font-size:0.72rem;margin-top:2px;">{pips}</div>
    </div>
  </div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;">
    <div style="display:flex;gap:8px;align-items:center;">
      <span style="background:{s_bg};color:#ccc;font-size:0.65rem;padding:2px 7px;
                   border-radius:2px;letter-spacing:0.06em;">{s_icon} {status}</span>
      <span style="color:#555;font-size:0.72rem;">{date}</span>
    </div>
    {link_html}
  </div>
</div>
""", unsafe_allow_html=True)


# ── Charts ─────────────────────────────────────────────────────────────────────

def _timeline_chart(df: pd.DataFrame):
    plot = df.dropna(subset=["Date Sort"]).copy()
    if plot.empty:
        return

    plot = plot.sort_values("Date Sort")
    plot["label"] = plot["Production Type"].str.strip() + ": " + plot["Title"].str[:40]
    plot["color"] = plot["Production Domain"].str.strip().map(DOMAIN_COLORS).fillna("#888")
    plot["y"] = plot["Production Domain"].str.strip().map(
        {"Knowledge": 3, "Cultural": 2, "Industrial": 1, "Autopoietic": 0}
    )

    fig = go.Figure()

    for domain, grp in plot.groupby("Production Domain"):
        color = DOMAIN_COLORS.get(domain.strip(), "#888")
        fig.add_trace(go.Scatter(
            x=grp["Date Sort"],
            y=grp["y"],
            mode="markers+text",
            marker=dict(
                size=grp["Impact Score"] * 6 + 4,
                color=color,
                opacity=0.85,
                line=dict(width=1, color="#000"),
            ),
            text=grp["Production Type"].str.strip().map(TYPE_ICONS).fillna("•"),
            textposition="middle center",
            textfont=dict(size=9),
            hovertext=grp["label"],
            hoverinfo="text+x",
            name=f"{DOMAIN_ICONS.get(domain.strip(),'•')} {domain.strip()}",
        ))

    fig.update_layout(
        height=260,
        paper_bgcolor="#0F0F0F",
        plot_bgcolor="#0F0F0F",
        font=dict(family="Crimson Text, serif", color="#888"),
        margin=dict(l=100, r=20, t=10, b=40),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            font=dict(size=10, color="#aaa"),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(gridcolor="#1a1a1a", tickfont=dict(size=10)),
        yaxis=dict(
            tickvals=[0, 1, 2, 3],
            ticktext=["🌱 Autopoietic", "⚙️ Industrial", "🎨 Cultural", "🔬 Knowledge"],
            gridcolor="#1a1a1a",
            tickfont=dict(size=10),
        ),
    )
    st.plotly_chart(fig, use_container_width=True, key="cv_timeline")


def _treemap_chart(df: pd.DataFrame):
    counts = (
        df.groupby(["Production Domain", "Production Type"])
        .agg(count=("Title", "count"), impact=("Impact Score", "sum"))
        .reset_index()
    )
    counts["Production Domain"] = counts["Production Domain"].str.strip()
    counts["Production Type"]   = counts["Production Type"].str.strip()

    labels  = []
    parents = []
    values  = []
    colors  = []

    # Domain nodes
    for domain in counts["Production Domain"].unique():
        labels.append(domain)
        parents.append("")
        values.append(0)
        colors.append(DOMAIN_COLORS.get(domain, "#888"))

    # Type leaf nodes
    for _, row in counts.iterrows():
        labels.append(f"{row['Production Type']}<br>({int(row['count'])})")
        parents.append(row["Production Domain"])
        values.append(int(row["impact"]))
        colors.append(DOMAIN_COLORS.get(row["Production Domain"], "#888"))

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors, line=dict(width=1, color="#000")),
        textfont=dict(family="Cinzel, serif", size=11, color="#E8E0D0"),
        hovertemplate="<b>%{label}</b><br>Impact: %{value}<extra></extra>",
    ))
    fig.update_layout(
        height=300,
        paper_bgcolor="#0F0F0F",
        margin=dict(l=0, r=0, t=0, b=0),
    )
    st.plotly_chart(fig, use_container_width=True, key="cv_treemap")


def _radar_chart(df: pd.DataFrame):
    domains = list(DOMAIN_COLORS.keys())
    scores = []
    for d in domains:
        subset = df[df["Production Domain"].str.strip() == d]
        scores.append(float(subset["Impact Score"].sum()) if not subset.empty else 0)

    labels = [f"{DOMAIN_ICONS[d]} {d}" for d in domains]

    fig = go.Figure(go.Scatterpolar(
        r=scores + [scores[0]],
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor="rgba(200,169,110,0.12)",
        line=dict(color="#C8A96E", width=2),
        marker=dict(color="#C8A96E", size=5),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#111",
            radialaxis=dict(visible=True, color="#444", gridcolor="#222"),
            angularaxis=dict(color="#aaa", gridcolor="#222"),
        ),
        paper_bgcolor="#0F0F0F",
        font=dict(family="Crimson Text, serif", color="#E8E0D0"),
        height=320,
        margin=dict(l=60, r=60, t=20, b=20),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, key="cv_radar")


# ── Main render ────────────────────────────────────────────────────────────────

def render():
    st.markdown("## 📜 Curriculum Vitae")
    st.markdown(
        '<p style="color:#666;font-style:italic;font-family:\'Crimson Text\',serif;">'
        'A living record of works produced, honours earned, and disciplines mastered.</p>',
        unsafe_allow_html=True,
    )

    df = load_cv()

    if df.empty:
        st.info("No CV data found. Make sure the sheet tab is shared and named correctly.")
        return

    # ── Summary metrics ────────────────────────────────────────────────────────
    total        = len(df)
    completed    = len(df[df["Status"].str.strip() == "Completed"]) if "Status" in df.columns else total
    in_progress  = len(df[df["Status"].str.strip() == "In Progress"]) if "Status" in df.columns else 0
    avg_impact   = df["Impact Score"].mean() if "Impact Score" in df.columns else 0
    linked       = df["Link"].astype(str).str.strip().replace("nan", "").ne("").sum() if "Link" in df.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📜 Total Achievements", total)
    c2.metric("✅ Completed",          completed)
    c3.metric("🔄 In Progress",        in_progress)
    c4.metric("⭐ Avg Impact Score",   f"{avg_impact:.1f} / 5")

    st.markdown("---")

    # ── Visualisations ─────────────────────────────────────────────────────────
    left_col, right_col = st.columns([3, 2])

    with left_col:
        st.markdown("### Achievement Timeline")
        _timeline_chart(df)

    with right_col:
        st.markdown("### Domain Spread")
        _radar_chart(df)

    st.markdown("### Output by Domain & Type")
    _treemap_chart(df)

    st.markdown("---")

    # ── Filters ────────────────────────────────────────────────────────────────
    st.markdown("### Achievement Ledger")

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        domain_opts = ["All"] + sorted(df["Production Domain"].str.strip().unique().tolist())
        domain_filter = st.selectbox("Domain", domain_opts, key="cv_domain")

    with filter_col2:
        type_opts = ["All"] + sorted(df["Production Type"].str.strip().unique().tolist())
        type_filter = st.selectbox("Type", type_opts, key="cv_type")

    with filter_col3:
        status_opts = ["All"] + sorted(df["Status"].str.strip().unique().tolist()) if "Status" in df.columns else ["All"]
        status_filter = st.selectbox("Status", status_opts, key="cv_status")

    filtered = df.copy()
    if domain_filter != "All":
        filtered = filtered[filtered["Production Domain"].str.strip() == domain_filter]
    if type_filter != "All":
        filtered = filtered[filtered["Production Type"].str.strip() == type_filter]
    if status_filter != "All" and "Status" in filtered.columns:
        filtered = filtered[filtered["Status"].str.strip() == status_filter]

    filtered = filtered.sort_values("Date Sort", ascending=False, na_position="last") if "Date Sort" in filtered.columns else filtered

    st.caption(f"Showing {len(filtered)} of {total} achievements")

    for _, row in filtered.iterrows():
        _achievement_card(row)
