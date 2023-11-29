from __future__ import annotations

import itertools
from dataclasses import dataclass
from math import sqrt
from os import path
from typing import ClassVar, Final, Optional, Tuple, TYPE_CHECKING, final

from .errors import ConfigDataNotFound, ConfigImportException, ConfigImportTwice


__all__ = (
    "ProblemConfig",
)


@dataclass(frozen=True, kw_only=True, slots=True)
class Customer:
    x: float
    y: float
    low: float
    high: float
    w: float


@dataclass(frozen=True, kw_only=True, slots=True)
class Vehicle:
    speed: float
    capacity: float
    cost_coefficient: float
    time_limit: float


@final
class ProblemConfig:

    __slots__ = (
        "trucks_count",
        "drones_count",
        "customers",
        "distances",

        # Constraints
        "truck",
        "drone",
        "time_limit",
    )
    __instance__: Optional[ProblemConfig] = None
    problem: ClassVar[Optional[str]] = None
    if TYPE_CHECKING:
        trucks_count: Final[int]
        drones_count: Final[int]
        customers: Final[Tuple[Customer, ...]]
        distances: Final[Tuple[Tuple[float, ...], ...]]

        # Constraints
        truck: Final[Vehicle]
        drone: Final[Vehicle]
        time_limit: Final[float]

    def __new__(cls, problem: Optional[str] = None, /) -> ProblemConfig:
        if cls.__instance__ is None:
            cls.problem = problem
            cls.__instance__ = super().__new__(cls)

        return cls.__instance__

    def __init__(self, problem: Optional[str] = None, /) -> None:
        if self.problem is not None:
            if problem is not None and problem != self.problem:
                raise ConfigImportTwice

            return

        if problem is None:
            raise ConfigDataNotFound

        ProblemConfig.problem = problem.removesuffix(".txt")
        try:
            with open(path.join("problems", "vrpdfd", f"{problem}.txt"), "r", encoding="utf-8") as file:
                trucks_count, drones_count, time_limit = map(float, file.readline().split())
                assert trucks_count.is_integer() and drones_count.is_integer()

                self.trucks_count = int(trucks_count)
                self.drones_count = int(drones_count)
                self.time_limit = int(time_limit)

                speed_truck, speed_drone, capacity_truck, capacity_drone, duration_drone = map(float, file.readline().split())
                self.truck = Vehicle(speed=speed_truck, capacity=capacity_truck, cost_coefficient=0.23, time_limit=float("inf"))
                self.drone = Vehicle(speed=speed_drone, capacity=capacity_drone, cost_coefficient=0.025, time_limit=duration_drone)

                customers= [Customer(x=0.0, y=0.0, low=0.0, high=0.0, w=0.0)]
                while line := file.readline().split():
                    x, y, low, high, w = map(float, line)
                    customers.append(Customer(x=x, y=y, low=low, high=high, w=w))

                self.customers = tuple(customers)

                customers_count = len(customers)
                distances = [[0.0] * (customers_count) for _ in range(customers_count)]
                for f, s in itertools.combinations(range(customers_count), 2):
                    distances[f][s] = distances[s][f] = sqrt((customers[f].x - customers[s].x) ** 2 + (customers[f].y - customers[s].y) ** 2)

                self.distances = tuple(map(tuple, distances))

        except BaseException as error:
            raise ConfigImportException(error) from error
