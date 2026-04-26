"""
utils/xp.py — XP and level calculations.

XP = total hours spent on a domain since inception.
Level formula: level = floor(sqrt(total_hours)) + 1
This gives a satisfying RPG-like curve that slows as you advance.
"""
import math
from dataclasses import dataclass


@dataclass
class LevelInfo:
    domain: str
    total_minutes: int
    total_hours: float
    level: int
    xp_this_level: float      # hours into current level
    xp_next_level: float      # hours needed to reach next level
    progress_pct: float       # 0–100


def compute_level(total_minutes: int) -> LevelInfo:
    raise NotImplementedError("Use domain_level_info instead")


def domain_level_info(domain: str, total_minutes: int) -> LevelInfo:
    hours = total_minutes / 60.0

    # Level = floor(sqrt(hours)) + 1, min level 1
    level = max(1, math.floor(math.sqrt(hours)) + 1)

    # Hours required to reach current level start and next level start
    hours_at_level     = (level - 1) ** 2
    hours_at_next      = level ** 2
    xp_this_level      = hours - hours_at_level
    xp_needed          = hours_at_next - hours_at_level   # always = 2*level - 1
    progress_pct       = min(100.0, (xp_this_level / xp_needed) * 100) if xp_needed > 0 else 100.0

    return LevelInfo(
        domain=domain,
        total_minutes=total_minutes,
        total_hours=round(hours, 1),
        level=level,
        xp_this_level=round(xp_this_level, 2),
        xp_next_level=round(xp_needed, 2),
        progress_pct=round(progress_pct, 1),
    )


DOMAIN_ICONS: dict[str, str] = {
    "chess":         "♟️",
    "fitness":       "🏋️",
    "research":      "🔬",
    "music":         "🎵",
    "visual_arts":   "🎨",
    "gardening":     "🌱",
    "cooking":       "🍳",
    "art_criticism": "🎭",
    "autodidactic":  "📚",
    "languages":     "🌐",
}

DOMAIN_LABELS: dict[str, str] = {
    "chess":         "Chess",
    "fitness":       "Fitness",
    "research":      "Scientific Research",
    "music":         "Music",
    "visual_arts":   "Visual Arts",
    "gardening":     "Gardening",
    "cooking":       "Cooking",
    "art_criticism": "Art Criticism",
    "autodidactic":  "Autodidactic Studies",
    "languages":     "Languages",
}

ALL_DOMAINS = list(DOMAIN_LABELS.keys())
