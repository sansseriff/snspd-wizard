from typing import Any
from abc import ABC, abstractmethod


class GenericSaver(ABC):
    """
    Abstract base class for all savers.

    This class defines the unified interface that all savers must follow.

    All public methods are abstract and must be implemented by subclasses.
    """

    @abstractmethod
    def save(self, data: dict[str, Any]) -> None:
        """
        Save the provided data.

        Args:
            data: Dictionary containing the data to be saved
        """
        pass
