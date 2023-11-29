from __future__ import annotations

import random
from typing import Type, TypeVar, Union, TYPE_CHECKING, final

from tqdm import tqdm

from .costs import BaseCostComparison
from ..bases import BaseIndividual
if TYPE_CHECKING:
    from .solutions import SingleObjectiveSolution


__all__ = (
    "SingleObjectiveIndividual",
)


if TYPE_CHECKING:
    _ST = TypeVar("_ST", bound=SingleObjectiveSolution)
else:
    _ST = TypeVar("_ST")


class SingleObjectiveIndividual(BaseIndividual[_ST], BaseCostComparison):
    """Base class for an individual encoded from a solution to a single-objective optimization problem"""

    __slots__ = ()

    @final
    @classmethod
    def genetic_algorithm(
        cls,
        *,
        generations_count: int,
        population_size: int,
        solution_cls: Type[_ST],
        verbose: bool,
    ) -> SingleObjectiveIndividual[_ST]:
        """Perform genetic algorithm to find an individual with the lowest cost

        Parameters
        -----
        generations_count:
            The number of generations to run
        population_size:
            The size of the population
        solution_cls:
            The solution class
        verbose:
            The verbose mode

        Returns
        -----
        An individual with the lowest cost among the generations
        """
        iterations: Union[range, tqdm[int]] = range(generations_count)
        if verbose:
            iterations = tqdm(iterations, ascii=" █")

        population = cls.initial(solution_cls=solution_cls, size=population_size)
        for _ in iterations:
            if isinstance(iterations, tqdm):
                optimum = min(population)
                iterations.set_description_str(f"GA ({optimum.cost:.2f})")

            # Double the population, then perform natural selection
            counter = 0
            while counter < population_size:
                first, second = random.sample(population, 2)
                offspring = first.crossover(second)

                if offspring is not None:
                    counter += 1
                    offspring.mutate()
                    population.append(offspring)

            population.sort()
            population = population[:population_size]

        return population[0]
