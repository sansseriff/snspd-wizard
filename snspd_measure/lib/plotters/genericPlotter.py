from abc import ABC, abstractmethod


class GenericPlotter(ABC):
    """
    Abstract base class for all plotters.

    This class defines the unified interface that all plotter implementations must follow.
    All public methods are abstract and must be implemented by subclasses.
    """

    @abstractmethod
    def plot(self, data: dict) -> None:
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
