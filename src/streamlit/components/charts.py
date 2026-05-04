import plotly.express as px
import plotly.graph_objects as go
from components.data import padded_range


def per_run_distance_chart(records, summary):
    fig = px.strip(
        records,
        x="algorithm",
        y="total_distance",
        color="algorithm",
        stripmode="overlay",
        title="Total distance per run",
    )
    fig.update_traces(
        jitter=0.22,
        marker=dict(size=10, line=dict(width=1, color="white"), opacity=0.85),
        showlegend=False,
    )
    for item in summary:
        fig.add_hline(
            y=item["avg_distance"],
            line_dash="dash",
            line_width=2,
            annotation_text=f"{item['algorithm']} mean",
            annotation_position="top left",
        )
    axis = padded_range([r["total_distance"] for r in records])
    if axis:
        fig.update_yaxes(range=axis)
    return fig


def per_run_time_chart(records, summary):
    fig = px.strip(
        records,
        x="algorithm",
        y="time_taken",
        color="algorithm",
        stripmode="overlay",
        title="Runtime per run",
    )
    fig.update_traces(
        jitter=0.22,
        marker=dict(size=10, line=dict(width=1, color="white"), opacity=0.85),
        showlegend=False,
    )
    for item in summary:
        fig.add_hline(
            y=item["avg_time"],
            line_dash="dash",
            line_width=2,
            annotation_text=f"{item['algorithm']} mean",
            annotation_position="top left",
        )
    axis = padded_range([r["time_taken"] for r in records])
    if axis:
        fig.update_yaxes(range=axis)
    return fig


def avg_vs_best_distance_chart(summary):
    fig = go.Figure()
    fig.add_bar(
        x=[r["algorithm"] for r in summary],
        y=[r["avg_distance"] for r in summary],
        text=[f"{r['avg_distance']:.2f}" for r in summary],
        textposition="outside",
    )
    fig.add_scatter(
        x=[r["algorithm"] for r in summary],
        y=[r["best_distance"] for r in summary],
        mode="markers+text",
        text=[f"best {r['best_distance']:.2f}" for r in summary],
        textposition="top center",
    )
    fig.update_layout(title="Average vs best distance", showlegend=False)
    axis = padded_range(
        [r["avg_distance"] for r in summary] + [r["best_distance"] for r in summary]
    )
    if axis:
        fig.update_yaxes(range=axis)
    return fig


def avg_vs_best_time_chart(summary):
    fig = go.Figure()
    fig.add_bar(
        x=[r["algorithm"] for r in summary],
        y=[r["avg_time"] for r in summary],
        text=[f"{r['avg_time']:.2f}s" for r in summary],
        textposition="outside",
    )
    fig.add_scatter(
        x=[r["algorithm"] for r in summary],
        y=[r["best_time"] for r in summary],
        mode="markers+text",
        text=[f"best {r['best_time']:.2f}s" for r in summary],
        textposition="top center",
    )
    fig.update_layout(title="Average vs best runtime", showlegend=False)
    axis = padded_range(
        [r["avg_time"] for r in summary] + [r["best_time"] for r in summary]
    )
    if axis:
        fig.update_yaxes(range=axis)
    return fig


def distance_vs_runtime_chart(records):
    fig = px.scatter(
        records,
        x="time_taken",
        y="total_distance",
        color="algorithm",
        hover_data=["run_uuid", "route_count", "capacity"],
        title="Distance vs runtime",
    )
    x_axis = padded_range([r["time_taken"] for r in records])
    y_axis = padded_range([r["total_distance"] for r in records])
    if x_axis:
        fig.update_xaxes(range=x_axis)
    if y_axis:
        fig.update_yaxes(range=y_axis)
    return fig
