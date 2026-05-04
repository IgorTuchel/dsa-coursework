import random
from math import inf

from algorithms.inital_solution import clarke_wright_algo
from models.base import InputParams, OutputBase
from models.individual import HGA, Individual
from models.vrp import Customer, Route
from utils.monitor import monitor


@monitor
def HGA_Algorithm(hga: HGA, input_params: InputParams) -> OutputBase:
    """
    Runs the HGA algorithm to find an optimal solution.

    Args:
        hga (HGA): The HGA instance.
        input_params (InputParams): The input parameters for the HGA.

    Returns:
        OutputBase: The output base containing the optimal solution and additional information.
    """
    routes = _HGA_Algorithm(hga, input_params)
    total_distance = sum(route.total_distance(input_params.depot) for route in routes)
    return OutputBase(
        routes=routes,
        input_params=input_params,
        additional_params=hga,
        total_distance=total_distance,
    )


def _HGA_Algorithm(hga: HGA, input_params: InputParams) -> list[Route]:
    """
    Internal engine of the HGA algorithm.

    Args:
        hga (HGA): The HGA instance.
        input_params (InputParams): The input parameters for the HGA.

    Returns:
        list[Route]: The list of routes representing the optimal solution.
    """
    rng = random.Random(hga.rand_seed)
    population = _init_population(hga, input_params, rng)
    best = min(population, key=lambda ind: ind.cost)
    itterations_without_improvement = 0

    while itterations_without_improvement < hga.max_itterations_without_improvement:
        child = _hybrid_evolutionary_framework(hga, population, input_params, rng)
        population = _insert_into_population(hga, population, child)
        current_best = min(population, key=lambda ind: ind.cost)
        itterations_without_improvement += 1
        if current_best.cost < best.cost:
            best = current_best
            itterations_without_improvement = 0

    return [Route(customers=route.customers[:]) for route in best.routes]


def _hybrid_evolutionary_framework(
    hga: HGA,
    population: list[Individual],
    input_params: InputParams,
    rng: random.Random,
) -> Individual:
    """
    This function implements the hybrid evolutionary framework for the HGA.
    - The function takes in a population, selects two parents, creates offsprings, from the off springs creates a new route.
    - The route can mutate, to increase diversity.
    - The route is then optimised through a local search, with a chance of a 2-opt search dictated by the deep_search variable.
    - The route is made into an individual and returned.

    Args:
        hga (HGA): The HGA instance.
        population (list[Individual]): The population of individuals.
        input_params (InputParams): The input parameters for the HGA.
        rng (random.Random): The random number generator.

    Returns:
        Individual: The individual created from the hybrid evolutionary framework.
    """
    parent1 = _tournament_selection(hga, population, rng)
    parent2 = _tournament_selection(hga, population, rng)
    offspring = _order_crossover(parent1, parent2, rng)

    routes = _split_optimal(offspring, input_params)

    if rng.random() < 0.1:
        routes = _mutate(routes, input_params, rng)

    deep_search = rng.random() < 0.1
    routes = _local_search(hga, routes, input_params, deep=deep_search)
    return _make_individual(routes, input_params)


def _mutate(
    routes: list[Route], input_params: InputParams, rng: random.Random
) -> list[Route]:
    """
    Mutates the routes by applying one of three mutation types: inverse, swap, or relocate.
    - Inverse: simply inverses the order of customers in a route.
    - Swap: swaps the positions of two customers in a route.
    - Relocate: relocates a customer from a route to a different route if the capacity allows.

    Args:
        routes (list[Route]): The routes to mutate.
        input_params (InputParams): The input parameters for the HGA.
        rng (random.Random): The random number generator.
    Returns:
        list[Route]: The mutated routes.
    """
    mutated = [
        Route(customers=route.customers[:], capacity=input_params.capacity)
        for route in routes
    ]

    mutation_type = rng.choice(["inverse", "swap", "relocate"])

    if mutation_type == "inverse":
        candidates = [r for r in mutated if len(r.customers) >= 4]
        if candidates:
            route = rng.choice(candidates)
            i, j = sorted(rng.sample(range(len(route.customers)), 2))
            route.customers[i : j + 1] = reversed(route.customers[i : j + 1])

    elif mutation_type == "swap":
        candidates = [r for r in mutated if len(r.customers) >= 2]
        if candidates:
            route = rng.choice(candidates)
            i, j = rng.sample(range(len(route.customers)), 2)
            route.customers[i], route.customers[j] = (
                route.customers[j],
                route.customers[i],
            )

    elif mutation_type == "relocate" and len(mutated) > 1:
        src_candidates = [i for i, r in enumerate(mutated) if len(r.customers) > 1]
        if src_candidates:
            src_idx = rng.choice(src_candidates)
            src_route = mutated[src_idx]

            src_pos = rng.randrange(len(src_route.customers))
            customer = src_route.customers.pop(src_pos)

            dst_candidates = [
                i
                for i, r in enumerate(mutated)
                if i != src_idx
                and r.total_demand + customer.weight <= input_params.capacity
            ]

            if dst_candidates:
                dst_idx = rng.choice(dst_candidates)
                dst_route = mutated[dst_idx]
                insert_pos = rng.randrange(len(dst_route.customers) + 1)
                dst_route.customers.insert(insert_pos, customer)
            else:
                src_route.customers.insert(src_pos, customer)

    return mutated


def _individual_sig(individual: Individual) -> tuple[tuple[int, ...], ...]:
    """
    Creates a signature for an individual.
    """
    return tuple(_route_sig(r) for r in individual.routes)


def _route_sig(route: Route) -> tuple[int, ...]:
    """
    Creates a signature for a route.
    """
    return tuple(c.id for c in route.customers)


def _insert_into_population(
    hga: HGA, population: list[Individual], offspring: Individual
) -> list[Individual]:
    """
    Population diversity, quality and insertion mechanism.
    - If the offspring is not already in the population, it is inserted based on its cost.
    - If the offspring is already in the population, it is replaced if it has a lower cost.
    - The population is sorted by cost, and the worst individuals are removed to maintain diversity.
    - An elite individual is preserved to avoid premature convergence.

    Args:
        hga (HGA): The HGA instance.
        population (list[Individual]): The current population of individuals.
        offspring (Individual): The offspring to insert into the population.

    Returns:
        list[Individual]: The updated population.
    """
    offspring_sig = _individual_sig(offspring)
    for ind in population:
        if _individual_sig(ind) == offspring_sig:
            if offspring.cost < ind.cost:
                population.remove(ind)
                population.append(offspring)
            return population  # offspring already exists no need to insert

    population.append(offspring)
    population.sort(key=lambda ind: ind.cost)

    max_pop = hga.population_scale * hga.minimum_population_size
    elite_size = max(1, hga.minimum_population_size // 5)

    if len(population) <= max_pop:
        return population

    elite = population[:elite_size]
    rest = population[elite_size:]

    while len(elite) + len(rest) > max_pop:
        rest.pop()

    return elite + rest


def _order_crossover(
    parent1: Individual, parent2: Individual, rng: random.Random
) -> list[Customer]:
    """
    The crossover operation of the HGA.

    - Performs order crossover on two parent individuals to produce a child individual.
    - The child individual is then mutated to increase diversity.

    Args:
        parent1 (Individual): The first parent individual.
        parent2 (Individual): The second parent individual.
        rng (random.Random): The random number generator.

    Returns:
        list[Customer]: The child individual.
    """
    cus1 = parent1.customers
    cus2 = parent2.customers

    if len(cus1) < 2:
        return cus1[:]

    start, end = sorted(rng.sample(range(len(cus1)), 2))

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


def _init_population(
    hga, input_params: InputParams, rng: random.Random
) -> list[Individual]:
    """
    Initialises the inital population for the HGA, always 2opt for clarke wright algo.

    Args:
        hga (HGA): The HGA instance.
        input_params (InputParams): The input parameters for the HGA.
        rng (random.Random): The random number generator.

    Returns:
        list[Individual]: The initial population of individuals.
    """
    population_size = hga.minimum_population_size * hga.population_scale
    population = []
    seen_individuals = set()

    routes = clarke_wright_algo(input_params.depot, input_params.customers)
    routes = _local_search(hga, routes, input_params, True)
    individual = _make_individual(routes, input_params)
    population.append(individual)
    seen_individuals.add(_individual_sig(individual))

    attempts = 0
    max_attempts = population_size * 10

    while len(population) < population_size and attempts < max_attempts:
        attempts += 1

        cc_customers = input_params.customers[:]
        rng.shuffle(cc_customers)

        routes = _split_optimal(cc_customers, input_params)
        deep_search = rng.random() < 0.1
        routes = _local_search(hga, routes, input_params, deep=deep_search)
        individual = _make_individual(routes, input_params)

        sig = _individual_sig(individual)
        if sig in seen_individuals:
            continue

        population.append(individual)
        seen_individuals.add(sig)

    return population


def _tournament_selection(hga: HGA, population: list[Individual], rng: random.Random):
    """
    Simple tournament selection algorithm for the HGA.

    Args:
        hga (HGA): The HGA instance.
        population (list[Individual]): The population of individuals to select from.
        rng (random.Random): The random number generator.

    Returns:
        Individual: The winner of the tournament.
    """
    tournament = rng.sample(population, hga.tournament_size)
    winner = min(tournament, key=lambda ind: ind.cost)
    return winner


def _split_optimal(customers: list[Customer], input_params: InputParams) -> list[Route]:
    """
    Splits the customers into routes, originally I used a greedy split but quickly noticed that the runtime
    was too slow for larger instances. This function uses dynamic programming principles to find the optimal split.

    Args:
        customers (list[Customer]): The list of customers to split.
        input_params (InputParams): The input parameters for the HGA.

    Returns:
        list[Route]: The list of routes.
    """
    depot = input_params.depot
    capacity = input_params.capacity
    n = len(customers)

    dp: list[float] = [inf] * (
        n + 1
    )  # dp[i] stores the minimum cost to split customers[:i]
    pred: list[int] = [-1] * (
        n + 1
    )  # pred[i] stores the index of the previous customer in the optimal split
    dp[0] = 0.0  # stores the cost of the optimal split for customers[:0]

    for i in range(n):
        load = 0
        cost = 0.0

        for j in range(i + 1, n + 1):
            cj = customers[j - 1]
            load += cj.weight

            if load > capacity:
                break

            if j == i + 1:
                cost = depot.dist(cj) + cj.dist(depot)
            else:
                prev = customers[j - 2]
                cost = cost - prev.dist(depot) + prev.dist(cj) + cj.dist(depot)

            new_cost = dp[i] + cost
            if new_cost < dp[j]:
                dp[j] = new_cost
                pred[j] = i

    if pred[n] == -1:
        raise ValueError(
            "No feasible split found."
        )  # just a check but so far never been thrown, the data would have to be too large for this to be theoretically thrown but even so the program would probably crash eariler

    routes: list[Route] = []
    end = n
    while end > 0:
        start = pred[end]
        routes.append(
            Route(customers=customers[start:end], capacity=input_params.capacity)
        )
        end = start
    routes.reverse()
    return routes


def _relocate_first_improvement(
    routes: list[Route], input_params: InputParams
) -> list[Route] | None:
    """
    Relocates customers from one route to another to improve the routes.

    Args:
        routes (list[Route]): The list of routes to improve.
        input_params (InputParams): The input parameters for the HGA.

    Returns:
        list[Route] | None: The improved list of routes, or None if no improvement was found.
    """
    depot = input_params.depot
    capacity = input_params.capacity

    for from_idx, from_route in enumerate(routes):
        if len(from_route.customers) <= 1:
            continue

        old_from_cost = from_route.total_distance(depot)

        for cust_idx, customer in enumerate(from_route.customers):
            remaining = (
                from_route.customers[:cust_idx] + from_route.customers[cust_idx + 1 :]
            )
            new_from_cost = (
                Route(customers=remaining, capacity=capacity).total_distance(depot)
                if remaining
                else 0.0
            )

            for to_idx, to_route in enumerate(routes):
                if from_idx == to_idx:
                    continue
                if to_route.total_demand + customer.weight > capacity:
                    continue

                old_to_cost = to_route.total_distance(depot)
                best_to_cost = float("inf")
                best_pos = None

                for pos in range(len(to_route.customers) + 1):
                    candidate = (
                        to_route.customers[:pos] + [customer] + to_route.customers[pos:]
                    )
                    candidate_cost = Route(
                        customers=candidate, capacity=capacity
                    ).total_distance(depot)
                    if candidate_cost < best_to_cost:
                        best_to_cost = candidate_cost
                        best_pos = pos

                if (new_from_cost + best_to_cost) < (old_from_cost + old_to_cost):
                    new_routes = [
                        Route(customers=r.customers[:], capacity=capacity)
                        for r in routes
                    ]
                    moved = new_routes[from_idx].customers.pop(cust_idx)
                    new_routes[to_idx].customers.insert(best_pos, moved)
                    return [r for r in new_routes if r.customers]

    return None


def _local_search(
    hga: HGA, routes: list[Route], input_params: InputParams, deep: bool = False
) -> list[Route]:
    """
    Plumbing for the correct local search algorithm. Originally only used 2-opt but the runtime was too large.
    Args:
        hga (HGA): The HGA instance.
        routes (list[Route]): The list of routes to improve.
        input_params (InputParams): The input parameters for the HGA.
        deep (bool): Whether to perform deep local search.

    Returns:
        list[Route]: The improved list of routes.
    """
    best = [
        Route(customers=route.customers[:], capacity=input_params.capacity)
        for route in routes
    ]

    improved = _relocate_first_improvement(best, input_params)
    if improved is not None:
        best = improved

    if deep:
        for _ in range(hga.max_local_search):
            changed = False
            for idx, route in enumerate(best):
                improved_route = _two_opt(route, input_params)
                if improved_route.total_distance(
                    input_params.depot
                ) < route.total_distance(input_params.depot):
                    best[idx] = improved_route
                    changed = True
            if not changed:
                break

    return best


def _two_opt(route: Route, input_params: InputParams) -> Route:
    """
    Applies the 2-opt algorithm to improve the route.

    Args:
        route (Route): The route to improve.
        input_params (InputParams): The input parameters for the HGA.

    Returns:
        Route: The improved route.
    """

    customers = route.customers[:]

    if len(customers) < 4:
        return Route(customers=customers)

    best_customers = customers[:]
    best_cost = Route(customers=best_customers).total_distance(input_params.depot)

    for i in range(len(customers) - 1):
        for j in range(i + 1, len(customers)):
            candidate = (
                customers[:i]
                + list(reversed(customers[i : j + 1]))
                + customers[j + 1 :]
            )
            candidate_route = Route(customers=candidate)
            candidate_cost = candidate_route.total_distance(input_params.depot)

            if candidate_cost < best_cost:
                best_customers = candidate
                best_cost = candidate_cost

    return Route(customers=best_customers)


def _make_individual(routes: list[Route], input_params: InputParams) -> Individual:
    """
    Makes an individual from the given routes and input parameters.

    Args:
        routes (list[Route]): The list of routes to include in the individual.
        input_params (InputParams): The input parameters for the HGA.

    Returns:
        Individual: The individual representing the routes.
    """
    c_routes = [Route(customers=route.customers[:]) for route in routes]
    customers = [customer for route in c_routes for customer in route.customers]
    return Individual(
        customers=customers,
        routes=c_routes,
        cost=_total_routes_cost(c_routes, input_params),
    )


def _total_routes_cost(routes: list[Route], input_params: InputParams) -> float:
    """
    Calculates the total cost of the routes.

    Args:
        routes (list[Route]): The list of routes to calculate the cost for.
        input_params (InputParams): The input parameters for the HGA.

    Returns:
        float: The total cost of the routes.
    """
    return sum(route.total_distance(input_params.depot) for route in routes)
