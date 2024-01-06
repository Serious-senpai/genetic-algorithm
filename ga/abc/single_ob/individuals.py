from __future__ import annotations

from typing import FrozenSet, List, Set, Type, TypeVar, Union, TYPE_CHECKING, final

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
    def before_generation_hook(
        cls,
        *,
        generation: int,
        last_improved: int,
        result: Self,
        population: Set[Self],
        verbose: bool,
    ) -> None:
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
        population:
            The current population
        verbose:
            The verbose mode
        """
        return

    @classmethod
    def after_generation_hook(
        cls,
        *,
        generation: int,
        last_improved: int,
        result: Self,
        population: Set[Self],
        verbose: bool,
    ) -> None:
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
        population:
            The current population
        verbose:
            The verbose mode
        """
        return

    @classmethod
    def selection(cls, *, population: FrozenSet[Self], size: int) -> Set[Self]:
        """Perform natural selection

        The default implementation selects the best individuals, but subclasses
        may override this behavior.

        Parameters
        -----
        population:
            The population to select from
        size:
            The selection size

        Returns
        -----
        The selected population
        """
        sorted_population = sorted(population)
        return set(sorted_population[:size])

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
        filtered = tuple(filter(lambda i: i.feasible(), population))
        if len(filtered) > 0:
            result = min(filtered)
        else:
            # The entire population is infeasible, so we pick the highest cost so that
            # in will be more likely to be replaced by a feasible individual later
            result = max(population)

        if len(population) < population_size:
            message = f"Initial population size {len(population)} < {population_size}"
            raise ValueError(message)

        last_improved = 0
        progress: List[float] = []
        progress.append(result.cost)

        try:
            for iteration in iterations:
                current_result = result
                if isinstance(iterations, tqdm):
                    display = f"GA ({result.cost:.2f})"
                    iterations.set_description_str(display)

                cls.before_generation_hook(
                    generation=iteration,
                    last_improved=last_improved,
                    result=result,
                    population=population,
                    verbose=verbose,
                )
                if len(population) > population_size:
                    message = f"Population size {len(population)} > {population_size}"
                    raise ValueError(message)

                # Expand the population, then perform natural selection
                while len(population) < population_expansion_limit:
                    first, second = cls.parents_selection(population=frozenset(population))
                    offspring = first.crossover(second)

                    for o in offspring:
                        if o.feasible():
                            # offspring may be mutated later, so we update result here
                            result = min(result, o)

                        o = o.mutate().educate()
                        population.add(o)

                filtered = tuple(filter(lambda i: i.feasible(), population))
                if len(filtered) > 0:
                    result = min(result, *filtered)

                population = cls.selection(population=frozenset(population), size=population_size)
                if len(population) > population_size:
                    message = f"Population size {len(population)} > {population_size}"
                    raise ValueError(message)

                if current_result != result:
                    last_improved = iteration

                cls.after_generation_hook(
                    generation=iteration,
                    last_improved=last_improved,
                    result=result,
                    population=population,
                    verbose=verbose,
                )
                if len(population) > population_size:
                    message = f"Population size {len(population)} > {population_size}"
                    raise ValueError(message)

                # after_generation_hook may add new individuals
                filtered = tuple(filter(lambda i: i.feasible(), population))
                if len(filtered) > 0:
                    result = min(result, *filtered)

                if current_result != result:
                    last_improved = iteration

                progress.append(result.cost)

            if verbose:
                pyplot.plot(progress)
                pyplot.xlabel("Generations")
                pyplot.ylabel("Cost")
                pyplot.show()
                pyplot.close()

        except KeyboardInterrupt:
            pass

        return result
