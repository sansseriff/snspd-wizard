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

from pydantic import Field
from typing import Any, Dict, Optional, Annotated

from snspd_measure.lib.instruments.general.mainframe import Mainframe
from lib.instruments.general.submodule import Submodule
from lib.instruments.sim900.comm import Comm
from lib.instruments.sim900.modules.sim928 import Sim928, Sim928Params
from lib.instruments.sim900.modules.sim970 import Sim970, Sim970Params
from lib.instruments.sim900.modules.sim921 import Sim921, Sim921Params
from lib.instruments.general.mainframe import MainframeParams

Sim900SubmoduleParams = Annotated[
    Sim928Params | Sim970Params | Sim921Params, Field(discriminator="type")
]


class Sim900Params(MainframeParams):
    """Parameters for SIM900 mainframe"""

    port: Annotated[str, Field(description="USB serial port")] = "/dev/ttyUSB0"
    gpibAddr: Annotated[int, Field(description="GPIB address number")] = 2
    timeout: Annotated[Optional[float], Field(description="Connection timeout (s)")] = (
        1.0
    )
    baudrate: Annotated[Optional[int], Field(description="Baud rate")] = 9600
    modules: dict[int, Sim900SubmoduleParams]


class Sim900(Mainframe[Sim900Params]):
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
        self.modules: Dict[int, Submodule[Sim900SubmoduleParams]] = {}

    @classmethod
    def from_params(cls, params: Sim900Params) -> "Sim900":
        """
        Create a Sim900 instance from parameters
        :param params: Parameters for the SIM900 mainframe
        :return: An instance of Sim900
        """
        return cls(
            port=params.port,
            gpibAddr=params.gpibAddr,
            timeout=params.timeout,
            baudrate=params.baudrate,
        )

    def create_submodule(
        self, params: Sim900SubmoduleParams
    ) -> Submodule[Sim900SubmoduleParams]:
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
