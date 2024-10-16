from __future__ import annotations

import itertools
from typing import ClassVar, Final, Iterable, List, Optional, Sequence, Tuple, Union, TYPE_CHECKING, final, overload

from matplotlib import axes, pyplot

from .config import ProblemConfig
from .errors import InfeasibleSolution
from .individuals import VRPDFDIndividual
from .types import SolutionInfo
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

        # violations
        "truck_time_violations",
        "truck_weight_violations",
        "drone_time_violations",
        "drone_flight_time_violations",
        "drone_weight_violations",
        "customer_weight_violations",
    )
    fine_coefficient: ClassVar[Tuple[float, float]] = (0, 0)
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

        # violations
        truck_time_violations: Final[Tuple[float, ...]]
        truck_weight_violations: Final[Tuple[int, ...]]
        drone_time_violations: Final[Tuple[float, ...]]
        drone_flight_time_violations: Final[Tuple[Tuple[float, ...], ...]]
        drone_weight_violations: Final[Tuple[Tuple[int, ...], ...]]
        customer_weight_violations: Final[Tuple[int, ...]]

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

        config = ProblemConfig.get_config()
        self.truck_time_violations = tuple(self._approx(d / config.truck.speed - config.time_limit) for d in self.truck_distances)
        self.truck_weight_violations = tuple(self._approx(self.calculate_total_weight(p) - config.truck.capacity) for p in self.truck_paths)
        self.drone_time_violations = tuple(self._approx(sum(d) / config.drone.speed - config.time_limit) for d in self.drone_distances)
        self.drone_flight_time_violations = tuple(
            tuple(self._approx(d / config.drone.speed - config.drone.time_limit) for d in distances)
            for distances in self.drone_distances
        )
        self.drone_weight_violations = tuple(
            tuple(self._approx(self.calculate_total_weight(p) - config.drone.capacity) for p in paths)
            for paths in self.drone_paths
        )

        total_weight: List[int] = [0] * len(config.customers)
        for path in itertools.chain(self.truck_paths, *self.drone_paths):
            for customer, weight in path:
                if customer == 0:
                    if weight != 0:
                        raise ValueError(f"Invalid path {path}")
                else:
                    total_weight[customer] += weight

        self.customer_weight_violations = tuple(
            self._approx(c.low - w) + self._approx(w - c.high)
            for w, c in zip(total_weight, config.customers, strict=True)
        )

    @overload
    @staticmethod
    def _approx(value: int, /) -> int: ...
    @overload
    @staticmethod
    def _approx(value: float, /) -> float: ...

    @staticmethod
    def _approx(value: Union[int, float], /) -> Union[int, float]:
        return 0 if isclose(value, 0) else positive_max(value)

    def assert_feasible(self) -> None:
        """Raise InfeasibleSolution if solution is infeasible"""
        errors: List[str] = []

        for truck, exceed in enumerate(self.truck_time_violations):
            if exceed > 0:
                errors.append(f"Truck {truck} exceeds system working time by {exceed}")

        for truck, exceed in enumerate(self.truck_weight_violations):
            if exceed > 0:
                errors.append(f"Truck {truck} exceeds capacity by {exceed}")

        for drone, exceed in enumerate(self.drone_time_violations):
            if exceed > 0:
                errors.append(f"Drone {drone} exceeds system working time by {exceed}")

        for drone, exceeds in enumerate(self.drone_flight_time_violations):
            for path_index, exceed in enumerate(exceeds):
                if exceed > 0:
                    errors.append(f"Path {path_index} of drone {drone} exceeds flight time by {exceed}")

        for drone, exceeds in enumerate(self.drone_weight_violations):
            for path_index, exceed in enumerate(exceeds):
                if exceed > 0:
                    errors.append(f"Path {path_index} of drone {drone} exceeds capacity by {exceed}")

        for path in itertools.chain(self.truck_paths, *self.drone_paths):
            for customer_index, weight in path:
                if weight < 0:
                    errors.append(f"Customer {customer_index} has negative weight {weight}")

                if path[0] != (0, 0):
                    errors.append(f"Path {path} does not start from the depot")

                if path[-1] != (0, 0):
                    errors.append(f"Path {path} does not end at the depot")

        for index, violation in enumerate(self.customer_weight_violations):
            if violation > 0:
                errors.append(f"Customer {index} violates weight bounds by {violation}")

        if max(self.violation) > 0.0:
            errors.append(f"Total violation = {self.violation}")

        if len(errors) > 0:
            raise InfeasibleSolution("Solution is infeasible\n" + "\n".join(errors))

    @staticmethod
    def calculate_total_weight(path: Sequence[Tuple[int, int]]) -> int:
        return sum(w for _, w in path)

    @staticmethod
    def calculate_distance(path: Sequence[Tuple[int, int]]) -> float:
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
                (sum(self.truck_time_violations) + sum(self.drone_time_violations)) / config.time_limit
                + sum(map(sum, self.drone_flight_time_violations)) / config.drone.time_limit
            )

            weight_violation = (
                sum(self.truck_weight_violations) / config.truck.capacity
                + sum(map(sum, self.drone_weight_violations)) / config.drone.capacity
                + sum(v / c.high for v, c in zip(self.customer_weight_violations, config.customers, strict=True) if v != 0)  # excluding depot
            )

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

    def feasible(self) -> bool:
        return max(self.violation) == 0

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

    def to_json(self) -> SolutionInfo:
        return {
            "profit": -self.cost,
            "feasible": self.feasible(),
            "truck_paths": self.truck_paths,
            "drone_paths": self.drone_paths,
        }

    @classmethod
    def tune_fine_coefficients(cls, population: Iterable[VRPDFDIndividual]) -> None:
        decoded = set(individual.decode() for individual in population)
        violations = (
            sum(s.violation[0] for s in decoded) / len(decoded),
            sum(s.violation[1] for s in decoded) / len(decoded),
        )

        best = min(decoded)
        worst = max(decoded)
        # Note: VRPDFDSolution.cost does NOT include stuck penalty
        base = max(worst.cost - best.cost, abs(worst.cost + best.cost))

        if max(violations) == 0:
            # The entire population is feasible
            cls.fine_coefficient = (base, base)

        else:
            cls.fine_coefficient = (
                base * violations[0] / (violations[0] ** 2 + violations[1] ** 2),
                base * violations[1] / (violations[0] ** 2 + violations[1] ** 2),
            )

    def __hash__(self) -> int:
        if self.__hash is None:
            self.__hash = hash((frozenset(self.truck_paths), frozenset(map(frozenset, self.drone_paths))))

        return self.__hash

    def __repr__(self) -> str:
        return f"VRPDFDSolution(truck_paths={self.truck_paths!r}, drone_paths={self.drone_paths!r})"
