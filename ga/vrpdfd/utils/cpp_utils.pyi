from typing import AbstractSet, Dict, List, Optional, Sequence, Set, Tuple

from ..individuals import VRPDFDIndividual


__all__ = (
    "setup",
    "setup_path_cache",
    "path_cache_info",
    "path_order",
    "decode",
    "educate",
    "local_search",
    "paths_from_flow",
)


def setup(
    low: Sequence[int],
    high: Sequence[int],
    w: Sequence[int],
    x: Sequence[float],
    y: Sequence[float],
    truck_distance_limit: float,
    drone_distance_limit: float,
    truck_capacity: int,
    drone_capacity: int,
    truck_cost_coefficient: float,
    drone_cost_coefficient: float,
) -> None: ...


def setup_path_cache(capacity: int) -> None: ...
def path_cache_info() -> Dict[str, int]: ...
def path_order(path: AbstractSet[int]) -> Tuple[float, List[int]]: ...


def decode(
    truck_paths: Sequence[AbstractSet[int]],
    drone_paths: Sequence[Sequence[AbstractSet[int]]],
) -> Tuple[
    List[Dict[int, int]],
    List[List[Dict[int, int]]],
]: ...


def educate(py_individual: VRPDFDIndividual) -> VRPDFDIndividual: ...
def local_search(py_individual: VRPDFDIndividual) -> Tuple[Optional[VRPDFDIndividual], VRPDFDIndividual]: ...


def paths_from_flow(
    truck_paths_count: int,
    drone_paths_count: Sequence[int],
    flows: Sequence[Sequence[int]],
    neighbors: Sequence[Set[int]],
) -> Tuple[
    List[Dict[int, int]],
    List[List[Dict[int, int]]],
]: ...
