"""
keysight53220A.py
Author: SNSPD Library Rewrite
Date: June 4, 2025

Keysight 53220A Universal Counter class.
"""

import random
from typing import Any
from pydantic import BaseModel

from snspd_measure.lib.instruments.general.visa_inst import VisaInst
from snspd_measure.lib.instruments.general.counter import Counter


class Keysight53220AConfig(BaseModel):
    """Configuration parameters specific to Keysight 53220A counter."""

    # Threshold configuration
    threshold_type: str = "absolute"  # "absolute", "auto", or "sweep"
    threshold_absolute: float = -50.0  # mV when threshold_type is "absolute"
    threshold_relative: float = 0.5  # fraction when threshold_type is "auto"
    threshold_start: float = -100.0  # mV when threshold_type is "sweep"
    threshold_end: float = -10.0  # mV when threshold_type is "sweep"
    threshold_steps: int = 5  # number of steps when threshold_type is "sweep"

    # Gate time settings
    default_gate_time: float = 1.0  # seconds

    # Trigger settings
    ext_trigger: bool = False
    trigger_slope: str = "positive"  # "positive" or "negative"

    # Input settings
    input_coupling: str = "DC"  # "DC" or "AC"
    input_impedance: str = "50"  # "50" or "1M"


class Keysight53220A(Counter):
    """Class for Keysight 53220A Universal Counter."""

    def __init__(
        self,
        ip_address: str,
        port: int = 5025,
        config: Keysight53220AConfig | None = None,
        **kwargs: Any,
    ):
        """Initialize Keysight 53220A counter."""
        # Create communication object (composition instead of inheritance)
        self.comm = VisaInst(ip_address, port, kwargs.get("offline", False))

        # Store configuration
        self.config = config or Keysight53220AConfig()

        # Initialize instrument settings from config
        self._gate_time = self.config.default_gate_time
        self._threshold = self.config.threshold_absolute

        # Set connected status based on communication object
        self.connected = not self.comm.offline

        # Apply configuration if connected (RAII principle)
        if self.connected:
            self._apply_configuration()

    def _apply_configuration(self) -> bool:
        """Apply the configuration settings to the instrument."""
        if self.comm.offline:
            return True

        success = True

        # Apply threshold settings
        if self.config.threshold_type == "absolute":
            success &= self.set_threshold(self.config.threshold_absolute)

        # Apply gate time
        success &= self.set_gate_time(self.config.default_gate_time)

        # Note: Input coupling and impedance methods would need to be implemented
        # if needed for this specific instrument

        return success

    def disconnect(self) -> bool:
        """Disconnect from the instrument."""
        success = self.comm.disconnect()
        self.connected = False
        return success

    def measure(self, channel: int | None = None) -> float:
        """Take a single measurement."""
        return self.read_counts()

    def count(self, gate_time: float = 1.0, channel: int | None = None) -> int:
        """Count events for a specified gate time."""
        # Set gate time if different
        if abs(gate_time - self._gate_time) > 0.001:
            self.set_gate_time(gate_time)

        # Read the count
        frequency = self.read_counts()
        return int(frequency * gate_time)

    def configure_measurement(self, measurement_type: str, **kwargs: Any) -> bool:
        """Configure the measurement settings."""
        if self.comm.offline:
            return True
        return True

    def read_counts(self) -> float:
        """Read a single count/frequency measurement."""
        if self.comm.offline:
            return float(random.randint(1000, 10000))

        # Read measurement
        values_str = self.comm.query("READ?")
        if not values_str or values_str == "":
            return 0.0

        # Parse the response
        counts = float(str(values_str).split(",")[0])
        return counts

    def set_threshold(self, threshold: float) -> bool:
        """Set trigger threshold in mV."""
        if self.comm.offline:
            self._threshold = threshold
            return True

        # Convert to volts
        threshold_v = threshold / 1000.0
        success = bool(self.comm.write(f"INP:LEV {threshold_v}"))
        if success:
            self._threshold = threshold
        return success

    def set_gate_time(self, gate_time: float, channel: int | None = None) -> bool:
        """Set the gate time for counting."""
        if self.comm.offline:
            self._gate_time = gate_time
            return True

        success = bool(self.comm.write(f"SENS:FREQ:GATE:TIME {gate_time}"))
        if success:
            self._gate_time = gate_time

        return success

    def reset(self) -> bool:
        """Reset the instrument to default settings."""
        if self.comm.offline:
            return True

        return bool(self.comm.write("*RST"))
