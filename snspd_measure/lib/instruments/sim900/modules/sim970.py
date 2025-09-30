from __future__ import annotations
from lib.instruments.general.vsense import VSense
from lib.instruments.general.parent_child import Child, ChildParams, Parent
from lib.instruments.sim900.comm import Sim900ChildDep
from lib.instruments.sim900.deps import Sim900Dep
import time
import numpy as np
from typing import Literal, Any, cast, TypeVar

TChild = TypeVar("TChild", bound=Child[Sim900Dep, Any])


class Sim970ChannelParams(ChildParams["Sim970Channel"]):
    """Lightweight params for an individual SIM970 channel child.

    No per-channel configuration is currently required; channel index is derived
    from the key used in the parent's children dict. Shared timing / retry
    configuration lives on the parent `Sim970Params`.
    """

    type: Literal["sim970_channel"] = "sim970_channel"

    @property
    def inst(self):  # type: ignore[override]
        return Sim970Channel


class Sim970Params(ChildParams["Sim970"]):
    """Parameters for SIM970 module (parent of 4 channel children).

    Shared configuration (settling_time, max_retries, offline) applies to all
    channel children.
    """

    type: Literal["sim970"] = "sim970"
    slot: int = 0
    num_children: int = 4
    children: dict[str, Any] = {}
    offline: bool | None = False
    settling_time: float = 0.1
    max_retries: int = 3

    @property
    def inst(self):  # type: ignore[override]
        return Sim970

    @property
    def parent_class(self) -> str:
        return "lib.instruments.sim900.sim900.Sim900"


class Sim970Channel(Child[Sim900Dep, Sim970ChannelParams], VSense):
    """Single SIM970 voltmeter channel implementing the VSense interface."""

    def __init__(
        self,
        dep: Sim900ChildDep,
        params: Sim970ChannelParams,
        channel_index: int,
        settling_time: float,
        max_retries: int,
    ):
        self._dep = dep
        self.params = params
        self.connected = True
        self.channel_index = channel_index  # 0-based

    @property
    def parent_class(self) -> str:
        return "lib.instruments.sim900.modules.sim970.Sim970"

    @classmethod
    def from_params_with_dep(
        cls, parent_dep: Sim900Dep, key: str, params: ChildParams[Any]
    ) -> "Sim970Channel":
        # This path should normally be exercised via Sim970.add_child which
        # supplies parent-wide timing settings. Provide a minimal fallback using
        # default Sim970Params values if misused directly.
        if not isinstance(params, Sim970ChannelParams):
            raise TypeError(
                f"Sim970Channel.from_params_with_dep expected Sim970ChannelParams, got {type(params).__name__}"
            )
        ch_idx = int(key)
        comm = Sim900ChildDep(parent_dep.serial, parent_dep.gpibAddr, ch_idx)
        # Fallback defaults
        return cls(comm, params, ch_idx, 0.1, 3)

    def disconnect(self) -> bool:
        self.connected = False
        return True

    def get_voltage(self) -> float:
        return self._get_voltage_impl(0)

    def _get_voltage_impl(self, recurse: int) -> float:
        if self._dep.offline:  # type: ignore[attr-defined]
            return float(np.random.uniform())

        # SIM970 channels are 1-4 in SCPI, our channel_index is 0-3
        channel_scpi = self.channel_index + 1
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


class Sim970(Child[Sim900Dep, Sim970Params], Parent[Sim900Dep, Sim970ChannelParams]):
    """SIM970 module (parent) containing 4 channel children.

    Each physical voltmeter input (1-4) is represented as a `Sim970Channel` child
    that implements the single-channel `VSense` interface. Code that previously
    instantiated a single `Sim970` and called `get_voltage(channel=...)` should
    instead acquire the appropriate channel child and call `get_voltage()` on
    that child.

    Backward compatibility: calling `get_voltage()` on the parent returns the
    reading from channel 0 (first channel) to minimize breakage while code is
    migrated.
    """

    def __init__(
        self, dep: Sim900ChildDep, parent_dep: Sim900Dep, params: Sim970Params
    ):
        self._dep = dep  # slot-scoped comm wrapper
        self._parent_dep = (
            parent_dep  # mainframe-level dependency for spawning channel comms
        )
        self.params = params
        self.connected = True
        self.slot = params.slot
        self.children: dict[str, Child[Sim900Dep, Sim970ChannelParams]] = {}
        # Initialize channels defined by params, or all by default
        if not params.children:
            for i in range(params.num_children):
                self.add_child(Sim970ChannelParams(), str(i))
        else:
            self.init_children()

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
        return cast(Sim900Dep, self._dep)  # type: ignore[return-value]

    def init_child_by_key(self, key: str) -> Child[Sim900Dep, Sim970ChannelParams]:
        params = cast(Sim970ChannelParams, self.params.children[key])  # type: ignore[index]
        child_cls = params.inst
        child = child_cls.from_params_with_dep(self.dep, key, params)
        self.children[key] = child
        return child

    def init_children(self) -> None:
        for key in list(self.params.children.keys()):
            self.init_child_by_key(key)

    def add_child(self, params: ChildParams[TChild], key: str) -> TChild:  # type: ignore[override]
        # Persist params object
        # Ensure correct param type
        if not isinstance(params, Sim970ChannelParams):
            raise TypeError(
                "Sim970.add_child expects Sim970ChannelParams for channel children"
            )
        self.params.children[key] = params
        # Derive channel index from key
        ch_idx = int(key)
        # Create comm for this channel using parent dependency (slot = module slot communicated via _dep)
        comm = Sim900ChildDep(
            self._parent_dep.serial,
            self._parent_dep.gpibAddr,
            ch_idx,
            offline=self.params.offline,
        )
        # Instantiate channel with shared timing config
        channel = Sim970Channel(
            comm,
            params,
            ch_idx,
            self.params.settling_time,
            self.params.max_retries,
        )
        self.children[key] = cast(Child[Sim900Dep, Any], channel)
        return channel  # type: ignore[return-value]

    def disconnect(self) -> bool:
        if not self.connected:
            return True
        for ch in self.children.values():
            try:
                getattr(ch, "disconnect", lambda: None)()
            except Exception:
                pass
        self.connected = False
        return True

    def __del__(self):
        if hasattr(self, "connected") and self.connected:
            self.disconnect()

    # Backward compatibility helper: allow get_voltage on module returning ch0
    def get_voltage(self) -> float:  # type: ignore[override]
        ch0 = self.children.get("0")
        if ch0 is None:
            raise RuntimeError("Channel 0 not initialized")
        return cast(Sim970Channel, ch0).get_voltage()
