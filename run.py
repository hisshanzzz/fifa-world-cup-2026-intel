"""One entry point for the whole project.

Usage:
  py run.py data        # (re)build the bundled dataset
  py run.py train       # train the match-outcome model
  py run.py predict     # print predictions + title odds in the terminal
  py run.py predictor   # launch the Streamlit match predictor
  py run.py tracker     # launch the Streamlit player tracker
  py run.py sentiment   # launch the Plotly Dash live sentiment dashboard
"""
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    py = sys.executable

    if cmd == "data":
        return subprocess.call([py, "data/build_data.py"])
    if cmd == "train":
        return subprocess.call([py, "-m", "match_predictor.model"])
    if cmd == "predict":
        return subprocess.call([py, "-m", "match_predictor.predict"])
    if cmd == "predictor":
        return subprocess.call([py, "-m", "streamlit", "run", "match_predictor/app.py"])
    if cmd == "tracker":
        return subprocess.call([py, "-m", "streamlit", "run", "player_tracker/app.py"])
    if cmd == "sentiment":
        return subprocess.call([py, "sentiment_analyzer/app.py"])

    print(f"Unknown command: {cmd}\n")
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
