import json
from collections import defaultdict
from pathlib import Path

RUNS_DIR = Path("./runs")


def load_json(path: str | Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_batch_files():
    return sorted([p for p in RUNS_DIR.glob("*_batch_*.json") if p.is_file()])


def flatten_run(
    run_data: dict, algorithm: str, batch_uuid: str, run_uuid: str, run_file: str
):
    params = run_data.get("additional_params") or {}
    input_params = run_data.get("input_params") or {}
    hardware = run_data.get("hardware_info") or {}
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
        "customers": len(input_params.get("customers", [])),
        "capacity": input_params.get("capacity"),
        "rand_seed": params.get("rand_seed"),
        "cpu_brand": hardware.get("cpu_brand"),
        "cpu_cores": hardware.get("cpu_cores"),
        "cpu_bits": hardware.get("cpu_bits"),
        "platform": hardware.get("platform"),
    }


def stability_label(values: list[float]) -> str:
    if not values:
        return "N/A"
    return (
        "Deterministic" if len(set(round(v, 10) for v in values)) == 1 else "Variable"
    )


def padded_range(values, pad_ratio: float = 0.06):
    nums = [float(v) for v in values if v is not None]
    if not nums:
        return None
    low = min(nums)
    high = max(nums)
    if low == high:
        pad = max(abs(low) * pad_ratio, 1.0)
        return [low - pad, high + pad]
    pad = (high - low) * pad_ratio
    return [low - pad, high + pad]


def pct_diff(value: float, reference: float, lower_is_better: bool = True) -> float:
    if reference in (None, 0) or value is None:
        return 0.0
    if lower_is_better:
        return (reference - value) / reference * 100
    return (value - reference) / reference * 100


def fmt_pct(value: float) -> str:
    return f"{value:+.2f}%"


def load_batch_context(selected_batch: str, selected_algorithms: list[str]):
    batch = load_json(selected_batch)
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
            run_data = load_json(run_file)
            run_payloads.append((algorithm, run_uuid, str(run_file), run_data))
            records.append(
                flatten_run(run_data, algorithm, batch_uuid, run_uuid, run_file.name)
            )

    grouped = defaultdict(list)
    for row in records:
        grouped[row["algorithm"]].append(row)

    summary = []
    for algorithm, rows in grouped.items():
        distances = [row["total_distance"] for row in rows]
        times = [row["time_taken"] for row in rows]
        routes = [row["route_count"] for row in rows]
        numeric_memory = [
            float(row["memory_usage"])
            for row in rows
            if isinstance(row["memory_usage"], (int, float))
        ]
        summary.append(
            {
                "algorithm": algorithm,
                "runs": len(rows),
                "avg_distance": sum(distances) / len(distances),
                "best_distance": min(distances),
                "worst_distance": max(distances),
                "avg_time": sum(times) / len(times),
                "best_time": min(times),
                "worst_time": max(times),
                "avg_routes": sum(routes) / len(routes),
                "min_routes": min(routes),
                "max_routes": max(routes),
                "avg_memory": (sum(numeric_memory) / len(numeric_memory))
                if numeric_memory
                else None,
                "distance_stability": stability_label(distances),
                "time_stability": stability_label(times),
            }
        )

    summary = sorted(summary, key=lambda row: row["avg_distance"])
    baseline = summary[0] if summary else None

    comparison_rows = []
    if baseline:
        for row in summary:
            comparison_rows.append(
                {
                    "algorithm": row["algorithm"],
                    "avg_distance": round(row["avg_distance"], 3),
                    "avg_distance_vs_baseline": fmt_pct(
                        pct_diff(row["avg_distance"], baseline["avg_distance"], True)
                    ),
                    "best_distance": round(row["best_distance"], 3),
                    "best_distance_vs_baseline": fmt_pct(
                        pct_diff(row["best_distance"], baseline["best_distance"], True)
                    ),
                    "avg_time": round(row["avg_time"], 3),
                    "avg_time_vs_baseline": fmt_pct(
                        pct_diff(row["avg_time"], baseline["avg_time"], True)
                    ),
                    "best_time": round(row["best_time"], 3),
                    "best_time_vs_baseline": fmt_pct(
                        pct_diff(row["best_time"], baseline["best_time"], True)
                    ),
                    "avg_routes": round(row["avg_routes"], 2),
                    "avg_routes_vs_baseline": fmt_pct(
                        pct_diff(row["avg_routes"], baseline["avg_routes"], True)
                    ),
                    "distance_stability": row["distance_stability"],
                    "time_stability": row["time_stability"],
                }
            )

    best_rows = []
    for algorithm, rows in grouped.items():
        best_rows.append(min(rows, key=lambda row: row["total_distance"]))

    return {
        "batch": batch,
        "records": records,
        "summary": summary,
        "comparison_rows": comparison_rows,
        "best_rows": best_rows,
        "run_payloads": run_payloads,
        "baseline": baseline,
        "batch_uuid": batch_uuid,
        "dataset_path": dataset_path,
        "path_name": path_name,
        "runs_per_algorithm": runs_per_algorithm,
    }
