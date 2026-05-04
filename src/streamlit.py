import json
from collections import defaultdict
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go

import streamlit as st

st.set_page_config(page_title="VRP Comparison Dashboard", layout="wide")

RUNS_DIR = Path("./runs")

st.title("VRP Comparison Dashboard")
st.caption("Compare batch algorithm results.")


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_batch_files():
    return sorted([p for p in RUNS_DIR.glob("*_batch_*.json") if p.is_file()])


def load_run(path: str):
    return load_json(path)


def padded_range(values, pad_ratio: float = 0.06):
    nums = [float(v) for v in values if v is not None]
    if not nums:
        return None
    lo = min(nums)
    hi = max(nums)
    if lo == hi:
        pad = max(abs(lo) * pad_ratio, 1.0)
        return [lo - pad, hi + pad]
    pad = (hi - lo) * pad_ratio
    return [lo - pad, hi + pad]


def flatten_run(
    run_data: dict, algorithm: str, batch_uuid: str, run_uuid: str, run_file: str
):
    hp = run_data.get("additional_params") or {}
    inp = run_data.get("input_params") or {}
    hw = run_data.get("hardware_info") or {}
    return {
        "batch_uuid": batch_uuid,
        "run_uuid": run_uuid,
        "file_name": run_file,
        "algorithm": algorithm,
        "dataset": run_data.get("data_used"),
        "total_distance": run_data.get("total_distance"),
        "time_taken": run_data.get("time_taken"),
        "memory_usage": run_data.get("memory_usage"),
        "route_count": len(run_data.get("routes", [])),
        "customers": len(inp.get("customers", [])),
        "capacity": inp.get("capacity"),
        "rand_seed": hp.get("rand_seed"),
        "cpu_brand": hw.get("cpu_brand"),
        "cpu_cores": hw.get("cpu_cores"),
        "cpu_bits": hw.get("cpu_bits"),
        "platform": hw.get("platform"),
    }


def stability_label(values: list[float]) -> str:
    if not values:
        return "N/A"
    rounded = set(round(v, 10) for v in values)
    return "Deterministic" if len(rounded) == 1 else "Variable"


def pct_diff(value: float, reference: float, lower_is_better: bool = True) -> float:
    if reference in (None, 0) or value is None:
        return 0.0
    if lower_is_better:
        return (reference - value) / reference * 100
    return (value - reference) / reference * 100


def fmt_pct(value: float) -> str:
    return f"{value:+.2f}%"


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

batch_uuid = batch.get("batch_uuid", "unknown")
dataset_path = batch.get("data_set_path", "")
path_name = batch.get("path_name", "")
runs_per_algorithm = batch.get("amount", 0)

records = []
run_payloads = []

for algorithm, uuids in (batch.get("outputs") or {}).items():
    if algorithm not in selected_algorithms:
        continue
    for run_uuid in uuids:
        run_file = RUNS_DIR / f"{batch_uuid}_{run_uuid}_{path_name}.json"
        if not run_file.exists():
            continue
        run_data = load_run(str(run_file))
        run_payloads.append((algorithm, run_uuid, str(run_file), run_data))
        records.append(
            flatten_run(run_data, algorithm, batch_uuid, run_uuid, run_file.name)
        )

if not records:
    st.error("No run files matched the selected algorithms.")
    st.stop()

st.caption(
    f"Batch {batch_uuid} • Dataset {path_name} • Source {dataset_path} • Runs per algorithm {runs_per_algorithm}"
)

cols = st.columns(4)
cols[0].metric("Runs loaded", len(records))
cols[1].metric("Algorithms", len(set(r["algorithm"] for r in records)))
cols[2].metric("Best distance", f"{min(r['total_distance'] for r in records):.3f}")
cols[3].metric("Fastest run", f"{min(r['time_taken'] for r in records):.3f}s")

by_algo = defaultdict(list)
for r in records:
    by_algo[r["algorithm"]].append(r)

summary = []
for algo, rows in by_algo.items():
    dist_values = [x["total_distance"] for x in rows]
    time_values = [x["time_taken"] for x in rows]
    route_values = [x["route_count"] for x in rows]
    numeric_memory = [
        float(x["memory_usage"])
        for x in rows
        if isinstance(x["memory_usage"], (int, float))
    ]

    summary.append(
        {
            "algorithm": algo,
            "runs": len(rows),
            "avg_distance": sum(dist_values) / len(dist_values),
            "best_distance": min(dist_values),
            "worst_distance": max(dist_values),
            "avg_time": sum(time_values) / len(time_values),
            "best_time": min(time_values),
            "worst_time": max(time_values),
            "avg_routes": sum(route_values) / len(route_values),
            "min_routes": min(route_values),
            "max_routes": max(route_values),
            "distance_stability": stability_label(dist_values),
            "time_stability": stability_label(time_values),
            "avg_memory": (sum(numeric_memory) / len(numeric_memory))
            if numeric_memory
            else None,
        }
    )

summary = sorted(summary, key=lambda x: x["avg_distance"])
baseline = summary[0]

comparison_rows = []
for row in summary:
    comparison_rows.append(
        {
            "algorithm": row["algorithm"],
            "avg_distance": round(row["avg_distance"], 3),
            "avg_distance_vs_baseline": fmt_pct(
                pct_diff(
                    row["avg_distance"], baseline["avg_distance"], lower_is_better=True
                )
            ),
            "best_distance": round(row["best_distance"], 3),
            "best_distance_vs_baseline": fmt_pct(
                pct_diff(
                    row["best_distance"],
                    baseline["best_distance"],
                    lower_is_better=True,
                )
            ),
            "avg_time": round(row["avg_time"], 3),
            "avg_time_vs_baseline": fmt_pct(
                pct_diff(row["avg_time"], baseline["avg_time"], lower_is_better=True)
            ),
            "best_time": round(row["best_time"], 3),
            "best_time_vs_baseline": fmt_pct(
                pct_diff(row["best_time"], baseline["best_time"], lower_is_better=True)
            ),
            "avg_routes": round(row["avg_routes"], 2),
            "avg_routes_vs_baseline": fmt_pct(
                pct_diff(
                    row["avg_routes"], baseline["avg_routes"], lower_is_better=True
                )
            ),
            "runs": row["runs"],
            "distance_stability": row["distance_stability"],
            "time_stability": row["time_stability"],
        }
    )

st.subheader("Algorithm summary")
st.dataframe(
    summary,
    width="stretch",
    hide_index=True,
)

st.subheader("Baseline comparison")
st.caption(f"Baseline: {baseline['algorithm']} (lowest average distance).")
st.dataframe(
    comparison_rows,
    width="stretch",
    hide_index=True,
)

best_rows = []
for algo, rows in by_algo.items():
    best = min(rows, key=lambda x: x["total_distance"])
    best_rows.append(best)

st.subheader("Best run per algorithm")
st.dataframe(
    best_rows,
    width="stretch",
    hide_index=True,
)

st.subheader("Per-run charts")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
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
    dist_range = padded_range([r["total_distance"] for r in records])
    if dist_range:
        fig.update_yaxes(range=dist_range)
    st.plotly_chart(fig, width="stretch")

with chart_col2:
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
    time_range = padded_range([r["time_taken"] for r in records])
    if time_range:
        fig.update_yaxes(range=time_range)
    st.plotly_chart(fig, width="stretch")

st.subheader("Summary charts")
chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    fig = go.Figure()
    fig.add_bar(
        x=[r["algorithm"] for r in summary],
        y=[r["avg_distance"] for r in summary],
        name="Average distance",
        text=[f"{r['avg_distance']:.2f}" for r in summary],
        textposition="outside",
    )
    fig.add_scatter(
        x=[r["algorithm"] for r in summary],
        y=[r["best_distance"] for r in summary],
        mode="markers+text",
        text=[f"best {r['best_distance']:.2f}" for r in summary],
        textposition="top center",
        name="Best distance",
    )
    fig.update_layout(title="Average vs best distance", showlegend=False)
    dist_axis = padded_range(
        [r["avg_distance"] for r in summary] + [r["best_distance"] for r in summary]
    )
    if dist_axis:
        fig.update_yaxes(range=dist_axis)
    st.plotly_chart(fig, width="stretch")

with chart_col4:
    fig = go.Figure()
    fig.add_bar(
        x=[r["algorithm"] for r in summary],
        y=[r["avg_time"] for r in summary],
        name="Average time",
        text=[f"{r['avg_time']:.2f}s" for r in summary],
        textposition="outside",
    )
    fig.add_scatter(
        x=[r["algorithm"] for r in summary],
        y=[r["best_time"] for r in summary],
        mode="markers+text",
        text=[f"best {r['best_time']:.2f}s" for r in summary],
        textposition="top center",
        name="Best time",
    )
    fig.update_layout(title="Average vs best runtime", showlegend=False)
    time_axis = padded_range(
        [r["avg_time"] for r in summary] + [r["best_time"] for r in summary]
    )
    if time_axis:
        fig.update_yaxes(range=time_axis)
    st.plotly_chart(fig, width="stretch")

st.subheader("Percentage deltas vs baseline")
delta_rows = []
for row in summary:
    delta_rows.append(
        {
            "algorithm": row["algorithm"],
            "distance_delta_%": round(
                pct_diff(
                    row["avg_distance"], baseline["avg_distance"], lower_is_better=True
                ),
                2,
            ),
            "time_delta_%": round(
                pct_diff(row["avg_time"], baseline["avg_time"], lower_is_better=True), 2
            ),
            "routes_delta_%": round(
                pct_diff(
                    row["avg_routes"], baseline["avg_routes"], lower_is_better=True
                ),
                2,
            ),
        }
    )

st.dataframe(
    delta_rows,
    width="stretch",
    hide_index=True,
)

delta_left, delta_right = st.columns(2)
with delta_left:
    fig = go.Figure()
    fig.add_bar(
        x=[r["algorithm"] for r in delta_rows],
        y=[r["distance_delta_%"] for r in delta_rows],
        text=[f"{r['distance_delta_%']:+.2f}%" for r in delta_rows],
        textposition="outside",
    )
    fig.update_layout(title="Average distance vs baseline", yaxis_title="Percent")
    st.plotly_chart(fig, width="stretch")

with delta_right:
    fig = go.Figure()
    fig.add_bar(
        x=[r["algorithm"] for r in delta_rows],
        y=[r["time_delta_%"] for r in delta_rows],
        text=[f"{r['time_delta_%']:+.2f}%" for r in delta_rows],
        textposition="outside",
    )
    fig.update_layout(title="Average runtime vs baseline", yaxis_title="Percent")
    st.plotly_chart(fig, width="stretch")

st.subheader("Route count stability")
route_summary = []
for algo, rows in by_algo.items():
    counts = [r["route_count"] for r in rows]
    route_summary.append(
        {
            "algorithm": algo,
            "min_routes": min(counts),
            "max_routes": max(counts),
            "avg_routes": sum(counts) / len(counts),
        }
    )

fig = go.Figure()
fig.add_bar(
    x=[r["algorithm"] for r in route_summary],
    y=[r["avg_routes"] for r in route_summary],
    name="Average routes",
    text=[f"{r['avg_routes']:.2f}" for r in route_summary],
    textposition="outside",
)
fig.add_scatter(
    x=[r["algorithm"] for r in route_summary],
    y=[r["min_routes"] for r in route_summary],
    mode="markers+text",
    text=[f"min {r['min_routes']}" for r in route_summary],
    textposition="bottom center",
    name="Min routes",
)
fig.add_scatter(
    x=[r["algorithm"] for r in route_summary],
    y=[r["max_routes"] for r in route_summary],
    mode="markers+text",
    text=[f"max {r['max_routes']}" for r in route_summary],
    textposition="top center",
    name="Max routes",
)
route_y = padded_range(
    [r["avg_routes"] for r in route_summary]
    + [r["min_routes"] for r in route_summary]
    + [r["max_routes"] for r in route_summary]
)
if route_y:
    fig.update_yaxes(range=route_y)
fig.update_layout(title="Route count stability", showlegend=False)
st.plotly_chart(fig, width="stretch")

st.subheader("Run table")
run_table = [
    {
        "algorithm": row["algorithm"],
        "run_uuid": row["run_uuid"],
        "distance": row["total_distance"],
        "time": row["time_taken"],
        "routes": row["route_count"],
        "capacity": row["capacity"],
        "seed": row["rand_seed"],
    }
    for row in records
]
st.dataframe(
    run_table,
    width="stretch",
    hide_index=True,
)

st.subheader("Selected run details")
selected_run = st.selectbox(
    "Choose a run",
    options=[f"{a} | {u}" for a, u, _, _ in run_payloads],
)

chosen = None
for a, u, p, data in run_payloads:
    if selected_run == f"{a} | {u}":
        chosen = (a, u, p, data)
        break

if chosen:
    a, u, p, data = chosen
    left, right = st.columns(2)
    with left:
        st.write(f"**Algorithm:** {a}")
        st.write(f"**UUID:** {u}")
        st.write(f"**File:** {p}")
        st.json(data.get("hardware_info", {}))
    with right:
        st.write("**Output summary**")
        st.json(
            {
                "uuid": data.get("uuid"),
                "data_used": data.get("data_used"),
                "total_distance": data.get("total_distance"),
                "time_taken": data.get("time_taken"),
                "memory_usage": data.get("memory_usage"),
                "algorithm_used": data.get("algorithm_used"),
            }
        )
    with st.expander("Routes"):
        st.json(data.get("routes", []))

st.subheader("Batch JSON")
st.json(batch)
