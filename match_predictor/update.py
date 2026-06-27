"""Record a finished match, so every prediction refreshes for the next one.

This is the "update after every match" loop: enter a final score, it's written
back to data/fixtures.csv (played=1), and the next run of predict/simulate uses
the new reality.

Examples:
  py -m match_predictor.update --match R32-04 --home-goals 2 --away-goals 1
  py -m match_predictor.update --list
"""
from __future__ import annotations

import argparse
import os
import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FIXTURES = os.path.join(DATA, "fixtures.csv")


def list_fixtures() -> pd.DataFrame:
    return pd.read_csv(FIXTURES)


def record_result(match_id: str, home_goals: int, away_goals: int) -> pd.Series:
    fx = pd.read_csv(FIXTURES)
    mask = fx.match_id == match_id
    if not mask.any():
        raise ValueError(f"Unknown match_id: {match_id}")
    fx.loc[mask, "played"] = 1
    fx.loc[mask, "home_goals"] = home_goals
    fx.loc[mask, "away_goals"] = away_goals
    fx.loc[mask, "result"] = ("H" if home_goals > away_goals
                              else ("A" if away_goals > home_goals else "D"))
    fx.to_csv(FIXTURES, index=False)
    return fx.loc[mask].iloc[0]


def main() -> None:
    ap = argparse.ArgumentParser(description="Record a World Cup match result.")
    ap.add_argument("--list", action="store_true", help="show fixtures and exit")
    ap.add_argument("--match", help="match_id, e.g. R32-04")
    ap.add_argument("--home-goals", type=int)
    ap.add_argument("--away-goals", type=int)
    args = ap.parse_args()

    if args.list:
        print(list_fixtures().to_string(index=False))
        return
    if not (args.match and args.home_goals is not None and args.away_goals is not None):
        ap.error("provide --match, --home-goals and --away-goals (or --list)")

    row = record_result(args.match, args.home_goals, args.away_goals)
    print(f"Recorded {row.home} {args.home_goals}-{args.away_goals} {row.away} "
          f"({row.result}). Predictions will refresh on next run.")


if __name__ == "__main__":
    main()
