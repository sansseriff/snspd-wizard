"""
sim900.py
Author: Claude, Andrew, based on work by Alex Walter, Boris Korzh
Original date: Dec 11, 2019
Updated: July 10, 2025

A series of sub classes for the SRS sim900 mainframe
Includes:
  sim970 (voltmeter)
  sim928 (voltage source)
  sim921 (AC resistance bridge)
"""

import time
import numpy as np
from pydantic import BaseModel
from typing import Any, Dict, Optional

from lib.instruments.general.serialInst import GPIBmodule
from lib.instruments.general.genericMainframe import GenericMainframe
from lib.instruments.general.submodule import Submodule


class Sim900Params(BaseModel):
    """Parameters for SIM900 mainframe"""

    port: str = "/dev/ttyUSB0"
    gpibAddr: int = 2
    timeout: Optional[float] = 1.0
    offline: Optional[bool] = False
    baudrate: Optional[int] = 9600


class Sim970Params(BaseModel):
    """Parameters for SIM970 voltmeter module"""

    slot: int
    type: str = "sim970"
    channel: Optional[int] = 1
    offline: Optional[bool] = False
    settling_time: Optional[float] = 0.1
    attribute: Optional[str] = None


class Sim928Params(BaseModel):
    """Parameters for SIM928 voltage source module"""

    slot: int
    type: str = "sim928"
    offline: Optional[bool] = False
    settling_time: Optional[float] = 0.4
    attribute: Optional[str] = None


class Sim921Params(BaseModel):
    """Parameters for SIM921 resistance bridge module"""

    slot: int
    type: str = "sim921"
    offline: Optional[bool] = False
    settling_time: Optional[float] = 0.1
    attribute: Optional[str] = None


class Sim900Comm:
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


class Sim900(GenericMainframe):
    """
    Class for the sim900 mainframe
    """

    def __init__(self, port: str, gpibAddr: int, **kwargs: Any):
        """
        :param port: The serial port. eg. '/dev/ttyUSB4'
        :param gpibAddr: The GPIB address number [int]
        :param **kwargs: defined in serialInst.py
            timeout - connection timeout (s)
            offline - if True, don't actually write/read over com
        """
        self.port = port
        self.gpibAddr = gpibAddr
        self.kwargs = kwargs
        self.modules: Dict[int, Submodule] = {}

    def create_submodule(
        self, params: Sim970Params | Sim928Params | Sim921Params
    ) -> Submodule:
        """
        Create a submodule with the given parameters
        :param params: Parameters containing module type, slot, and configuration
        :return: The created submodule
        """
        module_type = params.type
        slot = params.slot

        # Create communication object for this slot
        comm = Sim900Comm(self.port, self.gpibAddr, slot, **self.kwargs)

        # Create the appropriate submodule based on type
        if module_type == "sim970" and isinstance(params, Sim970Params):
            module = Sim970(comm, params)
        elif module_type == "sim928" and isinstance(params, Sim928Params):
            module = Sim928(comm, params)
        elif module_type == "sim921" and isinstance(params, Sim921Params):
            module = Sim921(comm, params)
        else:
            raise ValueError(f"Unknown module type: {module_type}")

        self.modules[slot] = module
        return module

    def get_module(self, slot: int) -> Optional[Submodule]:
        """
        Get a module by slot number
        :param slot: Slot number
        :return: The module in that slot
        """
        return self.modules.get(slot)


class Sim970(Submodule):
    """
    SIM970 module in the SIM900 mainframe.
    Voltmeter
    """

    def __init__(self, comm: Sim900Comm, params: Sim970Params):
        """
        :param comm: Communication object for this module
        :param params: Parameters for the module (contains channel info, etc.)
        """
        self.comm = comm
        self.channel = params.channel
        self.settling_time = params.settling_time
        self.attribute = params.attribute

    @property
    def mainframe_class(self) -> type[GenericMainframe]:
        return Sim900

    def getVoltage(self, ch: Optional[int] = None, _recurse: int = 0) -> float:
        """
        This gets the voltage
        :param ch: Channel 1-4 of the voltmeter
        :return: the voltage in V [float]
        """
        if self.comm.offline:
            return np.random.uniform()

        if ch is None:
            ch = self.channel

        cmd = "VOLT? " + str(ch)
        volts = self.comm.query(cmd)
        time.sleep(0.1)
        volts = self.comm.query(cmd)

        try:
            output = float(volts)
        except ValueError:
            if _recurse < 3:
                output = self.getVoltage(ch, _recurse + 1)
            else:
                raise ValueError(f"Could not parse voltage reading: {volts}")

        return output


class Sim928(Submodule):
    """
    SIM928 module in the SIM900 mainframe
    Voltage source
    """

    def __init__(self, comm: Sim900Comm, params: Sim928Params):
        """
        :param comm: Communication object for this module
        :param params: Parameters for the module
        """
        self.comm = comm
        self.settling_time = params.settling_time
        self.attribute = params.attribute

    @property
    def mainframe_class(self) -> type["GenericMainframe"]:
        return Sim900

    def setVoltage(self, voltage: float) -> int | bool | None:
        """
        :param voltage: The voltage you want to set in Volts [float]
        :return: the number of bytes written to the serial port
        """
        applyVoltage = "%0.3f" % voltage
        cmd = "VOLT " + str(applyVoltage)
        return self.comm.write(cmd)

    def turnOn(self) -> int | bool | None:
        """
        Turns the voltage source on
        :return: the number of bytes written to the serial port
        """
        return self.comm.write("OPON")

    def turnOff(self) -> int | bool | None:
        """
        Turns the voltage source off
        :return: the number of bytes written to the serial port
        """
        return self.comm.write("OPOF")


class Sim921(Submodule):
    """
    SIM921 module in the SIM900 mainframe
    Resistance bridge
    """

    def __init__(self, comm: Sim900Comm, params: Sim921Params):
        """
        :param comm: Communication object for this module
        :param params: Parameters for the module
        """
        self.comm = comm
        self.settling_time = params.settling_time
        self.attribute = params.attribute

    @property
    def mainframe_class(self) -> type["GenericMainframe"]:
        return Sim900

    def getResistance(self) -> float:
        """
        gets the resistance from the bridge
        :return: the resistance in Ohm [float]
        """
        cmd = "RVAL?"
        res = self.comm.query(cmd)
        return float(res)
