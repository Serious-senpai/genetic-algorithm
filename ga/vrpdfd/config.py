from __future__ import annotations

import csv
import itertools
import json
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

    @property
    def location(self) -> Tuple[float, float]:
        return self.x, self.y


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
        "customers_by_profit",
        "distances",

        # Constraints
        "truck",
        "drone",
        "time_limit",

        # Algorithm config
        "mutation_rate",
    )
    __instance__: Optional[ProblemConfig] = None
    problem: ClassVar[Optional[str]] = None
    if TYPE_CHECKING:
        trucks_count: Final[int]
        drones_count: Final[int]
        customers: Final[Tuple[Customer, ...]]
        customers_by_profit: Final[Tuple[int, ...]]
        distances: Final[Tuple[Tuple[float, ...], ...]]

        # Constraints
        truck: Final[Vehicle]
        drone: Final[Vehicle]
        time_limit: Final[float]

        # Algorithm config
        mutation_rate: float

    def __new__(cls, _: Optional[str] = None, /) -> ProblemConfig:
        if cls.__instance__ is None:
            cls.__instance__ = super().__new__(cls)

        return cls.__instance__

    def __init__(self, problem: Optional[str] = None, /) -> None:
        if self.problem is not None:
            if problem is not None and problem != self.problem:
                raise ConfigImportTwice(self.problem, problem)

            return

        if problem is None:
            raise ConfigDataNotFound

        ProblemConfig.problem = problem = problem.removesuffix(".csv")
        try:
            config_path = "problems/vrpdfd/params.csv"
            with open(config_path, "r", encoding="utf-8", newline="") as file:
                header = True  # Skip header
                for row in csv.reader(file):
                    if header:
                        header = False
                        continue

                    if row[2] == problem:
                        trucks_count, drones_count, time_limit, truck_capacity, drone_capacity, drone_speed, truck_speed, drone_duration = map(float, row[6:])
                        assert trucks_count.is_integer() and drones_count.is_integer()

                        self.trucks_count = int(trucks_count)
                        self.drones_count = int(drones_count)
                        self.time_limit = time_limit

                        with open("problems/vrpdfd/coefficients.json", "r", encoding="utf-8") as coefficients_file:
                            data = json.load(coefficients_file)
                            truck_coefficient = data["truck_cost_per_distance"]
                            drone_coefficient = data["drone_cost_per_distance"]

                        self.truck = Vehicle(speed=truck_speed, capacity=truck_capacity, cost_coefficient=truck_coefficient, time_limit=10 ** 9)
                        self.drone = Vehicle(speed=drone_speed, capacity=drone_capacity, cost_coefficient=drone_coefficient, time_limit=drone_duration)

                        break

            file_path = path.join("problems", "vrpdfd", f"{problem}.csv")
            with open(file_path, "r", encoding="utf-8", newline="") as file:
                header = True  # Skip header
                customers = [Customer(x=0.0, y=0.0, low=0.0, high=0.0, w=0.0)]
                for row in csv.reader(file):
                    if header:
                        header = False
                        continue

                    _, x, y, low, high, w = map(float, row)
                    customers.append(Customer(x=x, y=y, low=low, high=high, w=w))

                customers_count = len(customers)
                self.customers = tuple(customers)
                self.customers_by_profit = tuple(sorted(range(1, customers_count), key=lambda i: customers[i].w, reverse=True))

                distances = [[0.0] * (customers_count) for _ in range(customers_count)]
                for f, s in itertools.combinations(range(customers_count), 2):
                    distances[f][s] = distances[s][f] = sqrt((customers[f].x - customers[s].x) ** 2 + (customers[f].y - customers[s].y) ** 2)

                self.distances = tuple(map(tuple, distances))

        except BaseException as error:
            raise ConfigImportException(error) from error

    @property
    def customers_count(self) -> int:
        """Return the number of customers excluding the deport"""
        return len(self.customers) - 1

    @classmethod
    def reset_singleton(cls, problem: str, /) -> ProblemConfig:
        cls.__instance__ = None
        cls.problem = None
        return cls(problem)
