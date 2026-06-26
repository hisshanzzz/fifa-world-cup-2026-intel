"""Feature engineering for the match predictor.

We turn raw historical results into per-team strength/form signals, then build a
feature row for any (home, away) pairing. Keeping this in one place means the
training code and the live prediction code featurize matches *identically*.
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

FEATURE_COLS = [
    "rating_diff",
    "home_rating",
    "away_rating",
    "home_form",
    "away_form",
    "home_gf",
    "home_ga",
    "away_gf",
    "away_ga",
    "same_confed",
]


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    teams = pd.read_csv(os.path.join(DATA, "teams.csv"))
    history = pd.read_csv(os.path.join(DATA, "matches_history.csv"))
    return teams, history


def team_stats(teams: pd.DataFrame, history: pd.DataFrame, form_window: int = 8) -> pd.DataFrame:
    """Aggregate per-team rating, goals for/against, and recent form (pts/game)."""
    ratings = teams.set_index("team")["rating"].to_dict()
    confed = teams.set_index("team")["confederation"].to_dict()

    rows = []
    for team in teams["team"]:
        played = history[(history.home == team) | (history.away == team)].copy()
        played = played.sort_values("date")
        gf, ga, pts = [], [], []
        for _, m in played.iterrows():
            if m.home == team:
                gf.append(m.home_goals); ga.append(m.away_goals)
                pts.append(3 if m.result == "H" else (1 if m.result == "D" else 0))
            else:
                gf.append(m.away_goals); ga.append(m.home_goals)
                pts.append(3 if m.result == "A" else (1 if m.result == "D" else 0))
        recent_pts = pts[-form_window:] if pts else [0]
        rows.append({
            "team": team,
            "rating": ratings[team],
            "confederation": confed[team],
            "gf": float(np.mean(gf)) if gf else 1.0,
            "ga": float(np.mean(ga)) if ga else 1.0,
            "form": float(np.mean(recent_pts)) if recent_pts else 0.0,
        })
    return pd.DataFrame(rows).set_index("team")


def featurize(stats: pd.DataFrame, home: str, away: str) -> dict:
    h, a = stats.loc[home], stats.loc[away]
    return {
        "rating_diff": h.rating - a.rating,
        "home_rating": h.rating,
        "away_rating": a.rating,
        "home_form": h.form,
        "away_form": a.form,
        "home_gf": h.gf,
        "home_ga": h.ga,
        "away_gf": a.gf,
        "away_ga": a.ga,
        "same_confed": int(h.confederation == a.confederation),
    }


def build_training_frame(teams: pd.DataFrame, history: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    stats = team_stats(teams, history)
    X_rows, y = [], []
    for _, m in history.iterrows():
        if m.home not in stats.index or m.away not in stats.index:
            continue
        X_rows.append(featurize(stats, m.home, m.away))
        y.append(m.result)
    X = pd.DataFrame(X_rows)[FEATURE_COLS]
    return X, pd.Series(y, name="result")
