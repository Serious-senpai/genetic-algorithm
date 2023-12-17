from __future__ import annotations

import random
from typing import List, Type, TypeVar, Union, TYPE_CHECKING, final

from matplotlib import pyplot
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

    @classmethod
    def before_generation_hook(cls, generation: int, last_improved: int, result: Self, /) -> None:
        """A classmethod to be called before each generation

        The default implementation does nothing.

        Parameters
        -----
        generation:
            The current generation index (starting from 0)
        last_improved:
            The last generation when the best solution is improved
        result:
            The current best individual
        """
        return

    @classmethod
    def after_generation_hook(cls, generation: int, last_improved: int, result: Self, /) -> None:
        """A classmethod to be called after each generation

        The default implementation does nothing.

        Parameters
        -----
        generation:
            The current generation index (starting from 0)
        last_improved:
            The last generation when the best solution is improved
        result:
            The current best individual
        """
        return

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
    ) -> Self:
        """Perform genetic algorithm to find a solution with the lowest cost

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
        The individual with the lowest cost
        """
        iterations: Union[range, tqdm[int]] = range(generations_count)
        if verbose:
            iterations = tqdm(iterations, ascii=" █")

        population = cls.initial(solution_cls=solution_cls, size=population_size)
        result = min(population)
        if len(population) < population_size:
            message = f"Initial population size {len(population)} < {population_size}"
            raise ValueError(message)

        result = min(result, *population)

        last_improved = 0
        progress: List[float] = []
        if result is not None:
            progress.append(result.cost)

        try:
            for iteration in iterations:
                current_result = result
                if isinstance(iterations, tqdm):
                    display = f"GA ({result.cost:.2f})" if result is not None else "GA"
                    iterations.set_description_str(display)

                cls.before_generation_hook(iteration, last_improved, result)

                # Expand the population, then perform natural selection
                while len(population) < population_expansion_limit:
                    first, second = random.sample(tuple(population), 2)
                    offspring = first.crossover(second)

                    for o in offspring:
                        result = min(result, o)  # offspring may be mutated later, so we update result here
                        o = o.mutate().educate()
                        population.add(o)

                next_population = sorted(population)[:population_size]
                population = set(next_population)
                result = min(result, next_population[0])

                if current_result != result:
                    last_improved = iteration

                if result is not None:
                    progress.append(result.cost)

                cls.after_generation_hook(iteration, last_improved, result)

            if verbose:
                pyplot.plot(progress)
                pyplot.xlabel("Generations")
                pyplot.ylabel("Cost")
                pyplot.show()
                pyplot.close()

        except KeyboardInterrupt:
            pass

        return result