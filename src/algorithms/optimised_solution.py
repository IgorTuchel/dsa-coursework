import random
from typing import Any

from algorithms.inital_solution import clarke_wright_algo
from models.base import OutputBase
from models.individual import HGA, Individual
from models.vrp import Customer, Route
from utils.monitor import monitor


@monitor
def HGA_Algorithm(hga: HGA) -> OutputBase:
    routes = _HGA_Algorithm(hga)
    total_distance = sum(
        route.total_distance(hga.input_params.depot) for route in routes
    )

    return OutputBase(
        routes=routes,
        input_params=hga.input_params,
        additional_params=hga,
        total_distance=total_distance,
    )


def _HGA_Algorithm(hga: HGA) -> list[Route]:
    population = _init_population(hga)
    best = min(population, key=lambda ind: ind.cost)
    itterations_without_improvement = 0

    while itterations_without_improvement < hga.max_itterations_without_improvement:
        child = _hybrid_evolutionary_framework(hga, population)
        population = _insert_into_population(hga, population, child)

        current_best = min(population, key=lambda ind: ind.cost)
        if current_best.cost < best.cost:
            best = current_best
            itterations_without_improvement = 0
        else:
            itterations_without_improvement += 1

    return [Route(customers=route.customers[:]) for route in best.routes]


def _hybrid_evolutionary_framework(
    hga: HGA, population: list[Individual]
) -> Individual:
    parent1 = _tournament_selection(hga, population)
    parent2 = _tournament_selection(hga, population)
    offspring = _order_crossover(parent1, parent2)

    routes = _split(offspring)
    routes = _local_search(hga, routes)

    return _make_individual(hga, routes)


def _insert_into_population(
    hga: HGA, population: list[Individual], offspring: Individual
) -> list[Individual]:
    offspring_identity = tuple(customer.id for customer in offspring.customers)
    for index, individual in enumerate(population):
        sig = tuple(customer.id for customer in individual.customers)
        if sig == offspring_identity:
            if offspring.cost < individual.cost:
                population[index] = offspring
                population.sort(key=lambda ind: ind.cost)
            return population

    population.append(offspring)
    population.sort(key=lambda ind: ind.cost)
    max_pop = hga.population_scale * hga.minimum_population_size
    while len(population) > max_pop:
        population.pop()

    return population


def _order_crossover(parent1: Individual, parent2: Individual) -> list[Customer]:
    cus1 = parent1.customers
    cus2 = parent2.customers

    if len(cus1) < 2:
        return cus1[:]

    start, end = sorted(random.sample(range(len(cus1)), 2))

    child: list[Customer | None] = [None for _ in range(len(cus1))]
    child[start : end + 1] = cus1[start : end + 1]
    child_ids = {customer.id for customer in child if customer is not None}

    fill = [customer for customer in cus2 if customer.id not in child_ids]
    fill_idx = 0

    for i in range(len(child)):
        if child[i] is None:
            child[i] = fill[fill_idx]
            fill_idx += 1

    return child


def _init_population(hga):
    population_size = hga.minimum_population_size * hga.population_scale
    population = []
    seen_individuals = set()

    routes = clarke_wright_algo(hga.input_params.depot, hga.input_params.customers)
    routes = _local_search(hga, routes)
    individual = _make_individual(hga, routes)
    population.append(individual)
    seen_individuals.add(tuple(customer.id for customer in individual.customers))

    attempts = 0
    max_attempts = population_size * 10

    while len(population) < population_size and attempts < max_attempts:
        attempts += 1
        cc_customers = hga.input_params.customers[:]
        random.shuffle(cc_customers)
        routes = _split(cc_customers)
        routes = _local_search(hga, routes)
        individual = _make_individual(hga, routes)
        if tuple(customer.id for customer in individual.customers) in seen_individuals:
            continue

        population.append(individual)
        seen_individuals.add(tuple(customer.id for customer in individual.customers))

    return population


def _tournament_selection(hga: HGA, population: list[Individual]):
    tournament = random.sample(population, hga.tournament_size)
    winner = min(tournament, key=lambda ind: ind.cost)
    return winner


def _split(customers):
    routes = []
    current_route = Route(customers=[])
    for customer in customers:
        if not current_route.can_add(customer):
            routes.append(current_route)
            current_route = Route(customers=[])
        current_route.customers.append(customer)
    if current_route.customers:
        routes.append(current_route)
    return routes


def _local_search(hga, routes):
    best = [Route(customers=route.customers[:]) for route in routes]

    for _ in range(hga.max_local_search):
        improved = False
        for idx, route in enumerate(best):
            improved_route = _two_opt(hga, route)
            if improved_route and improved_route.total_distance(
                hga.input_params.depot
            ) < route.total_distance(hga.input_params.depot):
                best[idx] = improved_route
                improved = True
        if not improved:
            break
    return best


def _two_opt(hga, route):
    customers = route.customers[:]

    if len(customers) < 4:
        return Route(customers=customers)

    best_customers = customers[:]
    best_cost = Route(customers=best_customers).total_distance(hga.input_params.depot)

    for i in range(len(customers) - 1):
        for j in range(i + 1, len(customers)):
            candidate = (
                customers[:i]
                + list(reversed(customers[i : j + 1]))
                + customers[j + 1 :]
            )
            candidate_route = Route(customers=candidate)
            candidate_cost = candidate_route.total_distance(hga.input_params.depot)

            if candidate_cost < best_cost:
                best_customers = candidate
                best_cost = candidate_cost

    return Route(customers=best_customers)


def _make_individual(hga, routes):
    c_routes = [Route(customers=route.customers[:]) for route in routes]
    customers = [customer for route in c_routes for customer in route.customers]
    return Individual(
        customers=customers, routes=c_routes, cost=_total_routes_cost(hga, c_routes)
    )


def _total_routes_cost(hga, routes):
    return sum(route.total_distance(hga.input_params.depot) for route in routes)
