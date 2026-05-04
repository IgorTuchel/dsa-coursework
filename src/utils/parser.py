import csv
import json

from models.base import InputParams
from models.individual import HGA
from models.output import HardwareInformation, Output
from models.vrp import Customer, Route


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


def parse_run(path: str) -> Output:
    with open(path, "r") as f:
        data = json.load(f)
    return output_from_json(data)


def output_from_json(data: dict) -> Output:
    input_params_data = data["input_params"]
    additional_params_data = data.get("additional_params")
    hardware_info_data = data["hardware_info"]

    customers = [
        Customer(
            id=c["id"],
            pos_x=c["pos_x"],
            pos_y=c["pos_y"],
            weight=c["weight"],
        )
        for c in input_params_data["customers"]
    ]

    depot_data = input_params_data["depot"]
    depot = Customer(
        id=depot_data["id"],
        pos_x=depot_data["pos_x"],
        pos_y=depot_data["pos_y"],
        weight=depot_data["weight"],
    )

    input_params = InputParams(
        customers=customers,
        depot=depot,
        capacity=input_params_data["capacity"],
    )

    routes = []
    for route_data in data["routes"]:
        route_customers = [
            Customer(
                id=c["id"],
                pos_x=c["pos_x"],
                pos_y=c["pos_y"],
                weight=c["weight"],
            )
            for c in route_data["customers"]
        ]
        routes.append(
            Route(
                customers=route_customers,
                capacity=route_data.get("capacity", input_params.capacity),
            )
        )

    hga = None
    if additional_params_data is not None:
        hga = HGA(
            minimum_population_size=additional_params_data.get(
                "minimum_population_size", 10
            ),
            max_itterations_without_improvement=additional_params_data.get(
                "max_itterations_without_improvement", 100
            ),
            population_scale=additional_params_data.get("population_scale", 4),
            max_local_search=additional_params_data.get("max_local_search", 10),
            tournament_size=additional_params_data.get("tournament_size", 3),
            rand_seed=additional_params_data.get("rand_seed", 0),
        )

    hardware_info = HardwareInformation(
        cpu_brand=hardware_info_data["cpu_brand"],
        cpu_cores=hardware_info_data["cpu_cores"],
        cpu_architecture=hardware_info_data["cpu_architecture"],
        cpu_bits=hardware_info_data["cpu_bits"],
        cpu_version=hardware_info_data["cpu_version"],
        hz_friendly=hardware_info_data["hz_friendly"],
        platform=hardware_info_data["platform"],
        virtual_memory=hardware_info_data["virtual_memory"],
    )

    return Output(
        uuid=data["uuid"],
        data_used=data["data_used"],
        input_params=input_params,
        additional_params=hga,
        total_distance=data["total_distance"],
        routes=routes,
        memory_usage=data["memory_usage"],
        time_taken=data["time_taken"],
        hardware_info=hardware_info,
        algorithm_used=data["algorithm_used"],
    )
