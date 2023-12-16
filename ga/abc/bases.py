from __future__ import annotations

import abc
from typing import Generic, Iterable, Optional, Set, Type, TypeVar, TYPE_CHECKING, final

if TYPE_CHECKING:
    from typing_extensions import Self


__all__ = (
    "BaseSolution",
    "BaseIndividual",
)


class BaseSolution(abc.ABC):
    """Base class for solutions to any optimization problems."""

    __slots__ = ()

    @abc.abstractmethod
    def encode(self) -> BaseIndividual[Self]:
        """Encode this solution to an individual

        Subclasses must implement this.
        """
        ...

    @final
    @classmethod
    def from_individual(cls, individual: BaseIndividual[Self], /) -> Optional[Self]:
        """Decode `individual` into a solution"""
        return individual.decode()


_ST = TypeVar("_ST", bound=BaseSolution)


class BaseIndividual(abc.ABC, Generic[_ST]):
    """Base class for an individual encoded from a solution"""

    __slots__ = ()

    @property
    @abc.abstractmethod
    def cls(self) -> Type[_ST]:
        """The solution class"""
        ...

    @abc.abstractmethod
    def decode(self) -> Optional[_ST]:
        """Decode this individual into a solution

        Subclasses must implement this.

        Returns
        -----
        The decoded solution, or None is this individual is infeasible. If the returned result is not None,
        the algorithm will assume that the decoded solution is always feasible.
        """
        ...

    @abc.abstractmethod
    def crossover(self, other: Self, /) -> Iterable[Self]:
        """Perform a crossover operation

        Subclasses must implement this.
        """
        ...

    @abc.abstractmethod
    def mutate(self) -> Self:
        """Perform a mutation operation

        Subclasses must implement this.
        """
        ...

    def educate(self) -> Self:
        """Improve the quality of this individual

        The default implementation does nothing.
        """
        return self

    @classmethod
    @abc.abstractmethod
    def initial(cls, *, solution_cls: Type[_ST], size: int) -> Set[Self]:
        """Generate the initial population

        Subclasses must implement this.

        Parameters
        -----
        solution_cls:
            The solution class
        size:
            The population size

        Returns
        -----
        The initial population
        """
        ...
