from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from models.vrp import Customer, Route

# creates circular import issue without
if TYPE_CHECKING:
    from models.individual import HGA


@dataclass(frozen=True, slots=True)
class InputParams:
    customers: list[Customer]
    depot: Customer
    capacity: int


@dataclass(frozen=True, slots=True)
class OutputBase:
    routes: list[Route]
    input_params: InputParams
    additional_params: HGA | None
    total_distance: float
