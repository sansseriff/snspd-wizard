from __future__ import annotations

"""
saver.py
Author: SNSPD Library Rewrite
Date: June 4, 2025

Abstract base class for savers and a stand-in implementation.
"""

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


class StandInSaver(GenericSaver):
    """A no-op saver that logs actions and stores the last payload in memory."""

    # Hide from CLI auto-discovery/selection menus
    ignore_in_cli = True

    def __init__(self) -> None:
        self.saved_count: int = 0
        self.last_saved: dict[str, Any] | None = None
        print("Stand-in saver initialized.")

    def save(self, data: dict[str, Any]) -> None:
        """Pretend to save the provided data; store it locally and print a message."""
        keys = list(data.keys())
        print(f"Stand-in: Saving data (no-op). Keys: {keys}")
        self.last_saved = data
        self.saved_count += 1
