from __future__ import annotations

import itertools
from typing import Final, Optional, Sequence, Tuple, TYPE_CHECKING, final

from .config import ProblemConfig
from .errors import InfeasibleSolution
from .individuals import VRPDFDIndividual
from ..abc import SingleObjectiveSolution
from ..utils import positive_max


__all__ = ("VRPDFDSolution",)


@final
class VRPDFDSolution(SingleObjectiveSolution[VRPDFDIndividual]):

    __slots__ = (
        "__truck_distance",
        "__drone_distance",
        "__truck_distances",
        "__drone_distances",
        "__revenue",
        "__cost",
        "truck_paths",
        "drone_paths",
    )
    if TYPE_CHECKING:
        __truck_distance: Optional[float]
        __drone_distance: Optional[float]
        __truck_distances: Optional[Tuple[float, ...]]
        __drone_distances: Optional[Tuple[Tuple[float, ...], ...]]
        __revenue: Optional[float]
        __cost: Optional[float]
        truck_paths: Final[Tuple[Tuple[Tuple[int, float], ...], ...]]
        drone_paths: Final[Tuple[Tuple[Tuple[Tuple[int, float], ...], ...], ...]]

    def __init__(
        self,
        *,
        truck_paths: Tuple[Tuple[Tuple[int, float], ...], ...],
        drone_paths: Tuple[Tuple[Tuple[Tuple[int, float], ...], ...], ...],
        truck_distance: Optional[float] = None,
        drone_distance: Optional[float] = None,
        truck_distances: Optional[Tuple[float, ...]] = None,
        drone_distances: Optional[Tuple[Tuple[float, ...], ...]] = None,
        revenue: Optional[float] = None,
        cost: Optional[float] = None,
    ) -> None:
        self.truck_paths = truck_paths
        self.drone_paths = drone_paths
        self.__truck_distance = truck_distance
        self.__drone_distance = drone_distance
        self.__truck_distances = truck_distances
        self.__drone_distances = drone_distances
        self.__revenue = revenue
        self.__cost = cost

    def assert_feasible(self) -> None:
        """Raise InfeasibleSolution if solution is infeasible"""
        config = ProblemConfig()

        exceed = positive_max(self.calculate_total_weight(path) for path in self.truck_paths) - config.truck.capacity
        if exceed > 0.0:
            raise InfeasibleSolution(f"Truck capacity exceeded by {exceed}")

        exceed = positive_max(self.calculate_total_weight(path) for paths in self.drone_paths for path in paths) - config.drone.capacity
        if exceed > 0.0:
            raise InfeasibleSolution(f"Drone capacity exceeded by {exceed}")

        exceed = positive_max(self.truck_distances) / config.truck.speed - config.time_limit
        if exceed > 0.0:
            raise InfeasibleSolution(f"Truck paths violate system working time by {exceed}")

        exceed = positive_max(itertools.chain(*self.drone_distances)) / config.drone.speed - config.drone.time_limit
        if exceed > 0.0:
            raise InfeasibleSolution(f"Drone paths violate flight time by {exceed}")

        exceed = max(sum(distances) / config.drone.speed - config.time_limit for distances in self.drone_distances)
        if exceed > 0.0:
            raise InfeasibleSolution(f"Drone paths violate system working time by {exceed}")

        for index, customer in enumerate(config.customers):
            total = 0.0
            for path in self.truck_paths:
                total += sum(weight for customer_index, weight in path if customer_index == index)

            for paths in self.drone_paths:
                for path in paths:
                    total += sum(weight for customer_index, weight in path if customer_index == index)

            if total < customer.low or total > customer.high:
                raise InfeasibleSolution(f"Customer {index} has weight {total} outside [{customer.low}, {customer.high}]")

    @staticmethod
    def calculate_total_weight(path: Sequence[Tuple[int, float]]) -> float:
        return sum(w for _, w in path)

    @staticmethod
    def calculate_distance(path: Sequence[Tuple[int, float]]) -> float:
        config = ProblemConfig()
        distance = 0.0
        for index in range(len(path) - 1):
            current = path[index][0]
            next = path[index + 1][0]
            distance += config.distances[current][next]

        return distance

    @property
    def truck_distances(self) -> Tuple[float, ...]:
        if self.__truck_distances is None:
            self.__truck_distances = tuple(map(self.calculate_distance, self.truck_paths))

        return self.__truck_distances

    @property
    def truck_distance(self) -> float:
        if self.__truck_distance is None:
            self.__truck_distance = sum(self.truck_distances)

        return self.__truck_distance

    @property
    def drone_distances(self) -> Tuple[Tuple[float, ...], ...]:
        if self.__drone_distances is None:
            self.__drone_distances = tuple(tuple(map(self.calculate_distance, paths)) for paths in self.drone_paths)

        return self.__drone_distances

    @property
    def drone_distance(self) -> float:
        if self.__drone_distance is None:
            self.__drone_distance = sum(map(sum, self.drone_distances))

        return self.__drone_distance

    @property
    def revenue(self) -> float:
        if self.__revenue is None:
            revenue = 0.0
            config = ProblemConfig()
            for path in self.truck_paths:
                for value in path:
                    revenue += config.customers[value[0]].w * value[1]

            for paths in self.drone_paths:
                for path in paths:
                    for value in path:
                        revenue += config.customers[value[0]].w * value[1]

            self.__revenue = revenue

        return self.__revenue

    @property
    def cost(self) -> float:
        if self.__cost is None:
            config = ProblemConfig()
            result = (
                config.drone.cost_coefficient * self.drone_distance
                + config.truck.cost_coefficient * self.truck_distance
                - self.revenue
            )  # We want to maximize profit i.e. minimize cost = -profit

            fine_coefficient = 10 ** 9

            # Fine for exceeding time limit
            result += fine_coefficient * (
                sum(positive_max(self.calculate_total_weight(path) / config.truck.capacity - 1) for path in self.truck_paths)
                + sum(positive_max(self.calculate_total_weight(path) / config.drone.capacity - 1) for paths in self.drone_paths for path in paths)
                + sum(positive_max(distance / config.truck.speed / config.time_limit - 1) for distance in self.truck_distances)
                + sum(positive_max(distance / config.drone.speed / config.drone.time_limit - 1) for distances in self.drone_distances for distance in distances)
                + sum(positive_max(sum(distances) / config.drone.speed / config.time_limit - 1) for distances in self.drone_distances)
            )

            for index, customer in enumerate(config.customers[1:], start=1):
                total = 0.0
                for path in self.truck_paths:
                    total += sum(weight for customer_index, weight in path if customer_index == index)

                for paths in self.drone_paths:
                    for path in paths:
                        total += sum(weight for customer_index, weight in path if customer_index == index)

                result += fine_coefficient * (positive_max(customer.low - total) + positive_max(total - customer.high)) / customer.high

            self.__cost = result

        return self.__cost

    def encode(self) -> VRPDFDIndividual:
        return VRPDFDIndividual(
            cls=self.__class__,
            truck_paths=tuple(map(lambda path: frozenset(c[0] for c in path), self.truck_paths)),
            drone_paths=tuple(tuple(map(lambda path: frozenset(c[0] for c in path), paths)) for paths in self.drone_paths),
        )

    def __hash__(self) -> int:
        return hash((self.truck_paths, self.drone_paths))

    def __repr__(self) -> str:
        return f"VRPDFDSolution(truck_paths={self.truck_paths!r}, drone_paths={self.drone_paths!r})"
