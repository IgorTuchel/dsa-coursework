import csv

from model import Customer

def create_models_from_csv(path: str):
    with open(path, 'r', newline='') as nodes:
        next(nodes)
        reader = csv.reader(nodes, delimiter=',')
        return list(_set_customer(reader))

def _set_customer(data):
    for node in data:
        if (node_len := len(node)) != 4:
            raise ValueError(f"Data {node} has length {node_len}; expected 4")
        yield Customer(int(node[0]), int(node[1]), int(node[2]),int(node[3]))
