# Deploying the apps (all free tiers)

Three apps, two hosts. All free, all driven from this GitHub repo — no card needed.

| App | File | Best free host |
|-----|------|----------------|
| Match Predictor (Streamlit) | `match_predictor/app.py` | Streamlit Community Cloud |
| Player Tracker (Streamlit) | `player_tracker/app.py` | Streamlit Community Cloud |
| Sentiment Analyzer (Dash) | `sentiment_analyzer/app.py` | Render (Blueprint) |

> These cloud runners use Python 3.12, so everything installs cleanly. The core
> `requirements.txt` is intentionally light (no torch) so builds stay under the
> free size limits; sentiment defaults to the VADER backend.

---

## A. Streamlit apps → Streamlit Community Cloud (~3 min each)

**Already live:** [Match Predictor](https://wc2026-match-predictor.streamlit.app)

**Player Tracker — one click (form prefilled):**

https://share.streamlit.io/deploy?repository=hisshanzzz%2Ffifa-world-cup-2026-intel&branch=main&mainModule=player_tracker%2Fapp.py

1. Open the link above → sign in with GitHub if prompted.
2. **App URL (subdomain):** `wc2026-player-tracker` → `https://wc2026-player-tracker.streamlit.app`
3. **Advanced settings** → Python version: **3.12** (required — root `requirements.txt` targets 3.12).
4. **Deploy**.

Manual path (same fields): **https://share.streamlit.io** → Create app → repo `hisshanzzz/fifa-world-cup-2026-intel`, branch `main`, main file `player_tracker/app.py`.

## B. Dash sentiment app → Render (~5 min)

**One click (repo prefilled):**

https://dashboard.render.com/blueprint/new?repo=https%3A%2F%2Fgithub.com%2Fhisshanzzz%2Ffifa-world-cup-2026-intel

1. Open the link above → sign in with GitHub if prompted.
2. Confirm the `wc2026-sentiment` service from `render.yaml` → **Apply**.
3. First build takes a few minutes; live URL: `https://wc2026-sentiment.onrender.com`.

Manual path: **https://render.com** → New + → Blueprint → select this repo.

> Free Render services sleep after inactivity and take ~30s to wake on the first
> request — fine for a demo, just open it a minute before showing someone.

### Alternative for the Dash app: Hugging Face Spaces
Create a Space (SDK: Docker or Gradio→custom), point it at this repo, and use the
same start command: `gunicorn sentiment_analyzer.app:server --bind 0.0.0.0:$PORT`.

---

## After deploying

Live URLs (update README if subdomains differ):

- 🔮 Predictor: https://wc2026-match-predictor.streamlit.app
- 📊 Tracker: https://wc2026-player-tracker.streamlit.app *(after step A)*
- 📡 Sentiment: https://wc2026-sentiment.onrender.com *(after step B)*

Recommended demo order: **Predictor → Tracker → Sentiment** (finish on the live
goal-shift animation — it's the crowd-pleaser).

### Headless deploy (optional, for CI)

Neither host can be fully automated without account tokens:

| Host | Blocker | Fastest fix |
|------|---------|-------------|
| Streamlit Cloud | No API token in env; Streamlit 1.58 has no `streamlit cloud deploy` CLI yet | Use the prefilled deploy link above (browser, ~2 min) |
| Render | No `RENDER_API_KEY`; `render login` is browser-only | Use the Blueprint link above (browser, ~5 min) |

If you add `RENDER_API_KEY` to GitHub secrets later, a workflow can run
`render deploys create` — but the Blueprint must exist first (one browser deploy).
