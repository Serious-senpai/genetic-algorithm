from __future__ import annotations

import random
from typing import List, Optional, Type, TypeVar, Union, TYPE_CHECKING, final


from matplotlib import pyplot
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
        population_expansion_limit: int,
        solution_cls: Type[_ST],
        verbose: bool,
    ) -> Optional[_ST]:
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
        A feasible solution with the lowest cost among the generations, or
        None if no feasible individual is found
        """
        def optional_min(first: Optional[_ST], second: Optional[_ST]) -> Optional[_ST]:
            if first is None:
                return second

            if second is None:
                return first

            return min(first, second)

        iterations: Union[range, tqdm[int]] = range(generations_count)
        if verbose:
            iterations = tqdm(iterations, ascii=" █")

        result: Optional[_ST] = None
        population = cls.initial(solution_cls=solution_cls, size=population_size)
        if len(population) < population_size:
            message = f"Initial population size {len(population)} < {population_size}"
            raise ValueError(message)

        for individual in population:
            r = individual.decode()
            result = optional_min(result, r)

        last_improved = 0
        progress: List[float] = []
        if result is not None:
            progress.append(result.cost)

        for iteration in iterations:
            current_result = result
            if isinstance(iterations, tqdm):
                display = f"GA ({result.cost:.2f})" if result is not None else "GA"
                iterations.set_description_str(display)

            solution_cls.before_generation_hook(iteration, last_improved, result)

            # Expand the population, then perform natural selection
            while len(population) < population_expansion_limit:
                first, second = random.sample(tuple(population), 2)
                offspring = first.crossover(second)

                for o in offspring:
                    result = optional_min(result, o.decode())  # offspring may be mutated later, so we update result here
                    o = o.mutate().educate()
                    population.add(o)

            feasible = [individual for individual in population if individual.decode() is not None]
            infeasible = [individual for individual in population if individual.decode() is None]

            population.clear()
            population.update(feasible[:population_size // 2])
            population.update(infeasible[:population_size - len(population)])

            if len(feasible) > 0:
                result = optional_min(result, feasible[0].decode())

            if current_result != result:
                last_improved = iteration

            if result is not None:
                progress.append(result.cost)

            solution_cls.after_generation_hook(iteration, last_improved, result)

        if verbose:
            pyplot.plot(progress)
            pyplot.xlabel("Generations")
            pyplot.ylabel("Cost")
            pyplot.show()
            pyplot.close()

        return result
