"""Group players by playing style with KMeans.

We cluster on per-90 style signals (not raw volume), standardise them, then
auto-label each cluster from its dominant standardised features so the labels
read like scouting tags ("Finisher", "Creator", "Ball-winner", ...).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

STYLE_FEATURES = [
    "goals90", "assists90", "shots90", "key_passes90",
    "dribbles90", "tackles90", "interceptions90",
]

# Human-readable tag for whichever standardised feature dominates a cluster.
FEATURE_TAGS = {
    "goals90": "Finisher",
    "shots90": "Volume Shooter",
    "assists90": "Creator",
    "key_passes90": "Playmaker",
    "dribbles90": "Dribble-Carrier",
    "tackles90": "Ball-Winner",
    "interceptions90": "Interceptor",
}


def cluster_players(df: pd.DataFrame, k: int = 5, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    X = df[STYLE_FEATURES].fillna(0.0).values
    Xs = StandardScaler().fit_transform(X)

    km = KMeans(n_clusters=k, random_state=seed, n_init=10)
    df["cluster"] = km.fit_predict(Xs)

    # centroid in standardised space -> dominant feature -> label
    centers = pd.DataFrame(km.cluster_centers_, columns=STYLE_FEATURES)
    labels = {}
    used = set()
    for c in centers.index:
        ranked = centers.loc[c].sort_values(ascending=False)
        tag = "All-Rounder"
        for feat in ranked.index:
            cand = FEATURE_TAGS.get(feat)
            if cand and cand not in used and ranked[feat] > 0.25:
                tag, _ = cand, used.add(cand)
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
