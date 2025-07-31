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
from typing import Any, Dict, Optional, Annotated, Literal

from lib.instruments.general.parent import Parent
from lib.instruments.general.child import Child
from lib.instruments.sim900.comm import Comm
from lib.instruments.sim900.modules.sim928 import Sim928, Sim928Params
from lib.instruments.sim900.modules.sim970 import Sim970, Sim970Params
from lib.instruments.sim900.modules.sim921 import Sim921, Sim921Params
from lib.instruments.general.parent import ParentParams
from lib.instruments.general.serial import SerialComm
from lib.instruments.general.child import ChildParams

Sim900ChildParams = Annotated[
    Sim928Params | Sim970Params | Sim921Params, Field(discriminator="type")
]


class Sim900Params(ParentParams[Sim900ChildParams], ChildParams):
    """Parameters for SIM900 mainframe"""

    gpibAddr: Annotated[int, Field(description="GPIB address number")] = 2
    modules: dict[str, Sim900ChildParams] = {}
    type: Literal["sim900"] = "sim900"


class Sim900(Parent[Sim900Params]):
    """
    Class for the sim900 mainframe
    """

    def __init__(self, resource: SerialComm, gpibAddr: int):
        """
        :param comm: The communication object for the mainframe
        :param **kwargs: defined in serialInst.py
            timeout - connection timeout (s)
            offline - if True, don't actually write/read over com
        """
        self.serial_comm = resource
        self.gpibAddr = gpibAddr
        self.modules: Dict[int, Child] = {}

    @classmethod
    def from_params(
        cls, resource: SerialComm, params: Sim900Params
    ) -> "tuple[Sim900, Sim900Params]":
        """
        Create a Sim900 instance from parameters
        :param params: Parameters for the SIM900 mainframe
        :return: An instance of Sim900
        """

        return cls(resource, gpibAddr=params.gpibAddr), params

    def create_submodule(self, params: Sim900ChildParams) -> Child:
        """
        Create a submodule with the given parameters
        :param params: Parameters containing module type, slot, and configuration
        :return: The created submodule
        """
        module_type = params.type
        slot = params.slot

        # Create communication object for this slot
        comm = Comm(self.serial_comm, self.gpibAddr, slot, offline=params.offline)

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

    def get_module(self, slot: int) -> Optional[Child]:
        """
        Get a module by slot number
        :param slot: Slot number
        :return: The module in that slot
        """
        return self.modules.get(slot)
