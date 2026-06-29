"""Sentiment scoring with a HuggingFace-first, VADER-fallback design.

Why two backends?
  - HuggingFace transformers gives the strongest results, but needs torch, which
    has no wheels on bleeding-edge Python yet. So we keep it as the *preferred*
    backend and fall back to VADER (pure-python, installs everywhere) so the app
    always runs for free.

Pick with env var SENTIMENT_BACKEND = "hf" | "vader" (default: auto).
Every scorer returns a `polarity` in [-1, 1] so the dashboard is backend-agnostic.
"""
from __future__ import annotations

import os
from functools import lru_cache

_HF_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"


class VaderBackend:
    name = "vader"

    def __init__(self) -> None:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        self._an = SentimentIntensityAnalyzer()

    def polarity(self, text: str) -> float:
        return float(self._an.polarity_scores(text)["compound"])


class HFBackend:
    name = "hf"

    def __init__(self) -> None:
        from transformers import pipeline
        self._pipe = pipeline("sentiment-analysis", model=_HF_MODEL, truncation=True)

    def polarity(self, text: str) -> float:
        r = self._pipe(text[:512])[0]
        s = float(r["score"])
        return s if r["label"].upper().startswith("POS") else -s


@lru_cache(maxsize=1)
def get_backend():
    pref = os.getenv("SENTIMENT_BACKEND", "auto").lower()
    if pref == "vader":
        return VaderBackend()
    if pref == "hf":
        return HFBackend()
    # auto: try HF, fall back to VADER
    try:
        return HFBackend()
    except Exception:
        return VaderBackend()


def score_texts(texts: list[str]) -> list[float]:
    be = get_backend()
    return [be.polarity(t) for t in texts]


def label(polarity: float) -> str:
    if polarity > 0.15:
        return "positive"
    if polarity < -0.15:
        return "negative"
    return "neutral"


if __name__ == "__main__":
    be = get_backend()
    print(f"Active backend: {be.name}")
    samples = ["What a goal!! unreal", "terrible defending, embarrassing", "halftime and still level"]
    for s in samples:
        p = be.polarity(s)
        print(f"  [{label(p):>8}] {p:+.3f}  {s}")
