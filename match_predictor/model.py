"""Train and persist the match-outcome classifier.

Model: standardise features -> multinomial Logistic Regression over {H, D, A}.
Logistic Regression gives well-calibrated probabilities (important because we
feed them into a Monte-Carlo tournament simulation), trains in milliseconds, and
is easy to reason about. A RandomForest is included as an easy swap.

Run:  py -m match_predictor.model
"""
from __future__ import annotations

import os
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .features import FEATURE_COLS, build_training_frame, load_raw, team_stats

MODELS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
MODEL_PATH = os.path.join(MODELS, "predictor.joblib")


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("scale", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, C=1.0)),  # multinomial is default (lbfgs)
    ])


def train(save: bool = True) -> dict:
    teams, history = load_raw()
    X, y = build_training_frame(teams, history)
    pipe = build_pipeline()

    acc = cross_val_score(pipe, X, y, cv=5, scoring="accuracy")
    ll = cross_val_score(pipe, X, y, cv=5, scoring="neg_log_loss")
    pipe.fit(X, y)

    if save:
        os.makedirs(MODELS, exist_ok=True)
        joblib.dump({"pipeline": pipe, "features": FEATURE_COLS,
                     "stats": team_stats(teams, history)}, MODEL_PATH)

    metrics = {
        "cv_accuracy": round(float(np.mean(acc)), 3),
        "cv_logloss": round(float(-np.mean(ll)), 3),
        "n_samples": int(len(y)),
        "classes": list(pipe.named_steps["clf"].classes_),
    }
    return metrics


def load_model():
    if not os.path.exists(MODEL_PATH):
        train()
    return joblib.load(MODEL_PATH)


if __name__ == "__main__":
    m = train()
    print("Trained match predictor:")
    for k, v in m.items():
        print(f"  {k}: {v}")
    print(f"Saved -> {os.path.relpath(MODEL_PATH)}")
