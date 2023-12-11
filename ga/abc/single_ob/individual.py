from __future__ import annotations

import random
from typing import Type, TypeVar, Union, TYPE_CHECKING, final

from tqdm import tqdm
if TYPE_CHECKING:
    from typing_extensions import Self

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
        population_expansion_limit: int,
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

        population = sorted(cls.initial(solution_cls=solution_cls, size=population_size))
        if len(population) < population_size:
            message = f"Initial population size {len(population)} < {population_size}"
            raise ValueError(message)

        result = population[0]
        for iteration in iterations:
            if isinstance(iterations, tqdm):
                iterations.set_description_str(f"GA ({result.cost:.2f})")

            cls.before_generation_hook(iteration, result)

            # Double the population, then perform natural selection
            while len(population) < population_expansion_limit:
                first, second = random.sample(population, 2)
                offspring = first.crossover(second)

                for o in offspring:
                    result = min(result, o)  # offspring may be mutated later, so we update result here
                    o = o.mutate().educate()
                    population.append(o)

            population.sort()
            population = population[:population_size]
            result = min(result, population[0])

            cls.after_generation_hook(iteration, result)

        return result

    @classmethod
    def before_generation_hook(cls, generation: int, result: Self, /) -> None:
        """A classmethod to be called before each generation

        The default implementation does nothing.

        Parameters
        -----
        generation:
            The current generation index (starting from 0)
        result:
            The current best individual
        """
        return

    @classmethod
    def after_generation_hook(cls, generation: int, result: Self, /) -> None:
        """A classmethod to be called after each generation

        The default implementation does nothing.

        Parameters
        -----
        generation:
            The current generation index (starting from 0)
        result:
            The current best individual
        """
        return
