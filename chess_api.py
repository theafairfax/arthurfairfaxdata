"""
chess_api.py — Fetch Chess.com rapid stats for a given username.
"""
from typing import Optional
import requests
import streamlit as st

CHESS_COM_USERNAME = "arthurfairfax"
HEADERS = {"User-Agent": "arthurfairfax-life-tracker/1.0"}


def fetch_rapid_chess_stats(username: str = CHESS_COM_USERNAME) -> dict:
    """
    Fetches all-time rapid stats from Chess.com and returns:
    wins, losses, draws, w/l/d ratio, current rapid rating, best rapid rating.
    """
    result = {
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "win_ratio": 0.0,
        "loss_ratio": 0.0,
        "draw_ratio": 0.0,
        "current_rating": 0,
        "best_rating": 0,
    }

    try:
        url = f"https://api.chess.com/pub/player/{username}/stats"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            st.warning(f"Chess.com API returned {resp.status_code}")
            return result

        data = resp.json()
        rapid = data.get("chess_rapid", {})

        if not rapid:
            st.warning("No rapid chess data found for this account.")
            return result

        # All-time record
        record = rapid.get("record", {})
        wins   = record.get("win", 0)
        losses = record.get("loss", 0)
        draws  = record.get("draw", 0)
        total  = wins + losses + draws

        result["wins"]   = wins
        result["losses"] = losses
        result["draws"]  = draws

        if total > 0:
            result["win_ratio"]  = round(wins   / total, 4)
            result["loss_ratio"] = round(losses / total, 4)
            result["draw_ratio"] = round(draws  / total, 4)

        # Current and best rapid rating
        last   = rapid.get("last", {})
        best   = rapid.get("best", {})
        result["current_rating"] = last.get("rating", 0)
        result["best_rating"]    = best.get("rating", 0)

    except Exception as e:
        st.warning(f"Could not fetch Chess.com data: {e}")

    return result
