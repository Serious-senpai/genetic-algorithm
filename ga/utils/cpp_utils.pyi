from __future__ import annotations

from typing import List, Optional, Sequence, Set, Tuple


__all__ = (
    "flows_with_demands",
    "maximum_flow",
    "tsp_solver",
    "weighted_random",
)


def flows_with_demands(
    *,
    size: int,
    capacities: Sequence[Sequence[float]],
    neighbors: Sequence[Set[int]],
    source: int,
    sink: int,
) -> Optional[Tuple[float, List[List[float]]]]: ...


def maximum_flow(
    *,
    size: int,
    capacities: Sequence[Sequence[float]],
    neighbors: Sequence[Set[int]],
    source: int,
    sink: int,
) -> Tuple[float, List[List[float]]]: ...


def tsp_solver(cities: Sequence[Tuple[float, float]], *, first: int = 0) -> Tuple[float, List[int]]: ...
def weighted_random(weights: Sequence[float], *, count: int = 1) -> List[int]: ...
