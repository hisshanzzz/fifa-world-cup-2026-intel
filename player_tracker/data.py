"""Load player stats, normalise to per-90, and compute an Impact Score.

Data source: data/players.csv (bundled). Drop in a real export with the same
columns (e.g. from FBref / a free Kaggle World Cup dataset) and everything works
unchanged -- that's the "pull real world cup stats" hook.

Impact Score is a transparent, weighted blend of attacking output, creation,
and defensive work, all on a per-90 basis so subs and starters compare fairly.
"""
from __future__ import annotations

import os
import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PLAYERS = os.path.join(DATA, "players.csv")

PER90 = ["goals", "assists", "shots", "key_passes", "dribbles", "tackles", "interceptions", "xg", "xa"]

# Impact weights (per-90). Goals & assists dominate, creation/defense contribute.
WEIGHTS = {
    "goals90": 3.5,
    "assists90": 2.5,
    "xg90": 1.5,
    "xa90": 1.2,
    "key_passes90": 0.8,
    "dribbles90": 0.4,
    "tackles90": 0.5,
    "interceptions90": 0.5,
}


def load_players() -> pd.DataFrame:
    df = pd.read_csv(PLAYERS)
    nineties = (df["minutes"] / 90.0).clip(lower=0.5)  # avoid divide-by-tiny
    for col in PER90:
        df[f"{col}90"] = df[col] / nineties
    df["nineties"] = nineties.round(2)
    return df


def add_impact(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["impact_raw"] = sum(df[f"{k}"] * w for k, w in WEIGHTS.items())
    # scale 0-100 for readability
    lo, hi = df["impact_raw"].min(), df["impact_raw"].max()
    span = (hi - lo) or 1.0
    df["impact"] = ((df["impact_raw"] - lo) / span * 100).round(1)
    return df


def leaderboard(df: pd.DataFrame, by: str = "impact", top: int = 20) -> pd.DataFrame:
    cols = ["name", "team", "position", "minutes", "goals", "assists",
            "key_passes", "impact"]
    return df.sort_values(by, ascending=False)[cols].head(top).reset_index(drop=True)


def get_player_frame() -> pd.DataFrame:
    return add_impact(load_players())


if __name__ == "__main__":
    d = get_player_frame()
    print("Top 15 by Impact Score:")
    print(leaderboard(d, top=15).to_string(index=False))
