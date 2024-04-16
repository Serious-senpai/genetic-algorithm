from __future__ import annotations

from typing import Dict, Optional, Sequence, Tuple, TypedDict

from ..utils import LRUCacheInfo


__all__ = (
    "SolutionInfo",
    "CacheInfo",
    "SolutionJSON",
    "MILPSolutionJSON",
)


class SolutionInfo(TypedDict):
    profit: float
    feasible: bool
    truck_paths: Sequence[Sequence[Tuple[int, float]]]
    drone_paths: Sequence[Sequence[Sequence[Tuple[int, float]]]]


class CacheInfo(TypedDict):
    limit: int
    individual: LRUCacheInfo
    tsp: LRUCacheInfo


class SolutionJSON(TypedDict):
    problem: str
    generations: int
    population_size: int
    mutation_rate: float
    reset_after: int
    local_search_batch: int
    solution: SolutionInfo
    time: float
    fake_tsp_solver: bool
    last_improved: int
    extra: Optional[str]
    cache_info: CacheInfo


class MILPSolutionJSON(TypedDict):
    # We only annotate the fields in need here
    data_set: str
    status: str
    solve_time: float
    obj_value: float
    truck: Dict[str, float]
    drone: Dict[str, float]
    cusWeightByDrone: Dict[str, float]
    cusWeightByTruck: Dict[str, float]
