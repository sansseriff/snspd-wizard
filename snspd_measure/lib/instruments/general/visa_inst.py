"""
visa_inst.py - General utility class for VISA instruments

Based on the original visaInst.py from the SNSPD library but cleaned up for the new structure.
"""

import pyvisa as visa
from pyvisa.resources import MessageBasedResource
from typing import cast, Any
from types import TracebackType


class VisaInst:
    """
    Generic base class for instruments connected via VISA (TCP/IP, USB, etc.)

    Supports context manager protocol for automatic resource cleanup.
    """

    def __init__(self, ipAddress: str, port: int = 5025, offline: bool = False) -> None:
        """
        Initialize VISA instrument connection.

        Args:
            ipAddress: The IP address (e.g., '10.7.0.114')
            port: The port on the host computer
            offline: If True, simulate instrument communication for testing
        """
        self.ipAddress: str = ipAddress
        self.port: int = port
        self.offline: bool = offline
        self.inst: MessageBasedResource | None = None

        self.connect()  # RAII

    def __enter__(self) -> "VisaInst":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit with automatic cleanup."""
        self.disconnect()

    def connect(self) -> bool | MessageBasedResource:
        """Connect to the instrument."""
        if self.offline:
            print(f"Connected to offline instrument {self.__class__}")
            return True

        try:
            rm = visa.ResourceManager("@py")
            resource_string = f"TCPIP::{self.ipAddress}::{self.port}::SOCKET"
            print(f"Opening resource: {resource_string}")

            self.inst = cast(MessageBasedResource, rm.open_resource(resource_string))
            self.inst.read_termination = "\n"
            self.inst.timeout = max(10000, getattr(self.inst, "timeout", 5000))

            # Try to get instrument ID
            try:
                idn = self.query("*IDN?")
                print(f"Connected to: {idn}")
            except Exception:
                print("Connected (no IDN response)")

            return self.inst

        except Exception as e:
            print(f"Failed to connect to {self.ipAddress}:{self.port} - {e}")
            raise

    def disconnect(self) -> bool:
        """Disconnect from the instrument."""
        if self.offline:
            print(f"Disconnected from offline instrument {self.__class__}")
            return True

        if self.inst:
            self.inst.close()
            return True
        return True

    def write(self, cmd: str) -> bool | int:
        """Write command to instrument."""
        if self.offline:
            return True
        if not self.inst:
            raise RuntimeError("Not connected to instrument")
        return self.inst.write(cmd)

    def read(self) -> str:
        """Read response from instrument."""
        if self.offline:
            return ""
        if not self.inst:
            raise RuntimeError("Not connected to instrument")
        return self.inst.read()

    def query(self, cmd: str) -> str:
        """Send command and read response."""
        if self.offline:
            return ""
        if not self.inst:
            raise RuntimeError("Not connected to instrument")
        return self.inst.query(cmd)

    def write_binary_values(self, cmd: str, values: list[Any]) -> bool | int:
        """Write binary values to instrument."""
        if self.offline:
            return True
        if not self.inst:
            raise RuntimeError("Not connected to instrument")
        return self.inst.write_binary_values(cmd, values)
