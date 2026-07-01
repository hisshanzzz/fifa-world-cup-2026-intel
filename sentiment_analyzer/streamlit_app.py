"""Live match sentiment dashboard (Streamlit).

Replays tweets minute-by-minute with play/pause clock, rolling per-team sentiment,
goal markers, split bar, and overall mood gauge. Primary entry for local + cloud.

Run:  streamlit run sentiment_analyzer/streamlit_app.py
      python run.py sentiment
"""
from __future__ import annotations

import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotly.graph_objects as go
import streamlit as st

from sentiment_analyzer.ingest import list_matches_with_tweets
from sentiment_analyzer.pipeline import current_split, goals, score_match, timeline
from sentiment_analyzer.sentiment import get_backend

MAX_MIN = 95
COLORS = {"positive": "#2ca02c", "neutral": "#999", "negative": "#d62728"}

st.set_page_config(page_title="WC2026 Live Sentiment", page_icon="📡", layout="wide")
st.title("📡 FIFA World Cup 2026 — Live Match Sentiment")
st.caption(f"tweepy + HuggingFace/VADER + Streamlit · backend: {get_backend().name}")

matches = list_matches_with_tweets()
match_opts = {f"{r.home} vs {r.away}  ({r.match_id})": r.match_id
              for _, r in matches.iterrows()}

if "minute" not in st.session_state:
    st.session_state.minute = MAX_MIN
if "playing" not in st.session_state:
    st.session_state.playing = False


@st.fragment(run_every=timedelta(milliseconds=900))
def _auto_advance():
    if st.session_state.playing:
        if st.session_state.minute >= MAX_MIN:
            st.session_state.minute = 0
        else:
            st.session_state.minute += 2


def _timeline_fig(match_id: str, minute: int) -> go.Figure:
    tl = timeline(match_id, upto_minute=minute)
    gmins = [g for g in goals(match_id) if g <= minute]

    fig = go.Figure()
    for team, grp in tl.groupby("team"):
        fig.add_trace(go.Scatter(
            x=grp.match_minute, y=grp.rolling, mode="lines",
            name=team, line=dict(width=3),
        ))
    for gm in gmins:
        fig.add_vline(x=gm, line_dash="dash", line_color="crimson",
                      annotation_text="⚽ goal", annotation_position="top")
    fig.add_hline(y=0, line_color="#bbb")
    fig.update_layout(
        title="Rolling sentiment by team (−1 negative … +1 positive)",
        xaxis_title="match minute", yaxis_title="sentiment",
        yaxis=dict(range=[-1, 1]), height=420,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


def _split_fig(match_id: str, minute: int) -> go.Figure:
    sp = current_split(match_id, upto_minute=minute)
    fig = go.Figure(go.Bar(
        x=sp.sentiment, y=sp["count"],
        marker_color=[COLORS[s] for s in sp.sentiment],
    ))
    fig.update_layout(title="Tweet sentiment counts", height=320,
                      margin=dict(l=10, r=10, t=40, b=10))
    return fig


def _gauge_fig(match_id: str, minute: int) -> go.Figure:
    tl = timeline(match_id, upto_minute=minute)
    avg = tl.rolling.mean() if len(tl) else 0
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=round(float(avg), 3),
        title={"text": "Overall mood"},
        gauge={"axis": {"range": [-1, 1]},
               "bar": {"color": "#2ca02c" if avg >= 0 else "#d62728"},
               "steps": [{"range": [-1, 0], "color": "#fde2e1"},
                         {"range": [0, 1], "color": "#e3f4e1"}]}))
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10))
    return fig


if not match_opts:
    st.warning("No matches with tweets found in data/tweets_sample.csv.")
    st.stop()

default_label = next(iter(match_opts))
if "match_id" not in st.session_state:
    st.session_state.match_id = match_opts[default_label]

labels = list(match_opts.keys())
try:
    match_idx = next(i for i, k in enumerate(labels) if match_opts[k] == st.session_state.match_id)
except StopIteration:
    match_idx = 0

ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([3, 1, 1, 1])
with ctrl1:
    label = st.selectbox("Match", labels, index=match_idx)
    st.session_state.match_id = match_opts[label]
with ctrl2:
    if st.button("▶ Play"):
        st.session_state.playing = True
with ctrl3:
    if st.button("⏸ Pause"):
        st.session_state.playing = False
with ctrl4:
    st.metric("Clock", f"{st.session_state.minute}'")

_auto_advance()

minute = st.slider("Match minute", 0, MAX_MIN, st.session_state.minute,
                   format="%d'", key="minute_slider")
st.session_state.minute = minute

match_id = st.session_state.match_id
score_match(match_id)

st.plotly_chart(_timeline_fig(match_id, minute), use_container_width=True)
col_a, col_b = st.columns(2)
with col_a:
    st.plotly_chart(_split_fig(match_id, minute), use_container_width=True)
with col_b:
    st.plotly_chart(_gauge_fig(match_id, minute), use_container_width=True)
