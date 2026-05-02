from dataclasses import dataclass

from models.base import InputParams
from models.vrp import Customer, Route


@dataclass
class HGA:
    minimum_population_size: int
    max_itterations_without_improvement: int
    population_scale: int
    max_local_search: int
    tournament_size: int
    input_params: InputParams


@dataclass(slots=True)
class Individual:
    customers: list[Customer]
    routes: list[Route]
    cost: float
