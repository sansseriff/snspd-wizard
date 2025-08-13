from __future__ import annotations
from lib.instruments.general.vsense import VSense
from lib.instruments.general.parent_child import ChannelChildParams, Child
from lib.instruments.sim900.comm import Comm
import time
import numpy as np
from typing import Literal


class Sim970Params(ChannelChildParams):
    """Parameters for SIM970 voltmeter module"""

    type: Literal["sim970"] = "sim970"
    slot: int
    num_channels: int = 4
    channel: int | None = 1
    offline: bool | None = False
    settling_time: float | None = 0.1
    attribute: str | None = None
    max_retries: int | None = 3

    @property
    def corresponding_inst(self):  # type: ignore[override]
        return Sim970


class Sim970(Child, VSense):
    """
    SIM970 module in the SIM900 mainframe.
    Voltmeter
    """

    def __init__(self, comm: Comm, params: Sim970Params) -> None:
        """
        :param comm: Communication object for this module
        :param params: Parameters for the module (contains channel info, etc.)
        """
        self.comm = comm
        self.channel = params.channel
        self.settling_time = params.settling_time
        self.attribute = params.attribute
        self.connected = True  # Module is connected when initialized
        self.max_retries = params.max_retries or 3
        self.slot = params.slot

    @property
    def parent_class(self) -> str:  # renamed from mainframe_class
        return "lib.instruments.sim900.sim900.Sim900"

    @classmethod
    def from_params(cls, dep, params: Sim970Params):
        """
        Factory required by Child ABC. 'dep' must expose serial_comm & gpibAddr.
        """
        comm = Comm(dep.serial_comm, dep.gpibAddr, params.slot, offline=params.offline)
        inst = cls(comm, params)
        return inst, params

    def disconnect(self) -> bool:
        """
        Disconnect from the SIM970 module.

        Returns:
            bool: True if disconnection successful, False otherwise
        """
        self.connected = False
        return not self.connected

    def get_voltage(self, channel: int | None = None) -> float:
        """
        This gets the voltage
        :param channel: Channel 1-4 of the voltmeter
        :return: the voltage in V [float]
        """
        return self._get_voltage_impl(channel, 0)

    def _get_voltage_impl(self, channel: int | None, recurse_count: int) -> float:
        """Internal implementation with retry logic"""
        if self.comm.offline:
            return np.random.uniform()

        if channel is None:
            channel = self.channel

        cmd = "VOLT? " + str(channel)
        volts = self.comm.query(cmd)
        time.sleep(0.1)
        volts = self.comm.query(cmd)

        try:
            output = float(volts)
        except ValueError:
            if recurse_count < self.max_retries:
                output = self._get_voltage_impl(channel, recurse_count + 1)
            else:
                raise ValueError(f"Could not parse voltage reading: {volts}")

        return output
