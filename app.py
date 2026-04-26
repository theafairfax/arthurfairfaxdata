"""
app.py — Life Tracker entry point.
Navigation: Dashboard | Daily Entry
"""
import streamlit as st

st.set_page_config(
    page_title="Arthur Fairfax",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;900&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');

html, body, [class*="css"] {
    font-family: 'Crimson Text', serif;
}
h1, h2, h3 {
    font-family: 'Cinzel', serif !important;
    letter-spacing: 0.05em;
}
.stButton > button {
    font-family: 'Cinzel', serif;
    background: linear-gradient(135deg, #2a1f0e, #3d2b10);
    border: 1px solid #C8A96E;
    color: #C8A96E;
    letter-spacing: 0.1em;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #C8A96E, #a07840);
    color: #0F0F0F;
    border-color: #C8A96E;
}
.stProgress > div > div {
    background: linear-gradient(90deg, #8B4513, #C8A96E) !important;
}
div[data-testid="stSidebar"] {
    background: #111 !important;
    border-right: 1px solid #2a2a2a;
}
.metric-card {
    background: #1A1A1A;
    border: 1px solid #2a2a2a;
    border-left: 3px solid #C8A96E;
    border-radius: 4px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚔️ Life Tracker")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["🗺️ Dashboard", "📋 Daily Entry"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Data lands in your Google Sheet.\nXP = hours logged since inception.")

# ── Route ─────────────────────────────────────────────────────────────────────
if page == "🗺️ Dashboard":
    import dashboard
    dashboard.render()
else:
    import entry
    entry.render()
