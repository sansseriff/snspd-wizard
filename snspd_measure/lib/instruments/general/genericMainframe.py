from abc import ABC, abstractmethod
from typing import Any  # Changed Type to Any for generic type hint


class GenericMainframe(ABC):
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
