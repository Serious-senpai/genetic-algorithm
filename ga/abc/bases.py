from __future__ import annotations

from typing import Final, Generic, List, Optional, Type, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self


__all__ = (
    "BaseSolution",
    "BaseIndividual",
)


class BaseSolution:
    """Base class for solutions to any optimization problems."""

    def encode(self) -> BaseIndividual[Self]:
        """Encode this solution to an individual

        Subclasses must implement this.
        """
        raise NotImplementedError


_ST = TypeVar("_ST", bound=BaseSolution)


class BaseIndividual(Generic[_ST]):
    """Base class for an individual encoded from a solution"""

    __slots__ = ("cls")

    def __init__(self, cls: Type[_ST], /) -> None:
        self.cls: Final[Type[_ST]] = cls

    def decode(self) -> _ST:
        """Decode this individual into a solution

        Subclasses must implement this.
        """
        raise NotImplementedError

    def crossover(self, other: Self, /) -> Optional[Self]:
        """Perform a crossover operation

        Subclasses must implement this.
        """
        raise NotImplementedError

    def mutate(self) -> None:
        """Perform a mutation operation

        Subclasses must implement this.
        """
        raise NotImplementedError

    @classmethod
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
        raise NotImplementedError
