"""
pages/aspirations.py — View, log, and complete long-term milestones.
"""
import streamlit as st
import pandas as pd
import sheets
from xp import DOMAIN_LABELS, DOMAIN_ICONS

def render():
    st.markdown("## 🎯 Aspirations & Milestones")
    
    # ── Load Data ─────────────────────────────────────────────────────────────
    records = sheets.read_all(sheets.TAB_ASPIRATIONS)
    df = pd.DataFrame(records) if records else pd.DataFrame()
    
    # ── Quick Stats Summary ───────────────────────────────────────────────────
    if not df.empty and "Status" in df.columns:
        total_asp = len(df)
        completed_asp = len(df[df["Status"].str.lower() == "complete"])
        prospective_asp = total_asp - completed_asp
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📌 Total Goals", total_asp)
        col2.metric("🔥 Prospective", prospective_asp)
        col3.metric("✅ Completed", completed_asp)
        st.markdown("---")

    # ── Left Column: View & Update | Right Column: Create New ─────────────────
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.markdown("### 📜 Current Quest Log")
        if df.empty:
            st.info("No milestones found in your 'Aspirations' tab yet.")
        else:
            # Clean columns up
            df["Status"] = df["Status"].fillna("Prospective")
            
            # Filter into tabs
            view_tab1, view_tab2 = st.tabs(["⏳ Prospective Quests", "🏆 Completed Legends"])
            
            with view_tab1:
                prospective_df = df[df["Status"].str.lower() != "complete"]
                if prospective_df.empty:
                    st.success("All quests completed! Time to add more targets.")
                else:
                    for _, row in prospective_df.iterrows():
                        title = row.get("Title", "Untitled")
                        domain = row.get("Production Domain", "")
                        icon = DOMAIN_ICONS.get(domain, "🎯")
                        impact = row.get("Potential Impact Score", "—")
                        target_date = row.get("Target Date", "—")
                        desc = row.get("Description", "")
                        
                        # Custom matching metric-card format
                        st.markdown(f"""
                        <div class="metric-card">
                          <div style="display:flex;justify-content:between;align-items:baseline;">
                            <span style="font-family:'Cinzel',serif;font-size:1.1rem;color:#C8A96E;">
                              {icon} {title}
                            </span>
                            <span style="font-family:'Cinzel',serif;font-size:0.85rem;color:#888;">
                              Impact: ⭐{impact} &nbsp;·&nbsp; Target: {target_date}
                            </span>
                          </div>
                          <div style="color:#aaa;font-size:0.9rem;margin-top:6px;">
                            {desc}
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Action Button to complete item
                        if st.button(f"Mark Complete: {title}", key=f"comp_{title}"):
                            with st.spinner("Updating spreadsheet..."):
                                success = sheets.update_aspiration_status(title, "Complete")
                                if success:
                                    st.success(f"Quest Complete: '{title}'! level up incoming.")
                                    st.rerun()
                                else:
                                    st.error("Failed to update status. Double check row formatting.")

            with view_tab2:
                completed_df = df[df["Status"].str.lower() == "complete"]
                if completed_df.empty:
                    st.info("No completed milestones recorded yet.")
                else:
                    for _, row in completed_df.iterrows():
                        title = row.get("Title", "Untitled")
                        domain = row.get("Production Domain", "")
                        icon = DOMAIN_ICONS.get(domain, "🎯")
                        st.markdown(f"""
                        <div class="metric-card" style="border-left: 3px solid #4CAF50; opacity: 0.75;">
                          <span style="font-family:'Cinzel',serif;font-size:1rem;color:#4CAF50;text-decoration:line-through;">
                            {icon} {title}
                          </span><br>
                          <small style="color:#666;">Domain: {domain} | {row.get('Description', '')}</small>
                        </div>
                        """, unsafe_allow_html=True)

    with right_col:
        st.markdown("### ✍️ Draft New Aspiration")
        with st.form("new_aspiration_form", clear_on_submit=True):
            title = st.text_input("Aspiration Title*", placeholder="e.g., 20 Consecutive Pull-ups")
            
            # Map selection options directly using your existing domains layout
            domain_options = list(DOMAIN_LABELS.keys())
            selected_domain = st.selectbox("Production Domain", options=domain_options, format_func=lambda x: f"{DOMAIN_ICONS.get(x, '')} {DOMAIN_LABELS.get(x)}")
            
            prod_type = st.text_input("Production Type", placeholder="e.g., Fitness, Software, Writing")
            collaborators = st.text_input("Collaborators", placeholder="Leave blank if solo")
            target_date = st.text_input("Target Date", placeholder="MM/DD/YYYY or Q3 2026")
            impact_score = st.slider("Potential Impact Score (1-5)", min_value=1, max_value=5, value=3)
            description = st.text_area("Description / Criteria", placeholder="Detailed definitions of success...")
            
            submit = st.form_submit_submit("Inscribe into Log")
            
            if submit:
                if not title:
                    st.error("Title is a mandatory field.")
                else:
                    # Aligning order to match: Production Domain, Production Type, Status, Collaborators, Title, Description, Target Date, Potential Impact Score
                    new_row = [
                        selected_domain,
                        prod_type,
                        "Prospective",
                        collaborators,
                        title,
                        description,
                        target_date,
                        impact_score
                    ]
                    with st.spinner("Appending row..."):
                        sheets.append_row(sheets.TAB_ASPIRATIONS, new_row)
                        st.success(f"Added '{title}' to your tracking sheet!")
                        st.rerun()
