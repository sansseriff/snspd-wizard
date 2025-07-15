"""
genericSense.py
Author: SNSPD Library Rewrite
Date: June 4, 2025

Abstract base class for sensing instruments (multimeters, counters, oscilloscopes, etc.)
"""

from abc import ABC, abstractmethod
from typing import Union, Optional, List


class GenericSense(ABC):
    """
    Abstract base class for all sensing/measurement instruments.

    This class defines the common interface that all sensing instruments should implement.
    Sensing instruments include multimeters, counters, oscilloscopes, spectrum analyzers, etc.
    """

    def __init__(self, name: str = "Generic Sense"):
        self.name = name
        self.connected = False

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the instrument.

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the instrument.

        Returns:
            bool: True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    def measure(self, channel: Optional[int] = None) -> float:
        """
        Take a single measurement.

        Args:
            channel: Optional channel number for multi-channel instruments

        Returns:
            float: The measured value
        """
        pass

    @abstractmethod
    def configure_measurement(
        self, measurement_type: str, **kwargs: dict[str, Union[str, float, int]]
    ) -> bool:
        """
        Configure the measurement settings.

        Args:
            measurement_type: Type of measurement (e.g., 'DC voltage', 'frequency', 'count')
            **kwargs: Additional configuration parameters

        Returns:
            bool: True if configuration successful, False otherwise
        """
        pass

    def get_info(self) -> dict[str, Union[str, bool]]:
        """
        Get basic information about the instrument.

        Returns:
            dict: Dictionary containing instrument information
        """
        return {
            "name": self.name,
            "type": "Sense",
            "connected": self.connected,
            "class": self.__class__.__name__,
        }


class StandInGenericSense(GenericSense):
    """
    Stand-in class for GenericSense.
    This class is used when the actual instrument is not available.
    It provides default implementations for all methods.
    """

    ignore_in_cli = True

    def connect(self) -> bool:
        print("This is not a real instrument. Using stand-in GenericSense.")
        self.connected = True
        return True

    def disconnect(self) -> bool:
        print("This is not a real instrument. Using stand-in GenericSense.")
        self.connected = False
        return True

    def measure(self, channel: Optional[int] = None) -> float:
        print("This is not a real instrument. Using stand-in GenericSense.")
        return 0.0  # Default measurement value

    def configure_measurement(
        self, measurement_type: str, **kwargs: dict[str, Union[str, float, int]]
    ) -> bool:
        print("This is not a real instrument. Using stand-in GenericSense.")
        return True  # Default configuration success


class GenericCounter(GenericSense):
    """
    Abstract base class for counter instruments.

    Extends GenericSense with counter-specific functionality.
    """

    @abstractmethod
    def count(self, gate_time: float = 1.0, channel: Optional[int] = None) -> int:
        """
        Count events for a specified gate time.

        Args:
            gate_time: Gate time in seconds
            channel: Optional channel number for multi-channel instruments

        Returns:
            int: Number of counts
        """
        pass

    @abstractmethod
    def set_gate_time(self, gate_time: float, channel: Optional[int] = None) -> bool:
        """
        Set the gate time for counting.

        Args:
            gate_time: Gate time in seconds
            channel: Optional channel number for multi-channel instruments

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    def get_info(self) -> dict[str, Union[str, bool]]:
        """
        Get basic information about the counter instrument.

        Returns:
            dict: Dictionary containing instrument information
        """
        info = super().get_info()
        info["type"] = "Counter"
        return info


class StandInGenericCounter(GenericCounter):
    """
    Stand-in class for GenericCounter.
    This class is used when the actual counter instrument is not available.
    It provides default implementations for all methods.
    """

    ignore_in_cli = True

    def connect(self) -> bool:
        print("This is not a real counter. Using stand-in GenericCounter.")
        self.connected = True
        return True

    def disconnect(self) -> bool:
        print("This is not a real counter. Using stand-in GenericCounter.")
        self.connected = False
        return True

    def measure(self, channel: Optional[int] = None) -> float:
        print("This is not a real counter. Using stand-in GenericCounter.")
        return 0.0  # Default measurement value

    def count(self, gate_time: float = 1.0, channel: Optional[int] = None) -> int:
        print("This is not a real counter. Using stand-in GenericCounter.")
        return 0  # Default count value

    def set_gate_time(self, gate_time: float, channel: Optional[int] = None) -> bool:
        print("This is not a real counter. Using stand-in GenericCounter.")
        return True  # Default configuration success
