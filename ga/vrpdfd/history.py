from __future__ import annotations

import textwrap
from typing import Final, List, Literal, Optional, Set, Tuple, TYPE_CHECKING, final

if TYPE_CHECKING:
    from .individuals import VRPDFDIndividual


__all__ = ("HistoryRecord",)
HistoryType = Literal["crossover", "mutation", "local_search", "initial", "educate"]


@final
class HistoryRecord:

    __slots__ = (
        "message",
        "origin",
    )
    if TYPE_CHECKING:
        message: Final[HistoryType]
        origin: Final[Tuple[VRPDFDIndividual, ...]]

    def __init__(self, message: HistoryType, origin: Tuple[VRPDFDIndividual, ...]) -> None:
        # When calling this method from C++, origin may be a list instead
        self.message = message
        self.origin = origin

    def display(self, chain: Optional[Set[VRPDFDIndividual]] = None) -> str:
        if chain is None:
            chain = set()

        contents: List[str] = [self.message]
        for individual in self.origin:
            if individual in chain:
                contents.append(" [duplicated]")
            else:
                chain.add(individual)
                contents.append(f" {individual}")

                if individual.history is None:
                    contents.append("  [None]")
                else:
                    contents.append(textwrap.indent(individual.history.display(), "  "))

        return "\n".join(contents)
