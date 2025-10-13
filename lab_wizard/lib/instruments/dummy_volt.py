from __future__ import annotations

"""Dummy single-channel voltage sensing instrument for remote demo.

Acts like a very small subset of Sim970 but without channel fan-out. It uses the
DummyBackend / DummyChannelRequest pipeline so it can be exercised locally or via
remote Pyro broker transparently.
"""
from typing import Literal, Any, cast
from pydantic import BaseModel
from lib.instruments.general.parent_child import Child, ChildParams
from lib.instruments.general.computer import ComputerDep
from lib.instruments.general.comm import DummyChannelRequest
from lib.instruments.general.dummy_dep import DummyDep


class DummyVoltParams(ChildParams["DummyVolt"]):
    type: Literal["dummyVolt"] = "dummyVolt"
    name: str = "DummyVolt"
    resource_name: str = "demo0"  # maps to descriptor dummy:demo0

    @property
    def inst(self):  # type: ignore[override]
        return DummyVolt

    @property
    def parent_class(self) -> str:
        return "lib.instruments.general.computer.Computer"


class DummyVolt(Child[ComputerDep, DummyVoltParams]):
    def __init__(self, channel: DummyDep, params: DummyVoltParams, dep: ComputerDep):
        self._channel = channel
        self.params = params
        self._dep = dep
        self.connected = True

    @classmethod
    def from_params_with_dep(
        cls, parent_dep: ComputerDep, key: str, params: DummyVoltParams | Any
    ) -> "DummyVolt":
        if not isinstance(params, DummyVoltParams):
            raise TypeError(
                f"DummyVolt expects DummyVoltParams, got {type(params).__name__}"
            )
        # Allow key override of resource name for convenience
        resource = key or params.resource_name
        req = DummyChannelRequest(name=resource)
        dep = parent_dep.get_channel(req)
        return cls(dep, params, parent_dep)
    
    def parent_class(self) -> str:
        return "lib.instruments.general.computer.Computer"

    @property
    def dep(self) -> ComputerDep:  # type: ignore[override]
        return self._dep

    def disconnect(self) -> bool:  # type: ignore[override]
        self.connected = False
        return True

    def get_voltage(self) -> float:
        print("[DummyVolt client] issuing voltage command")
        self._channel.write("MEAS:VOLT?")
        raw = self._channel.read()
        try:
            return float(raw)
        except ValueError:
            raise RuntimeError(f"Unexpected dummy voltage response: {raw!r}")

    def __str__(self) -> str:
        return f"DummyVolt(resource={self.params.resource_name})"


__all__ = ["DummyVoltParams", "DummyVolt"]
