from __future__ import annotations

from typing import Sequence, Tuple, TypeVar


__all__ = ("fast_access",)
_T = TypeVar("_T")


def fast_access(array: Sequence[Sequence[_T]], index: Tuple[int, int], /) -> _T:
    return array[index[0]][index[1]]
