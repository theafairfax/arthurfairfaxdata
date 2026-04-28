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
TAB_DAILY   = "Daily"
TAB_CV      = "Main Tab"      # ← CV sheet tab name — update if yours differs
TAB_CHESS   = "Chess"
TAB_FITNESS = "Fitness"
TAB_FINANCE = "Finance"
TAB_RESEARCH= "Research"
TAB_MUSIC   = "Music"
TAB_ARTS    = "VisualArts"
TAB_GARDEN  = "Gardening"
TAB_COOKING = "Cooking"
TAB_CRITIC  = "ArtCriticism"
TAB_AUTODID = "Autodidactic"
TAB_LANG    = "Languages"


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

def write_daily(data: dict) -> None:
    ss = get_spreadsheet()
    ws = get_or_create_tab(ss, TAB_DAILY)
    headers = [
        "date", "sleep_hours", "supplements", "morning_routine", "nightly_routine",
        "chess_min", "fitness_min", "research_min", "music_min",
        "visual_arts_min", "gardening_min", "cooking_min", "art_criticism_min",
        "autodidactic_min", "languages_min",
    ]
    ensure_header(ws, headers)
    row = [data.get(h, "") for h in headers]
    ws.append_row(row, value_input_option="USER_ENTERED")


def write_domain(tab_name: str, headers: list[str], data: dict) -> None:
    ss = get_spreadsheet()
    ws = get_or_create_tab(ss, tab_name)
    ensure_header(ws, ["date"] + headers)
    row = [str(date.today())] + [data.get(h, "") for h in headers]
    ws.append_row(row, value_input_option="USER_ENTERED")
