from __future__ import annotations

import math
from collections import OrderedDict
from typing import Any, Iterable, Optional, Sequence, TypedDict, TypeVar, Union, TYPE_CHECKING, overload

from .cpp_utils import weighted_random


__all__ = ("LRUCacheInfo", "LRUCache", "isclose", "positive_max", "value", "weighted_random_choice", "weird_round")
_T = TypeVar("_T")
_K = TypeVar("_K")
_V = TypeVar("_V")


class LRUCacheInfo(TypedDict):
    max_size: Optional[int]
    hit: int
    miss: int
    cached: int


class LRUCache(OrderedDict[_K, _V]):

    __slots__ = ("max_size", "hit", "miss", "cached")
    if TYPE_CHECKING:
        max_size: Optional[int]
        hit: int
        miss: int
        cached: int

    def __init__(self, max_size: Optional[int] = None, /) -> None:
        self.max_size = max_size
        self.hit = 0
        self.miss = 0
        self.cached = 0

    def __getitem__(self, __key: _K) -> _V:
        try:
            value = super().__getitem__(__key)
            self.hit += 1
        except KeyError:
            self.miss += 1
            raise

        self.move_to_end(__key)
        return value

    def __setitem__(self, __key: _K, __value: _V) -> None:
        if self.max_size is not None:
            while self.__len__() >= self.max_size:
                self.popitem(last=False)

        self.cached += 1
        return super().__setitem__(__key, __value)

    def to_json(self) -> LRUCacheInfo:
        return {
            "max_size": self.max_size,
            "hit": self.hit,
            "miss": self.miss,
            "cached": self.cached,
        }


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
