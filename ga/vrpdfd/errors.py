from ..errors import GeneticAlgorithmException

from typing import TYPE_CHECKING


__all__ = (
    "VRPDFDException",
    "ConfigDataNotFound",
    "ConfigImportTwice",
    "ConfigImportException",
)


class VRPDFDException(GeneticAlgorithmException):
    """Base class for all exceptions when solving the VRPDFD problem"""
    pass


class ConfigDataNotFound(VRPDFDException):

    def __init__(self) -> None:
        super().__init__("No problem configuration data was imported")


class ConfigImportTwice(VRPDFDException):

    def __init__(self, current: str, new: str) -> None:
        super().__init__(f"Attempted to import problem configuration data twice, current problem {current!r}, attempted to import {new!r}")


class ConfigImportException(VRPDFDException):

    __slots__ = ("original",)
    if TYPE_CHECKING:
        original: BaseException

    def __init__(self, original: BaseException, /) -> None:
        self.original = original
        super().__init__(f"Failed to import problem configuration data: {original}")
