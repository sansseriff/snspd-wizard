"""
genericSense.py
Author: SNSPD Library Rewrite
Date: June 4, 2025

Abstract base class for sensing instruments (multimeters, counters, oscilloscopes, etc.)
"""

from abc import ABC, abstractmethod


class VSense(ABC):
    """
    Abstract base class for all sensing/measurement instruments.

    This class defines the common interface that all sensing instruments should implement.
    Sensing instruments include multimeters, counters, oscilloscopes, spectrum analyzers, etc.
    """

    def __init__(self):
        self.connected = False

        """
        NOTE: There is no 'connect' method here. Connection should happen in the constructor, thereby 
        following the RAII principle (Resource Acquisition Is Initialization).
        """

    def __del__(self):
        """
        Destructor that ensures proper cleanup.
        Calls disconnect() to handle instrument-specific disconnection.
        """
        if hasattr(self, "connected") and self.connected:
            self.disconnect()

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the instrument.

        Returns:
            bool: True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    def get_voltage(self, channel: int | None = None) -> float:
        """
        Get the voltage measurement from the instrument.

        Args:
            channel: Optional channel number for multi-channel instruments

        Returns:
            float: Measured voltage
        """
        pass


class StandInVSense(VSense):
    """
    Stand-in class for VSense.
    This class can be used for testing or as a placeholder when no actual instrument is available.
    """

    ignore_in_cli = True

    def __init__(self):
        self.connected = True  # Stand-in is always "connected"
        self.measurement_value = 0.0
        self.measurement_type = "voltage"
        print("Stand-in sensing instrument initialized.")

    def disconnect(self) -> bool:
        print("This is not a real instrument. Using stand-in GenericSense.")
        self.connected = False
        return not self.connected

    def get_voltage(self, channel: int | None = None) -> float:
        print("This is not a real instrument. Using stand-in GenericSense.")
        return self.measurement_value
