from __future__ import annotations

from typing import Final, Generic, Optional, Tuple, TypeVar, TYPE_CHECKING

from .config import ProblemConfig


__all__ = ("SupportCostsEvaluation",)
_T = TypeVar("_T", int, Tuple[int, float])


class SupportCostsEvaluation(Generic[_T]):

    __slots__ = (
        "__truck_distance",
        "__drone_distance",
        "__revenue",
        "truck_paths",
        "drone_paths",
    )
    if TYPE_CHECKING:
        __truck_distance: Optional[float]
        __drone_distance: Optional[float]
        __revenue: Optional[float]
        truck_paths: Final[Tuple[Tuple[_T, ...], ...]]  # type: ignore
        drone_paths: Final[Tuple[Tuple[Tuple[_T, ...], ...], ...]]  # type: ignore

    def __init__(
        self,
        *,
        truck_paths: Tuple[Tuple[_T, ...], ...],
        drone_paths: Tuple[Tuple[Tuple[_T, ...], ...], ...],
        truck_distance: Optional[float] = None,
        drone_distance: Optional[float] = None,
        revenue: Optional[float] = None,
    ) -> None:
        self.truck_paths = truck_paths
        self.drone_paths = drone_paths
        self.__truck_distance = truck_distance
        self.__drone_distance = drone_distance
        self.__revenue = revenue

    def get_waypoint(self, value: _T, /) -> int:
        if isinstance(value, tuple):
            return value[0]

        return value

    @property
    def truck_distance(self) -> float:
        if self.__truck_distance is None:
            distance = 0.0
            config = ProblemConfig()
            for path in self.truck_paths:
                for index in range(len(path) - 1):
                    current = self.get_waypoint(path[index])
                    next = self.get_waypoint(path[index + 1])
                    distance += config.distances[current][next]

            self.__truck_distance = distance

        return self.__truck_distance

    @property
    def drone_distance(self) -> float:
        if self.__drone_distance is None:
            distance = 0.0
            config = ProblemConfig()
            for paths in self.drone_paths:
                for path in paths:
                    for index in range(len(path) - 1):
                        current = self.get_waypoint(path[index])
                        next = self.get_waypoint(path[index + 1])
                        distance += config.distances[current][next]

            self.__drone_distance = distance

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
