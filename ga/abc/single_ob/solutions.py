from __future__ import annotations

from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from typing_extensions import Self

from .costs import BaseCostComparison
from ..bases import BaseSolution
if TYPE_CHECKING:
    from .individual import BaseSingleObjectiveIndividual


__all__ = (
    "BaseSingleObjectiveSolution",
)


class BaseSingleObjectiveSolution(BaseSolution, BaseCostComparison):
    """Base class for a solution to a single-objective optimization problem"""

    __slots__ = ()

    def encode(self) -> BaseSingleObjectiveIndividual[Self]:
        raise NotImplementedError

    @final
    @classmethod
    def genetic_algorithm(
        cls,
        *,
        generations_count: int,
        population_size: int,
        verbose: bool,
    ) -> BaseSingleObjectiveSolution:
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
        return BaseSingleObjectiveIndividual.genetic_algorithm(
            generations_count=generations_count,
            population_size=population_size,
            solution_cls=cls,
            verbose=verbose,
        ).decode()
