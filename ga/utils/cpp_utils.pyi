from __future__ import annotations

from typing import List, Optional, Sequence, Set, Tuple


__all__ = (
    "fake_tsp_solver",
    "flows_with_demands",
    "maximum_flow",
    "maximum_weighted_flow",
    "tsp_solver",
    "weighted_random",
)


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


def maximum_flow(
    *,
    size: int,
    capacities: Sequence[Sequence[float]],
    neighbors: Sequence[Set[int]],
    source: int,
    sink: int,
) -> Tuple[float, List[List[float]]]: ...


def maximum_weighted_flow(
    *,
    size: int,
    capacities: Sequence[Sequence[float]],
    neighbors: Sequence[Set[int]],
    flow_weights: Sequence[Sequence[float]],
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
