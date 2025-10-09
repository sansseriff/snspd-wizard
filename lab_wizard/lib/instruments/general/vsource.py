"""
genericSource.py
Author: SNSPD Library Rewrite
Date: June 4, 2025

Abstract base class for source instruments (voltage/current sources, signal generators, etc.)
"""

from abc import ABC, abstractmethod


class VSource(ABC):
    """
    Abstract base class for all source instruments.

    This class defines the common interface that all source instruments should implement.
    Source instruments include voltage sources, current sources, signal generators, etc.
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
    def set_voltage(self, voltage: float) -> bool:
        """
        Set the output voltage of the source.

        Args:
            voltage: The output voltage to set

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def turn_on(self) -> bool:
        """
        Turn on the output of the source.

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def turn_off(self) -> bool:
        """
        Turn off the output of the source.

        Returns:
            bool: True if successful, False otherwise
        """
        pass


class StandInVSource(VSource):
    """
    Stand-in class for VSource.
    This class can be used for testing or as a placeholder when no actual instrument is available.
    """

    ignore_in_cli = True

    def __init__(self):
        self.connected = True  # Stand-in is always "connected"
        self.voltage = 0.0
        self.output_enabled = False
        print("Stand-in voltage source initialized.")

    def disconnect(self) -> bool:
        print("This is not a real source. Using stand-in VSource.")
        self.connected = False
        return not self.connected

    def set_voltage(self, voltage: float) -> bool:
        """Set the voltage (stand-in behavior)."""
        print(f"Stand-in: Setting voltage to {voltage}V")
        self.voltage = voltage
        return True

    def turn_on(self) -> bool:
        """Turn on the output (stand-in behavior)."""
        print(f"Stand-in: Turning on output")
        self.output_enabled = True
        return True

    def turn_off(self) -> bool:
        """Turn off the output (stand-in behavior)."""
        print(f"Stand-in: Turning off output")
        self.output_enabled = False
        return True
        print(f"Stand-in: Turning on output{channel_str}")
        self.output_enabled = True
        return True

    def turn_off(self, channel: int | None = None) -> bool:
        """Turn off the output (stand-in behavior)."""
        channel_str = f" on channel {channel}" if channel is not None else ""
        print(f"Stand-in: Turning off output{channel_str}")
        self.output_enabled = False
        return True
