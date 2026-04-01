from dataclasses import dataclass, field
from functools import reduce
from math import hypot

@dataclass(frozen=True, slots=True)
class Customer:
    id: int
    pos_x: int
    pos_y: int
    weight: int
    
    def dist(self, other: "Customer") -> float:
        return hypot(self.pos_x - other.pos_x, self.pos_y - other.pos_y)

@dataclass
class Route:
    customers: list[Customer] = field(default_factory=list)
    capacity: int = 50

    @property
    def total_demand(self) -> int:
        return sum(cus.weight for cus in self.customers)
    
    def can_add(self, other: Customer) -> bool:
        return self.total_demand + other.weight <= self.capacity

    def can_merge(self, other: "Route") -> bool:
        return self.total_demand + other.total_demand <= self.capacity

    def total_distance(self, depot: Customer) -> float:
        stops = [depot] + self.customers + [depot]
        return sum(stops[i].dist(stops[i+1]) for i in range(len(stops) -1))
    
    def __str__(self) -> str:
        route_taken = "Depot -> " + " -> ".join(str(cus.id) for cus in self.customers) + " -> Depot\n"
        total_demand = f"Total Demand: {self.total_demand}\n"
        total_distance = f"Total Distance: {self.total_distance(Customer(0,0,0,0))}\n"
        return route_taken + total_demand + total_distance
