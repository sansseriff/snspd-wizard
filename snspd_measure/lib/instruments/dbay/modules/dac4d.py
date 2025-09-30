from lib.instruments.dbay.comm import Comm
from lib.instruments.dbay.addons.vsource import VsourceChange, ChSourceState
from lib.instruments.dbay.state import Core
from typing import Literal, cast
from lib.instruments.dbay.addons.vsource import IVsourceAddon
from lib.instruments.general.parent_child import (
    Child,
    ChildParams,
    # ChannelChildParams,
    Parent,
)
from lib.instruments.general.vsource import VSource
from pydantic import BaseModel
from typing import Any
from typing import Any, TypeVar
from pydantic import Field

# TypeVar for method-level inference
TChild = TypeVar("TChild", bound=Child[Comm, Any])


class Dac4DChannelParams(ChildParams["Dac4DChannel"]):
    type: Literal["dac4D_channel"] = "dac4D_channel"
    resource: str | None = None

    @property
    def inst(self):  # type: ignore[override]
        return Dac4DChannel


"""
Dac4DParams and Dac4DState are similar. Dac4DState is used to specify the full state of 
the module, while Dac4DParams is used to store the 'path' to any particular channels in use. 


If a channel is to be used in an experiment, Dac4DParams will be given a key/value pair
in the children dict, and the Dac4DChannelParams class will be given a resource string
"""


class Dac4DParams(ChildParams["Dac4D"]):
    type: Literal["dac4D"] = "dac4D"
    name: str = "Dac4D"
    num_children: int = 4
    children: dict[str, Dac4DChannelParams] = Field(default_factory=dict)

    @property
    def inst(self):  # type: ignore[override]
        return Dac4D

    @property
    def parent_class(self) -> str:
        return "lib.instruments.dbay.dbay.DBay"


class Dac4DState(BaseModel):
    module_type: Literal["dac4D"] = "dac4D"
    core: Core
    vsource: IVsourceAddon


# TypeVar for method-level inference
TChild = TypeVar("TChild", bound=Child[Comm, Any])


class Dac4DChannel(Child[Comm, Dac4DChannelParams], VSource):
    """Individual channel of a Dac4D module that implements the VSource interface."""

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
    ) -> "Dac4DChannel":
        # key is channel index within a module; here we require module context,
        # so this factory is not typically used directly. Provide a conservative impl.
        try:
            ch_idx = int(key)
        except ValueError:
            raise TypeError(f"Channel key must be int-like, got {key!r}")
        # Fallback: create a dummy channel with minimal state; callers should prefer
        # Dac4D to materialize channels from server state.
        dummy_state = ChSourceState(
            index=ch_idx,
            bias_voltage=0.0,
            activated=False,
            heading_text="CH",
            measuring=False,
        )
        return cls(parent_dep, -1, ch_idx, dummy_state)

    def disconnect(self) -> bool:
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
            self.comm.put("dac4D/vsource/", data=change.model_dump())
            self.connected = False
            return True
        except Exception as e:
            print(f"Error disconnecting dac4D channel {self.channel_index}: {e}")
            return False

    def set_voltage(self, voltage: float) -> bool:
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
            self.comm.put("dac4D/vsource/", data=change.model_dump())
            return True
        except Exception as e:
            print(f"Error setting voltage on channel {self.channel_index}: {e}")
            return False

    def turn_on(self) -> bool:
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
            self.comm.put("dac4D/vsource/", data=change.model_dump())
            return True
        except Exception as e:
            print(f"Error turning on channel {self.channel_index}: {e}")
            return False

    def turn_off(self) -> bool:
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
            self.comm.put("dac4D/vsource/", data=change.model_dump())
            return True
        except Exception as e:
            print(f"Error turning off channel {self.channel_index}: {e}")
            return False


class Dac4D(Child[Comm, Dac4DParams], Parent[Comm, Dac4DChannelParams]):
    @property
    def parent_class(self) -> str:
        return "lib.instruments.dbay.dbay.DBay"

    def __init__(self, data: dict[str, Any], comm: Comm):
        self.comm = comm
        self.data = Dac4DState(**data)
        # Construct core object from flattened data
        self.core = Core(
            slot=self.data.core.slot, type=self.data.core.type, name=self.data.core.name
        )

        # Parent-side containers
        self.children: dict[str, Child[Comm, Dac4DChannelParams]] = {}
        self.params = Dac4DParams()
        self.params.children = {}
        self.params.num_children = 4

        # Create individual channel objects as children
        for i in range(4):
            ch_params = Dac4DChannelParams()
            self.add_child(ch_params, str(i))

        self.connected = True  # Mark as connected after successful initialization

    # ---- Child API ----
    @classmethod
    def from_params_with_dep(
        cls,
        parent_dep: Comm,
        key: str,
        params: ChildParams[Any],
    ) -> "Dac4D":
        # Fetch current module state from DBay and construct
        try:
            slot = int(key)
        except ValueError:
            raise TypeError(f"Dac4D requires numeric key for slot, got {key!r}")

        full = parent_dep.get("full-state")
        data_list = full.get("data", [])
        module_info = data_list[slot]
        if module_info["core"]["type"] != "dac4D":
            raise ValueError(
                f"Slot {slot} is not dac4D (found {module_info['core']['type']})"
            )
        return cls(module_info, parent_dep)

    # ---- Parent API ----
    @property
    def dep(self) -> Comm:
        return self.comm

    def init_child_by_key(self, key: str) -> "Child[Comm, Dac4DChannelParams]":
        idx = int(key)
        ch = Dac4DChannel(
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
        """Disconnect from the dac4D module by disconnecting all channels."""
        if not self.connected:
            return True

        for ch in self.children.values():  # type: ignore[attr-defined]
            try:
                # ch is a Child[Comm, Dac4DChannelParams], but actual instance has disconnect
                getattr(ch, "disconnect", lambda: None)()
            except Exception:
                pass

        self.connected = False
        return True

    def __del__(self):
        print("Cleaning up Dac4D instance.")
        if hasattr(self, "connected") and self.connected:
            self.disconnect()

    def __str__(self):
        """Return a pretty string representation of the Dac4D module."""
        slot = self.core.slot
        active_channels = sum(1 for ch in self.data.vsource.channels if ch.activated)
        return f"Dac4D (Slot {slot}): {active_channels}/4 channels active"
