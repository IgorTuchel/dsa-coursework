import plotly.graph_objects as go
from components.charts import (
    avg_vs_best_distance_chart,
    avg_vs_best_time_chart,
    distance_vs_runtime_chart,
    per_run_distance_chart,
    per_run_time_chart,
)
from components.data import load_batch_context, load_batch_files, load_json, pct_diff
from components.ui import render_batch_header, render_table

import streamlit as st

st.set_page_config(page_title="Comparisons", layout="wide")
st.title("Comparisons")
st.caption("Compare algorithms across quality, runtime, and stability.")

batch_files = load_batch_files()
if not batch_files:
    st.warning("No batch JSON files found in ./runs")
    st.stop()

selected_batch = st.sidebar.selectbox("Batch file", [str(p) for p in batch_files])
batch = load_json(selected_batch)
algorithms = batch.get("algorithms", [])
selected_algorithms = st.sidebar.multiselect(
    "Algorithms", algorithms, default=algorithms
)

context = load_batch_context(selected_batch, selected_algorithms)
if not context["records"]:
    st.error("No run files matched the selected algorithms.")
    st.stop()

render_batch_header(
    context["batch_uuid"],
    context["path_name"],
    context["dataset_path"],
    context["runs_per_algorithm"],
)

render_table("Baseline comparison", context["comparison_rows"])

left, right = st.columns(2)
with left:
    st.plotly_chart(
        per_run_distance_chart(context["records"], context["summary"]),
        width="stretch",
    )
with right:
    st.plotly_chart(
        per_run_time_chart(context["records"], context["summary"]),
        width="stretch",
    )

left, right = st.columns(2)
with left:
    st.plotly_chart(
        avg_vs_best_distance_chart(context["summary"]),
        width="stretch",
    )
with right:
    st.plotly_chart(
        avg_vs_best_time_chart(context["summary"]),
        width="stretch",
    )

baseline = context["baseline"]
delta_rows = []

if baseline:
    for row in context["summary"]:
        delta_rows.append(
            {
                "algorithm": row["algorithm"],
                "distance_delta_pct": round(
                    pct_diff(
                        row["avg_distance"],
                        baseline["avg_distance"],
                        lower_is_better=True,
                    ),
                    2,
                ),
                "time_delta_pct": round(
                    pct_diff(
                        row["avg_time"],
                        baseline["avg_time"],
                        lower_is_better=True,
                    ),
                    2,
                ),
                "routes_delta_pct": round(
                    pct_diff(
                        row["avg_routes"],
                        baseline["avg_routes"],
                        lower_is_better=True,
                    ),
                    2,
                ),
            }
        )

st.subheader("Percentage deltas vs baseline")
st.caption(f"Baseline: {baseline['algorithm']} (set to lowest average distance).")
st.dataframe(delta_rows, width="stretch", hide_index=True)

left, right = st.columns(2)
with left:
    distance_delta_fig = go.Figure()
    distance_delta_fig.add_bar(
        x=[row["algorithm"] for row in delta_rows],
        y=[row["distance_delta_pct"] for row in delta_rows],
        text=[f"{row['distance_delta_pct']:+.2f}%" for row in delta_rows],
        textposition="outside",
    )
    distance_delta_fig.update_layout(
        title="Average distance vs baseline (%)",
        yaxis_title="Percent",
        showlegend=False,
    )
    st.plotly_chart(distance_delta_fig, width="stretch")

with right:
    time_delta_fig = go.Figure()
    time_delta_fig.add_bar(
        x=[row["algorithm"] for row in delta_rows],
        y=[row["time_delta_pct"] for row in delta_rows],
        text=[f"{row['time_delta_pct']:+.2f}%" for row in delta_rows],
        textposition="outside",
    )
    time_delta_fig.update_layout(
        title="Average runtime vs baseline (%)",
        yaxis_title="Percent",
        showlegend=False,
    )
    st.plotly_chart(time_delta_fig, width="stretch")

st.plotly_chart(distance_vs_runtime_chart(context["records"]), width="stretch")
