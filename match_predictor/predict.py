"""Predict remaining matches and simulate the rest of the tournament.

Two products:
  1. per-match probabilities  (H / D / A) for every un-played fixture
  2. title odds              -> Monte-Carlo the knockout bracket many times

Because the World Cup knockouts can't end in a draw, we convert the model's
{H, D, A} probabilities into a single "home advances" probability by splitting
the draw mass toward the stronger side (a light penalty-shootout prior).

Run:  py -m match_predictor.predict
"""
from __future__ import annotations

import os
import random
import numpy as np
import pandas as pd

from .features import featurize
from .model import load_model

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FIXTURES = os.path.join(DATA, "fixtures.csv")


def _proba(bundle, home: str, away: str) -> dict:
    pipe, stats, feats = bundle["pipeline"], bundle["stats"], bundle["features"]
    row = pd.DataFrame([featurize(stats, home, away)])[feats]
    p = pipe.predict_proba(row)[0]
    classes = list(pipe.named_steps["clf"].classes_)
    return {c: float(p[i]) for i, c in enumerate(classes)}


def predict_fixtures(bundle=None) -> pd.DataFrame:
    bundle = bundle or load_model()
    fx = pd.read_csv(FIXTURES)
    out = []
    for _, m in fx.iterrows():
        probs = _proba(bundle, m.home, m.away)
        out.append({
            "match_id": m.match_id,
            "kickoff": m.kickoff,
            "home": m.home,
            "away": m.away,
            "played": bool(m.played),
            "p_home": round(probs.get("H", 0), 3),
            "p_draw": round(probs.get("D", 0), 3),
            "p_away": round(probs.get("A", 0), 3),
            "score": (f"{int(m.home_goals)}-{int(m.away_goals)}"
                      if m.played else ""),
        })
    return pd.DataFrame(out)


def _advance_prob(probs: dict) -> float:
    """P(home advances) from {H,D,A}, splitting draws toward the favourite."""
    h, d, a = probs.get("H", 0), probs.get("D", 0), probs.get("A", 0)
    fav_home = h >= a
    return h + d * (0.55 if fav_home else 0.45)


def simulate_title_odds(bundle=None, n_sims: int = 5000, seed: int = 7) -> pd.DataFrame:
    bundle = bundle or load_model()
    fx = pd.read_csv(FIXTURES)
    # The knockout bracket starts at the Round of 32 (32 teams). Group-stage rows
    # are excluded so the single-elimination sim is well-formed.
    if "stage" in fx.columns and (fx.stage == "Round of 32").any():
        fx = fx[fx.stage == "Round of 32"]
    fx = fx.sort_values("match_id").reset_index(drop=True)
    rng = random.Random(seed)

    # cache advance probabilities
    cache: dict[tuple[str, str], float] = {}

    def adv(h, a):
        key = (h, a)
        if key not in cache:
            cache[key] = _advance_prob(_proba(bundle, h, a))
        return cache[key]

    titles = {t: 0 for t in pd.concat([fx.home, fx.away]).unique()}

    for _ in range(n_sims):
        # Round of 32 -> resolve to 16 winners (respect already-played results)
        round_teams = []
        for _, m in fx.iterrows():
            if bool(m.played):
                round_teams.append(m.home if m.result == "H" else m.away)
            else:
                round_teams.append(m.home if rng.random() < adv(m.home, m.away) else m.away)
        # subsequent rounds: pair sequentially until a champion remains
        while len(round_teams) > 1:
            nxt = []
            for i in range(0, len(round_teams), 2):
                h, a = round_teams[i], round_teams[i + 1]
                nxt.append(h if rng.random() < adv(h, a) else a)
            round_teams = nxt
        titles[round_teams[0]] += 1

    rows = [{"team": t, "title_prob": round(c / n_sims, 4)} for t, c in titles.items()]
    return pd.DataFrame(rows).sort_values("title_prob", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    b = load_model()
    print("\n=== Remaining-match predictions ===")
    preds = predict_fixtures(b)
    print(preds.to_string(index=False))
    print("\n=== Title odds (Monte-Carlo) ===")
    odds = simulate_title_odds(b, n_sims=3000)
    print(odds.head(12).to_string(index=False))
