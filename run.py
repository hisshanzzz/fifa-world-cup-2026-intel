"""One entry point for the whole project.

Usage:
  py run.py data --download  # fetch raw real source CSVs, then build dataset
  py run.py data             # rebuild dataset from already-downloaded sources
  py run.py train            # train the match-outcome model
  py run.py predict     # print predictions + title odds in the terminal
  py run.py predictor   # launch the Streamlit match predictor
  py run.py tracker     # launch the Streamlit player tracker
  py run.py sentiment   # launch the Plotly Dash live sentiment dashboard
"""
from __future__ import annotations

import os
import subprocess
import sys

# Fixed, non-conflicting ports so the local URL is always the same.
PREDICTOR_PORT = 8501
TRACKER_PORT = 8502
SENTIMENT_PORT = 8050


def _run_streamlit(py: str, app: str, port: int) -> int:
    url = f"http://localhost:{port}"
    print(f"\nOpen this in your browser: {url}  (or http://127.0.0.1:{port})\n")
    return subprocess.call([
        py, "-m", "streamlit", "run", app,
        "--server.port", str(port),
        "--server.address", "127.0.0.1",
        "--server.headless", "true",
    ])


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    py = sys.executable

    if cmd == "data":
        # Build from REAL free data (martj42 international results + goalscorers).
        # Pass --download the first time to fetch the raw source CSVs.
        return subprocess.call([py, "data/fetch_real_data.py", *sys.argv[2:]])
    if cmd == "train":
        return subprocess.call([py, "-m", "match_predictor.model"])
    if cmd == "predict":
        return subprocess.call([py, "-m", "match_predictor.predict"])
    if cmd == "predictor":
        return _run_streamlit(py, "match_predictor/app.py", PREDICTOR_PORT)
    if cmd == "tracker":
        return _run_streamlit(py, "player_tracker/app.py", TRACKER_PORT)
    if cmd == "sentiment":
        # Default to the offline VADER backend so it runs without API keys.
        os.environ.setdefault("SENTIMENT_BACKEND", "vader")
        url = f"http://localhost:{SENTIMENT_PORT}"
        print(f"\nOpen this in your browser: {url}  (or http://127.0.0.1:{SENTIMENT_PORT})\n")
        return subprocess.call([py, "sentiment_analyzer/app.py"])

    print(f"Unknown command: {cmd}\n")
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
