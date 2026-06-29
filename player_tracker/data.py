"""Load REAL 2026 World Cup goalscorer data and compute an Impact Score.

Source: data/players.csv, built by data/fetch_real_data.py from the public
martj42 `goalscorers.csv` (every goal: scorer, minute, penalty, own-goal).

What's real here: goals, penalty vs open-play split, goal minutes (so late /
first-half goals), matches scored in, and multi-goal games. What is NOT available
for free without scraping (assists, shots, xG, defensive actions) is intentionally
left out rather than faked -- drop in an FBref export to extend this.

Impact Score is a transparent weighting of real scoring contribution.
"""
from __future__ import annotations

import os
import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PLAYERS = os.path.join(DATA, "players.csv")

# Impact weights over REAL scoring signals.
WEIGHTS = {
    "open_play_goals": 3.0,  # open-play goals are worth most
    "penalty_goals": 1.8,    # penalties count, but less
    "late_goals": 1.2,       # goals from 75' onward (clutch)
    "multi_goal_games": 1.5,  # braces / hat-tricks
}


def load_players() -> pd.DataFrame:
    df = pd.read_csv(PLAYERS)
    df["goals_per_match"] = (df["goals"] / df["matches_scored"]).round(2)
    df["penalty_share"] = (df["penalty_goals"] / df["goals"]).round(3)
    df["late_share"] = (df["late_goals"] / df["goals"]).round(3)
    df["first_half_share"] = (df["first_half_goals"] / df["goals"]).round(3)
    return df


def add_impact(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["impact_raw"] = sum(df[k] * w for k, w in WEIGHTS.items())
    lo, hi = df["impact_raw"].min(), df["impact_raw"].max()
    span = (hi - lo) or 1.0
    df["impact"] = ((df["impact_raw"] - lo) / span * 100).round(1)
    return df


def leaderboard(df: pd.DataFrame, by: str = "impact", top: int = 20) -> pd.DataFrame:
    cols = ["name", "team", "goals", "open_play_goals", "penalty_goals",
            "late_goals", "matches_scored", "multi_goal_games", "impact"]
    return df.sort_values(by, ascending=False)[cols].head(top).reset_index(drop=True)


def get_player_frame() -> pd.DataFrame:
    return add_impact(load_players())


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # player names contain non-ASCII
    except Exception:
        pass
    d = get_player_frame()
    print("Top 15 World Cup 2026 scorers by Impact Score:")
    print(leaderboard(d, top=15).to_string(index=False))
