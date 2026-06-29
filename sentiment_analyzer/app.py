"""Live match sentiment dashboard (Plotly Dash).

A dcc.Interval advances a 'live' match clock; as the clock moves we reveal more
tweets and re-plot how sentiment shifts -- with dashed markers on every goal so
you can literally watch opinion swing after a goal.

Run:  python sentiment_analyzer/app.py   ->  http://127.0.0.1:8050
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State

from sentiment_analyzer.ingest import list_matches_with_tweets
from sentiment_analyzer.pipeline import current_split, goals, score_match, timeline
from sentiment_analyzer.sentiment import get_backend

MATCHES = list_matches_with_tweets()
MATCH_OPTS = [{"label": f"{r.home} vs {r.away}  ({r.match_id})", "value": r.match_id}
              for _, r in MATCHES.iterrows()]
MAX_MIN = 95

app = Dash(__name__, title="WC2026 Live Sentiment")
server = app.server

app.layout = html.Div(style={"fontFamily": "Inter, system-ui, sans-serif",
                             "maxWidth": "1100px", "margin": "0 auto", "padding": "16px"},
    children=[
        html.H2("📡 FIFA World Cup 2026 — Live Match Sentiment"),
        html.P(f"tweepy + HuggingFace/VADER + Plotly Dash · backend: {get_backend().name}",
               style={"color": "#666"}),
        html.Div(style={"display": "flex", "gap": "16px", "alignItems": "center"}, children=[
            dcc.Dropdown(id="match", options=MATCH_OPTS,
                         value=MATCH_OPTS[0]["value"] if MATCH_OPTS else None,
                         style={"width": "360px"}),
            html.Button("▶ Play", id="play", n_clicks=0),
            html.Button("⏸ Pause", id="pause", n_clicks=0),
            html.Div(id="clock", style={"fontWeight": "bold", "fontSize": "18px"}),
        ]),
        dcc.Slider(id="minute", min=0, max=MAX_MIN, step=1, value=MAX_MIN,
                   marks={0: "0'", 45: "HT", 90: "FT"}),
        dcc.Interval(id="tick", interval=900, disabled=True),
        dcc.Graph(id="timeline"),
        html.Div(style={"display": "flex", "gap": "16px"}, children=[
            dcc.Graph(id="split", style={"flex": 1}),
            dcc.Graph(id="gauge", style={"flex": 1}),
        ]),
    ])


@app.callback(Output("tick", "disabled"),
              Input("play", "n_clicks"), Input("pause", "n_clicks"))
def toggle(play, pause):
    return not (play > pause)


@app.callback(Output("minute", "value"),
              Input("tick", "n_intervals"), State("minute", "value"))
def advance(_, minute):
    return 0 if minute is None or minute >= MAX_MIN else minute + 2


@app.callback(
    Output("timeline", "figure"), Output("split", "figure"),
    Output("gauge", "figure"), Output("clock", "children"),
    Input("match", "value"), Input("minute", "value"))
def render(match_id, minute):
    if not match_id:
        return go.Figure(), go.Figure(), go.Figure(), ""
    tl = timeline(match_id, upto_minute=minute)
    gmins = [g for g in goals(match_id) if g <= minute]

    fig = go.Figure()
    for team, grp in tl.groupby("team"):
        fig.add_trace(go.Scatter(x=grp.match_minute, y=grp.rolling, mode="lines",
                                 name=team, line=dict(width=3)))
    for gm in gmins:
        fig.add_vline(x=gm, line_dash="dash", line_color="crimson",
                      annotation_text="⚽ goal", annotation_position="top")
    fig.add_hline(y=0, line_color="#bbb")
    fig.update_layout(title="Rolling sentiment by team (−1 negative … +1 positive)",
                      xaxis_title="match minute", yaxis_title="sentiment",
                      yaxis=dict(range=[-1, 1]), height=420,
                      margin=dict(l=10, r=10, t=40, b=10))

    sp = current_split(match_id, upto_minute=minute)
    colors = {"positive": "#2ca02c", "neutral": "#999", "negative": "#d62728"}
    split_fig = go.Figure(go.Bar(x=sp.sentiment, y=sp["count"],
                                 marker_color=[colors[s] for s in sp.sentiment]))
    split_fig.update_layout(title="Tweet sentiment counts", height=320,
                            margin=dict(l=10, r=10, t=40, b=10))

    avg = tl.rolling.mean() if len(tl) else 0
    gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=round(float(avg), 3),
        title={"text": "Overall mood"},
        gauge={"axis": {"range": [-1, 1]},
               "bar": {"color": "#2ca02c" if avg >= 0 else "#d62728"},
               "steps": [{"range": [-1, 0], "color": "#fde2e1"},
                         {"range": [0, 1], "color": "#e3f4e1"}]}))
    gauge.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10))

    return fig, split_fig, gauge, f"⏱ {minute}'"


if __name__ == "__main__":
    # warm the cache / backend once at startup
    if MATCH_OPTS:
        score_match(MATCH_OPTS[0]["value"])
    app.run(debug=False, port=8050)
