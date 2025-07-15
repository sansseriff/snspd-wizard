from typing import Optional

from lib.instruments.general.genericMainframe import GenericMainframe
from lib.instruments.general.submodule import Submodule, SubmoduleParams

from lib.instruments.sim900.comm import Comm
from pydantic import BaseModel

from lib.instruments.sim900.sim900 import Sim900
import time

import numpy as np


class Sim921Params(BaseModel, SubmoduleParams):
    """Parameters for SIM921 resistance bridge module"""

    slot: int
    type: str = "sim921"
    offline: Optional[bool] = False
    settling_time: Optional[float] = 0.1
    attribute: Optional[str] = None


class Sim921(Submodule):
    """
    SIM921 module in the SIM900 mainframe
    Resistance bridge
    """

    def __init__(self, comm: Comm, params: Sim921Params):
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
