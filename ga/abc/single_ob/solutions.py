from __future__ import annotations

import abc
from typing import Generic, TypeVar, TYPE_CHECKING

from .costs import BaseCostComparison
from ..bases import BaseSolution
if TYPE_CHECKING:
    from .individuals import SingleObjectiveIndividual


__all__ = (
    "SingleObjectiveSolution",
)
if TYPE_CHECKING:
    _IT = TypeVar("_IT", bound=SingleObjectiveIndividual)
else:
    _IT = TypeVar("_IT")


class SingleObjectiveSolution(BaseSolution, BaseCostComparison, Generic[_IT]):
    """Base class for a solution to a single-objective optimization problem"""

    __slots__ = ()

    @abc.abstractmethod
    def encode(self) -> _IT: ...
