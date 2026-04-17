"""
pages/entry.py — 3-step daily data entry flow.
Step 1: Sleep / Supplements / Routines
Step 2: Time per domain (pre-filled from Google Calendar)
Step 3: Domain-specific metrics
"""
from __future__ import annotations

from datetime import date, datetime, time

import streamlit as st

from chess_api import fetch_today_chess_stats

import sheets
import xp as xp_utils
from cal import fetch_today_domain_minutes
from xp import DOMAIN_LABELS, DOMAIN_ICONS, ALL_DOMAINS


# ── Session state helpers ──────────────────────────────────────────────────────

def _init_state():
    if "entry_step" not in st.session_state:
        st.session_state.entry_step = 1
    if "step1_data" not in st.session_state:
        st.session_state.step1_data = {}
    if "step2_data" not in st.session_state:
        st.session_state.step2_data = {}


def _next_step():
    st.session_state.entry_step += 1


def _prev_step():
    st.session_state.entry_step -= 1


def _reset():
    st.session_state.entry_step = 1
    st.session_state.step1_data = {}
    st.session_state.step2_data = {}


# ── Step renderers ─────────────────────────────────────────────────────────────

def _step1():
    st.markdown("## Step 1 of 3 — General Health")
    st.markdown("*Sleep, supplements, and routines from last night / this morning.*")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        bedtime = st.time_input("🌙 Time you went to sleep", value=time(23, 0))
    with col2:
        wakeup  = st.time_input("☀️ Time you woke up", value=time(7, 0))

    # Calculate sleep hours (handles crossing midnight)
    bed_dt  = datetime.combine(date.today(), bedtime)
    wake_dt = datetime.combine(date.today(), wakeup)
    if wake_dt < bed_dt:
        from datetime import timedelta
        wake_dt += timedelta(days=1)
    sleep_hours = round((wake_dt - bed_dt).total_seconds() / 3600, 2)
    st.info(f"⏱️ Calculated sleep: **{sleep_hours} hours**")

    st.markdown("#### Supplements taken today")
    supplement_options = ["Creatine", "Caffeine", "THC", "L-Theanine", "Ashwagandha", "Minoxidil"]
    supplements = st.multiselect("Select all that apply", supplement_options)

    st.markdown("#### Routines")
    col3, col4 = st.columns(2)
    with col3:
        morning_routine = st.radio("Morning routine completed?", ["Yes", "No"], horizontal=True)
    with col4:
        nightly_routine = st.radio("Nightly routine completed?", ["Yes", "No"], horizontal=True)

    st.markdown("---")
    if st.button("Continue →", use_container_width=True):
        st.session_state.step1_data = {
            "sleep_hours":      sleep_hours,
            "supplements":      ", ".join(supplements) if supplements else "None",
            "morning_routine":  morning_routine,
            "nightly_routine":  nightly_routine,
        }
        _next_step()
        st.rerun()


def _step2():
    st.markdown("## Step 2 of 3 — Time Spent per Domain")
    st.markdown("*Values pre-filled from Google Calendar. Edit anything that looks off.*")
    st.markdown("---")

    # Pull calendar data (cached per session)
    if "cal_minutes" not in st.session_state:
        with st.spinner("Fetching your Google Calendar…"):
            st.session_state.cal_minutes = fetch_today_domain_minutes()

    cal = st.session_state.cal_minutes
    edited: dict[str, int] = {}

    cols = st.columns(2)
    for i, domain in enumerate(ALL_DOMAINS):
        label = f"{DOMAIN_ICONS[domain]} {DOMAIN_LABELS[domain]}"
        default = cal.get(domain, 0)
        with cols[i % 2]:
            edited[domain] = st.number_input(
                f"{label} (min)",
                min_value=0,
                max_value=1440,
                value=default,
                step=5,
                key=f"time_{domain}",
            )

    st.markdown("---")
    col_back, col_fwd = st.columns([1, 3])
    with col_back:
        if st.button("← Back"):
            _prev_step()
            st.rerun()
    with col_fwd:
        if st.button("Continue →", use_container_width=True):
            st.session_state.step2_data = edited
            _next_step()
            st.rerun()


def _step3():
    st.markdown("## Step 3 of 3 — Domain Metrics")
    st.markdown("*Log accomplishments for any domain you engaged with today.*")
    st.markdown("---")

    # Only show sections for domains where time > 0
    active_domains = [d for d, m in st.session_state.step2_data.items() if m > 0]
    if not active_domains:
        st.info("No time logged for any domain today — you can still submit general data.")

    domain_data: dict[str, dict] = {}

    # ── Chess ──────────────────────────────────────────────────────────────────
    if "chess" in active_domains:
        with st.expander("♟️ Chess", expanded=True):
            # Auto-fetch from Chess.com
            if "chess_api_data" not in st.session_state:
                with st.spinner("Fetching Chess.com stats…"):
                    st.session_state.chess_api_data = fetch_today_chess_stats()
            api = st.session_state.chess_api_data

            if api["games_today"] > 0:
                st.caption(f"♟️ Found {api['games_today']} game(s) today on Chess.com — pre-filled below.")

        c1, c2, c3 = st.columns(3)
        with c1:
            wins   = st.number_input("Wins",   min_value=0, value=api["wins"],   key="chess_w")
            losses = st.number_input("Losses", min_value=0, value=api["losses"], key="chess_l")
            draws  = st.number_input("Draws",  min_value=0, value=api["draws"],  key="chess_d")
        with c2:
            current_rating = st.number_input("Current Rating", min_value=0, value=api["current_rating"], key="chess_cr")
            best_rating    = st.number_input("Best Rating",    min_value=0, value=api["best_rating"],    key="chess_br")
        with c3:
            goal_rating = st.number_input("Goal Rating", min_value=0, key="chess_gr")
        domain_data["chess"] = dict(
            wins=wins, losses=losses, draws=draws,
            current_rating=current_rating, best_rating=best_rating, goal_rating=goal_rating,
        )

    # ── Fitness ────────────────────────────────────────────────────────────────
    if "fitness" in active_domains:
        with st.expander("🏋️ Fitness", expanded=True):
            st.markdown("**Apple Watch / Scale**")
            c1, c2, c3 = st.columns(3)
            with c1:
                active_cal  = st.number_input("Active Calories", min_value=0, key="fit_ac")
                resting_hr  = st.number_input("Resting HR (bpm)", min_value=0, key="fit_hr")
            with c2:
                weight_lbs  = st.number_input("Weight (lbs)", min_value=0.0, format="%.1f", key="fit_wt")
                body_fat    = st.number_input("Body Fat %", min_value=0.0, max_value=100.0, format="%.1f", key="fit_bf")
            with c3:
                hrv         = st.number_input("HRV (ms)", min_value=0, key="fit_hrv")

            st.markdown("**Training Volume**")
            c4, c5, c6 = st.columns(3)
            with c4:
                run_dist_mi = st.number_input("Run Distance (mi)", min_value=0.0, format="%.2f", key="fit_rd")
                run_time_min= st.number_input("Run Time (min)",    min_value=0,   key="fit_rt")
            with c5:
                lift_sets   = st.number_input("Max Lift Sets",  min_value=0, key="fit_ls")
                lift_reps   = st.number_input("Max Lift Reps",  min_value=0, key="fit_lr")
            with c6:
                yoga_min    = st.number_input("Yoga Time (min)",       min_value=0, key="fit_yt")
                yoga_intensity = st.selectbox("Yoga Intensity", ["—", "Gentle", "Moderate", "Vigorous"], key="fit_yi")
            domain_data["fitness"] = dict(
                active_calories=active_cal, resting_hr=resting_hr,
                weight_lbs=weight_lbs, body_fat_pct=body_fat, hrv_ms=hrv,
                run_distance_mi=run_dist_mi, run_time_min=run_time_min,
                lift_sets=lift_sets, lift_reps=lift_reps,
                yoga_min=yoga_min, yoga_intensity=yoga_intensity,
            )

    # ── Research ───────────────────────────────────────────────────────────────
    if "research" in active_domains:
        with st.expander("🔬 Scientific Research", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                grants_app  = st.number_input("Grants Applied",    min_value=0, key="res_ga")
                grants_awd  = st.number_input("Grants Awarded",    min_value=0, key="res_gaw")
                fellow_app  = st.number_input("Fellowships Applied", min_value=0, key="res_fa")
                fellow_awd  = st.number_input("Fellowships Awarded", min_value=0, key="res_faw")
            with c2:
                pubs_sub    = st.number_input("Publications Submitted", min_value=0, key="res_ps")
                pubs_acc    = st.number_input("Publications Accepted",  min_value=0, key="res_pa")
                presentations = st.number_input("Presentations/Posters", min_value=0, key="res_pr")
                citations   = st.number_input("Total Citations",        min_value=0, key="res_ci")
            domain_data["research"] = dict(
                grants_applied=grants_app, grants_awarded=grants_awd,
                fellowships_applied=fellow_app, fellowships_awarded=fellow_awd,
                pubs_submitted=pubs_sub, pubs_accepted=pubs_acc,
                presentations=presentations, citations=citations,
            )

    # ── Music ──────────────────────────────────────────────────────────────────
    if "music" in active_domains:
        with st.expander("🎵 Music", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                casual_rep = st.number_input("Casual Repertoire (# songs)", min_value=0, key="mus_cr")
                soul_rep   = st.number_input("Soul Repertoire (# songs)",   min_value=0, key="mus_sr")
            with c2:
                exhibitions = st.number_input("Exhibitions / Gigs", min_value=0, key="mus_ex")
                songs_start = st.number_input("Songs Started",     min_value=0, key="mus_ss")
                songs_fin   = st.number_input("Songs Finished",    min_value=0, key="mus_sf")
            domain_data["music"] = dict(
                casual_repertoire=casual_rep, soul_repertoire=soul_rep,
                exhibitions=exhibitions, songs_started=songs_start, songs_finished=songs_fin,
            )

    # ── Visual Arts ────────────────────────────────────────────────────────────
    if "visual_arts" in active_domains:
        with st.expander("🎨 Visual Arts", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                pieces_start = st.number_input("Pieces Started",  min_value=0, key="va_ps")
                pieces_fin   = st.number_input("Pieces Finished", min_value=0, key="va_pf")
            with c2:
                exhibitions  = st.number_input("Exhibitions", min_value=0, key="va_ex")
                awards       = st.number_input("Awards",      min_value=0, key="va_aw")
            domain_data["visual_arts"] = dict(
                pieces_started=pieces_start, pieces_finished=pieces_fin,
                exhibitions=exhibitions, awards=awards,
            )

    # ── Gardening ──────────────────────────────────────────────────────────────
    if "gardening" in active_domains:
        with st.expander("🌱 Gardening", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                input_lbs   = st.number_input("Input (lbs seeds/starts)", min_value=0.0, format="%.2f", key="gard_i")
                yield_lbs   = st.number_input("Yield (lbs harvested)",    min_value=0.0, format="%.2f", key="gard_y")
            with c2:
                lifetime_yield = st.number_input("Lifetime Yield (lbs)", min_value=0.0, format="%.2f", key="gard_ly")
            domain_data["gardening"] = dict(input_lbs=input_lbs, yield_lbs=yield_lbs, lifetime_yield=lifetime_yield)

    # ── Cooking ────────────────────────────────────────────────────────────────
    if "cooking" in active_domains:
        with st.expander("🍳 Cooking", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                casual_rep = st.number_input("Casual Repertoire (# dishes)", min_value=0, key="cook_cr")
                soul_rep   = st.number_input("Soul Repertoire (# dishes)",   min_value=0, key="cook_sr")
            with c2:
                hosted = st.number_input("Hosted Meals", min_value=0, key="cook_hm")
            domain_data["cooking"] = dict(casual_repertoire=casual_rep, soul_repertoire=soul_rep, hosted_meals=hosted)

    # ── Art Criticism ──────────────────────────────────────────────────────────
    if "art_criticism" in active_domains:
        with st.expander("🎭 Art Criticism", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                films   = st.number_input("Film/TV Reviews (Letterboxd)",  min_value=0, key="ac_fi")
                books   = st.number_input("Book Reviews (StoryGraph)",      min_value=0, key="ac_bo")
            with c2:
                restaurants = st.number_input("Restaurant Reviews (Yelp)",  min_value=0, key="ac_re")
                music_rev   = st.number_input("Music Reviews (MusicBoard)", min_value=0, key="ac_mu")
            domain_data["art_criticism"] = dict(
                film_reviews=films, book_reviews=books,
                restaurant_reviews=restaurants, music_reviews=music_rev,
            )

    # ── Autodidactic ───────────────────────────────────────────────────────────
    if "autodidactic" in active_domains:
        with st.expander("📚 Autodidactic Studies", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                books_start = st.number_input("Books Started",  min_value=0, key="aut_bs")
                books_fin   = st.number_input("Books Finished", min_value=0, key="aut_bf")
            with c2:
                essays_start = st.number_input("Essays Started",    min_value=0, key="aut_es")
                essays_pub   = st.number_input("Essays Published",  min_value=0, key="aut_ep")
            domain_data["autodidactic"] = dict(
                books_started=books_start, books_finished=books_fin,
                essays_started=essays_start, essays_published=essays_pub,
            )

    # ── Languages ──────────────────────────────────────────────────────────────
    if "languages" in active_domains:
        with st.expander("🌐 Languages", expanded=True):
            language = st.text_input("Language", placeholder="e.g. Spanish", key="lang_lg")
            c1, c2 = st.columns(2)
            with c1:
                opic_score  = st.selectbox("OPIc Score", ["—","NL","NM","NH","IL","IM","IH","AL","AM","AH","S"], key="lang_op")
            with c2:
                app_minutes = st.number_input("Language App (min today)", min_value=0, key="lang_am")
            domain_data["languages"] = dict(language=language, opic_score=opic_score, app_minutes=app_minutes)

    # ── Finance ────────────────────────────────────────────────────────────────
    if "finance" in active_domains:
        with st.expander("💰 Personal Finance", expanded=True):
            if "ynab_data" not in st.session_state:
                with st.spinner("Fetching YNAB data…"):
                    st.session_state.ynab_data = fetch_finance_snapshot()
            api = st.session_state.ynab_data

            st.caption(f"💰 YNAB snapshot — income this month: ${api['monthly_income']:,.2f} · "
                   f"savings rate: {api['savings_rate_pct']:.1f}%")

            c1, c2 = st.columns(2)
            with c1:
                savings_rate = st.number_input("Savings Rate %",
                    min_value=0.0, max_value=100.0, format="%.1f",
                    value=float(api["savings_rate_pct"]), key="fin_sr")
            with c2:
                net_worth = st.number_input("Net Worth ($)",
                    min_value=0.0, format="%.2f",
                    value=float(api["net_worth"]), key="fin_nw")
            domain_data["finance"] = dict(savings_rate_pct=savings_rate, net_worth=net_worth)


def _submit(domain_data: dict):
    today = str(date.today())
    s1 = st.session_state.step1_data
    s2 = st.session_state.step2_data

    with st.spinner("Writing to Google Sheets…"):
        try:
            # Daily summary row
            daily_row = {
                "date":             today,
                "sleep_hours":      s1.get("sleep_hours", ""),
                "supplements":      s1.get("supplements", ""),
                "morning_routine":  s1.get("morning_routine", ""),
                "nightly_routine":  s1.get("nightly_routine", ""),
            }
            for domain in ALL_DOMAINS:
                daily_row[f"{domain}_min"] = s2.get(domain, 0)
            sheets.write_daily(daily_row)

            # Domain-specific rows
            tab_map = {
                "chess":         (sheets.TAB_CHESS,    ["wins","losses","draws","current_rating","best_rating","goal_rating"]),
                "fitness":       (sheets.TAB_FITNESS,  ["active_calories","resting_hr","weight_lbs","body_fat_pct","hrv_ms","run_distance_mi","run_time_min","lift_sets","lift_reps","yoga_min","yoga_intensity"]),
                "research":      (sheets.TAB_RESEARCH, ["grants_applied","grants_awarded","fellowships_applied","fellowships_awarded","pubs_submitted","pubs_accepted","presentations","citations"]),
                "music":         (sheets.TAB_MUSIC,    ["casual_repertoire","soul_repertoire","exhibitions","songs_started","songs_finished"]),
                "visual_arts":   (sheets.TAB_ARTS,     ["pieces_started","pieces_finished","exhibitions","awards"]),
                "gardening":     (sheets.TAB_GARDEN,   ["input_lbs","yield_lbs","lifetime_yield"]),
                "cooking":       (sheets.TAB_COOKING,  ["casual_repertoire","soul_repertoire","hosted_meals"]),
                "art_criticism": (sheets.TAB_CRITIC,   ["film_reviews","book_reviews","restaurant_reviews","music_reviews"]),
                "autodidactic":  (sheets.TAB_AUTODID,  ["books_started","books_finished","essays_started","essays_published"]),
                "languages":     (sheets.TAB_LANG,     ["language","opic_score","app_minutes"]),
                "finance":       (sheets.TAB_FINANCE,  ["savings_rate_pct","net_worth"]),
            }
            for domain, dd in domain_data.items():
                if domain in tab_map:
                    tab, headers = tab_map[domain]
                    sheets.write_domain(tab, headers, dd)

            st.success("✅ Entry saved! Great work today.")
            st.balloons()
            _reset()

        except Exception as e:
            st.error(f"Error writing to Google Sheets: {e}")
            st.info("Check your secrets.toml and Sheet permissions.")

# ── Navigation ────────────────────────────────────────────────────────────
    st.markdown("---")
    col_back, col_fwd = st.columns([1, 3])
    with col_back:
        if st.button("← Back"):
            _prev_step()
            st.rerun()
    with col_fwd:
        if st.button("✅ Submit Entry", use_container_width=True):
            _submit(domain_data)
            
# ── Main render ────────────────────────────────────────────────────────────────

def render():
    _init_state()

    # Progress indicator
    step = st.session_state.entry_step
    progress_labels = ["1 · Sleep & Health", "2 · Time Logged", "3 · Domain Metrics"]
    cols = st.columns(3)
    for i, label in enumerate(progress_labels):
        with cols[i]:
            color = "#C8A96E" if i + 1 == step else ("#555" if i + 1 > step else "#4a7c59")
            st.markdown(
                f'<div style="text-align:center;padding:6px;border-radius:4px;'
                f'background:#1a1a1a;border:1px solid {color};color:{color};'
                f'font-family:Cinzel,serif;font-size:0.8em;">{label}</div>',
                unsafe_allow_html=True,
            )
    st.markdown("<br>", unsafe_allow_html=True)

    if   step == 1: _step1()
    elif step == 2: _step2()
    elif step == 3: _step3()
