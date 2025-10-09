from lib.instruments.general.serial import SerialDep
import time


class GPIBComm:
    """
    GPIB communication layer that can use any underlying serial connection
    """

    def __init__(self, serial_comm: SerialDep, gpibAddr: int, offline: bool = False):
        """
        :param serial_comm: Shared SerialDep instance from parent connection
        :param gpibAddr: The GPIB address number [int]
        :param **kwargs: Additional parameters
            offline - if True, don't actually write/read over com
        """
        self.serial_comm = serial_comm
        self.gpibAddr = gpibAddr
        self.offline = offline

    def write(self, cmd: str) -> int | None:
        """
        Write command to GPIB device
        :param cmd: The command to send
        :return: number of bytes written or True if offline
        """
        if self.offline:
            return True

        # Format command for GPIB
        gpib_cmd = f"++addr {self.gpibAddr}\n{cmd}\n"
        return self.serial_comm.write(gpib_cmd)

    def read(self) -> bytes:
        """
        Read from GPIB device
        :return: response from the device
        """
        if self.offline:
            return b""
        return self.serial_comm.read()

    def query(self, cmd: str) -> bytes:
        """
        Query GPIB device (write then read)
        :param cmd: Command to send
        :return: Response from device
        """
        self.write(cmd)
        time.sleep(0.1)  # Small delay for response
        return self.read()

    # connect/disconnect should be managed only by the SerialConnection class
    # def connect(self) -> bool:
    #     return self.serial_comm.connect()

    # def disconnect(self) -> bool:
    #     return self.serial_comm.disconnect()
