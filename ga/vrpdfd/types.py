from __future__ import annotations

from typing import Final, Generic, List, Optional, Tuple, TypeVar, TYPE_CHECKING

from .config import ProblemConfig


__all__ = ("SupportCostsEvaluation",)
_T = TypeVar("_T", int, Tuple[int, float])


class SupportCostsEvaluation(Generic[_T]):

    __slots__ = (
        "__truck_distance",
        "__drone_distance",
        "__truck_distances",
        "__drone_distances",
        "__revenue",
        "truck_paths",
        "drone_paths",
    )
    if TYPE_CHECKING:
        __truck_distance: Optional[float]
        __drone_distance: Optional[float]
        __truck_distances: Optional[Tuple[float, ...]]
        __drone_distances: Optional[Tuple[Tuple[float, ...], ...]]
        __revenue: Optional[float]
        truck_paths: Final[Tuple[Tuple[_T, ...], ...]]  # type: ignore
        drone_paths: Final[Tuple[Tuple[Tuple[_T, ...], ...], ...]]  # type: ignore

    def __init__(
        self,
        *,
        truck_paths: Tuple[Tuple[_T, ...], ...],
        drone_paths: Tuple[Tuple[Tuple[_T, ...], ...], ...],
        truck_distances: Optional[Tuple[float, ...]] = None,
        drone_distances: Optional[Tuple[Tuple[float, ...]]] = None,
        revenue: Optional[float] = None,
    ) -> None:
        self.truck_paths = truck_paths
        self.drone_paths = drone_paths
        self.__truck_distance = None
        self.__drone_distance = None
        self.__truck_distances = truck_distances
        self.__drone_distances = drone_distances
        self.__revenue = revenue

    def get_waypoint(self, value: _T, /) -> int:
        if isinstance(value, tuple):
            return value[0]

        return value

    @property
    def truck_distances(self) -> Tuple[float, ...]:
        if self.__truck_distances is None:
            distances: List[float] = []
            config = ProblemConfig()
            for path in self.truck_paths:
                distances.append(0.0)
                for index in range(len(path) - 1):
                    current = self.get_waypoint(path[index])
                    next = self.get_waypoint(path[index + 1])
                    distances[-1] += config.distances[current][next]

            self.__truck_distances = tuple(distances)

        return self.__truck_distances

    @property
    def truck_distance(self) -> float:
        if self.__truck_distance is None:
            self.__truck_distance = sum(self.truck_distances)

        return self.__truck_distance

    @property
    def drone_distances(self) -> Tuple[Tuple[float, ...], ...]:
        if self.__drone_distances is None:
            distances: List[Tuple[float, ...]] = []
            config = ProblemConfig()
            for paths in self.drone_paths:
                distance: List[float] = []
                for path in paths:
                    distance.append(0.0)
                    for index in range(len(path) - 1):
                        current = self.get_waypoint(path[index])
                        next = self.get_waypoint(path[index + 1])
                        distance[-1] += config.distances[current][next]

                distances.append(tuple(distance))

            self.__drone_distances = tuple(distances)

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
                    if not isinstance(value, tuple):
                        raise ValueError(f"Cannot get delivered volume for path {path}")

                    revenue += config.customers[value[0]].w * value[1]

            for paths in self.drone_paths:
                for path in paths:
                    for value in path:
                        if not isinstance(value, tuple):
                            raise ValueError(f"Cannot get delivered volume for path {path}")

                        revenue += config.customers[value[0]].w * value[1]

            self.__revenue = revenue

        return self.__revenue

    @property
    def cost(self) -> float:
        config = ProblemConfig()
        return (
            config.drone.cost_coefficient * self.drone_distance
            + config.truck.cost_coefficient * self.truck_distance
            - self.revenue
        )  # We want to maximize profit i.e. minimize cost = -profit
