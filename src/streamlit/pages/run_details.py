from components.data import load_batch_context, load_batch_files, load_json
from components.ui import render_batch_header, render_table

import streamlit as st

st.set_page_config(page_title="Run Details", layout="wide")
st.title("Run Details")
st.caption("Inspect individual runs and raw output fields.")

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
    for row in context["records"]
]
render_table("Run table", run_table)

selected_run = st.selectbox(
    "Choose a run", options=[f"{a} | {u}" for a, u, _, _ in context["run_payloads"]]
)
selected_payload = None
for algorithm, run_uuid, file_path, run_data in context["run_payloads"]:
    if selected_run == f"{algorithm} | {run_uuid}":
        selected_payload = (algorithm, run_uuid, file_path, run_data)
        break

if selected_payload:
    algorithm, run_uuid, file_path, run_data = selected_payload
    left, right = st.columns(2)
    with left:
        st.write(f"**Algorithm:** {algorithm}")
        st.write(f"**UUID:** {run_uuid}")
        st.write(f"**File:** {file_path}")
        st.json(run_data.get("hardware_info", {}))
    with right:
        st.write("**Output summary**")
        st.json(
            {
                "uuid": run_data.get("uuid"),
                "data_used": run_data.get("data_used"),
                "total_distance": run_data.get("total_distance"),
                "time_taken": run_data.get("time_taken"),
                "memory_usage": run_data.get("memory_usage"),
                "algorithm_used": run_data.get("algorithm_used"),
            }
        )
    with st.expander("Routes"):
        st.json(run_data.get("routes", []))

st.subheader("Batch JSON")
st.json(context["batch"])
