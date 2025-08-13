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

from typing import Annotated, Literal
from pydantic import Field

# NEW imports from consolidated parent_child
from lib.instruments.general.parent_child import (
    Parent,
    ParentParams,
    Child,
    ChildParams,
    Dependency,
)
from lib.instruments.sim900.comm import Comm
from lib.instruments.sim900.modules.sim928 import Sim928, Sim928Params
from lib.instruments.sim900.modules.sim970 import Sim970, Sim970Params
from lib.instruments.sim900.modules.sim921 import Sim921, Sim921Params
from lib.instruments.general.serial import SerialComm

Sim900ChildParams = Annotated[
    Sim928Params | Sim970Params | Sim921Params, Field(discriminator="type")
]


class _Sim900Dep(Dependency):
    """Internal dependency passed to children (holds shared serial + gpib)."""

    def __init__(self, serial_comm: SerialComm, gpibAddr: int):
        self.serial_comm = serial_comm
        self.gpibAddr = gpibAddr


class Sim900Params(ParentParams[_Sim900Dep, Sim900ChildParams], ChildParams):
    """Parameters for SIM900 mainframe (ParentParams + ChildParams mixin)."""

    # Parent-specific
    children: dict[str, Sim900ChildParams] = Field(default_factory=dict)
    num_children: int = 8

    # Connection specifics
    gpibAddr: int = 2
    serial_comm: SerialComm  # required

    # ChildParams requirement
    type: Literal["sim900"] = "sim900"

    @property
    def corresponding_inst(self):  # type: ignore[override]
        return Sim900


class Sim900(Parent[_Sim900Dep, Sim900ChildParams]):
    """
    SIM900 mainframe implementing new Parent interface.
    """

    def __init__(self, params: Sim900Params):
        self.params = params
        self._dep = _Sim900Dep(params.serial_comm, params.gpibAddr)
        self.children: dict[str, Child[_Sim900Dep, Sim900ChildParams]] = {}

    # Parent abstract requirement
    @property
    def dep(self) -> _Sim900Dep:
        return self._dep

    def _build_child_comm(self, p: Sim900ChildParams) -> Comm:
        """Helper: create a Comm for a child params instance."""
        # Each child params must expose slot
        return Comm(self.dep.serial_comm, self.dep.gpibAddr, p.slot, offline=p.offline)

    def init_child_by_key(self, key: str) -> Child[_Sim900Dep, Sim900ChildParams]:
        params = self.params.children[key]
        # Use child's from_params (factory)
        child_cls = params.corresponding_inst
        # Build Comm and then construct directly (child.from_params expects dependency)
        # Provide dependency so child can create Comm itself (pattern); OR we create Comm now
        # We'll let child.from_params handle Comm creation using dependency.
        child, _ = child_cls.from_params(self.dep, params)
        self.children[key] = child
        return child

    def init_children(self) -> None:
        for key in list(self.params.children.keys()):
            self.init_child_by_key(key)

    @classmethod
    def from_params(cls, params: Sim900Params) -> "tuple[Sim900, Sim900Params]":
        inst = cls(params)
        return inst, params

    # Backwards-compatible helper similar to old create_submodule
    def create_submodule(self, params: Sim900ChildParams) -> Child:
        key = str(params.slot)
        self.params.children[key] = params
        return self.init_child_by_key(key)

    def get_module(self, slot: int) -> Child | None:
        return self.children.get(str(slot))
