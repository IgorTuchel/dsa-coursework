from __future__ import annotations

from models.base import (  # Note I had to change this myself as it did not know the import path
    InputParams,
    OutputBase,
)

# Assuming Customer, Route, InputParams, OutputBase are imported here
from models.vrp import Customer, Route
from utils.monitor import monitor


def two_opt(route_customers: list[Customer], depot: Customer) -> list[Customer]:
    """
    Optimizes a single route by reversing segments to find a shorter path (Local Search).
    """
    best_route = route_customers[:]
    improved = True

    def calc_dist(custs: list[Customer]) -> float:
        stops = [depot] + custs + [depot]
        return sum(stops[i].dist(stops[i + 1]) for i in range(len(stops) - 1))

    best_distance = calc_dist(best_route)

    while improved:
        improved = False
        # Iterate through all possible segments to reverse
        for i in range(len(best_route) - 1):
            for j in range(i + 2, len(best_route) + 1):
                # Create a new route by reversing the segment between i and j
                new_route = best_route[:]
                new_route[i:j] = reversed(best_route[i:j])
                new_distance = calc_dist(new_route)

                # Use a small epsilon to prevent floating-point precision infinite loops
                if new_distance < best_distance - 1e-6:
                    best_distance = new_distance
                    best_route = new_route
                    improved = True
                    break  # Break out to restart the search with the new best route
            if improved:
                break

    return best_route


@monitor  # Note I added this myself just so i can create a proper output object.
def solve_cvrp(params: InputParams) -> OutputBase:
    """
    Solves the CVRP using Nearest Neighbor followed by 2-Opt optimization.
    """
    depot = params.depot
    unvisited = set(params.customers)

    # Ensure depot is not in the unvisited customers set
    if depot in unvisited:
        unvisited.remove(depot)

    routes: list[Route] = []

    # 1. Constructive Phase: Nearest Neighbor
    while unvisited:
        current_route = Route(customers=[], capacity=params.capacity)
        current_node = depot

        while True:
            best_customer = None
            best_dist = float("inf")

            # Find the nearest unvisited customer that fits the remaining capacity
            for customer in unvisited:
                if current_route.can_add(customer):
                    distance = current_node.dist(customer)
                    if distance < best_dist:
                        best_dist = distance
                        best_customer = customer

            # If no customer can fit, dispatch the vehicle back to the depot
            if best_customer is None:
                break

            # Add the customer to the route
            current_route.customers.append(best_customer)
            unvisited.remove(best_customer)
            current_node = best_customer

        # 2. Improvement Phase: 2-Opt Optimization
        if len(current_route.customers) > 2:
            optimized_customers = two_opt(current_route.customers, depot)
            current_route.customers = optimized_customers

        routes.append(current_route)

    # Calculate final total distance
    total_dist = sum(r.total_distance(depot) for r in routes)

    return OutputBase(
        routes=routes,
        input_params=params,
        additional_params=None,  # HGA is forbidden, so this remains None
        total_distance=total_dist,
    )
