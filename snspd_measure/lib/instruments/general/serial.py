from typing import Union
from lib.instruments.general.parent import Parent, ParentParams
from typing import Annotated
from pydantic import Field

from lib.instruments.sim900.sim900 import Sim900Params, Sim900
from lib.instruments.general.gpib import GPIBComm
# Import other serial-connected instrument types as needed

SerialInstParams = Annotated[Sim900Params, Field(discriminator="type")]

import serial
from typing import Optional


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


class SerialConnectionParams(ParentParams[SerialInstParams]):
    port: str = "/dev/ttyUSB0"
    baudrate: int = 9600
    timeout: int = 1
    instruments: dict[str, SerialInstParams] = {}

    def promote(self) -> "SerialConnection":
        """
        Promote the parameters to a SerialConnection instance.
        :return: An instance of SerialConnection
        """
        return SerialConnection.from_params(self)


class SerialConnection(Parent[SerialConnectionParams]):
    def __init__(self, port: str, baudrate: int = 9600, timeout: int = 1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.instruments: dict[str, Union[Sim900, GPIBInstrument]] = {}
        self.comm = SerialComm(port, baudrate, timeout)
        self.connect()

    def connect(self):
        """Connect to the serial port"""
        self.comm.connect()

    def disconnect(self):
        """Disconnect from the serial port"""
        self.comm.disconnect()

    @classmethod
    def from_params(cls, params: SerialConnectionParams) -> "SerialConnection":
        """
        Create a SerialConnection instance from parameters
        :param params: Parameters for the SerialConnection
        :return: An instance of SerialConnection
        """
        instance = cls(
            port=params.port, baudrate=params.baudrate, timeout=params.timeout
        )

        # Create instruments from params
        for name, instrument_params in params.instruments.items():
            instrument = instance.create_subinstrument(instrument_params)
            instance.instruments[name] = instrument

        return instance

    def create_subinstrument(
        self, params: SerialSubinstrumentParams
    ) -> Union[Sim900, GPIBInstrument]:
        """
        Create an instrument that uses this serial connection
        """
        if params.type == "Sim900":
            return Sim900.from_params(params, self.comm)
        elif params.type == "GPIBInstrument":
            return GPIBInstrument.from_params(params, self.comm)
        else:
            raise ValueError(f"Unknown instrument type: {params.type}")

    def get_instrument(self, name: str):
        """Get an instrument by name"""
        return self.instruments.get(name)

    def list_instruments(self):
        """
        Pretty-print a list of all instruments on this serial connection.
        """
        print(f"Serial Connection ({self.port}) Instruments:")
        print("=" * 50)
        for name, instrument in self.instruments.items():
            print(f"{name}: {instrument}")
        print("=" * 50)
        return self.instruments
