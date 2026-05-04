import json
from dataclasses import asdict


def _serlise_json(output):
    return json.dumps(asdict(output))


def save_result(output, path: str) -> None:
    with open(path, "w") as f:
        f.write(_serlise_json(output))
