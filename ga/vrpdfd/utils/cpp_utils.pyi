from typing import AbstractSet, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple, Type

from ..individuals import VRPDFDIndividual
from ..solutions import VRPDFDSolution


__all__ = (
    "set_customers",
    "decode",
    "educate",
    "local_search",
    "paths_from_flow",
)


def set_customers(
    low: Sequence[int],
    high: Sequence[int],
    w: Sequence[int],
    x: Sequence[float],
    y: Sequence[float],
) -> None: ...


def decode(
    truck_paths: Sequence[AbstractSet[int]],
    drone_paths: Sequence[Sequence[AbstractSet[int]]],
    truck_capacity: int,
    drone_capacity: int,
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
