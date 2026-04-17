"""
chess_api.py — Fetch today's Chess.com games for a given username.
"""
from datetime import date
from typing import Optional
import requests
import streamlit as st

CHESS_COM_USERNAME = "arthurfairfax"
HEADERS = {"User-Agent": "arthurfairfax-life-tracker/1.0"}


def fetch_today_chess_stats(username: str = CHESS_COM_USERNAME) -> dict:
    """
    Fetches today's games from Chess.com and returns aggregated stats:
    wins, losses, draws, current rating, best rating.
    """
    today = date.today()
    year  = today.strftime("%Y")
    month = today.strftime("%m")

    result = {
        "wins": 0, "losses": 0, "draws": 0,
        "current_rating": 0, "best_rating": 0,
        "games_today": 0,
    }

    try:
        # Fetch this month's games archive
        url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            st.warning(f"Chess.com API returned {resp.status_code}")
            return result

        games = resp.json().get("games", [])

        # Filter to today's games only
        today_str = today.isoformat()
        todays_games = [
            g for g in games
            if date.fromtimestamp(g.get("end_time", 0)).isoformat() == today_str
        ]

        result["games_today"] = len(todays_games)
        best_rating = 0

        for game in todays_games:
            # Determine which color the user played
            white = game.get("white", {})
            black = game.get("black", {})

            if white.get("username", "").lower() == username.lower():
                player = white
                opponent = black
            else:
                player = black
                opponent = white

            outcome = player.get("result", "")
            rating  = player.get("rating", 0)

            if outcome == "win":
                result["wins"] += 1
            elif outcome in ("checkmated", "resigned", "timeout", "abandoned"):
                result["losses"] += 1
            elif outcome in ("agreed", "stalemate", "repetition", "insufficient",
                             "timevsinsufficient", "50move"):
                result["draws"] += 1

            if rating > best_rating:
                best_rating = rating
            result["current_rating"] = rating  # last game's rating = most recent

        result["best_rating"] = best_rating

    except Exception as e:
        st.warning(f"Could not fetch Chess.com data: {e}")

    return result
