from __future__ import annotations

import abc
from functools import total_ordering
from typing import Any


__all__ = ("BaseCostComparison",)


@total_ordering
class BaseCostComparison(abc.ABC):
    """Base class for objects holding a real-valued number as their costs"""

    __slots__ = ()

    @property
    @abc.abstractmethod
    def cost(self) -> float:
        """The cost of this object

        Subclasses must implement this.
        """
        ...

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, self.__class__):
            return self.cost == other.cost

        return NotImplemented

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, self.__class__):
            return self.cost < other.cost

        return NotImplemented
