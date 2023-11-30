from __future__ import annotations

from typing import Iterable, List


__all__ = (
    "weighted_random",
)


def weighted_random(weights: Iterable[float], count: int = 1) -> List[int]: ...
