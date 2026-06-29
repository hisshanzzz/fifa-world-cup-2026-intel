"""Glue: score a match's tweets and build the per-minute sentiment timeline."""
from __future__ import annotations

import pandas as pd

from .ingest import goal_minutes, tweets_for_match
from .sentiment import get_backend, label

_CACHE: dict[str, pd.DataFrame] = {}


def score_match(match_id: str) -> pd.DataFrame:
    """Score every tweet for a match once; cached per process."""
    if match_id in _CACHE:
        return _CACHE[match_id]
    df = tweets_for_match(match_id)
    be = get_backend()
    df["polarity"] = [be.polarity(t) for t in df.text]
    df["sentiment"] = df["polarity"].map(label)
    _CACHE[match_id] = df
    return df


def timeline(match_id: str, upto_minute: int | None = None) -> pd.DataFrame:
    """Rolling mean polarity per team per match-minute (up to `upto_minute`)."""
    df = score_match(match_id)
    if upto_minute is not None:
        df = df[df.match_minute <= upto_minute]
    if df.empty:
        return pd.DataFrame(columns=["match_minute", "team", "polarity", "rolling"])
    agg = (df.groupby(["match_minute", "team"])["polarity"].mean()
             .reset_index().sort_values("match_minute"))
    agg["rolling"] = (agg.groupby("team")["polarity"]
                        .transform(lambda s: s.rolling(5, min_periods=1).mean()))
    return agg


def current_split(match_id: str, upto_minute: int | None = None) -> pd.DataFrame:
    df = score_match(match_id)
    if upto_minute is not None:
        df = df[df.match_minute <= upto_minute]
    return (df.groupby("sentiment").size()
              .reindex(["positive", "neutral", "negative"], fill_value=0)
              .rename("count").reset_index())


def goals(match_id: str) -> list[int]:
    return goal_minutes(match_id)


if __name__ == "__main__":
    from .ingest import list_matches_with_tweets
    mid = list_matches_with_tweets().iloc[0].match_id
    print(f"Scoring {mid} ...")
    tl = timeline(mid)
    print(tl.tail(10).to_string(index=False))
    print("\nFinal split:")
    print(current_split(mid).to_string(index=False))
    print(f"Goal minutes: {goals(mid)}")
