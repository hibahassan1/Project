"""Plotly figures with one shared theme."""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .ui import C

FONT = "Figtree, system-ui, sans-serif"
HEAT = [[0, "#E6F3F1"], [0.25, "#F7E7B4"], [0.5, "#F3BE62"], [0.75, "#E58A3C"], [1, "#C4552B"]]


def _style(fig, h):
    fig.update_layout(height=h, font=dict(family=FONT, color=C["ink"], size=13),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=8, r=8, t=8, b=8), hoverlabel=dict(font_family=FONT),
                      legend=dict(orientation="h", y=1.14, x=0, bgcolor="rgba(0,0,0,0)"))
    fig.update_xaxes(showgrid=False, linecolor=C["line"], ticks="")
    fig.update_yaxes(gridcolor="#E8EDF1", zeroline=False)
    return fig


def short(s):
    return s


def heatmap(sites, dlabels, traj, cleans, rain):
    fig = go.Figure(go.Heatmap(
        z=[list(traj[s]) for s in sites], x=dlabels, y=[short(s) for s in sites],
        colorscale=HEAT, zmin=0, zmax=12, xgap=6, ygap=6,
        colorbar=dict(title=dict(text="Loss %", side="top"), thickness=10, len=0.9, outlinewidth=0),
        hovertemplate="%{y}<br>%{x}<br>Soiling loss %{z:.1f}%<extra></extra>"))
    for j, s in enumerate(sites):
        for i in range(len(dlabels)):
            v = traj[s][i]
            tag = "clean" if cleans[s][i] else ("rain" if rain[s][i] else "")
            txt = f"<b>{v:.1f}%</b>" + (f"<br><span style='font-size:11px'>{tag}</span>" if tag else "")
            fig.add_annotation(x=dlabels[i], y=short(s), text=txt, showarrow=False,
                               font=dict(color="#fff" if v > 8 else C["ink"], size=13))
            if cleans[s][i]:
                fig.add_shape(type="rect", x0=i - 0.5, x1=i + 0.5, y0=j - 0.5, y1=j + 0.5,
                              line=dict(color=C["teal"], width=4), fillcolor="rgba(0,0,0,0)")
    _style(fig, 300)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(side="top")
    fig.update_layout(margin=dict(l=8, r=8, t=30, b=8))
    return fig


def site_map(sites, coords, today):
    fig = go.Figure(go.Scattermap(
        lat=[coords[s][0] for s in sites], lon=[coords[s][1] for s in sites], mode="markers+text",
        text=[short(s) for s in sites], textposition="top right", textfont=dict(size=12, color=C["ink"]),
        marker=dict(size=15, color=[C["alert"] if today[s] > 6 else (C["amber"] if today[s] > 3 else C["teal"]) for s in sites]),
        hovertemplate="%{text}<extra></extra>"))
    fig.update_layout(map=dict(style="carto-positron", center=dict(lat=24.25, lon=54.7), zoom=6.1),
                      height=300, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def soiling_lines(dlabels, p10, p50, p90, ai, base, clean_flags, rain_flags):
    fig = go.Figure()
    for i, r in enumerate(rain_flags):
        if r:
            fig.add_vrect(x0=i - 0.5, x1=i + 0.5, fillcolor="#E3EEF8", opacity=0.9, line_width=0, layer="below")
    fig.add_trace(go.Scatter(x=dlabels, y=p90, line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=dlabels, y=p10, fill="tonexty", line=dict(width=0), name="No-clean range (P10 to P90)",
                             fillcolor="rgba(245,166,35,0.22)", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=dlabels, y=p50, name="No cleaning", line=dict(dash="dot", color=C["dust"], width=2)))
    fig.add_trace(go.Scatter(x=dlabels, y=base, name="Fixed calendar", line=dict(color="#8FA0AE", width=2)))
    fig.add_trace(go.Scatter(x=dlabels, y=ai, name="AI plan", line=dict(color=C["teal"], width=4)))
    cx = [d for d, f in zip(dlabels, clean_flags) if f]
    cy = [v for v, f in zip(ai, clean_flags) if f]
    if cx:
        fig.add_trace(go.Scatter(x=cx, y=cy, mode="markers", name="Clean", marker=dict(symbol="diamond", size=14,
                                 color="#fff", line=dict(color=C["teal"], width=3)), hovertemplate="Clean on %{x}<extra></extra>"))
    _style(fig, 380)
    fig.update_yaxes(title="Soiling loss (%)", rangemode="tozero")
    fig.update_layout(hovermode="x unified")
    return fig


def drivers(dlabels, pm10, rain_mm, storm):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=dlabels, y=pm10, name="PM10 (µg/m³)", marker_color=C["dust"], opacity=0.9), secondary_y=False)
    fig.add_trace(go.Bar(x=dlabels, y=rain_mm, name="Rain (mm)", marker_color=C["rain"]), secondary_y=True)
    fig.add_hline(y=storm, line=dict(color=C["alert"], dash="dash", width=1.5), secondary_y=False,
                  annotation_text="Storm threshold", annotation_position="top left", annotation_font_color=C["alert"])
    _style(fig, 260)
    fig.update_layout(barmode="group", bargap=0.35)
    fig.update_yaxes(title_text="PM10", secondary_y=False)
    fig.update_yaxes(title_text="Rain mm", secondary_y=True, showgrid=False, rangemode="tozero")
    return fig
