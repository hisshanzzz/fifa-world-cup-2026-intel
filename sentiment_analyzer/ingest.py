"""Tweet ingestion with a live-X-API path and a free replay path.

- If X/Twitter API keys exist in the environment, `live_search` uses tweepy.
- Otherwise (the default, free mode) we replay data/tweets_sample.csv minute by
  minute, which is what powers the "watch opinion shift after every goal" demo.

The dashboard only ever calls `tweets_for_match` / `replay_until`, so swapping in
real data is a one-line change.
"""
from __future__ import annotations

import os
import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
TWEETS = os.path.join(DATA, "tweets_sample.csv")
FIXTURES = os.path.join(DATA, "fixtures.csv")


def list_matches_with_tweets() -> pd.DataFrame:
    t = pd.read_csv(TWEETS)
    fx = pd.read_csv(FIXTURES)[["match_id", "home", "away"]]
    ids = t.match_id.unique()
    return fx[fx.match_id.isin(ids)].reset_index(drop=True)


def tweets_for_match(match_id: str) -> pd.DataFrame:
    t = pd.read_csv(TWEETS, parse_dates=["timestamp"])
    return t[t.match_id == match_id].sort_values("timestamp").reset_index(drop=True)


def replay_until(match_id: str, minute: int) -> pd.DataFrame:
    """Tweets posted up to `minute` of the match -- simulates the live feed."""
    df = tweets_for_match(match_id)
    return df[df.match_minute <= minute].reset_index(drop=True)


def goal_minutes(match_id: str) -> list[int]:
    df = tweets_for_match(match_id)
    return sorted(df.loc[df.event == "goal", "match_minute"].unique().tolist())


def has_live_keys() -> bool:
    return bool(os.getenv("X_BEARER_TOKEN"))


def live_search(query: str, max_results: int = 50) -> pd.DataFrame:
    """Real X API path (only used if keys are set). Returns same schema as sample."""
    if not has_live_keys():
        raise RuntimeError("No X API keys set; use replay mode (free).")
    import tweepy  # imported lazily so the app runs without tweepy installed

    client = tweepy.Client(bearer_token=os.getenv("X_BEARER_TOKEN"))
    resp = client.search_recent_tweets(query=query, max_results=max_results,
                                       tweet_fields=["created_at"])
    rows = []
    for i, tw in enumerate(resp.data or []):
        rows.append({"tweet_id": tw.id, "match_id": "live",
                     "timestamp": tw.created_at, "match_minute": i,
                     "team": "", "text": tw.text, "event": ""})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print("Matches with tweet data:")
    print(list_matches_with_tweets().to_string(index=False))
    m = list_matches_with_tweets().iloc[0].match_id
    print(f"\nGoal minutes for {m}: {goal_minutes(m)}")
    print(f"Tweets in first 10 min: {len(replay_until(m, 10))}")
