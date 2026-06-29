"""Live player dashboard: real WC2026 scorer ranking + scoring-style clusters.

Run:  streamlit run player_tracker/app.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotly.express as px
import streamlit as st

from player_tracker.clustering import STYLE_FEATURES, cluster_players
from player_tracker.data import get_player_frame, leaderboard

st.set_page_config(page_title="WC2026 Player Tracker", page_icon="📊", layout="wide")
st.title("📊 FIFA World Cup 2026 — Player Performance Tracker")
st.caption("Real goalscorer data (martj42) · pandas + plotly + KMeans · ranking by goals / impact · scoring-style clusters")


@st.cache_data
def load(k: int):
    df = get_player_frame()
    clustered, centers = cluster_players(df, k=k)
    return clustered, centers


with st.sidebar:
    st.header("Controls")
    k = st.slider("Number of style clusters (k)", 3, 7, 5)
    metric = st.selectbox("Rank by", ["impact", "goals", "open_play_goals",
                                      "late_goals", "goals_per_match", "multi_goal_games"])
    min_goals = st.slider("Min goals", 1, 5, 1)

df, centers = load(k)
df = df[df.goals >= min_goals]
with st.sidebar:
    team_filter = st.multiselect("Filter teams", sorted(df.team.unique()), help="leave empty for all")
if team_filter:
    df = df[df.team.isin(team_filter)]

st.info("Real data covers **goals** (open-play vs penalty), goal **minutes**, and "
        "**multi-goal games**. Assists / xG / defensive stats need an FBref export "
        "(the loader accepts one) — they're omitted here rather than faked.")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Scorers tracked", len(df))
k2.metric("Golden Boot", df.sort_values("goals", ascending=False).iloc[0]["name"],
          int(df.goals.max()))
top_clutch = df.sort_values("late_goals", ascending=False).iloc[0]
k3.metric("Most late goals", top_clutch["name"], int(top_clutch.late_goals))
k4.metric("Highest impact", df.sort_values("impact", ascending=False).iloc[0]["name"],
          float(df.impact.max()))

left, right = st.columns([3, 2])

with left:
    st.subheader(f"Leaderboard — by {metric}")
    lb = df.sort_values(metric, ascending=False).head(20)
    fig = px.bar(lb, x=metric, y="name", orientation="h", color="style",
                 hover_data=["team", "goals", "penalty_goals", "late_goals", "impact"])
    fig.update_layout(yaxis=dict(autorange="reversed"), height=600,
                      margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Scoring-style map")
    fig2 = px.scatter(
        df, x="avg_goal_minute", y="goals", size="impact", color="style",
        hover_name="name", hover_data=["team", "goals_per_match", "penalty_share"],
        size_max=26)
    fig2.update_layout(height=600, margin=dict(l=0, r=0, t=10, b=0),
                       xaxis_title="avg goal minute (earlier ← → later)")
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Style group profiles (averages)")
profile = df.groupby("style")[STYLE_FEATURES + ["goals", "impact"]].mean().round(2).reset_index()
st.dataframe(profile, use_container_width=True, hide_index=True)

st.subheader("Full leaderboard")
st.dataframe(leaderboard(df, by=metric, top=50), use_container_width=True, hide_index=True)
