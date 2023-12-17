from __future__ import annotations

from typing import Any, Iterable, Sequence, TypeVar, overload

from .cpp_utils import weighted_random


__all__ = ("isclose", "positive_max", "value", "weighted_random_choice")
_T = TypeVar("_T")


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
        return all(isclose(f, s) for f, s in zip(first, second))
    except TypeError:
        return abs(first - second) < 0.0001


def positive_max(values: Iterable[float], /) -> float:
    """Equivalent to max(0.0, 0.0, *values)"""
    return max(0.0, 0.0, *values)


def value(__x: _T, /) -> _T:
    return __x


def weighted_random_choice(choices: Sequence[float], /) -> int:
    return weighted_random(choices, count=1)[0]
