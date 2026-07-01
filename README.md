# FIFA World Cup 2026 — Intel ⚽📊📡

**Status:** all three apps working end-to-end · free/no-key stack · `python run.py <app>`

Three connected mini-products for the 2026 World Cup, all built on a free,
no-paid-API stack:

| # | Product | What it does | Stack |
|---|---------|--------------|-------|
| 1 | **Match Outcome Predictor** | Predicts the winner of every remaining match and updates after each result. Monte-Carlo simulates the knockout bracket into live **title odds**. | pandas · scikit-learn · Streamlit |
| 2 | **Player Performance Tracker** | Live leaderboard ranking real WC2026 scorers by goals / **Impact Score**, and groups them by **scoring style** with KMeans. | pandas · Plotly · scikit-learn (KMeans) |
| 3 | **Real-Time Sentiment Analyzer** | Replays match tweets minute-by-minute and visualizes how public opinion **shifts after every goal**. | tweepy · HuggingFace / VADER · Streamlit |

> **Real data, no paid keys.** Teams, ratings, training history, the live 2026
> fixtures, and player goals all come from the public-domain
> [martj42/international_results](https://github.com/martj42/international_results)
> dataset (CC0) — see [Data](#data). The only synthetic piece is tweet *text*
> (no free real-tweet firehose exists), and even those are anchored to real
> matches and real goal minutes. Drop in `tweepy` keys for live tweets.

---

## Show it to people 🎬

**Live apps (free hosting):**

| App | Status | URL |
|-----|--------|-----|
| 🔮 Match Predictor | **Live** | https://wc2026-match-predictor.streamlit.app |
| 📊 Player Tracker | Deploy (1 click) | [Open prefilled Streamlit deploy →](https://share.streamlit.io/deploy?repository=hisshanzzz%2Ffifa-world-cup-2026-intel&branch=main&mainModule=player_tracker%2Fapp.py) → set subdomain `wc2026-player-tracker`, Python **3.12**, Deploy |
| 📡 Sentiment Analyzer | Deploy (1 click) | [Open prefilled Streamlit deploy →](https://share.streamlit.io/deploy?repository=hisshanzzz%2Ffifa-world-cup-2026-intel&branch=main&mainModule=sentiment_analyzer%2Fstreamlit_app.py) → set subdomain `wc2026-sentiment`, Python **3.12**, Deploy |

Full walkthrough in **[DEPLOY.md](DEPLOY.md)**. Suggested demo order:
**Predictor → Tracker → Sentiment** (finish on the live goal-shift animation).

**Demo it locally in one go** (three terminals):

```bash
python run.py predictor   # http://localhost:8501
python run.py tracker     # http://localhost:8501  (use a second port if needed)
python run.py sentiment   # http://localhost:8050
```

Suggested flow: open the **Predictor** (title odds + a live "record a result"),
then the **Tracker** (top scorers + style clusters), and finish on the
**Sentiment** dashboard — hit ▶ Play and watch the mood swing on each goal.

---

## Quick start

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

python run.py data --download   # fetch real source CSVs + build dataset
python run.py train             # train the predictor on real results

python run.py predictor  # Streamlit  -> http://localhost:8501
python run.py tracker    # Streamlit  -> http://localhost:8501
python run.py sentiment  # Streamlit  -> http://localhost:8050
```

> On bleeding-edge Python where `torch` has no wheels yet, the sentiment app
> automatically falls back to **VADER** (pure-python). Set `SENTIMENT_BACKEND=hf`
> in `.env` to force HuggingFace once torch is installable.

---

## 1 · Match Outcome Predictor

- **Real ratings** (`data/fetch_real_data.py`): **Elo** computed over the full
  international match history (1872→now), with home advantage and margin-of-victory.
- **Features** (`match_predictor/features.py`): Elo rating, recent form
  (points/game), goals for/against, rating gap, same-confederation flag.
- **Model** (`match_predictor/model.py`): multinomial Logistic Regression over
  `{Home, Draw, Away}` — calibrated probabilities, 5-fold CV. On real data it
  lands around **0.52 accuracy / 0.99 log-loss** — international football is
  genuinely hard to predict (lots of draws), so this is an honest baseline.
- **Simulation** (`match_predictor/predict.py`): converts each tie to a
  "team advances" probability and Monte-Carlos the Round-of-32 bracket (default
  5,000 runs) to get title odds.
- **Update loop** (`match_predictor/update.py`): record a final score and every
  downstream prediction refreshes.

```bash
py -m match_predictor.update --match WC-074 --home-goals 2 --away-goals 1
py -m match_predictor.predict
```

## 2 · Player Performance Tracker

- **Impact Score** (`player_tracker/data.py`): transparent weighting of real
  scoring signals — open-play goals, penalties, late (75'+) goals, and multi-goal
  games — scaled 0–100.
- **Scoring-style clusters** (`player_tracker/clustering.py`): KMeans over real
  goal-profile features (goals/match, penalty share, late vs first-half share,
  avg goal minute), auto-labelled (Prolific Scorer, Clutch Finisher, Fast Starter,
  Penalty Specialist, Multi-Goal Threat, …).
- **Dashboard** (`player_tracker/app.py`): leaderboard, scoring-style map, profiles.
- **Note:** assists / xG / defensive stats aren't in the free dataset, so they're
  omitted rather than faked. The loader accepts an FBref export to add them.

## 3 · Real-Time Sentiment Analyzer

- **Ingest** (`sentiment_analyzer/ingest.py`): live `tweepy` search if keys are
  set, otherwise minute-by-minute replay of tweets anchored to real matches.
- **Scoring** (`sentiment_analyzer/sentiment.py`): HuggingFace `distilbert-sst-2`
  with automatic VADER fallback; both emit a polarity in `[-1, 1]`.
- **Dashboard** (`sentiment_analyzer/streamlit_app.py`): a play/pause "live" clock, rolling
  per-team sentiment lines, and **dashed goal markers** so you can watch the mood
  swing on every goal. (Legacy Dash version: `sentiment_analyzer/app.py`.)

---

## Data

All CSVs in `data/` are built by **`data/fetch_real_data.py`** from the public-domain
[martj42/international_results](https://github.com/martj42/international_results)
dataset (CC0): `results.csv` (every international match 1872→present, including the
live 2026 World Cup) and `goalscorers.csv` (every goal with scorer, minute, penalty).

```
teams.csv            48 WC2026 teams + confederation + REAL Elo rating
matches_history.csv  ~3.8k real recent results -> predictor training data
fixtures.csv         the REAL 2026 World Cup schedule (group + Round of 32)
players.csv          real 2026 WC goalscorer profiles
tweets_sample.csv    synthetic tweet text, anchored to real matches + goal minutes
```

Raw source dumps download into `data/raw/` (git-ignored). Rebuild any time with
`python run.py data --download`. `data/build_data.py` is kept as an offline
synthetic fallback. The previous synthetic-only version of the project is tagged
in git history if you want to compare.

Data credit: [martj42 International football results](https://github.com/martj42/international_results) (CC0 / public domain).

## Roadmap

- [ ] Add an FBref export to bring assists / xG / defensive stats into the tracker
- [ ] Calibrated draw model for group-stage matches
- [ ] Persist scored tweets so the sentiment app survives restarts
- [x] Deploy Match Predictor (Streamlit Community Cloud)
- [ ] Deploy Player Tracker + Sentiment Analyzer ([one-click links above](#show-it-to-people-))

## License

[MIT](LICENSE) © 2026 Hisshan M. Match data is CC0 (public domain) via
[martj42/international_results](https://github.com/martj42/international_results).
