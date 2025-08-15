from typing import Literal
from lib.instruments.general.parent_child import ChannelChildParams, Child
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.instruments.sim900.sim900 import Sim900Dep
from lib.instruments.sim900.comm import Comm


class Sim921Params(ChannelChildParams["Sim921"]):
    """Parameters for SIM921 resistance bridge module"""

    type: Literal["sim921"] = "sim921"
    slot: int
    num_channels: int = 1
    offline: bool | None = False
    settling_time: float | None = 0.1
    attribute: str | None = None

    @property
    def inst(self):  # type: ignore[override]
        return Sim921


class Sim921(Child["Sim900Dep"]):
    """
    SIM921 module in the SIM900 mainframe
    Resistance bridge
    """

    @property
    def parent_class(self) -> str:
        return "lib.instruments.sim900.sim900.Sim900"

    @classmethod
    def from_params(cls, dep: "Sim900Dep", params: Sim921Params):
        comm = Comm(dep.serial_comm, dep.gpibAddr, params.slot, offline=params.offline)
        inst = cls(comm, params)
        return inst, params

    def __init__(self, comm: Comm, params: Sim921Params):
        """
        :param comm: Communication object for this module
        :param params: Parameters for the module
        """
        self.comm = comm
        self.settling_time = params.settling_time
        self.attribute = params.attribute
        self.slot = params.slot

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
