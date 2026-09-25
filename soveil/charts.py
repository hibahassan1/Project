"""Plotly figures with one shared theme. Tuned to stay legible down to ~360px phone width."""
import numpy as np
import plotly.graph_objects as go
from .ui import C

FONT = "Figtree, system-ui, sans-serif"
HEAT = [[0, "#E6F3F1"], [0.25, "#F7E7B4"], [0.5, "#F3BE62"], [0.75, "#E58A3C"], [1, "#C4552B"]]


def _style(fig, h, legend=True, top_margin=None):
    t = top_margin if top_margin is not None else (54 if legend else 10)
    fig.update_layout(height=h, font=dict(family=FONT, color=C["ink"], size=11),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=6, r=6, t=t, b=6), hoverlabel=dict(font_family=FONT),
                      legend=dict(orientation="h", y=1.22, x=0, xanchor="left", bgcolor="rgba(0,0,0,0)",
                                 font=dict(size=10)) if legend else dict())
    fig.update_xaxes(showgrid=False, linecolor=C["line"], ticks="", tickfont=dict(size=10))
    fig.update_yaxes(gridcolor="#E8EDF1", zeroline=False, tickfont=dict(size=10))
    return fig


def short(s):
    return s


def heatmap(sites, dlabels, traj, cleans, rain):
    """No colorbar (it clipped on narrow screens) — colour meaning is given as a text legend
    underneath the chart via ui.gradient_legend(). Cell text is just the number; the clean/rain
    state is shown by the outline and a small dot instead of extra overlapping text."""
    fig = go.Figure(go.Heatmap(
        z=[list(traj[s]) for s in sites], x=dlabels, y=[short(s) for s in sites],
        colorscale=HEAT, zmin=0, zmax=12, xgap=5, ygap=5, showscale=False,
        hovertemplate="%{y}<br>%{x}<br>Soiling loss %{z:.1f}%<extra></extra>"))
    for j, s in enumerate(sites):
        for i in range(len(dlabels)):
            v = traj[s][i]
            fig.add_annotation(x=dlabels[i], y=short(s), text=f"<b>{v:.1f}%</b>", showarrow=False,
                               font=dict(color="#fff" if v > 8 else C["ink"], size=10.5))
            if cleans[s][i]:
                fig.add_shape(type="rect", x0=i - 0.5, x1=i + 0.5, y0=j - 0.5, y1=j + 0.5,
                              line=dict(color=C["teal"], width=3), fillcolor="rgba(0,0,0,0)")
            elif rain[s][i]:
                fig.add_shape(type="rect", x0=i - 0.5, x1=i + 0.5, y0=j - 0.5, y1=j + 0.5,
                              line=dict(color=C["rain"], width=1.5, dash="dot"), fillcolor="rgba(0,0,0,0)")
    _style(fig, 240, legend=False, top_margin=26)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(side="top")
    fig.update_layout(margin=dict(l=4, r=4, t=30, b=4))
    return fig


def site_map(sites, coords, today):
    fig = go.Figure(go.Scattermap(
        lat=[coords[s][0] for s in sites], lon=[coords[s][1] for s in sites], mode="markers+text",
        text=[short(s) for s in sites], textposition="top right", textfont=dict(size=11, color=C["ink"]),
        marker=dict(size=14, color=[C["alert"] if today[s] > 6 else (C["amber"] if today[s] > 3 else C["teal"]) for s in sites]),
        hovertemplate="%{text}<extra></extra>"))
    fig.update_layout(map=dict(style="carto-positron", center=dict(lat=24.25, lon=54.7), zoom=6.0),
                      height=240, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def soiling_lines(dlabels, p10, p50, p90, ai, base, clean_flags, rain_flags):
    """Short legend labels + a bigger top margin so the 5-item legend has room to wrap onto
    two lines without pushing into the plot area (the old bug on narrow screens)."""
    fig = go.Figure()
    for i, r in enumerate(rain_flags):
        if r:
            fig.add_vrect(x0=i - 0.5, x1=i + 0.5, fillcolor="#E3EEF8", opacity=0.9, line_width=0, layer="below")
    fig.add_trace(go.Scatter(x=dlabels, y=p90, line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=dlabels, y=p10, fill="tonexty", line=dict(width=0), name="P10–P90 range",
                             fillcolor="rgba(245,166,35,0.22)", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=dlabels, y=p50, name="No cleaning", line=dict(dash="dot", color=C["dust"], width=2)))
    fig.add_trace(go.Scatter(x=dlabels, y=base, name="Calendar", line=dict(color="#8FA0AE", width=2)))
    fig.add_trace(go.Scatter(x=dlabels, y=ai, name="AI plan", line=dict(color=C["teal"], width=3.5)))
    cx = [d for d, f in zip(dlabels, clean_flags) if f]
    cy = [v for v, f in zip(ai, clean_flags) if f]
    if cx:
        fig.add_trace(go.Scatter(x=cx, y=cy, mode="markers", name="Clean", marker=dict(symbol="diamond", size=12,
                                 color="#fff", line=dict(color=C["teal"], width=3)), hovertemplate="Clean on %{x}<extra></extra>"))
    _style(fig, 340, legend=True, top_margin=62)
    fig.update_yaxes(title=dict(text="Soiling loss (%)", font=dict(size=11)), rangemode="tozero")
    fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.28, x=0, xanchor="left",
                                                          font=dict(size=10), bgcolor="rgba(0,0,0,0)"))
    return fig


def drivers(dlabels, pm10, rain_mm, storm):
    """Single axis (rain scaled up ×20 and labelled as such) instead of a secondary y-axis —
    dual axes produced ugly auto-ticks and let the storm-threshold label collide with the legend.
    Legend now sits top-right, annotation stays top-left, so they never overlap."""
    rain_scaled = np.asarray(rain_mm) * 20
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dlabels, y=pm10, name="PM10 (µg/m³)", marker_color=C["dust"], opacity=0.9))
    fig.add_trace(go.Bar(x=dlabels, y=rain_scaled, name="Rain (mm ×20)", marker_color=C["rain"]))
    fig.add_hline(y=storm, line=dict(color=C["alert"], dash="dash", width=1.5),
                  annotation_text="Storm threshold", annotation_position="top left",
                  annotation_font=dict(color=C["alert"], size=10))
    _style(fig, 230, legend=True, top_margin=52)
    fig.update_layout(barmode="group", bargap=0.35,
                      legend=dict(orientation="h", y=1.24, x=1, xanchor="right", font=dict(size=10), bgcolor="rgba(0,0,0,0)"))
    fig.update_yaxes(title=dict(text="PM10 (µg/m³)", font=dict(size=11)))
    return fig
