"""Streamlit dashboard for the match predictor.

Run:  streamlit run match_predictor/app.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.express as px
import streamlit as st

from match_predictor.model import load_model, train
from match_predictor.predict import predict_fixtures, simulate_title_odds
from match_predictor.update import record_result

st.set_page_config(page_title="WC2026 Match Predictor", page_icon="⚽", layout="wide")
st.title("⚽ FIFA World Cup 2026 — Match Outcome Predictor")
st.caption("pandas + scikit-learn · multinomial logistic regression · Monte-Carlo bracket sim")


@st.cache_resource
def get_model():
    return load_model()


@st.cache_data
def get_predictions():
    return predict_fixtures(get_model())


@st.cache_data
def get_odds(n_sims: int):
    return simulate_title_odds(get_model(), n_sims=n_sims)


with st.sidebar:
    st.header("Controls")
    n_sims = st.slider("Monte-Carlo simulations", 1000, 20000, 5000, step=1000)
    stage_filter = st.selectbox("Stage", ["Round of 32", "Group", "All"], index=0)
    only_remaining = st.checkbox("Only unplayed matches", value=True)
    if st.button("Retrain model"):
        with st.spinner("Training..."):
            m = train()
        st.success(f"Retrained. CV acc={m['cv_accuracy']}, logloss={m['cv_logloss']}")
        st.cache_resource.clear(); st.cache_data.clear()
    st.divider()
    st.subheader("Record a result")
    preds = get_predictions()
    pending = preds[~preds.played]
    if len(pending):
        mid = st.selectbox("Match", pending.match_id.tolist())
        row = pending[pending.match_id == mid].iloc[0]
        st.write(f"**{row.home} vs {row.away}**")
        hg = st.number_input(f"{row.home} goals", 0, 15, 1)
        ag = st.number_input(f"{row.away} goals", 0, 15, 0)
        if st.button("Save result & refresh"):
            record_result(mid, int(hg), int(ag))
            st.cache_data.clear()
            st.success("Saved. Predictions updated.")
            st.rerun()
    else:
        st.info("All fixtures recorded.")

preds = get_predictions()


def apply_filters(df):
    out = df.copy()
    if stage_filter != "All" and "stage" in out.columns:
        out = out[out.stage == stage_filter]
    if only_remaining:
        out = out[~out.played]
    return out


col1, col2 = st.columns([3, 2])

with col1:
    label = "Remaining" if only_remaining else "All"
    st.subheader(f"{label} {stage_filter if stage_filter != 'All' else ''} predictions".replace("  ", " ").strip())
    show = apply_filters(preds)
    if len(show):
        show["pick"] = show.apply(
            lambda r: r.home if r.p_home >= max(r.p_draw, r.p_away)
            else (r.away if r.p_away >= r.p_draw else "Draw"), axis=1)
        cols = ["match_id", "kickoff", "stage", "home", "away", "p_home", "p_draw", "p_away", "pick", "played", "score"]
        st.dataframe(show[[c for c in cols if c in show.columns]],
                     use_container_width=True, hide_index=True)
    else:
        st.info("No matches for this filter.")

with col2:
    st.subheader("Title odds")
    odds = get_odds(n_sims)
    fig = px.bar(odds.head(12), x="title_prob", y="team", orientation="h",
                 color="title_prob", color_continuous_scale="Viridis")
    fig.update_layout(yaxis=dict(autorange="reversed"), height=460,
                      coloraxis_showscale=False, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Next match win-probability breakdown")
_scope = preds[preds.stage == stage_filter] if stage_filter != "All" else preds
nxt = _scope[~_scope.played].head(1)
if len(nxt):
    r = nxt.iloc[0]
    bd = pd.DataFrame({
        "outcome": [f"{r.home} win", "Draw", f"{r.away} win"],
        "prob": [r.p_home, r.p_draw, r.p_away],
    })
    st.plotly_chart(px.bar(bd, x="outcome", y="prob", color="outcome"),
                    use_container_width=True)
else:
    st.info("No upcoming matches — tournament complete.")
