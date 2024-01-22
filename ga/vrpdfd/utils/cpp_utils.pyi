from typing import AbstractSet, Dict, List, Optional, Sequence, Set, Tuple

from ..individuals import VRPDFDIndividual


__all__ = (
    "set_customers",
    "paths_from_flow",
    "paths_from_flow_chained",
    "local_search",
    "educate",
)


def set_customers(
    low: Sequence[int],
    high: Sequence[int],
    w: Sequence[int],
    x: Sequence[float],
    y: Sequence[float],
) -> None: ...


def paths_from_flow(
    truck_paths_count: int,
    drone_paths_count: Sequence[int],
    flows: Sequence[Sequence[int]],
    neighbors: Sequence[Set[int]],
) -> Tuple[
    List[Dict[int, int]],
    List[List[Dict[int, int]]],
]: ...


def paths_from_flow_chained(
    truck_paths: Sequence[AbstractSet[int]],
    drone_paths: Sequence[Sequence[AbstractSet[int]]],
    truck_capacity: int,
    drone_capacity: int,
) -> Tuple[
    List[Dict[int, int]],
    List[List[Dict[int, int]]],
]: ...


def local_search(py_individual: VRPDFDIndividual) -> Tuple[Optional[VRPDFDIndividual], VRPDFDIndividual]: ...
def educate(py_individual: VRPDFDIndividual) -> VRPDFDIndividual: ...
