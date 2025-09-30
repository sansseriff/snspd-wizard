from typing import Any, Literal, List, TypeVar, cast

from pydantic import BaseModel, Field

from lib.instruments.dbay.addons.vsense import ChSenseState
from lib.instruments.dbay.addons.vsource import (
    IVsourceAddon,
    VsourceChange,
    SharedVsourceChange,
    ChSourceState,
)
from lib.instruments.dbay.comm import Comm
from lib.instruments.dbay.state import Core
from lib.instruments.general.parent_child import (
    Child,
    ChildParams,
    # ChannelChildParams,
    Parent,
)
from lib.instruments.general.vsource import VSource


# ---------------------- Params & State Models ----------------------

TChild = TypeVar("TChild", bound=Child[Comm, Any])


class Dac16DChannelParams(ChildParams["Dac16DChannel"]):
    resource: str | None = None

    @property
    def inst(self):  # type: ignore[override]
        return Dac16DChannel


class Dac16DParams(ChildParams["Dac16D"]):
    type: Literal["dac16D"] = "dac16D"
    name: str = "Dac16D"
    num_children: int = 16
    children: dict[str, Dac16DChannelParams] = Field(default_factory=dict)

    @property
    def inst(self):  # type: ignore[override]
        return Dac16D

    @property
    def parent_class(self) -> str:
        return "lib.instruments.dbay.dbay.DBay"


class Dac16DState(BaseModel):
    module_type: Literal["dac16D"] = "dac16D"
    core: Core
    vsource: IVsourceAddon
    # Additional state fields specific to 16D
    vsb: ChSourceState
    vr: ChSenseState


# ---------------------------- Channel -----------------------------


class Dac16DChannel(Child[Comm, Dac16DChannelParams], VSource):
    """Individual channel of a Dac16D module that implements the VSource interface."""

    def __init__(
        self,
        comm: Comm,
        module_slot: int,
        channel_index: int,
        channel_data: ChSourceState,
    ):
        self.comm = comm
        self.module_slot = module_slot
        self.channel_index = channel_index
        self.channel_data = channel_data
        self.connected = True

    @property
    def parent_class(self) -> str:
        return "lib.instruments.dbay.dbay.DBay"

    @classmethod
    def from_params_with_dep(
        cls,
        parent_dep: Comm,
        key: str,
        params: ChildParams[Any],
    ) -> "Dac16DChannel":
        # key is channel index within a module; here we require module context,
        # so this factory is not typically used directly. Provide a conservative impl.
        try:
            ch_idx = int(key)
        except ValueError:
            raise TypeError(f"Channel key must be int-like, got {key!r}")
        # Fallback: create a dummy channel with minimal state; callers should prefer
        # Dac16D to materialize channels from server state.
        dummy_state = ChSourceState(
            index=ch_idx,
            bias_voltage=0.0,
            activated=False,
            heading_text="CH",
            measuring=False,
        )
        return cls(parent_dep, -1, ch_idx, dummy_state)

    def disconnect(self) -> bool:  # type: ignore[override]
        """Disconnect this channel by reverting to its original config."""
        if not self.connected:
            return True

        try:
            change = VsourceChange(
                module_index=self.module_slot,
                index=self.channel_index,
                bias_voltage=self.channel_data.bias_voltage,
                activated=self.channel_data.activated,
                heading_text=self.channel_data.heading_text,
                measuring=False,
            )
            self.comm.put("dac16D/vsource/", data=change.model_dump())
            self.connected = False
            return True
        except Exception as e:
            print(f"Error disconnecting dac16D channel {self.channel_index}: {e}")
            return False

    def set_voltage(self, voltage: float) -> bool:  # type: ignore[override]
        """Set voltage for this channel."""
        try:
            change = VsourceChange(
                module_index=self.module_slot,
                index=self.channel_index,
                bias_voltage=voltage,
                activated=self.channel_data.activated,
                heading_text=self.channel_data.heading_text,
                measuring=True,
            )
            self.comm.put("dac16D/vsource/", data=change.model_dump())
            return True
        except Exception as e:
            print(f"Error setting voltage on channel {self.channel_index}: {e}")
            return False

    def turn_on(self) -> bool:  # type: ignore[override]
        """Turn on output for this channel."""
        try:
            change = VsourceChange(
                module_index=self.module_slot,
                index=self.channel_index,
                bias_voltage=self.channel_data.bias_voltage,
                activated=True,
                heading_text=self.channel_data.heading_text,
                measuring=True,
            )
            self.comm.put("dac16D/vsource/", data=change.model_dump())
            return True
        except Exception as e:
            print(f"Error turning on channel {self.channel_index}: {e}")
            return False

    def turn_off(self) -> bool:  # type: ignore[override]
        """Turn off output for this channel."""
        try:
            change = VsourceChange(
                module_index=self.module_slot,
                index=self.channel_index,
                bias_voltage=self.channel_data.bias_voltage,
                activated=False,
                heading_text=self.channel_data.heading_text,
                measuring=True,
            )
            self.comm.put("dac16D/vsource/", data=change.model_dump())
            return True
        except Exception as e:
            print(f"Error turning off channel {self.channel_index}: {e}")
            return False


# ----------------------------- Parent -----------------------------


class Dac16D(Child[Comm, Dac16DParams], Parent[Comm, Dac16DChannelParams]):
    @property
    def parent_class(self) -> str:
        return "lib.instruments.dbay.dbay.DBay"

    def __init__(self, data: dict[str, Any], comm: Comm):
        self.comm = comm
        self.data = Dac16DState(**data)
        # Construct core object from flattened data
        self.core = Core(
            slot=self.data.core.slot, type=self.data.core.type, name=self.data.core.name
        )

        # Parent-side containers
        self.children: dict[str, Child[Comm, Dac16DChannelParams]] = {}
        self.params = Dac16DParams()
        self.params.children = {}
        self.params.num_children = 16

        # Create individual channel objects as children
        for i in range(16):
            ch_params = Dac16DChannelParams()
            self.add_child(ch_params, str(i))

        self.connected = True  # Mark as connected after successful initialization

    # ---- Child API ----
    @classmethod
    def from_params_with_dep(
        cls,
        parent_dep: Comm,
        key: str,
        params: ChildParams[Any],
    ) -> "Dac16D":
        # Fetch current module state from DBay and construct
        try:
            slot = int(key)
        except ValueError:
            raise TypeError(f"Dac16D requires numeric key for slot, got {key!r}")

        full = parent_dep.get("full-state")
        data_list = full.get("data", [])
        module_info = data_list[slot]
        if module_info["core"]["type"] != "dac16D":
            raise ValueError(
                f"Slot {slot} is not dac16D (found {module_info['core']['type']})"
            )
        return cls(module_info, parent_dep)

    # ---- Parent API ----
    @property
    def dep(self) -> Comm:
        return self.comm

    def init_child_by_key(self, key: str) -> "Child[Comm, Dac16DChannelParams]":
        idx = int(key)
        ch = Dac16DChannel(
            self.comm, self.core.slot, idx, self.data.vsource.channels[idx]
        )
        self.children[key] = ch
        return ch

    def init_children(self) -> None:
        for key in list(self.params.children.keys()):
            self.init_child_by_key(key)

    def add_child(self, params: ChildParams[TChild], key: str) -> TChild:
        self.params.children[key] = params  # type: ignore[assignment]
        child_cls = params.inst
        child = child_cls.from_params_with_dep(self.dep, key, params)
        self.children[key] = cast(Child[Comm, Any], child)
        return child

    def disconnect(self) -> bool:
        """Disconnect from the dac16D module by disconnecting all channels."""
        if not self.connected:
            return True

        for ch in self.children.values():  # type: ignore[attr-defined]
            try:
                getattr(ch, "disconnect", lambda: None)()
            except Exception:
                pass

        self.connected = False
        return True

    def __del__(self):
        print("Cleaning up Dac16D instance.")
        if hasattr(self, "connected") and self.connected:
            self.disconnect()

    def __str__(self):
        """Return a pretty string representation of the Dac16D module."""
        slot = self.core.slot
        active_channels = sum(1 for ch in self.data.vsource.channels if ch.activated)
        return f"Dac16D (Slot {slot}): {active_channels}/16 channels active"

    # ---- Multi-channel operations ----
    def voltage_set_shared(
        self, voltage: float, activated: bool = True, channels: List[bool] | None = None
    ) -> bool:
        """Set the same voltage to multiple channels at once and silently update children state."""
        if channels is None:
            channels = [True] * 16
        if len(channels) != 16:
            raise ValueError(f"channels mask must be length 16, got {len(channels)}")

        try:
            change = VsourceChange(
                module_index=self.core.slot,
                index=0,  # Index doesn't matter for shared changes
                bias_voltage=voltage,
                activated=activated,
                heading_text=self.data.vsource.channels[0].heading_text,
                measuring=True,
            )

            shared_change = SharedVsourceChange(change=change, link_enabled=channels)

            self.comm.put("dac16D/vsource_shared/", data=shared_change.model_dump())

            # Silent local state update to keep API consistent with backend action
            for i, linked in enumerate(channels):
                if not linked:
                    continue
                # Update cached module state
                ch_state = self.data.vsource.channels[i]
                ch_state.bias_voltage = voltage
                ch_state.activated = activated
                ch_state.measuring = True
                # Update child object if it exists without triggering backend calls
                child = self.children.get(str(i))
                if isinstance(child, Dac16DChannel):
                    child.channel_data.bias_voltage = voltage
                    child.channel_data.activated = activated
                    child.channel_data.measuring = True

            return True
        except Exception as e:
            print(f"Error setting shared voltage: {e}")
            return False

    def set_vsb(self, voltage: float, activated: bool = True) -> bool:
        """Set VSB voltage on the module."""
        try:
            change = VsourceChange(
                module_index=self.core.slot,
                index=0,
                bias_voltage=voltage,
                activated=activated,
                heading_text="VSB",
                measuring=True,
            )

            self.comm.put("dac16D/vsb/", data=change.model_dump())
            # Optional: cache VSB state locally
            self.data.vsb.bias_voltage = voltage
            self.data.vsb.activated = activated
            self.data.vsb.measuring = True
            return True
        except Exception as e:
            print(f"Error setting VSB voltage: {e}")
            return False
