from ..errors import GeneticAlgorithmException

from typing import TYPE_CHECKING


__all__ = (
    "VRPDFDException",
    "ConfigImportException",
    "PopulationInitializationException",
    "InfeasibleSolution",
)


class VRPDFDException(GeneticAlgorithmException):
    """Base class for all exceptions when solving the VRPDFD problem"""
    pass


class ConfigImportException(VRPDFDException):

    __slots__ = ("original",)
    if TYPE_CHECKING:
        original: BaseException

    def __init__(self, original: BaseException, /) -> None:
        self.original = original
        super().__init__(f"Failed to import problem configuration data: {original}")


class PopulationInitializationException(VRPDFDException):

    __slots__ = ("original",)
    if TYPE_CHECKING:
        original: BaseException

    def __init__(self, original: BaseException, /) -> None:
        self.original = original
        super().__init__(str(original))


class InfeasibleSolution(VRPDFDException):
    pass
