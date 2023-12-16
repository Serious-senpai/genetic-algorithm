from __future__ import annotations

import abc
from typing import Generic, Optional, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self

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

    @classmethod
    def before_generation_hook(cls, generation: int, result: Optional[Self], /) -> None:
        """A classmethod to be called before each generation

        The default implementation does nothing.

        Parameters
        -----
        generation:
            The current generation index (starting from 0)
        result:
            The current best solution
        """
        return

    @classmethod
    def after_generation_hook(cls, generation: int, result: Optional[Self], /) -> None:
        """A classmethod to be called after each generation

        The default implementation does nothing.

        Parameters
        -----
        generation:
            The current generation index (starting from 0)
        result:
            The current best solution
        """
        return
