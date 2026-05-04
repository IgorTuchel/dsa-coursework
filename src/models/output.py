from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from models.base import InputParams
from models.vrp import Route

# without it creates a ciruclar import
if TYPE_CHECKING:
    from models.individual import HGA


@dataclass
class Output:
    uuid: str
    data_used: str
    input_params: InputParams | None
    additional_params: HGA | None
    total_distance: float
    routes: list[Route]
    memory_usage: Any
    time_taken: float
    hardware_info: HardwareInformation
    algorithm_used: str


@dataclass
class HardwareInformation:
    cpu_brand: str
    cpu_cores: int | None
    cpu_architecture: str
    cpu_bits: int
    cpu_version: str
    hz_friendly: str
    platform: str
    virtual_memory: int
