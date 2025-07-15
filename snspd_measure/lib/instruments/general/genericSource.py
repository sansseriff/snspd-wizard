"""
genericSource.py
Author: SNSPD Library Rewrite
Date: June 4, 2025

Abstract base class for source instruments (voltage/current sources, signal generators, etc.)
"""

from abc import ABC, abstractmethod
from typing import Union, Optional


class GenericSource(ABC):
    """
    Abstract base class for all source instruments.

    This class defines the common interface that all source instruments should implement.
    Source instruments include voltage sources, current sources, signal generators, etc.
    """

    def __init__(self, name: str = "Generic Source"):
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
    def set_output(self, value: float, channel: Optional[int] = None) -> bool:
        """
        Set the output value of the source.

        Args:
            value: The output value to set
            channel: Optional channel number for multi-channel instruments

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_output(self, channel: Optional[int] = None) -> float:
        """
        Get the current output value of the source.

        Args:
            channel: Optional channel number for multi-channel instruments

        Returns:
            float: The current output value
        """
        pass

    @abstractmethod
    def enable_output(
        self, enabled: bool = True, channel: Optional[int] = None
    ) -> bool:
        """
        Enable or disable the output.

        Args:
            enabled: True to enable output, False to disable
            channel: Optional channel number for multi-channel instruments

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def is_output_enabled(self, channel: Optional[int] = None) -> bool:
        """
        Check if the output is enabled.

        Args:
            channel: Optional channel number for multi-channel instruments

        Returns:
            bool: True if output is enabled, False otherwise
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
            "type": "Source",
            "connected": self.connected,
            "class": self.__class__.__name__,
        }

    @abstractmethod
    def turn_off(self) -> bool:
        """
        Turn off the output of the source.

        Returns:
            bool: True if successful, False otherwise
        """
        return self.set_output(0.0)


class StandInGenericSource(GenericSource):
    """
    Stand-in class for GenericSource.
    This class can be used for testing or as a placeholder when no actual instrument is available.
    """

    ignore_in_cli = True

    def connect(self) -> bool:
        print("This is not a real source. Using stand-in GenericSource.")
        self.connected = True
        return self.connected

    def disconnect(self) -> bool:
        print("This is not a real source. Using stand-in GenericSource.")
        self.connected = False
        return not self.connected

    def set_output(self, value: float, channel: Optional[int] = None) -> bool:
        print("This is not a real source. Using stand-in GenericSource.")
        return True

    def get_output(self, channel: Optional[int] = None) -> float:
        print("This is not a real source. Using stand-in GenericSource.")
        return 0.0

    def enable_output(
        self, enabled: bool = True, channel: Optional[int] = None
    ) -> bool:
        print("This is not a real source. Using stand-in GenericSource.")
        return True

    def is_output_enabled(self, channel: Optional[int] = None) -> bool:
        print("This is not a real source. Using stand-in GenericSource.")
        return True

    def turn_off(self) -> bool:
        print("This is not a real source. Using stand-in GenericSource.")
        return True
