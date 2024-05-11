from __future__ import annotations

from typing import AbstractSet, Generic, Hashable, Iterator, List, Optional, Sequence, Set, Tuple, TypeVar

from .py_utils import LRUCacheInfo


__all__ = (
    "crowding_distance_sort",
    "fake_tsp_solver",
    "flows_with_demands",
    "jaccard_distance",
    "LRUCache",
    "maximum_flow",
    "smallest_circle",
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


KT = TypeVar("KT", bound=Hashable)
VT = TypeVar("VT")


class LRUCache(Generic[KT, VT]):
    capacity: int
    hit: int
    miss: int
    cached: int

    def __init__(self, capacity: int) -> None: ...
    def get(self, key: KT) -> Optional[VT]: ...
    def set(self, key: KT, value: VT) -> None: ...
    def to_json(self) -> LRUCacheInfo: ...
    def items(self) -> Iterator[Tuple[KT, VT]]: ...
    def __getitem__(self, key: KT) -> VT: ...
    def __setitem__(self, key: KT, value: VT) -> None: ...
    def __contains__(self, key: KT) -> bool: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[KT]: ...


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
