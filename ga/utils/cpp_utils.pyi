from __future__ import annotations

from typing import List, Sequence, Set, Tuple


__all__ = (
    "maximum_flow",
    "tsp_solver",
    "weighted_random",
)


def maximum_flow(
    *,
    size: int,
    capacities: Sequence[Sequence[float]],
    neighbors: Sequence[Set[int]],
    source: int,
    sink: int,
) -> Tuple[float, List[List[float]]]: ...


def tsp_solver(distances: Sequence[Tuple[int, int]]) -> Tuple[float, List[int]]: ...
def weighted_random(weights: Sequence[float], *, count: int = 1) -> List[int]: ...
