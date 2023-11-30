from __future__ import annotations

import abc
from typing import Generic, List, Optional, Type, TypeVar, TYPE_CHECKING, final

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
    def from_individual(cls, individual: BaseIndividual[Self], /) -> Self:
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
    def decode(self) -> _ST:
        """Decode this individual into a solution

        Subclasses must implement this.
        """
        ...

    @abc.abstractmethod
    def crossover(self, other: Self, /) -> Optional[Self]:
        """Perform a crossover operation

        Subclasses must implement this.
        """
        ...

    @abc.abstractmethod
    def mutate(self) -> None:
        """Perform a mutation operation

        Subclasses must implement this.
        """
        ...

    @final
    @classmethod
    def from_solution(cls, solution: _ST, /) -> BaseIndividual[_ST]:
        """Encode `solution` into an individual"""
        return solution.encode()

    @classmethod
    @abc.abstractmethod
    def initial(cls, *, solution_cls: Type[_ST], size: int) -> List[Self]:
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
