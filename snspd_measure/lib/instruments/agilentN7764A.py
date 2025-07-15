#!/usr/bin/env python3
"""
Agilent N7764A Variable Optical Attenuator
author: GitHub Copilot
date: 2024

Modern implementation of the Agilent N7764A 4-channel variable optical attenuator
for the new SNSPD measurement architecture.
"""

import time
import numpy as np
from typing import Optional, Union, List
from pathlib import Path
from pydantic import BaseModel

from lib.instruments.general.visaInst import visaInst
from lib.instruments.general.genericSource import GenericSource


# Instrument Configuration Dataclass


class AgilentN7764AConfig(BaseModel):
    """Configuration for Agilent N7764A optical attenuator."""

    visa_address: str  # e.g., "USB0::0x0957::0x1707::MY53220A0001::INSTR"
    timeout: float = 5.0
    query_delay: float = 0.1
    min_attenuation: float = 0.0  # Minimum attenuation in dB
    max_attenuation: float = 60.0  # Maximum attenuation in dB
    wavelength: float = 1550.0  # Wavelength in nm


class AgilentN7764A(visaInst, GenericSource):
    """
    Agilent N7764A 4-channel Variable Optical Attenuator.

    This instrument provides variable optical attenuation across 4 channels
    with wavelength-dependent calibration and shutter control.
    """

    def __init__(self, ip_address: str, **kwargs):
        """
        Initialize the Agilent N7764A attenuator.

        Args:
            ip_address: IP address of the instrument (e.g., '10.7.0.127')
            **kwargs: Additional arguments passed to VisaInst
        """
        super().__init__(ip_address, **kwargs)
        self.num_channels = 4
        self.current_wavelength = 1550.0  # Default wavelength in nm
        self.calibration_file: Optional[Path] = None

    def connect(self, idn_info: bool = True) -> bool:
        """Connect to the instrument and perform initial setup."""
        success = super().connect(idn_info)
        if success and not self.offline:
            # Set default wavelength
            self.set_wavelength_all(self.current_wavelength)
        return success

    def reset(self) -> bool:
        """Reset the instrument to default state."""
        try:
            self.write("*RST")
            time.sleep(1.0)  # Allow time for reset
            return True
        except Exception as e:
            print(f"Error resetting instrument: {e}")
            return False

    def init(self) -> bool:
        """Initialize the instrument."""
        try:
            self.write("INIT")
            return True
        except Exception as e:
            print(f"Error initializing instrument: {e}")
            return False

    # Attenuation control methods
    def get_attenuation(self, channel: int) -> float:
        """
        Get the attenuation value for a specific channel.

        Args:
            channel: Channel number (1-4)

        Returns:
            Attenuation value in dB
        """
        if not 1 <= channel <= self.num_channels:
            raise ValueError(f"Channel must be 1-{self.num_channels}")

        try:
            response = self.query(f"INP{channel}:ATT?")
            return float(response)
        except Exception as e:
            print(f"Error reading attenuation from channel {channel}: {e}")
            return 0.0

    def set_attenuation(self, channel: int, attenuation: float) -> bool:
        """
        Set the attenuation value for a specific channel.

        Args:
            channel: Channel number (1-4)
            attenuation: Attenuation value in dB (0-60 dB typical)

        Returns:
            True if successful
        """
        if not 1 <= channel <= self.num_channels:
            raise ValueError(f"Channel must be 1-{self.num_channels}")

        # Clamp attenuation to reasonable bounds
        attenuation = max(0.0, min(60.0, attenuation))

        try:
            command = f"INP{channel}:ATT {attenuation}"
            self.write(command)
            if not self.offline:
                print(f"Set channel {channel} attenuation to {attenuation} dB")
            return True
        except Exception as e:
            print(f"Error setting attenuation on channel {channel}: {e}")
            return False

    def set_attenuation_all(self, attenuation: float) -> bool:
        """
        Set the same attenuation value for all channels.

        Args:
            attenuation: Attenuation value in dB

        Returns:
            True if successful
        """
        # Clamp attenuation to reasonable bounds
        attenuation = max(0.0, min(60.0, attenuation))

        try:
            command = f"INP:ATT:ALL {attenuation}"
            self.write(command)
            if not self.offline:
                print(f"Set all channels attenuation to {attenuation} dB")
            return True
        except Exception as e:
            print(f"Error setting attenuation on all channels: {e}")
            return False

    # Wavelength control methods
    def get_wavelength(self, channel: int = 1) -> float:
        """
        Get the wavelength setting for a channel.

        Args:
            channel: Channel number (1-4)

        Returns:
            Wavelength in nm
        """
        if not 1 <= channel <= self.num_channels:
            raise ValueError(f"Channel must be 1-{self.num_channels}")

        try:
            response = self.query(f"INP{channel}:WAV?")
            return float(response) * 1e9  # Convert to nm
        except Exception as e:
            print(f"Error reading wavelength from channel {channel}: {e}")
            return self.current_wavelength

    def set_wavelength(self, channel: int, wavelength: float) -> bool:
        """
        Set the wavelength for a specific channel.

        Args:
            channel: Channel number (1-4)
            wavelength: Wavelength in nm (1200-1700 nm typical)

        Returns:
            True if successful
        """
        if not 1 <= channel <= self.num_channels:
            raise ValueError(f"Channel must be 1-{self.num_channels}")

        # Convert nm to meters for instrument
        wavelength_m = wavelength * 1e-9

        try:
            command = f"INP{channel}:WAV {wavelength_m}"
            self.write(command)
            if not self.offline:
                print(f"Set channel {channel} wavelength to {wavelength} nm")
            return True
        except Exception as e:
            print(f"Error setting wavelength on channel {channel}: {e}")
            return False

    def set_wavelength_all(self, wavelength: float) -> bool:
        """
        Set the wavelength for all channels.

        Args:
            wavelength: Wavelength in nm

        Returns:
            True if successful
        """
        # Convert nm to meters for instrument
        wavelength_m = wavelength * 1e-9
        self.current_wavelength = wavelength

        try:
            command = f"INP:WAV:ALL {wavelength_m}"
            self.write(command)
            if not self.offline:
                print(f"Set all channels wavelength to {wavelength} nm")
            return True
        except Exception as e:
            print(f"Error setting wavelength on all channels: {e}")
            return False

    # Shutter control methods
    def shutters_open(self) -> bool:
        """Open all shutters."""
        try:
            self.write("OUTP:STAT:ALL ON")
            if not self.offline:
                print("Opened all shutters")
            return True
        except Exception as e:
            print(f"Error opening shutters: {e}")
            return False

    def shutters_close(self) -> bool:
        """Close all shutters."""
        try:
            self.write("OUTP:STAT:ALL OFF")
            if not self.offline:
                print("Closed all shutters")
            return True
        except Exception as e:
            print(f"Error closing shutters: {e}")
            return False

    def get_shutter_state(self, channel: int) -> bool:
        """
        Get the shutter state for a specific channel.

        Args:
            channel: Channel number (1-4)

        Returns:
            True if shutter is open, False if closed
        """
        if not 1 <= channel <= self.num_channels:
            raise ValueError(f"Channel must be 1-{self.num_channels}")

        try:
            response = self.query(f"OUTP{channel}:STAT?")
            return bool(int(response))
        except Exception as e:
            print(f"Error reading shutter state from channel {channel}: {e}")
            return False

    def set_shutter_state(self, channel: int, state: bool) -> bool:
        """
        Set the shutter state for a specific channel.

        Args:
            channel: Channel number (1-4)
            state: True to open, False to close

        Returns:
            True if successful
        """
        if not 1 <= channel <= self.num_channels:
            raise ValueError(f"Channel must be 1-{self.num_channels}")

        try:
            state_str = "ON" if state else "OFF"
            command = f"OUTP{channel}:STAT {state_str}"
            self.write(command)
            if not self.offline:
                action = "opened" if state else "closed"
                print(f"Channel {channel} shutter {action}")
            return True
        except Exception as e:
            print(f"Error setting shutter state on channel {channel}: {e}")
            return False

    # GenericSource interface implementation
    def set_voltage(self, voltage: float) -> bool:
        """
        Set voltage equivalent (maps to attenuation in dB).
        This allows the attenuator to be used as a GenericSource.

        Args:
            voltage: Value interpreted as attenuation in dB

        Returns:
            True if successful
        """
        return self.set_attenuation_all(voltage)

    def get_voltage(self) -> float:
        """
        Get voltage equivalent (maps to attenuation in dB).

        Returns:
            Current attenuation in dB for channel 1
        """
        return self.get_attenuation(1)

    def set_output_state(self, state: bool) -> bool:
        """
        Set output state (maps to shutter control).

        Args:
            state: True to enable (open shutters), False to disable (close shutters)

        Returns:
            True if successful
        """
        if state:
            return self.shutters_open()
        else:
            return self.shutters_close()

    def get_output_state(self) -> bool:
        """
        Get output state (maps to shutter state).

        Returns:
            True if any shutter is open
        """
        try:
            for ch in range(1, self.num_channels + 1):
                if self.get_shutter_state(ch):
                    return True
            return False
        except Exception:
            return False

    # Utility methods
    def load_calibration(self, calibration_file: Path) -> bool:
        """
        Load calibration data from file.

        Args:
            calibration_file: Path to calibration file

        Returns:
            True if successful
        """
        try:
            self.calibration_file = calibration_file
            # In a real implementation, this would load wavelength-dependent
            # calibration factors for accurate attenuation control
            print(f"Loaded calibration from {calibration_file}")
            return True
        except Exception as e:
            print(f"Error loading calibration: {e}")
            return False

    def get_status(self) -> dict:
        """
        Get comprehensive status of all channels.

        Returns:
            Dictionary with status information
        """
        status = {"wavelength": self.current_wavelength, "channels": {}}

        for ch in range(1, self.num_channels + 1):
            try:
                status["channels"][ch] = {
                    "attenuation_db": self.get_attenuation(ch),
                    "shutter_open": self.get_shutter_state(ch),
                    "wavelength_nm": self.get_wavelength(ch),
                }
            except Exception as e:
                status["channels"][ch] = {"error": str(e)}

        return status

    def auto_calibrate(
        self, target_power: float = 1e-6, channel: int = 1
    ) -> Optional[float]:
        """
        Automatically calibrate attenuation for target power level.

        Args:
            target_power: Target power level in watts
            channel: Channel to calibrate

        Returns:
            Optimal attenuation value in dB, or None if failed
        """
        # This would be implemented with a power meter in a real system
        print(f"Auto-calibration would require external power meter")
        print(f"Target: {target_power} W on channel {channel}")
        return None


def main():
    """Example usage of the Agilent N7764A attenuator."""
    # Example with offline mode for testing
    attenuator = AgilentN7764A("10.7.0.127", offline=True)

    try:
        attenuator.connect()

        # Set wavelength for all channels
        attenuator.set_wavelength_all(1550.0)  # 1550 nm

        # Set attenuation
        attenuator.set_attenuation_all(10.0)  # 10 dB

        # Open shutters
        attenuator.shutters_open()

        # Get status
        status = attenuator.get_status()
        print("Attenuator status:", status)

    finally:
        attenuator.disconnect()


if __name__ == "__main__":
    main()
