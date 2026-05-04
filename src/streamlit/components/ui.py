import streamlit as st


def render_batch_header(
    batch_uuid: str, path_name: str, dataset_path: str, runs_per_algorithm: int
):
    st.caption(
        f"Batch {batch_uuid} - Dataset {path_name} - Source {dataset_path} - Runs per algorithm {runs_per_algorithm}"
    )


def render_top_metrics(records):
    cols = st.columns(4)
    cols[0].metric("Runs loaded", len(records))
    cols[1].metric("Algorithms", len(set(r["algorithm"] for r in records)))
    cols[2].metric("Best distance", f"{min(r['total_distance'] for r in records):.3f}")
    cols[3].metric("Fastest run", f"{min(r['time_taken'] for r in records):.3f}s")


def render_table(title: str, rows):
    st.subheader(title)
    st.dataframe(rows, width="stretch", hide_index=True)
