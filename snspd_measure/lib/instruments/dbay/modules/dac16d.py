from lib.instruments.dbay.addons.vsource import VsourceChange, SharedVsourceChange
from lib.instruments.dbay.state import Core
from typing import Literal, List
from lib.instruments.dbay.addons.vsource import IVsourceAddon, ChSourceState
from lib.instruments.dbay.addons.vsense import ChSenseState

from lib.instruments.general.child import Child, ChildParams
from lib.instruments.dbay.comm import Comm
from typing import Any

from lib.instruments.general.vsource import VSource


class Dac16DParams(ChildParams):
    type: Literal["dac16D"] = "dac16D"
    slot: int
    name: str
    vsource: IVsourceAddon
    vsb: ChSourceState
    vr: ChSenseState


class Dac16DChannel(VSource):
    """Individual channel of a Dac16D module that implements the VSource interface."""

    def __init__(
        self,
        comm: Comm,
        module_slot: int,
        channel_index: int,
        channel_data: ChSourceState,
    ):
        super().__init__()
        self.comm = comm
        self.module_slot = module_slot
        self.channel_index = channel_index
        self.channel_data = channel_data
        self.connected = True

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
            self.comm.put("dac16D/vsource/", data=change.model_dump())
            self.connected = False
            return True
        except Exception as e:
            print(f"Error disconnecting dac16D channel {self.channel_index}: {e}")
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
            self.comm.put("dac16D/vsource/", data=change.model_dump())
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
            self.comm.put("dac16D/vsource/", data=change.model_dump())
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
            self.comm.put("dac16D/vsource/", data=change.model_dump())
            return True
        except Exception as e:
            print(f"Error turning off channel {self.channel_index}: {e}")
            return False


class Dac16D(Child[Dac16DParams]):
    def __init__(self, data: Any, comm: Comm):
        super().__init__()
        self.comm = comm
        self.data = Dac16DParams(**data)
        # Construct core object from flattened data
        self.core = Core(slot=self.data.slot, type=self.data.type, name=self.data.name)

        # Create individual channel objects
        self.channels = [
            Dac16DChannel(comm, self.core.slot, i, self.data.vsource.channels[i])
            for i in range(16)
        ]

        self.connected = True  # Mark as connected after successful initialization

    @property
    def parent_class(self) -> str:
        return "lib.instruments.dbay.dbay.DBay"

    def disconnect(self) -> bool:
        """Disconnect from the dac16D module by disconnecting all channels."""
        if not self.connected:
            return True

        for channel in self.channels:
            channel.disconnect()

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

    def voltage_set_shared(
        self, voltage: float, activated: bool = True, channels: List[bool] | None = None
    ) -> bool:
        """
        Set same voltage to multiple channels at once
        """
        if channels is None:
            # Default to all channels
            channels = [True] * 16

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
            return True
        except Exception as e:
            print(f"Error setting shared voltage: {e}")
            return False

    def set_vsb(self, voltage: float, activated: bool = True) -> bool:
        """
        Set VSB voltage
        """
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
            return True
        except Exception as e:
            print(f"Error setting VSB voltage: {e}")
            return False
