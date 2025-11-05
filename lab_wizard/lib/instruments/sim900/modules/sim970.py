from __future__ import annotations
from lib.instruments.general.vsense import VSense
from lib.instruments.general.parent_child import Child, ChildParams, ChannelChild
from lib.instruments.sim900.comm import Sim900ChildDep
from lib.instruments.sim900.deps import Sim900Dep
import time
import numpy as np
from typing import Literal, Any, cast, TypeVar

TChild = TypeVar("TChild", bound=Child[Sim900Dep, Any])


class Sim970Params(ChildParams["Sim970"]):
    """Parameters for SIM970 module.

    Unlike the previous version, individual channel params are no longer
    represented. Channels are automatically materialized inside the Sim970
    instance based on ``num_channels``. Users access channels via
    ``sim970.channels[index]``.
    """

    type: Literal["sim970"] = "sim970"
    slot: int = 0
    num_channels: int = 4
    offline: bool | None = False
    settling_time: float = 0.1
    max_retries: int = 3
    export_name: str = "Sim970"
    channel_export_names: list[str] | None = None

    @property
    def inst(self):  # type: ignore[override]
        return Sim970

    @property
    def parent_class(self) -> str:
        return "lib.instruments.sim900.sim900.Sim900"


class Sim970Channel(VSense):
    """Single SIM970 voltmeter channel implementing the VSense interface.

    Now a lightweight object without its own ChildParams; created internally by
    the parent ``Sim970`` and exposed via ``Sim970.channels``.
    """

    def __init__(
        self, dep: Sim900ChildDep, channel_index: int, settling: float, retries: int
    ):
        self._dep = dep
        self.channel_index = channel_index
        self.settling_time = settling
        self.max_retries = retries
        self.connected = True

    def disconnect(self) -> bool:  # type: ignore[override]
        self.connected = False
        return True

    def get_voltage(self) -> float:  # type: ignore[override]
        return self._get_voltage_impl(0)

    def _get_voltage_impl(self, recurse: int) -> float:
        if getattr(self._dep, "offline", False):  # offline simulation
            return float(np.random.uniform())
        channel_scpi = self.channel_index + 1  # hardware channels are 1-based
        cmd = f"VOLT? {channel_scpi}"
        volts = self._dep.query(cmd)  # type: ignore[attr-defined]
        time.sleep(self.settling_time)
        volts = self._dep.query(cmd)  # type: ignore[attr-defined]
        try:
            return float(volts)
        except ValueError:
            if recurse < self.max_retries:
                return self._get_voltage_impl(recurse + 1)
            raise ValueError(f"Could not parse voltage reading: {volts}")


class Sim970(Child[Sim900Dep, Sim970Params], ChannelChild[Sim970Channel]):
    """SIM970 module representing a 4-channel voltmeter.

    Channels are now exposed via the ``channels`` list and are not Pydantic
    Child objects. The previous API that required ``Sim970ChannelParams`` is
    deprecated.
    """

    def __init__(
        self, dep: Sim900ChildDep, parent_dep: Sim900Dep, params: Sim970Params
    ):
        self._dep = dep
        self._parent_dep = parent_dep
        self.params = params
        self.connected = True
        self.slot = params.slot
        self.channels: list[Sim970Channel] = []
        for i in range(params.num_channels):
            ch_dep = Sim900ChildDep(
                parent_dep.serial, parent_dep.gpibAddr, i, offline=params.offline
            )
            self.channels.append(
                Sim970Channel(ch_dep, i, params.settling_time, params.max_retries)
            )

    @property
    def parent_class(self) -> str:
        return "lib.instruments.sim900.sim900.Sim900"

    @classmethod
    def from_params_with_dep(
        cls, parent_dep: Sim900Dep, key: str, params: ChildParams[Any]
    ) -> "Sim970":
        if not isinstance(params, Sim970Params):
            raise TypeError(
                f"Sim970.from_params_with_dep expected Sim970Params, got {type(params).__name__}"
            )
        comm = Sim900ChildDep(
            parent_dep.serial, parent_dep.gpibAddr, int(key), offline=params.offline
        )
        # Align slot number with key if not explicitly set
        params.slot = int(key)
        return cls(comm, parent_dep, params)

    # ---- Parent API ----
    @property
    def dep(self) -> Sim900Dep:  # type: ignore[override]
        return cast(Sim900Dep, self._dep)

    def disconnect(self) -> bool:
        if not self.connected:
            return True
        for ch in self.channels:
            try:
                ch.disconnect()
            except Exception:
                pass
        self.connected = False
        return True

    def __del__(self):
        if hasattr(self, "connected") and self.connected:
            self.disconnect()

    # Backward compatibility helper: allow get_voltage on module returning ch0
    def get_voltage(self) -> float:  # type: ignore[override]
        if not self.channels:
            raise RuntimeError("No channels initialized")
        return self.channels[0].get_voltage()
