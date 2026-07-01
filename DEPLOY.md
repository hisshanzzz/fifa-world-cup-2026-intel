# Deploying the apps (all free tiers)

All three apps run on **Streamlit Community Cloud** — free, no credit card, all driven
from this GitHub repo.

| App | File | Host |
|-----|------|------|
| Match Predictor | `match_predictor/app.py` | Streamlit Community Cloud |
| Player Tracker | `player_tracker/app.py` | Streamlit Community Cloud |
| Sentiment Analyzer | `sentiment_analyzer/streamlit_app.py` | Streamlit Community Cloud |

> Cloud runners use Python 3.12, so everything installs cleanly. The core
> `requirements.txt` is intentionally light (no torch) so builds stay under the
> free size limits; sentiment defaults to the VADER backend.

> **Note:** `render.yaml` is optional legacy config for the old Dash app — you do
> **not** need Render or a billing account to deploy any of the three apps.

---

## Streamlit Community Cloud (~3 min each)

**Already live:** [Match Predictor](https://wc2026-match-predictor.streamlit.app)

**Player Tracker — one click (form prefilled):**

https://share.streamlit.io/deploy?repository=hisshanzzz%2Ffifa-world-cup-2026-intel&branch=main&mainModule=player_tracker%2Fapp.py

1. Open the link above → sign in with GitHub if prompted.
2. **App URL (subdomain):** `wc2026-player-tracker` → `https://wc2026-player-tracker.streamlit.app`
3. **Advanced settings** → Python version: **3.12** (required — root `requirements.txt` targets 3.12).
4. **Deploy**.

**Sentiment Analyzer — one click (form prefilled):**

https://share.streamlit.io/deploy?repository=hisshanzzz%2Ffifa-world-cup-2026-intel&branch=main&mainModule=sentiment_analyzer%2Fstreamlit_app.py

1. Open the link above → sign in with GitHub if prompted.
2. **App URL (subdomain):** `wc2026-sentiment` → `https://wc2026-sentiment.streamlit.app`
3. **Advanced settings** → Python version: **3.12**.
4. **Deploy**.

Manual path (same fields): **https://share.streamlit.io** → Create app → repo
`hisshanzzz/fifa-world-cup-2026-intel`, branch `main`, main file as listed above.

---

## After deploying

Live URLs (update README if subdomains differ):

- 🔮 Predictor: https://wc2026-match-predictor.streamlit.app
- 📊 Tracker: https://wc2026-player-tracker.streamlit.app *(after deploy)*
- 📡 Sentiment: https://wc2026-sentiment.streamlit.app *(after deploy)*

Recommended demo order: **Predictor → Tracker → Sentiment** (finish on the live
goal-shift animation — it's the crowd-pleaser).

### Headless deploy (optional, for CI)

Streamlit Cloud has no API token in env; Streamlit 1.58 has no `streamlit cloud deploy`
CLI yet. Use the prefilled deploy links above (browser, ~2 min each).
