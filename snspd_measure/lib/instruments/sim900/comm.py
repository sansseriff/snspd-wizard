from snspd_measure.lib.instruments.general.serialInst import GPIBmodule
from typing import Any


class Comm:
    """
    Communication class for sim900 mainframe modules
    Handles GPIB communication with slot-specific commands
    """

    def __init__(self, port: str, gpibAddr: int, slot: int, **kwargs: Any):
        """
        :param port: The serial port. eg. '/dev/ttyUSB4'
        :param gpibAddr: The GPIB address number [int]
        :param slot: The slot number in the sim900 mainframe [int]
        :param **kwargs: defined in serialInst.py
            timeout - connection timeout (s)
            offline - if True, don't actually write/read over com
        """
        self.gpib_module = GPIBmodule(port, gpibAddr, **kwargs)
        self.slot = slot
        self.offline: bool = kwargs.get("offline", False)

    def write(self, cmd: str) -> int | bool | None:
        """
        Write command to specific slot
        :param cmd: The command you want to send. eg. VOLT? 1
        :return: number of bytes written to the port
        """
        cmd = "CONN " + str(self.slot) + ', "esc"\r\n' + cmd + "\r\nesc"
        return self.gpib_module.write(cmd)

    def read(self) -> bytes | str:
        """
        Read from the GPIB module
        :return: response from the instrument
        """
        return self.gpib_module.read()

    def query(self, cmd: str) -> bytes | str:
        """
        Query the instrument (write then read)
        :param cmd: Command to send
        :return: Response from instrument
        """
        self.write(cmd)
        return self.read()

    def connect(self) -> bool:
        """Connect to the instrument"""
        result = self.gpib_module.connect()
        return result is not None

    def disconnect(self) -> bool:
        """Disconnect from the instrument"""
        result = self.gpib_module.disconnect()
        return result is not None
