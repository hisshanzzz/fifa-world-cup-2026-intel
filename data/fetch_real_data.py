"""Build the project dataset from REAL, free, no-API-key sources.

Source: martj42/international_results (public domain, CC0) -- mirrored on GitHub.
  - results.csv     every international match 1872 -> present, incl. the live
                    2026 World Cup (played results + scheduled fixtures)
  - goalscorers.csv every goal: scorer, minute, penalty, own-goal

From this we derive, with ZERO synthetic match data:
  teams.csv            real Elo ratings (computed over the full history) + confed
  matches_history.csv  real recent results -> training data for the predictor
  fixtures.csv         the REAL 2026 World Cup schedule (group + Round of 32)
  players.csv          real 2026 World Cup goalscorer profiles
  tweets_sample.csv    synthetic tweet TEXT, but anchored to REAL matches and
                       REAL goal minutes (no free firehose of real tweets exists)

Download the raw files first (once):
  py data/fetch_real_data.py --download
Then build:
  py data/fetch_real_data.py
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import random
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
RESULTS = os.path.join(RAW, "international_results.csv")
GOALS = os.path.join(RAW, "goalscorers.csv")

BASE = "https://raw.githubusercontent.com/martj42/international_results/master"
TODAY = datetime(2026, 6, 29)  # "now" in tournament time: later matches are unplayed

CONFED = {
    "UEFA": ["Austria", "Belgium", "Bosnia and Herzegovina", "Croatia", "Czech Republic",
             "England", "France", "Germany", "Netherlands", "Norway", "Portugal",
             "Scotland", "Spain", "Sweden", "Switzerland", "Turkey"],
    "CONMEBOL": ["Argentina", "Brazil", "Colombia", "Ecuador", "Paraguay", "Uruguay"],
    "CONCACAF": ["Canada", "Cura\u00e7ao", "Haiti", "Mexico", "Panama", "United States"],
    "CAF": ["Algeria", "Cape Verde", "DR Congo", "Egypt", "Ghana", "Ivory Coast",
            "Morocco", "Senegal", "South Africa", "Tunisia"],
    "AFC": ["Australia", "Iran", "Iraq", "Japan", "Jordan", "Qatar", "Saudi Arabia",
            "South Korea", "Uzbekistan"],
    "OFC": ["New Zealand"],
}
TEAM_CONFED = {t: c for c, ts in CONFED.items() for t in ts}


def download() -> None:
    os.makedirs(RAW, exist_ok=True)
    for name in ("results.csv", "goalscorers.csv"):
        dst = os.path.join(RAW, "international_results.csv" if name == "results.csv" else name)
        print(f"  downloading {name} ...")
        urllib.request.urlretrieve(f"{BASE}/{name}", dst)
    print("  done.")


# ---------------------------------------------------------------- read helpers
def read_results() -> list[dict]:
    with open(RESULTS, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_goals() -> list[dict]:
    with open(GOALS, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


def is_played(row: dict) -> bool:
    return row["home_score"] not in ("", "NA") and row["away_score"] not in ("", "NA")


# ---------------------------------------------------------------- Elo ratings
def compute_elo(rows: list[dict], k: float = 30.0, home_adv: float = 65.0) -> dict:
    rating: dict[str, float] = defaultdict(lambda: 1500.0)
    for r in sorted(rows, key=lambda x: x["date"]):
        if not is_played(r):
            continue
        if parse_date(r["date"]) >= TODAY:
            continue  # don't peek at future results
        h, a = r["home_team"], r["away_team"]
        hs, as_ = int(float(r["home_score"])), int(float(r["away_score"]))
        neutral = str(r.get("neutral", "FALSE")).upper() == "TRUE"
        ra = rating[h] + (0 if neutral else home_adv)
        rb = rating[a]
        ea = 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))
        res = 1.0 if hs > as_ else (0.5 if hs == as_ else 0.0)
        gd = abs(hs - as_)
        mult = 1.0 + math.log1p(gd) * 0.5  # bigger wins move ratings a bit more
        rating[h] += k * mult * (res - ea)
        rating[a] += k * mult * ((1 - res) - (1 - ea))
    return rating


# ---------------------------------------------------------------- writers
def write_csv(path: str, header: list[str], rows: list[list]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote {os.path.relpath(path, HERE)}  ({len(rows)} rows)")


def wc_2026(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["tournament"] == "FIFA World Cup"
            and parse_date(r["date"]).year == 2026]


def build_teams(elo: dict, wc_rows: list[dict]) -> list[str]:
    teams = sorted({r["home_team"] for r in wc_rows} | {r["away_team"] for r in wc_rows})
    out = [[t, TEAM_CONFED.get(t, "OTHER"), round(elo.get(t, 1500.0), 1)] for t in teams]
    out.sort(key=lambda x: -x[2])
    write_csv(os.path.join(HERE, "teams.csv"), ["team", "confederation", "rating"], out)
    return teams


def build_history(rows: list[dict], teams: set[str], since_year: int = 2018) -> None:
    out = []
    for r in rows:
        if not is_played(r):
            continue
        d = parse_date(r["date"])
        if d.year < since_year or d >= TODAY:
            continue
        if r["home_team"] not in teams and r["away_team"] not in teams:
            continue
        hs, as_ = int(float(r["home_score"])), int(float(r["away_score"]))
        res = "H" if hs > as_ else ("A" if as_ > hs else "D")
        out.append([r["date"], r["home_team"], r["away_team"], hs, as_, res,
                    r["tournament"]])
    write_csv(os.path.join(HERE, "matches_history.csv"),
              ["date", "home", "away", "home_goals", "away_goals", "result", "stage"], out)


def build_fixtures(wc_rows: list[dict]) -> list[list]:
    rows = []
    for i, r in enumerate(sorted(wc_rows, key=lambda x: x["date"]), start=1):
        d = parse_date(r["date"])
        stage = "Group" if d < datetime(2026, 6, 28) else "Round of 32"
        played = 1 if is_played(r) else 0
        hg = int(float(r["home_score"])) if played else ""
        ag = int(float(r["away_score"])) if played else ""
        res = ("" if not played else ("H" if hg > ag else ("A" if ag > hg else "D")))
        rows.append([f"WC-{i:03d}", f"{r['date']} 18:00", stage,
                     r["home_team"], r["away_team"], played, hg, ag, res])
    write_csv(os.path.join(HERE, "fixtures.csv"),
              ["match_id", "kickoff", "stage", "home", "away", "played",
               "home_goals", "away_goals", "result"], rows)
    return rows


def build_players(goals: list[dict]) -> None:
    g26 = [g for g in goals if parse_date(g["date"]).year == 2026
           and str(g.get("own_goal", "FALSE")).upper() != "TRUE"]
    agg: dict[tuple, dict] = {}
    games: dict[tuple, set] = defaultdict(set)
    per_game: dict[tuple, dict] = defaultdict(lambda: defaultdict(int))
    for g in g26:
        key = (g["scorer"], g["team"])
        mins = int(float(g["minute"])) if g["minute"] not in ("", "NA") else 45
        pen = str(g.get("penalty", "FALSE")).upper() == "TRUE"
        a = agg.setdefault(key, {"goals": 0, "pen": 0, "late": 0, "fh": 0, "min_sum": 0})
        a["goals"] += 1
        a["pen"] += int(pen)
        a["late"] += int(mins >= 75)
        a["fh"] += int(mins <= 45)
        a["min_sum"] += mins
        gid = (g["date"], g["home_team"], g["away_team"])
        games[key].add(gid)
        per_game[key][gid] += 1

    rows = []
    for pid, (key, a) in enumerate(sorted(agg.items(), key=lambda x: -x[1]["goals"]), start=1):
        scorer, team = key
        n_games = len(games[key])
        multi = sum(1 for c in per_game[key].values() if c >= 2)
        rows.append([
            pid, scorer, team, a["goals"], a["pen"], a["goals"] - a["pen"],
            n_games, round(a["min_sum"] / a["goals"], 1), a["late"], a["fh"], multi,
        ])
    write_csv(os.path.join(HERE, "players.csv"),
              ["player_id", "name", "team", "goals", "penalty_goals", "open_play_goals",
               "matches_scored", "avg_goal_minute", "late_goals", "first_half_goals",
               "multi_goal_games"], rows)


# ---------------------------------------------------------------- tweets (text synthetic, anchored to real matches/goals)
POS = ["Massive goal!! {team} sending us", "{team} are flying, what a finish",
       "unreal from {team}, get in!!", "{team} look the real deal today",
       "this {team} side is special", "scenes for {team} fans rn"]
NEG = ["{team} all over the place at the back", "shocking from {team}, wake up",
       "{team} bottling this again smh", "ref against {team} as usual",
       "worst {team} display ive seen", "{team} need to change it now"]
NEU = ["{team} knocking it around", "tense one for {team} here",
       "{team} fans nervous", "anyone streaming {team}?",
       "half chance for {team}", "{team} subs warming up"]


def build_tweets(fixtures: list[list], goals: list[dict], seed: int = 11) -> None:
    rng = random.Random(seed)
    fx = {(r[3], r[4], r[1][:10]): r for r in fixtures}  # (home,away,date)->row
    # pick the 3 played matches with the most goals for a lively demo
    g26 = [g for g in goals if parse_date(g["date"]).year == 2026]
    by_match: dict[tuple, list] = defaultdict(list)
    for g in g26:
        by_match[(g["home_team"], g["away_team"], g["date"])].append(g)
    played_rows = {(r[3], r[4], r[1][:10]): r for r in fixtures if r[5] == 1}
    candidates = [(k, v) for k, v in by_match.items() if k in played_rows]
    candidates.sort(key=lambda kv: -len(kv[1]))
    chosen = candidates[:3]

    out = []
    tid = 1
    for (home, away, date), glist in chosen:
        row = played_rows[(home, away, date)]
        match_id = row[0]
        kickoff = datetime.strptime(row[1], "%Y-%m-%d %H:%M")
        goal_events = []
        for g in glist:
            m = int(float(g["minute"])) if g["minute"] not in ("", "NA") else 45
            goal_events.append((m, g["team"], g["scorer"]))
        goal_minutes = {m for m, _, _ in goal_events}
        for minute in range(0, 96):
            for _ in range(rng.randint(1, 4)):
                team = rng.choice([home, away])
                near = any(0 <= minute - gm <= 6 for gm in goal_minutes)
                tmpl = (rng.choices([POS, NEG, NEU], weights=[5, 3, 2])[0] if near
                        else rng.choices([POS, NEG, NEU], weights=[3, 3, 4])[0])
                text = rng.choice(tmpl).format(team=team)
                ts = kickoff + timedelta(minutes=minute, seconds=rng.randint(0, 59))
                ev = "goal" if minute in goal_minutes else ""
                out.append([tid, match_id, ts.strftime("%Y-%m-%d %H:%M:%S"),
                            minute, team, text, ev])
                tid += 1
    write_csv(os.path.join(HERE, "tweets_sample.csv"),
              ["tweet_id", "match_id", "timestamp", "match_minute", "team", "text", "event"], out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true", help="re-download raw source CSVs")
    args = ap.parse_args()

    if args.download or not (os.path.exists(RESULTS) and os.path.exists(GOALS)):
        download()

    print("Building dataset from REAL international results + goalscorers...")
    rows = read_results()
    goals = read_goals()
    elo = compute_elo(rows)
    wc_rows = wc_2026(rows)
    teams = build_teams(elo, wc_rows)
    build_history(rows, set(teams))
    fixtures = build_fixtures(wc_rows)
    build_players(goals)
    build_tweets(fixtures, goals)
    print("Done. Real data is in ./data")


if __name__ == "__main__":
    main()
