import csv

from models.vrp import Customer


def create_models_from_csv(path: str) -> tuple[int, int, int, list[Customer]]:
    with open(path, "r", newline="") as nodes:
        reader = csv.reader(nodes, delimiter=",")
        amount, max_size, max_weight = _extract_metadata(reader)
        next(reader)
        return (amount, max_size, max_weight, list(_set_customer(reader)))


def _extract_metadata(data):
    amount = int(next(data)[0].split("=")[1])
    max_size = int(next(data)[0].split("=")[1])
    max_weight = int(next(data)[0].split("=")[1])
    return amount, max_size, max_weight


def _set_customer(data):
    for node in data:
        if (node_len := len(node)) != 4:
            raise ValueError(f"Data {node} has length {node_len}; expected 4")
        yield Customer(int(node[0]), int(node[1]), int(node[2]), int(node[3]))
