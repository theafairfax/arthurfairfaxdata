"""
utils/sheets.py — Google Sheets read/write via gspread + service account.
"""
import json
from datetime import date
from typing import Any

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

# ── Tab names (must match your Google Sheet exactly) ──────────────────────────
TAB_DAILY    = "Daily"
TAB_CV       = "Main Tab"      # ← CV sheet tab name — update if yours differs
TAB_CULTURAL = "Cultural"
TAB_CHESS    = "Chess"
TAB_FITNESS = "Fitness"
TAB_RESEARCH= "Research"
TAB_MUSIC   = "Music"
TAB_ARTS    = "Arts"
TAB_COOKING = "Cooking"
TAB_AUTODID = "Autodidactic"
TAB_LANG    = "Languages"
TAB_INDUSTRIAL = "Industrial" # Replaced TAB_GARDEN
TAB_FRAMEWORK  = "Framework"  # Added
TAB_ASPIRATIONS = "Aspirations"


@st.cache_resource(show_spinner=False)
def get_sheet_client() -> gspread.Client:
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(creds)


def get_spreadsheet() -> gspread.Spreadsheet:
    client = get_sheet_client()
    return client.open_by_key(st.secrets["google"]["spreadsheet_id"])


def get_or_create_tab(spreadsheet: gspread.Spreadsheet, tab_name: str) -> gspread.Worksheet:
    try:
        return spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=30)
        return ws


def ensure_header(ws: gspread.Worksheet, headers: list[str]) -> None:
    """Write header row if the sheet is empty."""
    if not ws.row_values(1):
        ws.append_row(headers)


def append_row(tab_name: str, row: list[Any]) -> None:
    ss = get_spreadsheet()
    ws = get_or_create_tab(ss, tab_name)
    ws.append_row(row, value_input_option="USER_ENTERED")


def read_all(tab_name: str) -> list[dict]:
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(tab_name)
        records = ws.get_all_records()
        return records
    except gspread.WorksheetNotFound:
        return []


# ── High-level write helpers ───────────────────────────────────────────────────

def get_last_target_wake_time() -> str:
    """Retrieves the target wake-up time set in the most recent Daily entry."""
    records = read_all(TAB_DAILY)
    if not records:
        return ""
    # Find the latest record with a set target_wake_time
    for record in reversed(records):
        target = record.get("target_wake_time")
        if target:
            return str(target)
    return ""
    
def write_daily(data: dict) -> None:
    ss = get_spreadsheet()
    # ADD THIS LINE: Define the worksheet 'ws' before using it below
    ws = get_or_create_tab(ss, TAB_DAILY)
    
    headers = [
        "date", "sleep_hours", "supplements", "morning_routine", "nightly_routine",
        "chess_min", "fitness_min", "research_min", "music_min",
        "arts_min", "industrial_min", "cooking_min",
        "autodidactic_min", "languages_min", "framework_min"
    ]
    
    # Now 'ws' is defined and can be passed to ensure_header
    ensure_header(ws, headers)
    row = [data.get(h, "") for h in headers]
    ws.append_row(row, value_input_option="USER_ENTERED")


# sheets.py

# utils/sheets.py


def write_domain(tab_name: str, headers: list[str], data: dict) -> None:
    ss = get_spreadsheet()
    # Ensure the worksheet is defined as 'ws'
    ws = get_or_create_tab(ss, tab_name) 
    
    # Now ws is defined and can be passed to ensure_header
    ensure_header(ws, ["date"] + headers)
    
    row = [str(date.today())] + [data.get(h, "") for h in headers]
    ws.append_row(row, value_input_option="USER_ENTERED")

def update_aspiration_status(title: str, new_status: str) -> bool:
    """Finds an aspiration by title and updates its Status cell."""
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(TAB_ASPIRATIONS)
        records = ws.get_all_records()
        headers = ws.row_values(1)
        
        if "Title" not in headers or "Status" not in headers:
            return False
            
        title_col_idx = headers.index("Title")
        status_col_idx = headers.index("Status") + 1 # 1-based index
        
        for idx, row in enumerate(records):
            # ws.get_all_records() shifts row references down by 2 (1 for header, 1 for 0-indexing)
            if str(row.get("Title")).strip() == str(title).strip():
                row_to_update = idx + 2
                ws.update_cell(row_to_update, status_col_idx, new_status)
                return True
        return False
    except Exception:
        return False
