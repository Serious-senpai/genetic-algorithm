from __future__ import annotations

from typing import AbstractSet, List, Optional, Sequence, Set, Tuple


__all__ = (
    "crowding_distance_sort",
    "fake_tsp_solver",
    "flows_with_demands",
    "jaccard_distance",
    "maximum_flow",
    "tsp_solver",
    "weighted_random",
)


def crowding_distance_sort(sets: Sequence[Sequence[AbstractSet[int]]], *, k: int = 2) -> List[int]: ...


def fake_tsp_solver(
    cities: Sequence[Tuple[float, float]],
    *,
    first: int = 0,
    heuristic_hint: Optional[Sequence[int]] = None,
) -> Tuple[float, List[int]]: ...


def flows_with_demands(
    *,
    size: int,
    demands: Sequence[Sequence[float]],
    capacities: Sequence[Sequence[float]],
    neighbors: Sequence[Set[int]],
    source: int,
    sink: int,
) -> Optional[List[List[float]]]: ...


def jaccard_distance(first: AbstractSet[int], second: AbstractSet[int]) -> float: ...


def maximum_flow(
    *,
    size: int,
    capacities: Sequence[Sequence[float]],
    neighbors: Sequence[Set[int]],
    source: int,
    sink: int,
) -> Tuple[float, List[List[float]]]: ...


def tsp_solver(
    cities: Sequence[Tuple[float, float]],
    *,
    first: int = 0,
    heuristic_hint: Optional[Sequence[int]] = None,
) -> Tuple[float, List[int]]: ...


def weighted_random(weights: Sequence[float], *, count: int = 1) -> List[int]: ...
