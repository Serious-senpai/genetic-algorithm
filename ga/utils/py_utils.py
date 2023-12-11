from __future__ import annotations

from typing import Any, Sequence, Tuple, TypeVar, overload

from .cpp_utils import weighted_random


__all__ = ("fast_get", "fast_set", "value", "weighted_random_choice")
_T = TypeVar("_T")


@overload
def fast_get(array: Sequence[Sequence[_T]], index: Tuple[int, int], /) -> _T: ...
@overload
def fast_get(array: Sequence[Sequence[Sequence[_T]]], index: Tuple[int, int, int], /) -> _T: ...


def fast_get(array: Any, index: Sequence[int], /) -> Any:
    result = array
    for i in index:
        result = result[i]

    return result


@overload
def fast_set(array: Sequence[Sequence[_T]], index: Tuple[int, int], value: _T, /) -> None: ...
@overload
def fast_set(array: Sequence[Sequence[Sequence[_T]]], index: Tuple[int, int, int], value: _T, /) -> None: ...


def fast_set(array: Any, index: Sequence[int], value: Any, /) -> Any:
    for i in index[:-1]:
        array = array[i]

    array[index[-1]] = value


def value(__x: _T, /) -> _T:
    return __x


def weighted_random_choice(choices: Sequence[Tuple[_T, float]], /) -> _T:
    index = weighted_random([choice[1] for choice in choices], count=1)[0]
    return choices[index][0]
