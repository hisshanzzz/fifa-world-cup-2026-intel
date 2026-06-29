"""Group scorers by their REAL scoring profile with KMeans.

Features are all derived from real goal data: how often they score, penalty
reliance, how late their goals come, how early, and how many multi-goal games.
Clusters are auto-labelled from the dominant standardised feature so they read
like scouting tags ("Penalty Specialist", "Clutch Finisher", ...).
"""
from __future__ import annotations

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

STYLE_FEATURES = [
    "goals_per_match", "penalty_share", "late_share",
    "first_half_share", "avg_goal_minute", "multi_goal_games",
]

FEATURE_TAGS = {
    "penalty_share": "Penalty Specialist",
    "late_share": "Clutch Finisher",
    "first_half_share": "Fast Starter",
    "goals_per_match": "Prolific Scorer",
    "multi_goal_games": "Multi-Goal Threat",
    "avg_goal_minute": "Late-Game Scorer",
}


def cluster_players(df: pd.DataFrame, k: int = 5, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    X = df[STYLE_FEATURES].fillna(0.0).values
    Xs = StandardScaler().fit_transform(X)

    km = KMeans(n_clusters=k, random_state=seed, n_init=10)
    df["cluster"] = km.fit_predict(Xs)

    centers = pd.DataFrame(km.cluster_centers_, columns=STYLE_FEATURES)
    labels, used = {}, set()
    for c in centers.index:
        ranked = centers.loc[c].sort_values(ascending=False)
        tag = "Squad Contributor"
        for feat in ranked.index:
            cand = FEATURE_TAGS.get(feat)
            if cand and cand not in used and ranked[feat] > 0.25:
                tag = cand
                used.add(cand)
                break
        labels[c] = tag
    df["style"] = df["cluster"].map(labels)
    centers["style"] = centers.index.map(labels)
    return df, centers


if __name__ == "__main__":
    from .data import get_player_frame
    d, centers = cluster_players(get_player_frame())
    print("Cluster sizes / styles:")
    print(d.groupby("style").size().to_string())
    print("\nStyle centroids (standardised):")
    print(centers.round(2).to_string(index=False))
