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

1. Go to **https://share.streamlit.io** and sign in with GitHub.
2. **Create app** → **Deploy from repo**.
3. Fill in:
   - Repository: `hisshanzzz/fifa-world-cup-2026-intel`
   - Branch: `main`
   - Main file path: `match_predictor/app.py`   *(repeat with `player_tracker/app.py` for the second app)*
4. **Advanced settings** → Python version: **3.12**.
5. **Deploy**. You get a public URL like `https://<name>.streamlit.app`.

Do it twice (once per Streamlit app) — you'll have two shareable links.

## B. Dash sentiment app → Render (~5 min)

1. Go to **https://render.com** and sign in with GitHub.
2. **New +** → **Blueprint** → select this repo. Render reads `render.yaml`.
3. Confirm the `wc2026-sentiment` service → **Apply**.
4. First build takes a few minutes; then you get `https://wc2026-sentiment.onrender.com`.

> Free Render services sleep after inactivity and take ~30s to wake on the first
> request — fine for a demo, just open it a minute before showing someone.

### Alternative for the Dash app: Hugging Face Spaces
Create a Space (SDK: Docker or Gradio→custom), point it at this repo, and use the
same start command: `gunicorn sentiment_analyzer.app:server --bind 0.0.0.0:$PORT`.

---

## After deploying

Add the three live URLs to the top of `README.md` so anyone can click straight in.
Recommended demo order: **Predictor → Tracker → Sentiment** (finish on the live
goal-shift animation — it's the crowd-pleaser).
