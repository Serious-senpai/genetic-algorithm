from __future__ import annotations

import itertools
from typing import Final, List, Optional, Sequence, Tuple, TYPE_CHECKING, final

from .config import ProblemConfig
from .errors import InfeasibleSolution
from .individuals import VRPDFDIndividual
from ..abc import SingleObjectiveSolution
from ..utils import positive_max


__all__ = ("VRPDFDSolution",)


@final
class VRPDFDSolution(SingleObjectiveSolution[VRPDFDIndividual]):

    __slots__ = (
        "__hash",
        "__encoded",
        "__truck_distance",
        "__drone_distance",
        "__truck_distances",
        "__drone_distances",
        "__revenue",
        "__cost",
        "__fine",
        "__fine_coefficient",
        "truck_paths",
        "drone_paths",
    )
    if TYPE_CHECKING:
        __hash: Optional[int]
        __encoded: Optional[VRPDFDIndividual]
        __truck_distance: Optional[float]
        __drone_distance: Optional[float]
        __truck_distances: Optional[Tuple[float, ...]]
        __drone_distances: Optional[Tuple[Tuple[float, ...], ...]]
        __revenue: Optional[float]
        __cost: Optional[float]
        __fine: Optional[float]
        __fine_coefficient: float
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
        fine: Optional[float] = None,
    ) -> None:
        config = ProblemConfig.get_config()
        self.__hash = None
        self.__encoded = None

        self.truck_paths = truck_paths
        self.drone_paths = drone_paths
        self.__truck_distance = truck_distance
        self.__drone_distance = drone_distance
        self.__truck_distances = truck_distances
        self.__drone_distances = drone_distances
        self.__revenue = revenue
        self.__cost = cost
        self.__fine = fine

        assert config.initial_fine_coefficient is not None
        self.__fine_coefficient = config.initial_fine_coefficient

    def assert_feasible(self) -> None:
        """Raise InfeasibleSolution if solution is infeasible"""
        config = ProblemConfig.get_config()

        errors: List[str] = []
        exceed = positive_max(self.calculate_total_weight(path) for path in self.truck_paths) - config.truck.capacity
        if exceed > 0.0:
            errors.append(f"Truck capacity exceeded by {exceed}")

        exceed = positive_max(self.calculate_total_weight(path) for paths in self.drone_paths for path in paths) - config.drone.capacity
        if exceed > 0.0:
            errors.append(f"Drone capacity exceeded by {exceed}")

        exceed = positive_max(self.truck_distances) / config.truck.speed - config.time_limit
        if exceed > 0.0:
            errors.append(f"Truck paths violate system working time by {exceed}")

        for drone, drone_distances in enumerate(self.drone_distances):
            for index, drone_distance in enumerate(drone_distances):
                exceed = drone_distance / config.drone.speed - config.drone.time_limit
                if exceed > 0.0:
                    errors.append(f"Path {index} of drone {drone} violates flight time by {exceed}")

        for drone, drone_distances in enumerate(self.drone_distances):
            exceed = sum(drone_distances) / config.drone.speed - config.time_limit
            if exceed > 0.0:
                errors.append(f"Drone {drone} violates system working time by {exceed}")

        for path in itertools.chain(self.truck_paths, *self.drone_paths):
            for customer_index, weight in path:
                if weight < 0.0:
                    errors.append(f"Customer {customer_index} has negative weight {weight}")

                if path[0] != (0, 0.0):
                    errors.append(f"Path {path} does not start from the depot")

                if path[-1] != (0, 0.0):
                    errors.append(f"Path {path} does not end at the depot")

        for index, customer in enumerate(config.customers):
            total = 0.0
            for path in self.truck_paths:
                total += sum(weight for customer_index, weight in path if customer_index == index)

            for path in itertools.chain(*self.drone_paths):
                total += sum(weight for customer_index, weight in path if customer_index == index)

            if total < customer.low or total > customer.high:
                errors.append(f"Customer {index} has weight {total} outside [{customer.low}, {customer.high}]")

        if self.fine > 0.0:
            errors.append(f"Total fine = {self.fine_coefficient} * {self.fine}")

        if len(errors) > 0:
            raise InfeasibleSolution("Solution is infeasible\n" + "\n".join(errors))

    @staticmethod
    def calculate_total_weight(path: Sequence[Tuple[int, float]]) -> float:
        return sum(w for _, w in path)

    @staticmethod
    def calculate_distance(path: Sequence[Tuple[int, float]]) -> float:
        config = ProblemConfig.get_config()
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
            config = ProblemConfig.get_config()
            for path in self.truck_paths:
                for value in path:
                    revenue += config.customers[value[0]].w * value[1]

            for path in itertools.chain(*self.drone_paths):
                for value in path:
                    revenue += config.customers[value[0]].w * value[1]

            self.__revenue = revenue

        return self.__revenue

    @property
    def truck_cost(self) -> float:
        config = ProblemConfig.get_config()
        return config.truck.cost_coefficient * self.truck_distance

    @property
    def drone_cost(self) -> float:
        config = ProblemConfig.get_config()
        return config.drone.cost_coefficient * self.drone_distance

    @property
    def cost(self) -> float:
        if self.__cost is None:
            # We want to maximize profit i.e. minimize cost = -profit
            self.__cost = self.truck_cost + self.drone_cost - self.revenue

        return self.__cost + self.__fine_coefficient * self.fine

    @property
    def fine(self) -> float:
        if self.__fine is None:
            # Fine for exceeding time limit
            config = ProblemConfig.get_config()
            result = (
                sum(positive_max(self.calculate_total_weight(path) / config.truck.capacity - 1) for path in self.truck_paths)
                + sum(positive_max(self.calculate_total_weight(path) / config.drone.capacity - 1) for paths in self.drone_paths for path in paths)
                + sum(positive_max(distance / config.truck.speed / config.time_limit - 1) for distance in self.truck_distances)
                + sum(positive_max(distance / config.drone.speed / config.drone.time_limit - 1) for distance in itertools.chain(*self.drone_distances))
                + sum(positive_max(sum(distances) / config.drone.speed / config.time_limit - 1) for distances in self.drone_distances)
            )

            total_weight = [0.0] * len(config.customers)
            for path in itertools.chain(self.truck_paths, *self.drone_paths):
                for customer_index, weight in path:
                    total_weight[customer_index] += weight

            for index, customer in enumerate(config.customers):
                if index != 0:
                    result += (
                        positive_max(customer.low - total_weight[index])
                        + positive_max(total_weight[index] - customer.high)
                    ) / customer.high

            self.__fine = result

        return self.__fine

    @property
    def fine_coefficient(self) -> float:
        return self.__fine_coefficient

    def bump_fine_coefficient(self) -> None:
        config = ProblemConfig.get_config()
        assert config.fine_coefficient_increase_rate is not None
        self.__fine_coefficient *= config.fine_coefficient_increase_rate
        self.__fine_coefficient = min(self.__fine_coefficient, 10 ** 9)

    def encode(self, *, create_new: bool = False) -> VRPDFDIndividual:
        factory = VRPDFDIndividual if create_new else VRPDFDIndividual.from_cache
        result = factory(
            solution_cls=self.__class__,
            truck_paths=tuple(map(lambda path: frozenset(c[0] for c in path), self.truck_paths)),
            drone_paths=tuple(tuple(map(lambda path: frozenset(c[0] for c in path), paths)) for paths in self.drone_paths),
            decoded=self,
        )

        if create_new:
            return result

        if self.__encoded is None:
            self.__encoded = result

        return self.__encoded

    def __hash__(self) -> int:
        if self.__hash is None:
            self.__hash = hash((frozenset(self.truck_paths), frozenset(map(frozenset, self.drone_paths))))

        return self.__hash

    def __repr__(self) -> str:
        return f"VRPDFDSolution(truck_paths={self.truck_paths!r}, drone_paths={self.drone_paths!r})"
