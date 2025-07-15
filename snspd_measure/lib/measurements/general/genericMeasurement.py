from abc import ABC, abstractmethod


class GenericMeasurement(ABC):
    @abstractmethod
    def run_measurement(self):
        """
        Run the measurement process.

        This method should be implemented by subclasses to define the specific measurement logic.
        """
        pass
