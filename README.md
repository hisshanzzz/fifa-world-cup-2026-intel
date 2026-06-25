# FIFA World Cup 2026 — Intel ⚽📊📡

Three connected mini-products for the 2026 World Cup, all built on a free,
no-paid-API stack:

| # | Product | What it does | Stack |
|---|---------|--------------|-------|
| 1 | **Match Outcome Predictor** | Predicts the winner of every remaining match and updates after each result. Monte-Carlo simulates the knockout bracket into live **title odds**. | pandas · scikit-learn · Streamlit |
| 2 | **Player Performance Tracker** | Live leaderboard ranking players by goals / assists / **Impact Score**, and groups players by **playing style** with KMeans. | pandas · Plotly · scikit-learn (KMeans) |
| 3 | **Real-Time Sentiment Analyzer** | Replays match tweets minute-by-minute and visualizes how public opinion **shifts after every goal**. | tweepy · HuggingFace / VADER · Plotly Dash |

> **Free mode by default.** The X/Twitter API is now paid, so the sentiment app
> ships with a bundled, minute-stamped tweet dataset and a one-line swap-in for
> real `tweepy` keys. Likewise the player tracker reads `data/players.csv`; drop
> in a real FBref/Kaggle export with the same columns and it just works.

---

## Quick start

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

python run.py data       # build the dataset
python run.py train      # train the predictor

python run.py predictor  # Streamlit  -> http://localhost:8501
python run.py tracker    # Streamlit  -> http://localhost:8501
python run.py sentiment  # Dash       -> http://localhost:8050
```

> On bleeding-edge Python where `torch` has no wheels yet, the sentiment app
> automatically falls back to **VADER** (pure-python). Set `SENTIMENT_BACKEND=hf`
> in `.env` to force HuggingFace once torch is installable.

---

## 1 · Match Outcome Predictor

- **Features** (`match_predictor/features.py`): team rating, recent form
  (points/game), goals for/against, rating gap, same-confederation flag.
- **Model** (`match_predictor/model.py`): multinomial Logistic Regression over
  `{Home, Draw, Away}` — calibrated probabilities, 5-fold CV.
- **Simulation** (`match_predictor/predict.py`): converts each tie to a
  "team advances" probability and Monte-Carlos the bracket (default 5,000 runs)
  to get title odds.
- **Update loop** (`match_predictor/update.py`): record a final score and every
  downstream prediction refreshes.

```bash
py -m match_predictor.update --match R32-04 --home-goals 2 --away-goals 1
py -m match_predictor.predict
```

## 2 · Player Performance Tracker

- **Impact Score** (`player_tracker/data.py`): transparent per-90 weighted blend
  of goals, assists, xG, xA, key passes, dribbles, and defensive actions, scaled
  0–100.
- **Style clusters** (`player_tracker/clustering.py`): KMeans on per-90 style
  signals, auto-labelled (Finisher, Creator, Ball-Winner, Dribble-Carrier, …).
- **Dashboard** (`player_tracker/app.py`): leaderboard, style map, group profiles.

## 3 · Real-Time Sentiment Analyzer

- **Ingest** (`sentiment_analyzer/ingest.py`): live `tweepy` search if keys are
  set, otherwise minute-by-minute replay of the bundled dataset.
- **Scoring** (`sentiment_analyzer/sentiment.py`): HuggingFace `distilbert-sst-2`
  with automatic VADER fallback; both emit a polarity in `[-1, 1]`.
- **Dashboard** (`sentiment_analyzer/app.py`): a play/pause "live" clock, rolling
  per-team sentiment lines, and **dashed goal markers** so you can watch the mood
  swing on every goal.

---

## Data

All CSVs live in `data/` and are produced by `data/build_data.py` (seeded, so
it's reproducible). Swap any file for a real export with the same columns to go
from demo to live data.

```
teams.csv            32 R32 teams + confederation + rating
matches_history.csv  training results (form/strength signals)
fixtures.csv         the Round-of-32 bracket (played flag + scores)
players.csv          per-player tournament stats
tweets_sample.csv    minute-stamped match tweets with goal events
```

## Roadmap

- [ ] Wire real FBref player exports into the tracker
- [ ] Calibrated draw model for group-stage matches
- [ ] Persist scored tweets so the sentiment app survives restarts
- [ ] Deploy all three (Streamlit Community Cloud + a Dash host)
