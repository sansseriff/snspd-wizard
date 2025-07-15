from typing import Optional

from lib.instruments.general.genericMainframe import GenericMainframe
from lib.instruments.general.genericSource import GenericSource
from lib.instruments.general.submodule import Submodule

from lib.instruments.sim900.comm import Comm
from pydantic import BaseModel

from lib.instruments.sim900.sim900 import Sim900
import time

import numpy as np


class Sim928Params(BaseModel):
    """Parameters for SIM928 voltage source module"""

    slot: int
    type: str = "sim928"
    offline: Optional[bool] = False
    settling_time: Optional[float] = 0.4
    attribute: Optional[str] = None


class Sim928(Submodule, GenericSource):
    """
    SIM928 module in the SIM900 mainframe
    Voltage source
    """

    def __init__(self, comm: Comm, params: Sim928Params):
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
