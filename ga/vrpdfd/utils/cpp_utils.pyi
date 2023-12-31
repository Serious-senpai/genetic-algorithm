from typing import AbstractSet, Dict, List, Sequence, Set, Tuple


def set_customers(low: Sequence[float], high: Sequence[float], w: Sequence[float]) -> None: ...


def paths_from_flow(
    truck_paths_count: int,
    drone_paths_count: Sequence[int],
    flows: Sequence[Sequence[float]],
    neighbors: Sequence[Set[int]],
) -> Tuple[
    List[Dict[int, float]],
    List[List[Dict[int, float]]],
]: ...


def paths_from_flow_chained(
    truck_paths: Sequence[AbstractSet[int]],
    drone_paths: Sequence[Sequence[AbstractSet[int]]],
    truck_capacity: float,
    drone_capacity: float,
) -> Tuple[
    List[Dict[int, float]],
    List[List[Dict[int, float]]],
]: ...
