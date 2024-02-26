from __future__ import annotations

from typing import AbstractSet, Generic, List, Optional, Sequence, Set, Tuple, TypedDict, TypeVar


__all__ = (
    "crowding_distance_sort",
    "fake_tsp_solver",
    "flows_with_demands",
    "jaccard_distance",
    "LRUCacheInfo",
    "LRUCache",
    "maximum_flow",
    "smallest_circle",
    "tsp_solver",
    "weighted_random",
)
KT = TypeVar("KT")
VT = TypeVar("VT")


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


class LRUCacheInfo(TypedDict):
    max_size: Optional[int]
    hit: int
    miss: int
    cached: int


class LRUCache(Generic[KT, VT]):
    capacity: int
    hit: int
    miss: int
    cached: int

    def __init__(self, capacity: int) -> None: ...
    def get(self, key: KT) -> Optional[VT]: ...
    def set(self, key: KT, value: VT) -> None: ...
    def to_json(self) -> LRUCacheInfo: ...
    def __getitem__(self, key: KT) -> VT: ...
    def __setitem__(self, key: KT, value: VT) -> None: ...
    def __contains__(self, key: KT) -> bool: ...


def maximum_flow(
    *,
    size: int,
    capacities: Sequence[Sequence[float]],
    neighbors: Sequence[Set[int]],
    source: int,
    sink: int,
) -> Tuple[float, List[List[float]]]: ...


def smallest_circle(points: Sequence[Tuple[float, float]]) -> Tuple[float, Tuple[float, float]]: ...


def tsp_solver(
    cities: Sequence[Tuple[float, float]],
    *,
    first: int = 0,
    heuristic_hint: Optional[Sequence[int]] = None,
) -> Tuple[float, List[int]]: ...


def weighted_random(weights: Sequence[float], *, count: int = 1) -> List[int]: ...
