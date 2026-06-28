"""Live player dashboard: ranking + playing-style clusters.

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
st.caption("pandas + plotly + KMeans · ranking by goals / assists / impact · style clusters")


@st.cache_data
def load(k: int):
    df = get_player_frame()
    clustered, centers = cluster_players(df, k=k)
    return clustered, centers


with st.sidebar:
    st.header("Controls")
    k = st.slider("Number of style clusters (k)", 3, 7, 5)
    metric = st.selectbox("Rank by", ["impact", "goals", "assists", "key_passes", "goals90", "assists90"])

df, centers = load(k)
with st.sidebar:
    team_filter = st.multiselect("Filter teams", sorted(df.team.unique()), help="leave empty for all")
if team_filter:
    df = df[df.team.isin(team_filter)]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Players tracked", len(df))
k2.metric("Top scorer", df.sort_values("goals", ascending=False).iloc[0]["name"],
          int(df.goals.max()))
k3.metric("Most assists", df.sort_values("assists", ascending=False).iloc[0]["name"],
          int(df.assists.max()))
k4.metric("Highest impact", df.sort_values("impact", ascending=False).iloc[0]["name"],
          float(df.impact.max()))

left, right = st.columns([3, 2])

with left:
    st.subheader(f"Leaderboard — by {metric}")
    lb = df.sort_values(metric, ascending=False).head(20)
    fig = px.bar(lb, x=metric, y="name", orientation="h", color="style",
                 hover_data=["team", "position", "goals", "assists", "impact"])
    fig.update_layout(yaxis=dict(autorange="reversed"), height=560,
                      margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Playing-style map")
    fig2 = px.scatter(
        df, x="dribbles90", y="goals90", size="impact", color="style",
        hover_name="name", hover_data=["team", "assists90", "key_passes90"],
        size_max=24)
    fig2.update_layout(height=560, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Style group profiles (avg per-90)")
profile = df.groupby("style")[STYLE_FEATURES + ["impact"]].mean().round(2).reset_index()
st.dataframe(profile, use_container_width=True, hide_index=True)

st.subheader("Full leaderboard")
st.dataframe(leaderboard(df, by=metric, top=50), use_container_width=True, hide_index=True)
