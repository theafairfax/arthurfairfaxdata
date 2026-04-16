"""
utils/calendar.py — Fetch today's events from Google Calendar and map them
to tracker domains by keyword matching.
"""
import json
import os
import pickle
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import streamlit as st

# Domain keyword mapping — extend freely
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "chess":          ["chess", "lichess", "chess.com"],
    "fitness":        ["gym", "run", "yoga", "lift", "workout", "crossfit", "swim", "bike", "training"],
    "finance":        ["finance", "budget", "invest", "portfolio", "money", "savings"],
    "research":       ["research", "lab", "experiment", "paper", "grant", "fellowship", "conference", "poster"],
    "music":          ["music", "guitar", "piano", "practice", "jam", "rehearsal", "gig"],
    "visual_arts":    ["art", "paint", "draw", "sketch", "studio", "sculpture"],
    "gardening":      ["garden", "plant", "prune", "harvest", "compost", "seed"],
    "cooking":        ["cook", "meal prep", "bake", "recipe", "kitchen"],
    "art_criticism":  ["letterboxd", "storygraph", "yelp", "musicboard", "review", "film", "movie", "book club"],
    "autodidactic": ["study", "read", "course", "book", "essay", "lecture", "autodidactic"],
    "languages":      ["spanish", "french", "german", "japanese", "mandarin", "duolingo", "anki", "language"],
}

TOKEN_PATH = Path("/tmp/gcal_token.pkl")


def _build_service():
    """Build the Google Calendar service.  Handles both OAuth2 (local) and
    service-account-impersonation patterns.  For Streamlit Cloud we store
    the token as a Streamlit secret."""
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        # Try service account first (server-side deployment)
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        )
        return build("calendar", "v3", credentials=creds)
    except Exception:
        pass

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        import google.oauth2.credentials

        SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
        creds = None

        if TOKEN_PATH.exists():
            with open(TOKEN_PATH, "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                cred_json = json.loads(st.secrets["google"]["calendar_credentials_json"])
                flow = InstalledAppFlow.from_client_config(cred_json, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, "wb") as f:
                pickle.dump(creds, f)

        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        st.warning(f"Google Calendar unavailable: {e}")
        return None


def fetch_today_domain_minutes(target_date: Optional[date] = None) -> dict[str, int]:
    """
    Returns a dict mapping domain name → total minutes from Google Calendar events today.
    Falls back to zeros if Calendar is unreachable.
    """
    target = target_date or date.today()
    TZ = timezone(timedelta(hours=-6))
    start = datetime(target.year, target.month, target.day, 0, 0, 0, tzinfo=TZ).isoformat()
    end   = datetime(target.year, target.month, target.day, 23, 59, 59, tzinfo=TZ).isoformat()

    domain_minutes: dict[str, int] = {k: 0 for k in DOMAIN_KEYWORDS}

    service = _build_service()
    if service is None:
        return domain_minutes

    try:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=start,
            timeMax=end,
            singleEvents=True,
            orderBy="startTime",
            maxResults=50,
        ).execute()

        events = events_result.get("items", [])
        st.write(f"DEBUG: Found {len(events)} events")
        for event in events:
            st.write(f"DEBUG event: {event.get('summary')} | start: {event.get('start')}")

        for event in events_result.get("items", []):
            summary = (event.get("summary") or "").lower()
            description = (event.get("description") or "").lower()
            text = summary + " " + description

            # Calculate duration
            s = event.get("start", {})
            e = event.get("end", {})
            if "dateTime" in s and "dateTime" in e:
                dt_start = datetime.fromisoformat(s["dateTime"])
                dt_end   = datetime.fromisoformat(e["dateTime"])
                duration_min = int((dt_end - dt_start).total_seconds() / 60)
            else:
                duration_min = 0

            # Assign to first matching domain
            for domain, keywords in DOMAIN_KEYWORDS.items():
                if any(kw in text for kw in keywords):
                    domain_minutes[domain] += duration_min
                    break

    except Exception as e:
        st.warning(f"Could not fetch Calendar events: {e}")

    return domain_minutes
