from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class Customer:
    id: int
    pos_x: int
    pos_y: int
    weight: int
    
    def dist(self, other: "Customer") -> float:
        return ((self.pos_x - other.pos_x)**2 + (self.pos_y-other.pos_y)**2 )**0.5

@dataclass
class Route:
    customers: list[Customer] = field(default_factory=list)
    capacity: int = 50

    @property
    def total_demand(self) -> int:
        return sum(cus.weight for cus in self.customers)
    
    def can_add(self, other: Customer) -> bool:
        return self.total_demand + other.weight <= self.capacity

    def total_distance(self, depot: Customer) -> float:
        stops = [depot] + self.customers + [depot]
        return sum(stops[i].dist(stops[i+1]) for i in range(len(stops) -1))
