from __future__ import annotations

import math
from typing import Any, Iterable, Optional, Sequence, TypeVar, TypedDict, Union, overload

from .cpp_utils import weighted_random


__all__ = ("LRUCacheInfo", "isclose", "positive_max", "value", "weighted_random_choice", "weird_round")
_T = TypeVar("_T")


class LRUCacheInfo(TypedDict):
    max_size: Optional[int]
    hit: int
    miss: int
    cached: int


@overload
def isclose(
    first: float,
    second: float,
    /,
) -> bool: ...


@overload
def isclose(
    first: Sequence[float],
    second: Sequence[float],
    /,
) -> bool: ...


@overload
def isclose(
    first: Sequence[Sequence[float]],
    second: Sequence[Sequence[float]],
    /,
) -> bool: ...


@overload
def isclose(
    first: Sequence[Sequence[Sequence[float]]],
    second: Sequence[Sequence[Sequence[float]]],
    /,
) -> bool: ...


@overload
def isclose(
    first: Sequence[Sequence[Sequence[Sequence[float]]]],
    second: Sequence[Sequence[Sequence[Sequence[float]]]],
    /,
) -> bool: ...


@overload
def isclose(
    first: Sequence[Sequence[Sequence[Sequence[Sequence[float]]]]],
    second: Sequence[Sequence[Sequence[Sequence[Sequence[float]]]]],
    /,
) -> bool: ...


def isclose(first: Any, second: Any, /) -> bool:
    try:
        return all(isclose(f, s) for f, s in zip(first, second, strict=True))
    except TypeError:
        return abs(first - second) < 0.0001


def positive_max(*values: Union[float, Iterable[float]]) -> float:
    """Equivalent to max(0.0, 0.0, *values)"""
    result = 0.0
    for value in values:
        if isinstance(value, (float, int)):
            result = max(result, value)
        else:
            result = max(result, result, *value)  # must have at least 2 arguments

    return result


def value(__x: _T, /) -> _T:
    return __x


def weighted_random_choice(choices: Sequence[float], /) -> int:
    return weighted_random(choices, count=1)[0]


def weird_round(number: float, precision: int, /) -> float:
    factor = 10 ** precision
    return math.ceil(number * factor) / factor
