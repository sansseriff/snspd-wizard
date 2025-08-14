"""
sim900.py
Author: Andrew Mueller, based on an older library by Alex Walter & Boris Korzh
Updated: July 10, 2025 by Andrew Mueller

A series of sub classes for the SRS sim900 mainframe
Includes:
  sim970 (voltmeter)
  sim928 (voltage source)
  sim921 (AC resistance bridge)
"""

from typing import Annotated, Literal, TYPE_CHECKING, cast, TypeVar, Any
from pydantic import Field


from lib.instruments.general.parent_child import (
    Parent,
    ParentParams,
    Child,
    ChannelChildParams,
    Dependency,
    ChildParams,
)
from lib.instruments.sim900.comm import Comm
from lib.instruments.sim900.modules.sim928 import Sim928Params
from lib.instruments.sim900.modules.sim970 import Sim970Params
from lib.instruments.sim900.modules.sim921 import Sim921Params
from lib.instruments.general.serial import SerialComm  # still needed for Sim900Dep

if TYPE_CHECKING:
    from lib.instruments.general.serial import SerialDep  # parent dependency type

Sim900ChildParams = Annotated[
    Sim928Params | Sim970Params | Sim921Params, Field(discriminator="type")
]


class Sim900Dep(Dependency):
    """Internal dependency passed to SIM modules (holds shared serial + gpib)."""

    def __init__(self, serial_comm: SerialComm, gpibAddr: int):
        self.serial_comm = serial_comm
        self.gpibAddr = gpibAddr


class Sim900Params(
    ParentParams[Sim900Dep, Sim900ChildParams], ChannelChildParams["Sim900"]
):
    """Parameters for SIM900 mainframe (hybrid Parent + Child)."""

    # Parent-specific
    children: dict[str, Sim900ChildParams] = Field(default_factory=dict)
    num_channels: int = 8
    gpibAddr: int = 2
    type: Literal["sim900"] = "sim900"

    @property
    def corresponding_inst(self):
        return Sim900


TChild = TypeVar("TChild", bound=Child[Sim900Dep, Any])


class Sim900(Parent[Sim900Dep, Sim900ChildParams], Child["SerialDep", Sim900Params]):
    """
    SIM900 mainframe hybrid:
      - As Child of SerialConnection: consumes SerialDep (shared SerialComm)
      - As Parent of SIM modules: supplies Sim900Dep (serial + GPIB address)
    """

    def __init__(self, parent_dep: "SerialDep", params: Sim900Params):
        self.params = params
        self._parent_dep = parent_dep  # dependency from SerialConnection
        self._dep = Sim900Dep(parent_dep.serial_comm, params.gpibAddr)  # for children
        self.children: dict[str, Child[Sim900Dep, Sim900ChildParams]] = {}

    # Child interface requirement
    @property
    def parent_class(self) -> str:
        return "SerialConnection"

    @classmethod
    def from_params(  # type: ignore[override]
        cls,
        dep: "SerialDep",
        params: Sim900Params,
    ) -> tuple["Sim900", Sim900Params]:
        inst = cls(dep, params)
        return inst, params

    # Parent abstract requirement
    @property
    def dep(self) -> Sim900Dep:
        return self._dep

    def _build_child_comm(self, p: Sim900ChildParams) -> Comm:
        return Comm(self.dep.serial_comm, self.dep.gpibAddr, p.slot, offline=p.offline)

    def init_child_by_key(self, key: str) -> Child[Sim900Dep, Sim900ChildParams]:
        params = self.params.children[key]
        child_cls = params.corresponding_inst
        # The specific param subtype matches child_cls, but the type checker
        # cannot express this dependency (params is a union). Cast to silence
        # the variance/union complaint.
        child_typed = cast(type[Child[Sim900Dep, Sim900ChildParams]], child_cls)
        child, _ = child_typed.from_params(self.dep, params)
        self.children[key] = child
        return child

    def init_children(self) -> None:
        for key in list(self.params.children.keys()):
            self.init_child_by_key(key)

    def add_child(self, key: str, params: ChildParams[TChild]) -> TChild:
        self.params.children[key] = params  # type: ignore[assignment]
        child_cls = params.corresponding_inst
        child, _ = child_cls.from_params(self.dep, params)
        # Record in children dict with erased union type
        self.children[key] = cast(Child[Sim900Dep, Sim900ChildParams], child)
        return child
