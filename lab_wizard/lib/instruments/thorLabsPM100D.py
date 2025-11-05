"""
ThorLabs PM100D Power Meter

Modern implementation of ThorLabs PM100D power meter interface
with GenericSense interface compliance.
"""

import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from numpy import log10

try:
    from ThorlabsPM100 import ThorlabsPM100, USBTMC

    THORLABS_AVAILABLE = True
except ImportError:
    THORLABS_AVAILABLE = False
    print(
        "Warning: ThorlabsPM100 library not available. Install with: pip install ThorlabsPM100"
    )

from lab_wizard.lib.instruments.general.vsense import GenericSense


# Instrument Configuration Dataclass
@dataclass
class ThorLabsPM100DConfig:
    """Configuration for ThorLabs PM100D power meter."""

    device_path: str  # e.g., "USB0::0x1313::0x8078::P0011656::INSTR"
    timeout: float = 5.0
    wavelength: float = 1550.0  # Wavelength in nm
    auto_range: bool = True
    averaging_count: int = 1


class ThorLabsPM100D(GenericSense):
    """
    ThorLabs PM100D Power Meter

    Implements optical power measurements with both linear (W) and logarithmic (dBm) scales.
    Supports averaging and various measurement configurations.
    """

    def __init__(self, device_path: str, **kwargs):
        """
        Initialize ThorLabs PM100D power meter

        Args:
            device_path: Device path (e.g., '/dev/usbtmc0')
            **kwargs: Additional configuration parameters
        """
        super().__init__()

        if not THORLABS_AVAILABLE:
            raise ImportError(
                "ThorlabsPM100 library required. Install with: pip install ThorlabsPM100"
            )

        self.device_path = device_path
        self.inst = None
        self.pm = None
        self._connected = False

        # Configuration
        self.averaging_count = kwargs.get("averaging_count", 1)
        self.wavelength = kwargs.get("wavelength", 1550)  # nm

    def connect(self) -> bool:
        """Connect to the power meter"""
        try:
            self.inst = USBTMC(device=self.device_path)
            self.pm = ThorlabsPM100(inst=self.inst)

            # Configure default settings
            self.set_averaging(self.averaging_count)
            if hasattr(self.pm.sense.correction, "wavelength"):
                self.pm.sense.correction.wavelength = self.wavelength

            self._connected = True
            print(f"Connected to ThorLabs PM100D at {self.device_path}")
            return True

        except Exception as e:
            print(f"Failed to connect to ThorLabs PM100D: {e}")
            self._connected = False
            return False

    def disconnect(self) -> bool:
        """Disconnect from the power meter"""
        try:
            if self.inst:
                # ThorlabsPM100 doesn't have explicit disconnect
                self.inst = None
                self.pm = None
            self._connected = False
            print("Disconnected from ThorLabs PM100D")
            return True

        except Exception as e:
            print(f"Error disconnecting from ThorLabs PM100D: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if instrument is connected"""
        return self._connected and self.pm is not None

    def get_value(self) -> float:
        """
        Get power measurement in Watts

        Returns:
            Power in Watts
        """
        if not self.is_connected():
            raise RuntimeError("Power meter not connected")

        try:
            return float(self.pm.read)
        except Exception as e:
            raise RuntimeError(f"Failed to read power: {e}")

    def get_power_watts(self) -> float:
        """
        Get power measurement in Watts

        Returns:
            Power in Watts
        """
        return self.get_value()

    def get_power_dbm(self) -> float:
        """
        Get power measurement in dBm

        Returns:
            Power in dBm
        """
        power_watts = self.get_power_watts()
        if power_watts <= 0:
            raise ValueError("Cannot convert negative or zero power to dBm")

        power_dbm = 10 * log10(power_watts) + 30
        return power_dbm

    def set_averaging(self, count: int):
        """
        Set averaging count for measurements

        Args:
            count: Number of measurements to average
        """
        if not self.is_connected():
            raise RuntimeError("Power meter not connected")

        try:
            self.pm.sense.average.count = count
            self.averaging_count = count
            print(f"Set averaging count to {count}")
        except Exception as e:
            raise RuntimeError(f"Failed to set averaging: {e}")

    def set_wavelength(self, wavelength_nm: float):
        """
        Set the wavelength for power correction

        Args:
            wavelength_nm: Wavelength in nanometers
        """
        if not self.is_connected():
            raise RuntimeError("Power meter not connected")

        try:
            if hasattr(self.pm.sense.correction, "wavelength"):
                self.pm.sense.correction.wavelength = wavelength_nm
                self.wavelength = wavelength_nm
                print(f"Set wavelength to {wavelength_nm} nm")
            else:
                print("Warning: Wavelength correction not supported")
        except Exception as e:
            raise RuntimeError(f"Failed to set wavelength: {e}")

    def get_range(self) -> tuple:
        """
        Get the current measurement range

        Returns:
            Tuple of (min_power, max_power) in Watts
        """
        if not self.is_connected():
            raise RuntimeError("Power meter not connected")

        try:
            # Get current range if available
            if hasattr(self.pm.sense.power, "range"):
                current_range = self.pm.sense.power.range.upper
                return (0, current_range)
            else:
                # Return typical range for PM100D
                return (1e-12, 200e-3)  # 1 pW to 200 mW
        except Exception as e:
            print(f"Could not get range: {e}")
            return (1e-12, 200e-3)

    def set_range(self, max_power: float):
        """
        Set the measurement range

        Args:
            max_power: Maximum expected power in Watts
        """
        if not self.is_connected():
            raise RuntimeError("Power meter not connected")

        try:
            if hasattr(self.pm.sense.power.range, "upper"):
                self.pm.sense.power.range.upper = max_power
                print(f"Set power range to {max_power} W")
            else:
                print("Warning: Manual range setting not supported")
        except Exception as e:
            print(f"Warning: Could not set range: {e}")

    def auto_range(self):
        """Enable automatic range selection"""
        if not self.is_connected():
            raise RuntimeError("Power meter not connected")

        try:
            if hasattr(self.pm.sense.power.range, "auto"):
                self.pm.sense.power.range.auto = True
                print("Enabled auto-ranging")
            else:
                print("Warning: Auto-ranging not supported")
        except Exception as e:
            print(f"Warning: Could not enable auto-ranging: {e}")

    def get_info(self) -> Dict[str, Any]:
        """Get instrument information"""
        info = {
            "instrument_type": "ThorLabs PM100D Power Meter",
            "device_path": self.device_path,
            "connected": self.is_connected(),
            "averaging_count": self.averaging_count,
            "wavelength_nm": self.wavelength,
        }

        if self.is_connected():
            try:
                range_info = self.get_range()
                info["power_range_watts"] = range_info
                info["power_range_dbm"] = (
                    10 * log10(range_info[0]) + 30,
                    10 * log10(range_info[1]) + 30,
                )
            except Exception:
                pass

        return info

    def reset(self):
        """Reset the power meter to default settings"""
        if not self.is_connected():
            raise RuntimeError("Power meter not connected")

        try:
            if hasattr(self.pm, "system"):
                self.pm.system.preset()

            # Restore our default settings
            self.set_averaging(1)
            self.set_wavelength(1550)
            self.auto_range()

            print("Power meter reset to default settings")

        except Exception as e:
            print(f"Warning: Reset may not be complete: {e}")

    def __str__(self) -> str:
        """String representation"""
        status = "connected" if self.is_connected() else "disconnected"
        return f"ThorLabs PM100D Power Meter ({self.device_path}) - {status}"


def main():
    """Example usage"""
    # Example device path - adjust according to your system
    device_path = "/dev/usbtmc0"

    print("ThorLabs PM100D Power Meter Example")
    print("Note: Adjust device path and ensure proper permissions")
    print(f"Example device path: {device_path}")

    if THORLABS_AVAILABLE:
        print("ThorlabsPM100 library is available")
    else:
        print(
            "ThorlabsPM100 library not available - install with: pip install ThorlabsPM100"
        )


if __name__ == "__main__":
    main()
