from __future__ import annotations

import textwrap
from collections import Counter
from typing import Final, Iterable, Set, Tuple, TYPE_CHECKING, final

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

    @staticmethod
    def display(individual: VRPDFDIndividual, *, hide_unchanged: bool = True) -> str:
        def _display(individual: VRPDFDIndividual, chain: Set[VRPDFDIndividual]) -> str:
            history = individual.history
            if hide_unchanged and history is not None:
                for origin in history.origin:
                    if frozenset(individual.truck_paths) != frozenset(origin.truck_paths):
                        continue

                    diff = False
                    for individual_paths, origin_paths in zip(individual.drone_paths, origin.drone_paths, strict=True):
                        individual_counter = Counter(individual_paths)
                        origin_counter = Counter(origin_paths)
                        if individual_counter != origin_counter:
                            diff = True
                            break

                    if diff:
                        continue

                    return _display(origin, chain)

            contents = [str(individual)]
            if history is None:
                contents.append(" [none]")

            elif individual in chain:
                contents.append(" [duplicated]")

            else:
                chain.add(individual)

                contents.append(f" {history.message}")
                for origin in history.origin:
                    contents.append(textwrap.indent(_display(origin, chain), "  "))

            return "\n".join(contents)

        return _display(individual, set())

    def __repr__(self) -> str:
        return f"<HistoryRecord message={self.message!r}>"
