from lib.instruments.dbay.comm import Comm
from lib.instruments.dbay.addons.vsource import VsourceChange, ChSourceState
from lib.instruments.dbay.state import Core
from typing import Literal
from lib.instruments.dbay.addons.vsource import IVsourceAddon
from lib.instruments.general.child import (
    Child,
    ChildParams,
    ChannelChildParams,
)
from lib.instruments.general.parent import Parent
from lib.instruments.general.vsource import VSource
from pydantic import BaseModel
from typing import Any


class Dac4DChannelParams(ChildParams):
    resource: str | None = None


"""
Dac4DParams and Dac4DState are similar. Dac4DState is used to specify the full state of 
the module, while Dac4DParams is used to store the 'path' to any particular channels in use. 


If a channel is to be used in an experiment, Dac4DParams will be given a key/value pair
in the channels dict, and the Dac4DChannelParams class will be given a resource string
"""


class Dac4DParams(ChannelChildParams):
    type: Literal["dac4D"] = "dac4D"
    name: str = "Dac4D"
    channels: dict[str, Dac4DChannelParams] = {}

    @property
    def parent_class(self) -> str:
        return "lib.instruments.dbay.dbay.DBay"


class Dac4DState(BaseModel):
    module_type: Literal["dac4D"] = "dac4D"
    core: Core
    vsource: IVsourceAddon


class Dac4DChannel(Child[Dac4DChannelParams], VSource):
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


class Dac4D(Child[Dac4DParams], Parent):
    @property
    def parent_class(self) -> str:
        return "lib.instruments.dbay.dbay.DBay"

    def __init__(self, data: dict[str, Any], comm: Comm):
        super().__init__()
        self.comm = comm
        self.data = Dac4DState(**data)
        # Construct core object from flattened data
        self.core = Core(
            slot=self.data.core.slot, type=self.data.core.type, name=self.data.core.name
        )

        # Create individual channel objects
        self.channels = [
            Dac4DChannel(comm, self.core.slot, i, self.data.vsource.channels[i])
            for i in range(4)
        ]

        self.connected = True  # Mark as connected after successful initialization

    def disconnect(self) -> bool:
        """Disconnect from the dac4D module by disconnecting all channels."""
        if not self.connected:
            return True

        for channel in self.channels:
            channel.disconnect()

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
