from __future__ import annotations

import itertools
from typing import ClassVar, Final, List, Optional, Sequence, Tuple, TYPE_CHECKING, final

from matplotlib import axes, pyplot

from .config import ProblemConfig
from .errors import InfeasibleSolution
from .individuals import VRPDFDIndividual
from ..abc import SingleObjectiveSolution
from ..utils import isclose, positive_max


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
        "__violation",
        "truck_paths",
        "drone_paths",
    )
    initial_fine_coefficient: ClassVar[float] = 0
    fine_coefficient: ClassVar[Tuple[float, float]] = (0, 0)
    fine_coefficient_increment: ClassVar[float] = 0
    fine_coefficient_sensitivity: ClassVar[float] = 0
    if TYPE_CHECKING:
        __hash: Optional[int]
        __encoded: Optional[VRPDFDIndividual]
        __truck_distance: Optional[float]
        __drone_distance: Optional[float]
        __truck_distances: Optional[Tuple[float, ...]]
        __drone_distances: Optional[Tuple[Tuple[float, ...], ...]]
        __revenue: Optional[int]
        __cost: Optional[float]
        __violation: Optional[Tuple[float, float]]
        truck_paths: Final[Tuple[Tuple[Tuple[int, int], ...], ...]]
        drone_paths: Final[Tuple[Tuple[Tuple[Tuple[int, int], ...], ...], ...]]

    def __init__(
        self,
        *,
        truck_paths: Tuple[Tuple[Tuple[int, int], ...], ...],
        drone_paths: Tuple[Tuple[Tuple[Tuple[int, int], ...], ...], ...],
        truck_distance: Optional[float] = None,
        drone_distance: Optional[float] = None,
        truck_distances: Optional[Tuple[float, ...]] = None,
        drone_distances: Optional[Tuple[Tuple[float, ...], ...]] = None,
        revenue: Optional[int] = None,
        cost: Optional[float] = None,
        violation: Optional[Tuple[float, float]] = None,
    ) -> None:
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
        self.__violation = violation

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

        if max(self.violation) > 0.0:
            errors.append(f"Total violation = {self.violation}")

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
            revenue = 0
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

        return self.__cost + sum(coeff * vio for coeff, vio in zip(self.fine_coefficient, self.violation, strict=True))

    @property
    def violation(self) -> Tuple[float, float]:
        if self.__violation is None:
            config = ProblemConfig.get_config()

            time_violation = (
                sum(positive_max(distance / config.truck.speed / config.time_limit - 1) for distance in self.truck_distances)
                + sum(positive_max(distance / config.drone.speed / config.drone.time_limit - 1) for distance in itertools.chain(*self.drone_distances))
                + sum(positive_max(sum(distances) / config.drone.speed / config.time_limit - 1) for distances in self.drone_distances)
            )

            weight_violation = (
                sum(positive_max(self.calculate_total_weight(path) / config.truck.capacity - 1) for path in self.truck_paths)
                + sum(positive_max(self.calculate_total_weight(path) / config.drone.capacity - 1) for paths in self.drone_paths for path in paths)
            )

            total_weight = [0.0] * len(config.customers)
            for path in itertools.chain(self.truck_paths, *self.drone_paths):
                for customer_index, weight in path:
                    total_weight[customer_index] += weight

            for index, customer in enumerate(config.customers):
                if index != 0:
                    weight_violation += (
                        positive_max(customer.low - total_weight[index])
                        + positive_max(total_weight[index] - customer.high)
                    ) / customer.high

            if isclose(time_violation, 0.0):
                time_violation = 0.0

            if isclose(weight_violation, 0.0):
                weight_violation = 0.0

            self.__violation = (time_violation, weight_violation)

        return self.__violation

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

    def plot(self, file_name: Optional[str] = None) -> None:
        _, ax = pyplot.subplots()
        assert isinstance(ax, axes.Axes)

        config = ProblemConfig.get_config()

        for path in self.truck_paths:
            truck_x: List[float] = []
            truck_y: List[float] = []
            truck_u: List[float] = []
            truck_v: List[float] = []

            for index in range(len(path) - 1):
                current, _ = path[index]
                after, _ = path[index + 1]

                truck_x.append(config.customers[current].x)
                truck_y.append(config.customers[current].y)
                truck_u.append(config.customers[after].x - config.customers[current].x)
                truck_v.append(config.customers[after].y - config.customers[current].y)

            ax.quiver(
                truck_x,
                truck_y,
                truck_u,
                truck_v,
                color="darkviolet",
                angles="xy",
                scale_units="xy",
                scale=1,
                width=0.004,
            )

        for paths in self.drone_paths:
            drone_x: List[float] = []
            drone_y: List[float] = []
            drone_u: List[float] = []
            drone_v: List[float] = []

            for path in paths:
                for index in range(len(path) - 1):
                    current, _ = path[index]
                    after, _ = path[index + 1]

                    drone_x.append(config.customers[current].x)
                    drone_y.append(config.customers[current].y)
                    drone_u.append(config.customers[after].x - config.customers[current].x)
                    drone_v.append(config.customers[after].y - config.customers[current].y)

            ax.quiver(
                drone_x,
                drone_y,
                drone_u,
                drone_v,
                color="cyan",
                angles="xy",
                scale_units="xy",
                scale=1,
                width=0.004,
            )

        ax.scatter((0,), (0,), c="black", label="Depot")
        ax.scatter(
            tuple(customer.x for customer in config.customers[1:]),
            tuple(customer.y for customer in config.customers[1:]),
            c="red",
            label="Customers",
        )

        ax.annotate("0", (0, 0))
        for index in range(1, len(config.customers)):
            ax.annotate(f"{index} (w={config.customers[index].w})", config.customers[index].location)

        ax.grid(True)

        pyplot.legend()

        if file_name is None:
            pyplot.show()
        else:
            pyplot.savefig(file_name)

        pyplot.close()

    def __hash__(self) -> int:
        if self.__hash is None:
            self.__hash = hash((frozenset(self.truck_paths), frozenset(map(frozenset, self.drone_paths))))

        return self.__hash

    def __repr__(self) -> str:
        return f"VRPDFDSolution(truck_paths={self.truck_paths!r}, drone_paths={self.drone_paths!r})"
