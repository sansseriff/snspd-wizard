from __future__ import annotations

"""
plotter.py
Author: SNSPD Library Rewrite
Date: June 4, 2025

Abstract base class for plotters and a stand-in implementation.
"""

from typing import Any
from abc import ABC, abstractmethod


class GenericPlotter(ABC):
    """
    Abstract base class for all plotters.

    This class defines the unified interface that all plotter implementations must follow.
    All public methods are abstract and must be implemented by subclasses.
    """

    @abstractmethod
    def plot(self, data: dict[str, Any]) -> None:
        """
        Plot the provided data.

        Args:
            data: Dictionary containing the data to be plotted
        """
        pass

    @abstractmethod
    def save_plot(self, filename: str) -> None:
        """
        Save the current plot to a file.

        Args:
            filename: Name of the file to save the plot
        """
        pass


class StandInPlotter(GenericPlotter):
    """A no-op plotter that logs actions and stores the last payload in memory."""

    # Hide from CLI auto-discovery/selection menus
    ignore_in_cli = True

    def __init__(self) -> None:
        self.plotted_count: int = 0
        self.last_data: dict[str, Any] | None = None
        self.last_saved_filename: str | None = None
        print("Stand-in plotter initialized.")

    def plot(self, data: dict[str, Any]) -> None:
        """Pretend to plot the provided data; store it locally and print a message."""
        keys = list(data.keys())
        print(f"Stand-in: Plotting data (no-op). Keys: {keys}")
        self.last_data = data
        self.plotted_count += 1

    def save_plot(self, filename: str) -> None:
        """Pretend to save a plot; record the filename and print a message."""
        print(f"Stand-in: Saving plot to '{filename}' (no-op)")
        self.last_saved_filename = filename
