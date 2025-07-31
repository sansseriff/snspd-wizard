from lib.instruments.general.child import ChannelChildParams, Child
from lib.instruments.sim900.comm import Comm
from typing import Literal


class Sim921Params(ChannelChildParams):
    """Parameters for SIM921 resistance bridge module"""

    type: Literal["sim921"] = "sim921"
    offline: bool | None = False
    settling_time: float | None = 0.1
    attribute: str | None = None


class Sim921(Child):
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
    def mainframe_class(self) -> str:
        return "lib.instruments.sim900.sim900.Sim900"

    def getResistance(self) -> float:
        """
        gets the resistance from the bridge
        :return: the resistance in Ohm [float]
        """
        cmd = "RVAL?"
        res = self.comm.query(cmd)
        return float(res)
