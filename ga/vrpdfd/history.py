from __future__ import annotations

import textwrap
from typing import Final, Iterable, Optional, Set, Tuple, TYPE_CHECKING, final

if TYPE_CHECKING:
    from .individuals import VRPDFDIndividual


__all__ = ("HistoryRecord",)


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

    def display(self, chain: Optional[Set[VRPDFDIndividual]] = None) -> str:
        if chain is None:
            chain = set()

        contents = [self.message]
        for individual in self.origin:
            contents.append(f" {individual}")
            if individual in chain:
                contents.append(" [duplicated]")
            else:
                chain.add(individual)

                if individual.history is None:
                    contents.append("  [None]")
                else:
                    contents.append(textwrap.indent(individual.history.display(chain), "  "))

        return "\n".join(contents)

    def __repr__(self) -> str:
        return f"<HistoryRecord message={self.message!r}>"
