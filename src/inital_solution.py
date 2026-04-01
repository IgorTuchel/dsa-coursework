from itertools import combinations
from model import Customer, Route

def _generate_pairs(customers: list[Customer], depot: Customer):
    pairs = [(i,j,_savings(depot, i, j)) for i, j in combinations(customers, 2)]
    return sorted(pairs, key=lambda x: x[2], reverse=True) # Sort it with most savings -> least savings

def _savings(depot: Customer, customer_i: Customer, customer_j: Customer) -> float:
    c1i = depot.dist(customer_i)
    c1j = depot.dist(customer_j)
    cij = customer_i.dist(customer_j)
    
    # Distance savings -> (c1i + c1i + c1j + c1j)(To customer from depot and back, to another customer and back) - (c1i + cij + c1j) (From depot to customer, to customer, back to depot) = evalutes to (c1i + c1j - cij)

    return c1i + c1j - cij

def clarke_wright_algo(depot: Customer, customers: list[Customer]):
    routes = [Route(customers=[cus]) for cus in customers]
    pairs = _generate_pairs(customers, depot)

    for i, j, _ in pairs:
        route_i = next((route for route in routes if route.customers[-1] == i), None)
        route_j = next((route for route in routes if route.customers[0] == j), None)

        if route_i is None or route_j is None:
            continue
        if route_i == route_j:
            continue
        if not route_i.can_merge(route_j):
            continue

        merge = Route(route_i.customers + route_j.customers)
        routes.remove(route_i)
        routes.remove(route_j)
        routes.append(merge)

    return routes
