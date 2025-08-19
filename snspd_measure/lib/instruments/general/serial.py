import serial
from typing import Optional

from lib.instruments.general.parent_child import Dependency


class SerialDep(Dependency):
    """Unified serial communication + dependency object.

    This replaces the prior SerialComm (transport) + SerialDep (wrapper) pair.
    Parent instruments now pass this object directly to children.
    """

    def __init__(self, port: str, baudrate: int = 9600, timeout: int = 1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None
        self.offline: bool = False

        self.connect()  # RAII

    def connect(self) -> bool:
        try:
            self.serial = serial.Serial(
                port=self.port, baudrate=self.baudrate, timeout=self.timeout
            )
            return True
        except Exception as e:
            print(f"Failed to connect to {self.port}: {e}")
            self.offline = True
            return False

    def disconnect(self) -> bool:
        if self.serial and self.serial.is_open:
            self.serial.close()
        return True

    def __del__(self):
        self.disconnect()

    def write(self, cmd: str) -> int | None:
        if self.offline:
            return len(cmd)
        if not self.serial or not self.serial.is_open:
            raise RuntimeError("Serial connection not open")
        self.serial.flush()
        return self.serial.write(cmd.encode())

    def read(self) -> bytes:
        if self.offline:
            return b""
        if not self.serial or not self.serial.is_open:
            raise RuntimeError("Serial connection not open")
        return self.serial.readline()

    def query(self, cmd: str) -> bytes:
        self.write(cmd)
        return self.read()
