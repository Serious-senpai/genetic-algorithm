from __future__ import annotations

import abc
from typing import Generic, TypeVar, TYPE_CHECKING, final

if TYPE_CHECKING:
    from typing_extensions import Self

from .costs import BaseCostComparison
from ..bases import BaseSolution
if TYPE_CHECKING:
    from .individual import SingleObjectiveIndividual


__all__ = (
    "SingleObjectiveSolution",
)
_IT = TypeVar("_IT", bound=SingleObjectiveIndividual)


class SingleObjectiveSolution(BaseSolution, BaseCostComparison, Generic[_IT]):
    """Base class for a solution to a single-objective optimization problem"""

    __slots__ = ()

    @abc.abstractmethod
    def encode(self) -> _IT: ...

    @final
    @classmethod
    def genetic_algorithm(
        cls,
        *,
        generations_count: int,
        population_size: int,
        verbose: bool,
    ) -> Self:
        """Perform genetic algorithm to find a solution with the lowest cost

        Parameters
        -----
        generations_count:
            The number of generations to run
        population_size:
            The size of the population
        verbose:
            The verbose mode

        Returns
        -----
        A solution with the lowest cost
        """
        return SingleObjectiveIndividual.genetic_algorithm(
            generations_count=generations_count,
            population_size=population_size,
            solution_cls=cls,
            verbose=verbose,
        ).decode()
