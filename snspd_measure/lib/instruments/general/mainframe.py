from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic
from pydantic import BaseModel


class MainframeParams(BaseModel):
    pass


M = TypeVar("M", bound=MainframeParams)


class Mainframe(ABC, Generic[M]):
    @abstractmethod
    def create_submodule(self, params: Any) -> Any:  # Changed dataclass to Any
        """
        Create a submodule with the given parameters.

        Args:
            params: Parameters for the submodule, typically a dataclass instance

        Returns:
            The created submodule instance
        """
        pass

    @classmethod
    @abstractmethod
    def from_params(cls, params: M) -> "Mainframe[M]":
        pass
