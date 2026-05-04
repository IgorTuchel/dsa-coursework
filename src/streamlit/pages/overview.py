from components.data import load_batch_context, load_batch_files, load_json
from components.ui import render_batch_header, render_table, render_top_metrics

import streamlit as st

st.set_page_config(page_title="Overview", layout="wide")
st.title("Overview")
st.caption("High-level summary of the selected VRP batch.")

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
render_top_metrics(context["records"])
render_table("Algorithm summary", context["summary"])
render_table("Best run per algorithm", context["best_rows"])
