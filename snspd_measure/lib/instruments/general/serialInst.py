"""
serialInst.py - General utility classes for serial instruments

Based on the original serialInst.py from the SNSPD library but cleaned up for the new structure.
"""

import serial
import time


class serialInst:
    """
    Generic base class for an instrument connected over serial port
    """

    def __init__(
        self, port: str, timeout: int = 1, offline: bool = False, baudrate: int = 9600
    ):
        """
        :param port: The serial port
        :param timeout: the serial timeout
        :param offline: For testing purposes when your computer is not connected to the instrument
        :param baudrate: Serial communication baud rate
        """
        self.serial = serial.Serial()
        self.timeout = timeout
        self.port = port
        self.serial.port = port
        self.serial.timeout = timeout
        self.serial.baudrate = baudrate
        self.offline = offline

    def connect(self) -> bool | None:
        if self.offline:
            print(f"Connected to offline instrument {self.__class__}")
            return True
        return self.serial.open()

    def disconnect(self) -> bool | None:
        if self.offline:
            print(f"Disconnected from offline instrument {self.__class__}")
            return True
        return self.serial.close()

    def read(self) -> str | bytes:
        if self.offline:
            return ""
        return self.serial.readline()

    def write(self, cmd: str) -> int | bool:
        if self.offline:
            return True
        self.serial.flush()
        result = self.serial.write(cmd.encode())
        return result if result is not None else 0

    def query(self, cmd: str) -> str | bytes:
        self.write(cmd)
        return self.read()


class GPIBmodule(serialInst):
    """
    Serial to GPIB adapter for instruments that use GPIB over serial
    """

    def __init__(
        self,
        port: str,
        gpibAddr: int,
        timeout: int = 1,
        offline: bool = False,
        baudrate: int = 9600,
    ):
        """
        :param port: The serial port
        :param gpibAddr: GPIB address of the instrument
        :param timeout: Serial timeout
        :param offline: Testing mode flag
        :param baudrate: Serial communication baud rate
        """
        super().__init__(port, timeout, offline, baudrate)
        self.gpibAddr = gpibAddr

    def write(self, cmd: str) -> int | bool:
        """
        Write command with GPIB addressing
        """
        if self.offline:
            return True

        # Format command for GPIB
        gpib_cmd = f"++addr {self.gpibAddr}\n{cmd}\n"
        return super().write(gpib_cmd)

    def query(self, cmd: str) -> str | bytes:
        """
        Query with GPIB addressing
        """
        self.write(cmd)
        time.sleep(0.1)  # Small delay for response
        return self.read()
