from __future__ import annotations

import textwrap
from typing import Final, Iterable, Set, Tuple, TYPE_CHECKING, final

if TYPE_CHECKING:
    from .individuals import VRPDFDIndividual


__all__ = ("HistoryRecord",)
PREFIX = "  "


@final
class HistoryRecord:

    __slots__ = (
        "message",
        "origin",
    )
    if TYPE_CHECKING:
        message: Final[str]
        origin: Final[Tuple[VRPDFDIndividual, ...]]

    def __init__(self, message: str, origin: Iterable[VRPDFDIndividual]) -> None:
        self.message = message
        self.origin = tuple(origin)

    @staticmethod
    def display(individual: VRPDFDIndividual, *, hide_unchanged: bool = True) -> str:
        def _display(individual: VRPDFDIndividual, chain: Set[VRPDFDIndividual]) -> str:
            history = individual.history
            if hide_unchanged and history is not None:
                for origin in history.origin:
                    if origin == individual:  # Similar cost, 99% having the same config for random data, ignore that 1% :)
                        return _display(origin, chain)

            contents = [str(individual)]
            if history is None:
                contents.append(f"{PREFIX}[none]")

            elif individual in chain:
                contents.append(f"{PREFIX}[duplicated]")

            else:
                chain.add(individual)

                contents.append(f"{PREFIX}{history.message}")
                for origin in history.origin:
                    contents.append(textwrap.indent(_display(origin, chain), PREFIX * 2))

            return "\n".join(contents)

        return _display(individual, set())

    def __repr__(self) -> str:
        return f"<HistoryRecord message={self.message!r}>"
