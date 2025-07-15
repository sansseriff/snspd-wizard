"""
keysight53220A.py
Author: SNSPD Library Rewrite
Date: June 4, 2025

Keysight 53220A Universal Counter class.
"""

import random
from typing import Optional, Any
from pydantic import BaseModel

from lib.instruments.general.visaInst import visaInst
from lib.instruments.general.genericSense import GenericCounter


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


class Keysight53220A(visaInst, GenericCounter):
    """Class for Keysight 53220A Universal Counter."""

    def __init__(
        self,
        ip_address: str,
        port: int = 5025,
        config: Optional[Keysight53220AConfig] = None,
        **kwargs: Any,
    ):
        """Initialize Keysight 53220A counter."""
        # Initialize parent classes
        visaInst.__init__(self, ip_address, port, kwargs.get("offline", False))
        GenericCounter.__init__(self, name=f"Keysight53220A@{ip_address}")

        # Store configuration
        self.config = config or Keysight53220AConfig()

        # Initialize instrument settings from config
        self._gate_time = self.config.default_gate_time
        self._threshold = self.config.threshold_absolute

        # Auto-connect if requested
        if kwargs.get("auto_connect", True):
            self.connect()
            self._apply_configuration()

    def _apply_configuration(self) -> bool:
        """Apply the configuration settings to the instrument."""
        if self.offline:
            return True

        success = True

        # Apply threshold settings
        if self.config.threshold_type == "absolute":
            success &= self.set_threshold(self.config.threshold_absolute)

        # Apply gate time
        success &= self.set_gate_time(self.config.default_gate_time)

        # Apply input settings
        if hasattr(self, "set_input_coupling"):
            success &= self.set_input_coupling(self.config.input_coupling)
        if hasattr(self, "set_input_impedance"):
            success &= self.set_input_impedance(self.config.input_impedance)

        return success

    def connect(self) -> bool:
        """Connect to the instrument and initialize settings."""
        success = super().connect()
        self.connected = success
        return success

    def disconnect(self) -> bool:
        """Disconnect from the instrument."""
        if hasattr(self, "inst") and self.inst is not None:
            try:
                self.inst.close()
                self.connected = False
                return True
            except Exception:
                pass
        self.connected = False
        return True

    def measure(self, channel: Optional[int] = None) -> float:
        """Take a single measurement."""
        return self.read_counts()

    def count(self, gate_time: float = 1.0, channel: Optional[int] = None) -> int:
        """Count events for a specified gate time."""
        # Set gate time if different
        if abs(gate_time - self._gate_time) > 0.001:
            self.set_gate_time(gate_time)

        # Read the count
        frequency = self.read_counts()
        return int(frequency * gate_time)

    def configure_measurement(self, measurement_type: str, **kwargs: Any) -> bool:
        """Configure the measurement settings."""
        if self.offline:
            return True
        return True

    def read_counts(self) -> float:
        """Read a single count/frequency measurement."""
        if self.offline:
            return float(random.randint(1000, 10000))

        # Read measurement
        values_str = self.query("READ?")
        if not values_str or values_str == "":
            return 0.0

        # Parse the response
        counts = float(str(values_str).split(",")[0])
        return counts

    def set_threshold(self, threshold: float) -> bool:
        """Set trigger threshold in mV."""
        if self.offline:
            self._threshold = threshold
            return True

        # Convert to volts
        threshold_v = threshold / 1000.0
        success = bool(self.write(f"INP:LEV {threshold_v}"))
        if success:
            self._threshold = threshold
        return success

    def set_gate_time(self, gate_time: float, channel: Optional[int] = None) -> bool:
        """Set the gate time for counting."""
        if self.offline:
            self._gate_time = gate_time
            return True

        success = bool(self.write(f"SENS:FREQ:GATE:TIME {gate_time}"))
        if success:
            self._gate_time = gate_time

        return success

    def reset(self) -> bool:
        """Reset the instrument to default settings."""
        if self.offline:
            return True

        return bool(self.write("*RST"))
