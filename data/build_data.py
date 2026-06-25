"""
Deterministic data builder for the FIFA World Cup 2026 Intel project.

We pick "free / no-key" mode, so instead of hammering a paid API we generate a
plausible, fully self-consistent dataset seeded from real-ish team strengths.

Everything downstream (predictor, player tracker, sentiment) reads the CSVs this
writes into ./data. If you later drop *real* CSVs with the same columns in here,
the apps will use them instead -- nothing else needs to change.

Run:  py data/build_data.py
"""
from __future__ import annotations

import csv
import math
import os
import random
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 2026
random.seed(SEED)

# --- 32 teams that reached the Round of 32, with a base "power" rating ---------
# Ratings are loosely Elo-flavoured and only used to make the synthetic data
# internally consistent. Replace data/teams.csv with real numbers any time.
TEAMS = {
    "Argentina": 2105, "France": 2080, "Spain": 2075, "England": 2060,
    "Brazil": 2055, "Portugal": 2040, "Netherlands": 2025, "Germany": 2015,
    "Belgium": 1995, "Italy": 1985, "Croatia": 1970, "Uruguay": 1965,
    "Morocco": 1955, "USA": 1945, "Mexico": 1940, "Colombia": 1935,
    "Japan": 1920, "Senegal": 1910, "Switzerland": 1905, "Denmark": 1900,
    "Korea Republic": 1885, "Ecuador": 1880, "Australia": 1870, "Canada": 1865,
    "Nigeria": 1860, "Serbia": 1855, "Poland": 1850, "Austria": 1845,
    "Ghana": 1830, "Cameroon": 1825, "Saudi Arabia": 1810, "Qatar": 1795,
}

CONFED = {
    "Argentina": "CONMEBOL", "Brazil": "CONMEBOL", "Uruguay": "CONMEBOL",
    "Colombia": "CONMEBOL", "Ecuador": "CONMEBOL", "France": "UEFA",
    "Spain": "UEFA", "England": "UEFA", "Portugal": "UEFA", "Netherlands": "UEFA",
    "Germany": "UEFA", "Belgium": "UEFA", "Italy": "UEFA", "Croatia": "UEFA",
    "Switzerland": "UEFA", "Denmark": "UEFA", "Serbia": "UEFA", "Poland": "UEFA",
    "Austria": "UEFA", "Morocco": "CAF", "Senegal": "CAF", "Nigeria": "CAF",
    "Ghana": "CAF", "Cameroon": "CAF", "USA": "CONCACAF", "Mexico": "CONCACAF",
    "Canada": "CONCACAF", "Japan": "AFC", "Korea Republic": "AFC",
    "Australia": "AFC", "Saudi Arabia": "AFC", "Qatar": "AFC",
}


def win_prob(r_a: float, r_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((r_b - r_a) / 400.0))


def sample_goals(strength: float, opp: float) -> int:
    # Expected goals scale with strength difference; Poisson-ish draw.
    lam = max(0.25, 1.35 + (strength - opp) / 250.0)
    g = 0
    p = math.exp(-lam)
    cum = p
    u = random.random()
    k = 0
    while u > cum and k < 8:
        k += 1
        p *= lam / k
        cum += p
    g = k
    return g


def write_csv(path: str, header: list[str], rows: list[list]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote {os.path.relpath(path, HERE)}  ({len(rows)} rows)")


def build_teams() -> None:
    rows = [[t, CONFED[t], r] for t, r in sorted(TEAMS.items(), key=lambda x: -x[1])]
    write_csv(os.path.join(HERE, "teams.csv"), ["team", "confederation", "rating"], rows)


def build_history() -> None:
    """Synthetic results from the qualification + friendlies window used to train."""
    teams = list(TEAMS)
    rows = []
    start = datetime(2024, 6, 1)
    mid = 0
    for _ in range(900):
        a, b = random.sample(teams, 2)
        d = start + timedelta(days=mid // 4)
        mid += 1
        ga = sample_goals(TEAMS[a], TEAMS[b])
        gb = sample_goals(TEAMS[b], TEAMS[a])
        # slight home edge for team a
        if random.random() < 0.55 and ga == gb:
            ga += 1
        result = "H" if ga > gb else ("A" if gb > ga else "D")
        rows.append([d.strftime("%Y-%m-%d"), a, b, ga, gb, result, "qualifier"])
    write_csv(
        os.path.join(HERE, "matches_history.csv"),
        ["date", "home", "away", "home_goals", "away_goals", "result", "stage"],
        rows,
    )


def build_fixtures() -> None:
    """The Round of 32 bracket. First few are marked played to seed live updates."""
    seeds = list(TEAMS)  # already sorted by rating in build_teams output
    seeds = [t for t, _ in sorted(TEAMS.items(), key=lambda x: -x[1])]
    # Pair 1v32, 2v31, ... classic seeding
    pairs = [(seeds[i], seeds[31 - i]) for i in range(16)]
    rows = []
    base = datetime(2026, 6, 28, 16, 0)  # R32 kicks off Jun 28
    for i, (h, a) in enumerate(pairs):
        kickoff = base + timedelta(hours=4 * (i % 3) + 24 * (i // 3))
        match_id = f"R32-{i+1:02d}"
        # Mark the first 3 matches as already played (so "update after match" has data)
        if i < 3:
            ga = sample_goals(TEAMS[h], TEAMS[a])
            gb = sample_goals(TEAMS[a], TEAMS[h])
            if ga == gb:  # knockout: decide it
                ga += 1 if win_prob(TEAMS[h], TEAMS[a]) >= 0.5 else 0
                gb += 0 if win_prob(TEAMS[h], TEAMS[a]) >= 0.5 else 1
            played, hg, ag = 1, ga, gb
            res = "H" if hg > ag else "A"
        else:
            played, hg, ag, res = 0, "", "", ""
        rows.append([match_id, kickoff.strftime("%Y-%m-%d %H:%M"), "R32", h, a, played, hg, ag, res])
    write_csv(
        os.path.join(HERE, "fixtures.csv"),
        ["match_id", "kickoff", "stage", "home", "away", "played", "home_goals", "away_goals", "result"],
        rows,
    )


# --- players -----------------------------------------------------------------
FIRST = ["Leo", "Kylian", "Pedri", "Jude", "Vini", "Bruno", "Cody", "Jamal",
         "Kevin", "Nico", "Luka", "Darwin", "Achraf", "Christian", "Hirving",
         "James", "Takefusa", "Ismaila", "Granit", "Rasmus", "Heung-min",
         "Moises", "Mathew", "Alphonso", "Victor", "Dusan", "Robert", "Marcel",
         "Mohammed", "Andre", "Salem", "Akram"]
LAST = ["Garcia", "Silva", "Lopez", "Bellingham", "Junior", "Fernandes", "Gakpo",
        "Musiala", "DeBruyne", "Williams", "Modric", "Nunez", "Hakimi", "Pulisic",
        "Lozano", "Rodriguez", "Kubo", "Sarr", "Xhaka", "Hojlund", "Son",
        "Caicedo", "Ryan", "Davies", "Osimhen", "Vlahovic", "Lewandowski",
        "Sabitzer", "Kudus", "Ayew", "AlDawsari", "Afif"]
POS = ["FW", "FW", "MF", "MF", "FW", "MF", "FW", "MF", "MF", "FW", "MF", "FW",
       "DF", "FW", "FW", "MF", "MF", "FW", "MF", "FW", "FW", "MF", "GK", "DF",
       "FW", "FW", "FW", "MF", "FW", "FW", "MF", "MF"]


def build_players() -> None:
    teams = [t for t, _ in sorted(TEAMS.items(), key=lambda x: -x[1])]
    rows = []
    pid = 1
    for ti, team in enumerate(teams):
        strength = TEAMS[team]
        n = random.randint(6, 8)  # squad sample per team
        for j in range(n):
            name = f"{random.choice(FIRST)} {random.choice(LAST)}"
            pos = random.choices(["FW", "MF", "DF", "GK"], weights=[4, 4, 3, 1])[0]
            minutes = random.randint(180, 540)
            atk = (strength - 1800) / 300.0
            goals = max(0, int(random.gauss(2.2 * atk if pos == "FW" else 0.8 * atk, 1.1)))
            assists = max(0, int(random.gauss(1.4 * atk if pos in ("FW", "MF") else 0.4, 0.9)))
            shots = goals * random.randint(2, 5) + random.randint(0, 6)
            key_passes = assists * random.randint(2, 4) + random.randint(0, 8)
            dribbles = max(0, int(random.gauss(8 * atk if pos in ("FW", "MF") else 2, 4)))
            tackles = max(0, int(random.gauss(2 if pos in ("FW", "MF") else 10, 4)))
            interceptions = max(0, int(random.gauss(1 if pos == "FW" else 7, 3)))
            xg = round(goals * random.uniform(0.7, 1.2) + random.uniform(0, 0.6), 2)
            xa = round(assists * random.uniform(0.7, 1.2) + random.uniform(0, 0.5), 2)
            rows.append([pid, name, team, pos, minutes, goals, assists, shots,
                         key_passes, dribbles, tackles, interceptions, xg, xa])
            pid += 1
    write_csv(
        os.path.join(HERE, "players.csv"),
        ["player_id", "name", "team", "position", "minutes", "goals", "assists",
         "shots", "key_passes", "dribbles", "tackles", "interceptions", "xg", "xa"],
        rows,
    )


# --- sample tweets (for sentiment when no X API keys) -------------------------
POS_TMPL = ["What a goal by {team}!! unreal", "{team} looking unstoppable today",
            "{player} is on another level, {team} fans happy",
            "absolute scenes for {team}, deserved win", "{team} defense is rock solid",
            "best team in the tournament {team} no doubt", "{player} carrying {team}"]
NEG_TMPL = ["{team} are so disappointing", "terrible defending from {team}",
            "{player} missed an open goal, {team} in trouble",
            "ref is robbing {team} smh", "{team} crashing out, embarrassing",
            "worst performance by {team} in years", "send {player} home, {team} deserved to lose"]
NEU_TMPL = ["{team} vs the world, lets see", "halftime and {team} still level",
            "watching {team} with the family", "{player} subbed on for {team}",
            "anyone got a stream for {team}?", "{team} lineup just dropped"]


def build_tweets() -> None:
    teams = list(TEAMS)
    rows = []
    tid = 1
    # tie tweets to the first 3 (played) fixtures so the goal-shift demo works
    seeds = [t for t, _ in sorted(TEAMS.items(), key=lambda x: -x[1])]
    pairs = [(seeds[0], seeds[31]), (seeds[1], seeds[30]), (seeds[2], seeds[29])]
    base = datetime(2026, 6, 28, 16, 0)
    for mi, (h, a) in enumerate(pairs):
        kickoff = base + timedelta(hours=4 * mi)
        match_id = f"R32-{mi+1:02d}"
        # simulate 90 minutes of tweets with a couple of "goal events"
        goal_minutes = sorted(random.sample(range(5, 88), random.randint(2, 4)))
        for minute in range(0, 95, 1):
            n = random.randint(1, 4)
            for _ in range(n):
                team = random.choice([h, a])
                player = f"{random.choice(FIRST)} {random.choice(LAST)}"
                # after a goal, skew positive for one side, negative for other
                near_goal = any(0 <= minute - gm <= 6 for gm in goal_minutes)
                if near_goal:
                    tmpl = random.choices([POS_TMPL, NEG_TMPL, NEU_TMPL], weights=[5, 3, 2])[0]
                else:
                    tmpl = random.choices([POS_TMPL, NEG_TMPL, NEU_TMPL], weights=[3, 3, 4])[0]
                text = random.choice(tmpl).format(team=team, player=player)
                ts = kickoff + timedelta(minutes=minute, seconds=random.randint(0, 59))
                rows.append([tid, match_id, ts.strftime("%Y-%m-%d %H:%M:%S"), minute,
                             team, text, ("goal" if minute in goal_minutes else "")])
                tid += 1
    write_csv(
        os.path.join(HERE, "tweets_sample.csv"),
        ["tweet_id", "match_id", "timestamp", "match_minute", "team", "text", "event"],
        rows,
    )


def main() -> None:
    print("Building FIFA World Cup 2026 Intel dataset (free/no-key mode)...")
    build_teams()
    build_history()
    build_fixtures()
    build_players()
    build_tweets()
    print("Done. CSVs are in ./data")


if __name__ == "__main__":
    main()
