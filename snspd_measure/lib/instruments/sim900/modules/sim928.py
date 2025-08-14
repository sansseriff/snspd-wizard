from lib.instruments.general.vsource import VSource
from typing import Literal
from lib.instruments.general.parent_child import ChannelChildParams, Child, ChildParams
from lib.instruments.sim900.comm import Comm
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # only for type checking to avoid circular import at runtime
    from lib.instruments.sim900.sim900 import Sim900Dep


class Sim928Params(ChildParams["Sim928"]):
    """Parameters for SIM928 voltage source module"""

    type: Literal["sim928"] = "sim928"
    slot: int = 0  # default so Sim928Params() works in chain demo
    offline: bool | None = False
    settling_time: float | None = 0.4
    attribute: str | None = None

    @property
    def corresponding_inst(self):  # type: ignore[override]
        return Sim928


class Sim928(Child["Sim900Dep", Sim928Params], VSource):
    """
    SIM928 module in the SIM900 mainframe
    Voltage source
    """

    @property
    def parent_class(self) -> str:
        return "lib.instruments.sim900.sim900.Sim900"

    @classmethod
    def from_params(
        cls, dep: "Sim900Dep", params: Sim928Params
    ) -> tuple["Sim928", Sim928Params]:
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

    # Implement abstract VSource interface (single-channel instrument)
    def set_voltage(self, voltage: float) -> bool:  # type: ignore[override]
        apply_voltage = f"{voltage:0.3f}"
        result = self.comm.write(f"VOLT {apply_voltage}")
        return result is not None and result is not False

    def turn_on(self) -> bool:  # type: ignore[override]
        result = self.comm.write("OPON")
        return result is not None and result is not False

    def turn_off(self) -> bool:  # type: ignore[override]
        result = self.comm.write("OPOF")
        return result is not None and result is not False

    def disconnect(self) -> bool:  # type: ignore[override]
        self.connected = False
        return True
