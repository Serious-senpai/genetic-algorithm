from __future__ import annotations

import csv
import io
import itertools
import json
from dataclasses import dataclass
from math import sqrt
from os import path
from typing import ClassVar, Dict, Final, FrozenSet, Optional, Tuple, TYPE_CHECKING, final

from .errors import ConfigImportException
from .utils import set_customers
from ..utils import LRUCache, tsp_solver, weird_round


__all__ = (
    "ProblemConfig",
)


@dataclass(frozen=True, kw_only=True, slots=True)
class Customer:
    x: float
    y: float
    low: int
    high: int
    w: int

    @property
    def location(self) -> Tuple[float, float]:
        return self.x, self.y


@dataclass(frozen=True, kw_only=True, slots=True)
class Vehicle:
    speed: float
    capacity: int
    cost_coefficient: float
    time_limit: float


@final
class ProblemConfig:

    __slots__ = (
        "__tsp_cache",

        "problem",
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
        "__cache_limit",
        "mutation_rate",
        "initial_fine_coefficient",
        "fine_coefficient_increase_rate",
        "reset_after",
        "stuck_penalty_increase_rate",
        "local_search_batch",
        "logger",
        "record_history",
    )
    __cache__: ClassVar[Dict[str, ProblemConfig]] = {}
    context: ClassVar[str] = "None"
    if TYPE_CHECKING:
        __tsp_cache: Final[LRUCache[FrozenSet[int], Tuple[float, Tuple[int, ...]]]]

        problem: Final[str]
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
        __cache_limit: Optional[int]
        mutation_rate: Optional[float]
        initial_fine_coefficient: Optional[float]
        fine_coefficient_increase_rate: Optional[float]
        reset_after: Optional[int]
        stuck_penalty_increase_rate: Optional[float]
        local_search_batch: Optional[int]
        logger: Optional[io.TextIOWrapper]
        record_history: bool

    def __init__(self, problem: str, /) -> None:
        self.problem = problem = problem.removesuffix(".csv")
        self.__tsp_cache = LRUCache()
        self.__cache_limit = None
        self.mutation_rate = None
        self.initial_fine_coefficient = None
        self.fine_coefficient_increase_rate = None
        self.reset_after = None
        self.stuck_penalty_increase_rate = None
        self.local_search_batch = None
        self.logger = None
        self.record_history = False
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
                        assert (
                            trucks_count.is_integer()
                            and drones_count.is_integer()
                            and truck_capacity.is_integer()
                            and drone_capacity.is_integer()
                        )

                        self.trucks_count = int(trucks_count)
                        self.drones_count = int(drones_count)
                        self.time_limit = time_limit

                        with open("problems/vrpdfd/coefficients.json", "r", encoding="utf-8") as coefficients_file:
                            data = json.load(coefficients_file)
                            truck_coefficient = data["truck_cost_over_time"] / truck_speed
                            drone_coefficient = data["drone_cost_over_time"] / drone_speed

                        self.truck = Vehicle(speed=truck_speed, capacity=int(truck_capacity), cost_coefficient=truck_coefficient, time_limit=10 ** 9)
                        self.drone = Vehicle(speed=drone_speed, capacity=int(drone_capacity), cost_coefficient=drone_coefficient, time_limit=drone_duration)

                        break

            file_path = path.join("problems", "vrpdfd", f"{problem}.csv")
            with open(file_path, "r", encoding="utf-8", newline="") as file:
                header = True  # Skip header
                customers = [Customer(x=0.0, y=0.0, low=0, high=0, w=0)]
                for row in csv.reader(file):
                    if header:
                        header = False
                        continue

                    _, x, y, low, high, w = map(float, row)
                    assert low.is_integer() and high.is_integer() and w.is_integer()
                    customers.append(Customer(x=x, y=y, low=int(low), high=int(high), w=int(w)))

                customers_count = len(customers)
                self.customers = tuple(customers)
                self.customers_by_profit = tuple(sorted(range(1, customers_count), key=lambda i: customers[i].w, reverse=True))

                distances = [[0.0] * (customers_count) for _ in range(customers_count)]
                for f, s in itertools.combinations(range(customers_count), 2):
                    distances[f][s] = distances[s][f] = weird_round(sqrt((customers[f].x - customers[s].x) ** 2 + (customers[f].y - customers[s].y) ** 2), 2)

                self.distances = tuple(map(tuple, distances))

                set_customers(
                    [customer.low for customer in customers],
                    [customer.high for customer in customers],
                    [customer.w for customer in customers],
                    [customer.x for customer in customers],
                    [customer.y for customer in customers],
                    self.time_limit * self.truck.speed,
                    self.drone.time_limit * self.drone.speed,
                    self.truck.capacity,
                    self.drone.capacity,
                    self.truck.cost_coefficient,
                    self.drone.cost_coefficient,
                )

        except BaseException as error:
            raise ConfigImportException(error) from error

    @property
    def tsp_cache(self) -> LRUCache[FrozenSet[int], Tuple[float, Tuple[int, ...]]]:
        return self.__tsp_cache

    @property
    def cache_limit(self) -> Optional[int]:
        return self.__cache_limit

    @cache_limit.setter
    def cache_limit(self, value: Optional[int]) -> None:
        self.__cache_limit = value
        self.__tsp_cache.max_size = value

    @property
    def customers_count(self) -> int:
        """Return the number of customers excluding the deport"""
        return len(self.customers) - 1

    @classmethod
    def get_config(cls, problem: Optional[str] = None, /) -> ProblemConfig:
        if problem is None:
            return cls.__cache__[cls.context]

        try:
            return cls.__cache__[problem]

        except KeyError:
            cls.__cache__[problem] = config = cls(problem)
            return config

    def path_order(self, path: FrozenSet[int]) -> Tuple[float, Tuple[int, ...]]:
        try:
            return self.__tsp_cache[path]

        except KeyError:
            customers = tuple(path)
            depot_index = customers.index(0)
            distance, path_index = tsp_solver([self.customers[i].location for i in customers], first=depot_index)

            ordered = list(map(customers.__getitem__, path_index))
            ordered.append(0)

            self.__tsp_cache[path] = result = distance, tuple(ordered)
            return result

    @classmethod
    def debug_setup(cls, problem: str, /) -> ProblemConfig:
        config = cls.get_config(problem)
        ProblemConfig.context = problem
        config.initial_fine_coefficient = 1000.0
        return config
