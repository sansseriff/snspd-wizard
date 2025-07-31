from typing import Any
import time

from lib.instruments.general.gpib import GPIBComm
from lib.instruments.general.serial import SerialComm


class Comm:
    """
    Communication class for sim900 mainframe modules
    Handles GPIB communication with slot-specific commands
    """

    def __init__(
        self, serial_comm: SerialComm, gpibAddr: int, slot: int, **kwargs: Any
    ):
        """
        :param serial_comm: Shared SerialComm instance from SerialConnection
        :param gpibAddr: The GPIB address number [int]
        :param slot: The slot number in the sim900 mainframe [int]
        :param **kwargs: Additional parameters
            offline - if True, don't actually write/read over com
        """
        self.gpib_comm = GPIBComm(serial_comm, gpibAddr, **kwargs)
        self.slot = slot
        self.offline: bool = kwargs.get("offline", False)

    def write(self, cmd: str) -> int | bool | None:
        """
        Write command to specific slot
        :param cmd: The command you want to send. eg. VOLT? 1
        :return: number of bytes written to the port
        """
        if self.offline:
            return True

        # Format command for sim900 slot communication
        slot_cmd = f'CONN {self.slot}, "esc"\r\n{cmd}\r\nesc'
        return self.gpib_comm.write(slot_cmd)

    def read(self) -> bytes | str:
        """
        Read from the GPIB module
        :return: response from the instrument
        """
        if self.offline:
            return ""
        return self.gpib_comm.read()

    def query(self, cmd: str) -> bytes | str:
        """
        Query the instrument (write then read)
        :param cmd: Command to send
        :return: Response from instrument
        """
        if self.offline:
            return ""
        self.write(cmd)
        time.sleep(0.1)  # Small delay for slot communication
        return self.read()

    def connect(self) -> bool:
        """
        Connect to the instrument
        :return: True if successful
        """
        if self.offline:
            print(f"Connected to offline sim900 slot {self.slot}")
            return True
        return self.gpib_comm.connect()

    def disconnect(self) -> bool:
        """
        Disconnect from the instrument
        :return: True if successful
        """
        if self.offline:
            print(f"Disconnected from offline sim900 slot {self.slot}")
            return True
        return self.gpib_comm.disconnect()
