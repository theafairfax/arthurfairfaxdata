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

# ── Password gate: no navigation, modules, or sheet reads before login ─────────
# Configure APP_PASSWORD in Streamlit Community Cloud → App settings → Secrets.
import hmac

def require_login() -> None:
    try:
        expected = st.secrets["APP_PASSWORD"]
    except (KeyError, FileNotFoundError):
        st.error("App password is not configured. Add APP_PASSWORD to Streamlit Secrets.")
        st.stop()

    if not isinstance(expected, str) or not expected:
        st.error("APP_PASSWORD must be a non-empty string in Streamlit Secrets.")
        st.stop()

    if st.session_state.get("authenticated", False):
        return

    # Only the sign-in form is displayed before authentication.
    st.markdown("## ⚔️ Arthur Fairfax")
    st.markdown("Enter the password to access the application.")
    with st.form("login_form"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Unlock")
    if submitted:
        if hmac.compare_digest(password, expected):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()


require_login()

# ── Sidebar navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚔️ Arthur Fairfax")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["🗺️ Arete", "📋 Daily Entry", "🎯 Aspirations", "📜 Curriculum Vitae"], # ← Added "🎯 Aspirations" here
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Data lands in your Google Sheet.\nXP = hours logged since inception.")
    if st.button("Log out"):
        st.session_state.authenticated = False
        st.rerun()

# ── Route ─────────────────────────────────────────────────────────────────────
if page == "🗺️ Arete":
    import dashboard
    dashboard.render()
elif page == "🎯 Aspirations": # ← Added routing step here
    import aspirations
    aspirations.render()
elif page == "📜 Curriculum Vitae":
    import cv
    cv.render()
else:
    import entry
    entry.render()
