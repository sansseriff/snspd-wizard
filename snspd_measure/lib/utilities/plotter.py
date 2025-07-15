"""
plotter.py
Author: SNSPD Library Rewrite
Date: June 4, 2025

Real-time plotting utility for measurements.
Based on the original plotter functionality but simplified and modernized.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import List, Optional, Tuple
import threading
import time


class Plotter:
    """
    Real-time plotting utility for measurement data.

    Provides functionality for live updating plots during measurements.
    """

    def __init__(self, figsize: Tuple[float, float] = (8, 6)):
        """
        Initialize the plotter.

        Args:
            figsize: Figure size as (width, height) in inches
        """
        self.figsize = figsize
        self.fig = None
        self.ax = None
        self.line = None

        # Data storage
        self.x_data: List[float] = []
        self.y_data: List[float] = []

        # Plot properties
        self.title = ""
        self.xlabel = ""
        self.ylabel = ""

        # Threading for non-blocking updates
        self._update_thread = None
        self._stop_updating = False

    def setup_plot(
        self,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        interactive: bool = True,
    ) -> None:
        """
        Set up the plot with labels and styling.

        Args:
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            interactive: Enable interactive mode for real-time updates
        """
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel

        # Enable interactive mode for real-time updates
        if interactive:
            plt.ion()

        # Create figure and axis
        self.fig, self.ax = plt.subplots(figsize=self.figsize)

        # Set labels
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)

        # Create empty line for data
        (self.line,) = self.ax.plot([], [], "b-o", markersize=3, linewidth=1)

        # Grid and styling
        self.ax.grid(True, alpha=0.3)
        self.ax.set_axisbelow(True)

        # Show the plot
        plt.show(block=False)
        plt.pause(0.001)

    def add_point(self, x: float, y: float, update_now: bool = True) -> None:
        """
        Add a new data point to the plot.

        Args:
            x: X coordinate
            y: Y coordinate
            update_now: Whether to update the plot immediately
        """
        self.x_data.append(x)
        self.y_data.append(y)

        if update_now and self.line is not None:
            self.update_plot()

    def add_points(
        self, x_points: List[float], y_points: List[float], update_now: bool = True
    ) -> None:
        """
        Add multiple data points to the plot.

        Args:
            x_points: List of X coordinates
            y_points: List of Y coordinates
            update_now: Whether to update the plot immediately
        """
        self.x_data.extend(x_points)
        self.y_data.extend(y_points)

        if update_now and self.line is not None:
            self.update_plot()

    def update_plot(self) -> None:
        """
        Update the plot with current data.
        """
        if self.line is None or len(self.x_data) == 0:
            return

        try:
            # Update line data
            self.line.set_data(self.x_data, self.y_data)

            # Auto-scale axes
            self.ax.relim()
            self.ax.autoscale_view()

            # Refresh the plot
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            plt.pause(0.001)

        except Exception as e:
            print(f"Error updating plot: {e}")

    def clear_data(self) -> None:
        """
        Clear all data from the plot.
        """
        self.x_data.clear()
        self.y_data.clear()

        if self.line is not None:
            self.line.set_data([], [])
            self.update_plot()

    def save_plot(self, filename: str, dpi: int = 300) -> bool:
        """
        Save the current plot to a file.

        Args:
            filename: Output filename
            dpi: Resolution in dots per inch

        Returns:
            bool: True if save successful
        """
        if self.fig is None:
            print("No plot to save")
            return False

        try:
            self.fig.savefig(filename, dpi=dpi, bbox_inches="tight")
            print(f"Plot saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving plot: {e}")
            return False

    def show(self, block: bool = True) -> None:
        """
        Show the plot.

        Args:
            block: Whether to block execution until plot is closed
        """
        if self.fig is not None:
            plt.show(block=block)

    def close(self) -> None:
        """
        Close the plot and clean up resources.
        """
        self._stop_updating = True

        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.ax = None
            self.line = None

    def set_axis_limits(
        self,
        xlim: Optional[Tuple[float, float]] = None,
        ylim: Optional[Tuple[float, float]] = None,
    ) -> None:
        """
        Set axis limits manually.

        Args:
            xlim: X-axis limits as (min, max)
            ylim: Y-axis limits as (min, max)
        """
        if self.ax is None:
            return

        if xlim is not None:
            self.ax.set_xlim(xlim)

        if ylim is not None:
            self.ax.set_ylim(ylim)

        self.update_plot()

    def set_log_scale(self, x_log: bool = False, y_log: bool = False) -> None:
        """
        Set logarithmic scaling for axes.

        Args:
            x_log: Use log scale for X-axis
            y_log: Use log scale for Y-axis
        """
        if self.ax is None:
            return

        if x_log:
            self.ax.set_xscale("log")
        else:
            self.ax.set_xscale("linear")

        if y_log:
            self.ax.set_yscale("log")
        else:
            self.ax.set_yscale("linear")

        self.update_plot()

    def get_data(self) -> Tuple[List[float], List[float]]:
        """
        Get the current plot data.

        Returns:
            Tuple[List[float], List[float]]: (x_data, y_data)
        """
        return self.x_data.copy(), self.y_data.copy()

    def start_auto_update(self, interval: float = 0.1) -> None:
        """
        Start automatic plot updating in a separate thread.

        Args:
            interval: Update interval in seconds
        """
        if self._update_thread is not None:
            return

        self._stop_updating = False

        def update_loop():
            while not self._stop_updating:
                self.update_plot()
                time.sleep(interval)

        self._update_thread = threading.Thread(target=update_loop, daemon=True)
        self._update_thread.start()

    def stop_auto_update(self) -> None:
        """
        Stop automatic plot updating.
        """
        self._stop_updating = True
        if self._update_thread is not None:
            self._update_thread.join(timeout=1.0)
            self._update_thread = None


class MultiPlotter:
    """
    Manager for multiple real-time plots.
    """

    def __init__(self):
        """
        Initialize the multi-plotter.
        """
        self.plotters: dict[str, Plotter] = {}

    def add_plotter(self, name: str, plotter: Plotter) -> None:
        """
        Add a named plotter.

        Args:
            name: Unique name for the plotter
            plotter: Plotter instance
        """
        self.plotters[name] = plotter

    def create_plotter(
        self,
        name: str,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        figsize: Tuple[float, float] = (8, 6),
    ) -> Plotter:
        """
        Create and add a new plotter.

        Args:
            name: Unique name for the plotter
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size

        Returns:
            Plotter: The created plotter instance
        """
        plotter = Plotter(figsize=figsize)
        plotter.setup_plot(title=title, xlabel=xlabel, ylabel=ylabel)
        self.plotters[name] = plotter
        return plotter

    def get_plotter(self, name: str) -> Optional[Plotter]:
        """
        Get a plotter by name.

        Args:
            name: Name of the plotter

        Returns:
            Optional[Plotter]: The plotter instance or None if not found
        """
        return self.plotters.get(name)

    def update_all(self) -> None:
        """
        Update all plotters.
        """
        for plotter in self.plotters.values():
            plotter.update_plot()

    def close_all(self) -> None:
        """
        Close all plotters.
        """
        for plotter in self.plotters.values():
            plotter.close()
        self.plotters.clear()

    def save_all(self, directory: str = ".", prefix: str = "plot") -> None:
        """
        Save all plots to files.

        Args:
            directory: Directory to save plots
            prefix: Filename prefix
        """
        for name, plotter in self.plotters.items():
            filename = f"{directory}/{prefix}_{name}.png"
            plotter.save_plot(filename)
