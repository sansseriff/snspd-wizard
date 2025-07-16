from typing import Optional

from lib.instruments.general.genericMainframe import GenericMainframe
from lib.instruments.general.genericSense import GenericSense
from lib.instruments.general.submodule import Submodule

from lib.instruments.sim900.comm import Comm

from lib.instruments.sim900.sim900 import Sim900, Sim970Params
import time

import numpy as np


class Sim970(Submodule, GenericSense):
    """
    SIM970 module in the SIM900 mainframe.
    Voltmeter
    """

    def __init__(self, comm: Comm, params: Sim970Params):
        """
        :param comm: Communication object for this module
        :param params: Parameters for the module (contains channel info, etc.)
        """
        self.comm = comm
        self.channel = params.channel
        self.settling_time = params.settling_time
        self.attribute = params.attribute

    @property
    def mainframe_class(self) -> str:
        return "lib.instruments.sim900.sim900.Sim900"

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
