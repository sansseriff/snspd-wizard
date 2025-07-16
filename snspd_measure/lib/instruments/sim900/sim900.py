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
from lib.instruments.general.submodule import Submodule, SubmoduleParams


from lib.instruments.sim900.comm import Comm
from lib.instruments.sim900.modules.sim928 import Sim928
from lib.instruments.sim900.modules.sim970 import Sim970
from lib.instruments.sim900.modules.sim921 import Sim921
from pydantic import BaseModel, Field
from typing import ClassVar


class Sim921Params(SubmoduleParams):
    """Parameters for SIM921 resistance bridge module"""

    slot: ClassVar[int]
    type: ClassVar[str] = "sim921"
    offline: bool | None = False
    settling_time: float | None = 0.1
    attribute: str | None = None


class Sim928Params(SubmoduleParams):
    """Parameters for SIM928 voltage source module"""

    slot: ClassVar[int]
    type: ClassVar[str] = "sim928"
    offline: bool | None = False
    settling_time: float | None = 0.4
    attribute: str | None = None


class Sim970Params(SubmoduleParams):
    """Parameters for SIM970 voltmeter module"""

    slot: ClassVar[int]
    type: ClassVar[str] = "sim970"
    channel: int | None = 1
    offline: bool | None = False
    settling_time: float | None = 0.1
    attribute: str | None = None


class Sim900Params(BaseModel):
    """Parameters for SIM900 mainframe"""

    port: str = "/dev/ttyUSB0"
    gpibAddr: int = 2
    timeout: Optional[float] = 1.0
    baudrate: Optional[int] = 9600
    modules: Sim928Params | Sim970Params | Sim921Params = Field(discriminator="type")


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

    def create_submodule(self, params: SubmoduleParams) -> Submodule:
        """
        Create a submodule with the given parameters
        :param params: Parameters containing module type, slot, and configuration
        :return: The created submodule
        """
        module_type = params.type
        slot = params.slot

        # Create communication object for this slot
        comm = Comm(self.port, self.gpibAddr, slot, **self.kwargs)

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
