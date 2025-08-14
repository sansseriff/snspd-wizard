import serial
from typing import Optional

from lib.instruments.general.parent_child import Dependency


class SerialComm:
    """
    Communication class for serial connections
    Manages the shared serial connection for multiple instruments
    """

    def __init__(self, port: str, baudrate: int = 9600, timeout: int = 1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None

    def connect(self) -> bool:
        """Connect to the serial port"""
        try:
            self.serial = serial.Serial(
                port=self.port, baudrate=self.baudrate, timeout=self.timeout
            )
            return True
        except Exception as e:
            print(f"Failed to connect to {self.port}: {e}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from the serial port"""
        if self.serial and self.serial.is_open:
            self.serial.close()
        return True

    def write(self, cmd: str) -> int | None:
        """Write to the serial port"""
        if not self.serial or not self.serial.is_open:
            raise RuntimeError("Serial connection not open")

        self.serial.flush()
        return self.serial.write(cmd.encode())

    def read(self) -> bytes:
        """Read from the serial port"""
        if not self.serial or not self.serial.is_open:
            raise RuntimeError("Serial connection not open")

        return self.serial.readline()

    def query(self, cmd: str) -> bytes:
        """Write then read"""
        self.write(cmd)
        return self.read()


# New dependency passed from SerialConnection to its children
class SerialDep(Dependency):
    def __init__(self, serial_comm: SerialComm):
        self.serial_comm = serial_comm
