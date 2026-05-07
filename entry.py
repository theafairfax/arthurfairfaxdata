"""
pages/entry.py — Arthur Fairfax · 3-step daily data entry flow.
Step 1: Sleep / Supplements / Routines
Step 2: Time per domain (pre-filled from Google Calendar)
Step 3: Arete — Domain-specific metrics & cultural consumption
"""
from __future__ import annotations

from datetime import date, datetime, time

import streamlit as st

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

# entry.py

# [ ... Step 1 and Step 2 remain as they are ... ]

def _step3():
    st.markdown("## Step 3 of 3 — Arete")
    st.markdown("*Categorize the labor performed in each active domain.*")
    st.markdown("---")

    active_domains = [d for d, m in st.session_state.step2_data.items() if m > 0]
    domain_data: dict[str, dict] = {}

    LABOR_CATEGORIES = {
        "research": ["Bench", "Coursework", "Literature"],
        "music": ["Technique", "Creation", "Teaching", "DAW"],
        "arts": ["Visual Arts", "Photography", "Poetry"],
        "languages": ["German", "Spanish", "Russian"],
        "autodidactic": ["Reading", "Writing", "Criticism"],
        "cooking": ["Old", "New", "Hosting"],
        "fitness": ["Yoga", "Resistance", "Calisthenic", "Cardio"],
        "industrial": ["Gardening", "Restoration", "Construction", "Engineering", "Business"]
    }

    for domain in active_domains:
        if domain in ["chess", "framework"]:
            domain_data[domain] = {}
            continue

        if domain in LABOR_CATEGORIES:
            with st.expander(f"{DOMAIN_ICONS[domain]} {DOMAIN_LABELS[domain]}", expanded=True):
                options = LABOR_CATEGORIES[domain]
                selected = st.multiselect(f"Labor Type ({DOMAIN_LABELS[domain]})", options, key=f"lab_{domain}")
                domain_data[domain] = {"labor_type": ", ".join(selected)}

    # ── Cultural Consumption ───────────────────────────────────────────────────
    with st.expander("🎬 Cultural Consumption", expanded=True):
        st.markdown("*Select all kinds of cultural products consumed today.*")

        CULTURAL_TYPES = {
            "film":       ("🎬", "Film",        "Title of film watched"),
            "tv":         ("📺", "TV Series",   "Title of series watched"),
            "book":       ("📖", "Book",        "Title of book read"),
            "music":      ("🎵", "Music",       "Artist / album / song listened to"),
            "restaurant": ("🍽️", "Restaurant",  "Name of restaurant visited"),
        }

        selected_types = st.multiselect(
            "Select types",
            options=list(CULTURAL_TYPES.keys()),
            format_func=lambda k: f"{CULTURAL_TYPES[k][0]} {CULTURAL_TYPES[k][1]}",
            key="cult_types",
        )

        cultural_entries: list[dict] = []

        for ct in selected_types:
            icon, label, placeholder = CULTURAL_TYPES[ct]
            st.markdown(f"**{icon} {label}**")

            if f"cult_{ct}_count" not in st.session_state:
                st.session_state[f"cult_{ct}_count"] = 1

            for idx in range(st.session_state[f"cult_{ct}_count"]):
                c1, c2 = st.columns([3, 1])
                with c1:
                    title = st.text_input(f"Title #{idx+1}", placeholder=placeholder, key=f"cult_{ct}_{idx}_t", label_visibility="collapsed")
                with c2:
                    reviewed = st.selectbox("Review?", ["No", "Yes"], key=f"cult_{ct}_{idx}_r", label_visibility="collapsed")
                if title:
                    cultural_entries.append({"type": label, "title": title, "review_left": reviewed})

            if st.button(f"+ Add {label}", key=f"cult_{ct}_add"):
                st.session_state[f"cult_{ct}_count"] += 1
                st.rerun()

    # ── Navigation ────────────────────────────────────────────────────────────
    st.markdown("---")
    col_back, col_fwd = st.columns([1, 3])
    with col_back:
        if st.button("← Back"):
            _prev_step()
            st.rerun()
    with col_fwd:
        if st.button("✅ Submit Entry", use_container_width=True):
            _submit(domain_data, cultural_entries)

def _submit(domain_data: dict, cultural_entries: list | None = None):
    today = str(date.today())
    s1 = st.session_state.step1_data
    s2 = st.session_state.step2_data

    with st.spinner("Writing to Google Sheets…"):
        try:
            # 1. Daily summary row
            daily_row = {
                "date": today,
                "sleep_hours": s1.get("sleep_hours", ""),
                "supplements": s1.get("supplements", ""),
                "morning_routine": s1.get("morning_routine", ""),
                "nightly_routine": s1.get("nightly_routine", ""),
            }
            for domain in ALL_DOMAINS:
                daily_row[f"{domain}_min"] = s2.get(domain, 0)
            sheets.write_daily(daily_row)

            # 2. Cultural consumption rows
            if cultural_entries:
                for entry in cultural_entries:
                    sheets.write_domain(
                        sheets.TAB_CULTURAL,
                        ["date", "type", "title", "review_left"],
                        {"date": today, **entry},
                    )

            # 3. Domain-specific rows (Simplified to "labor_type" only)
            tab_map = {
                "chess":         (sheets.TAB_CHESS,    []),
                "fitness":       (sheets.TAB_FITNESS,  ["labor_type"]),
                "research":      (sheets.TAB_RESEARCH, ["labor_type"]),
                "music":         (sheets.TAB_MUSIC,    ["labor_type"]),
                "arts":          (sheets.TAB_ARTS,     ["labor_type"]),
                "cooking":       (sheets.TAB_COOKING,  ["labor_type"]),
                "languages":     (sheets.TAB_LANG,     ["labor_type"]),
                "industrial":    (sheets.TAB_INDUSTRIAL, ["labor_type"]),
                "autodidactic":  (sheets.TAB_AUTODID,    ["labor_type"]),
                "framework":     (sheets.TAB_FRAMEWORK,  []),
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

# ── Main render ────────────────────────────────────────────────────────────────

def render():
    _init_state()
    step = st.session_state.entry_step
    progress_labels = ["1 · Sleep & Health", "2 · Time Logged", "3 · Arete"]
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
