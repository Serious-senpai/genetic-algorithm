from __future__ import annotations

import math
from typing import Any, Final, Iterable, Iterator, Optional, Sequence, Set, TypeVar, TypedDict, Union, TYPE_CHECKING, overload

import tqdm

from .cpp_utils import weighted_random


__all__ = ("LRUCacheInfo", "isclose", "positive_max", "value", "weighted_random_choice", "weird_round", "SizeMonitoredSet")
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
    result = 0.0
    for value in values:
        if isinstance(value, (float, int)):
            result = max(result, value)
        else:
            result = max(result, positive_max(*value))

    return result


def value(__x: _T, /) -> _T:
    return __x


def weighted_random_choice(choices: Sequence[float], /) -> int:
    return weighted_random(choices, count=1)[0]


def weird_round(number: float, precision: int, /) -> float:
    factor = 10 ** precision
    return math.ceil(number * factor) / factor


class SizeMonitoredSet(Iterable[_T]):

    __slots__ = (
        "__progress",
        "__tqdm_iter",
        "__set",
    )
    if TYPE_CHECKING:
        __progress: int
        __tqdm_iter: Final[Iterator[int]]

    def __init__(
        self,
        *,
        initial: Optional[Set[_T]] = None,
        max_size: int,
        color: Optional[str] = None,
        description: str,
    ) -> None:
        if initial is None:
            initial = set()

        displayer = tqdm.tqdm(range(max_size), ascii=" █", colour=color)
        displayer.set_description_str(description)

        self.__progress = 0
        self.__tqdm_iter = iter(displayer)
        self.__set: Final[Set[_T]] = initial

    def __update(self) -> None:
        while len(self.__set) >= self.__progress:
            try:
                next(self.__tqdm_iter)
            except StopIteration:
                pass

            self.__progress += 1

    def add(self, value: _T, /) -> None:
        self.__set.add(value)
        self.__update()

    def __iter__(self) -> Iterator[_T]:
        return iter(self.__set)

    def __len__(self) -> int:
        return len(self.__set)
