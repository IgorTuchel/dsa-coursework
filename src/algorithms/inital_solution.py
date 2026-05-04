from itertools import combinations
from typing import Any

from models.base import InputParams, OutputBase
from models.vrp import Customer, Route
from utils.monitor import monitor


@monitor
def solve_clarke_wright(input_params: InputParams) -> OutputBase:
    depot = input_params.depot
    customers = input_params.customers
    capacity_limit = input_params.capacity
    routes = clarke_wright_algo(depot, customers, capacity_limit)
    total_distance = sum(route.total_distance(depot) for route in routes)
    output = OutputBase(
        routes=routes,
        input_params=input_params,
        additional_params=None,
        total_distance=total_distance,
    )
    return output


def _generate_pairs(customers: list[Customer], depot: Customer) -> list[Any]:
    pairs = []
    for i, j in combinations(customers, 2):
        s = _savings(depot, i, j)
        pairs.append((i, j, s))
        pairs.append((j, i, s))
    return sorted(
        pairs, key=lambda x: x[2], reverse=True
    )  # Sort it with most savings -> least savings


def _savings(depot: Customer, customer_i: Customer, customer_j: Customer) -> float:
    c1i = depot.dist(customer_i)
    c1j = depot.dist(customer_j)
    cij = customer_i.dist(customer_j)

    # Distance savings -> (c1i + c1i + c1j + c1j)(To customer from depot and back, to another customer and back) - (c1i + cij + c1j) (From depot to customer, to customer, back to depot) = evalutes to (c1i + c1j - cij)

    return c1i + c1j - cij


def clarke_wright_algo(
    depot: Customer, customers: list[Customer], capacity_limit=250
) -> list[Route]:
    routes = [Route(customers=[cus], capacity=capacity_limit) for cus in customers]
    customer_route = {cus: route for route in routes for cus in route.customers}
    pairs = _generate_pairs(customers, depot)

    for i, j, _ in pairs:
        route_i = customer_route.get(i)
        route_j = customer_route.get(j)
        if route_i is None or route_j is None:
            continue
        if route_i == route_j:
            continue
        if route_i.customers[-1] != i:
            continue
        if route_j.customers[0] != j:
            continue
        if not route_i.can_merge(route_j):
            continue

        merge = Route(route_i.customers + route_j.customers)
        for cus in merge.customers:
            customer_route[cus] = merge
        routes.remove(route_i)
        routes.remove(route_j)
        routes.append(merge)

    return routes
