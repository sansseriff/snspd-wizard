from lib.instruments.general.vsource import VSource
from typing import Literal
from lib.instruments.general.parent_child import ChannelChildParams, Child
from lib.instruments.sim900.comm import Comm


class Sim928Params(ChannelChildParams):
    """Parameters for SIM928 voltage source module"""

    type: Literal["sim928"] = "sim928"
    slot: int
    num_channels: int = 1
    offline: bool | None = False
    settling_time: float | None = 0.4
    attribute: str | None = None

    @property
    def corresponding_inst(self):  # type: ignore[override]
        return Sim928


class Sim928(Child, VSource):
    """
    SIM928 module in the SIM900 mainframe
    Voltage source
    """

    @property
    def parent_class(self) -> str:
        return "lib.instruments.sim900.sim900.Sim900"

    @classmethod
    def from_params(cls, dep, params: Sim928Params):
        comm = Comm(dep.serial_comm, dep.gpibAddr, params.slot, offline=params.offline)
        inst = cls(comm, params)
        return inst, params

    def __init__(self, comm: Comm, params: Sim928Params):
        """
        :param comm: Communication object for this module
        :param params: Parameters for the module
        """
        self.comm = comm
        self.settling_time = params.settling_time
        self.attribute = params.attribute
        self.connected = True  # Assume connected after initialization
        self.slot = params.slot

    @property
    def mainframe_class(self) -> str:
        return "lib.instruments.sim900.sim900.Sim900"

    def disconnect(self) -> bool:
        """
        Disconnect from the SIM928 module.

        Returns:
            bool: True if disconnection successful, False otherwise
        """
        if hasattr(self, "connected") and self.connected:
            self.comm.disconnect()
            self.connected = False
        return not self.connected

    def __del__(self):
        """
        Cleanup when the instance is deleted.
        """
        self.disconnect()

    def set_voltage(self, voltage: float, channel: int | None = None) -> bool:
        """
        :param voltage: The voltage you want to set in Volts [float]
        :param channel: Optional channel number (ignored for SIM928)
        :return: True if successful, False otherwise
        """
        applyVoltage = "%0.3f" % voltage
        cmd = "VOLT " + str(applyVoltage)
        result = self.comm.write(cmd)
        return result is not None and result > 0

    def turn_on(self, channel: int | None = None) -> bool:
        """
        Turns the voltage source on
        :param channel: Optional channel number (ignored for SIM928)
        :return: True if successful, False otherwise
        """
        result = self.comm.write("OPON")
        return result is not None and result > 0

    def turn_off(self, channel: int | None = None) -> bool:
        """
        Turns the voltage source off
        :param channel: Optional channel number (ignored for SIM928)
        :return: True if successful, False otherwise
        """
        result = self.comm.write("OPOF")
        return result is not None and result > 0
