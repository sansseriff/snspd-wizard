from lib.instruments.dbay.comm import Comm
from lib.instruments.dbay.addons.vsource import VsourceChange, ChSourceState
from lib.instruments.dbay.state import Core
from typing import Literal
from lib.instruments.dbay.addons.vsource import IVsourceAddon
from typing import Union
from lib.instruments.general.submodule import Submodule, SubmoduleParams
from snspd_measure.lib.instruments.general.vsource import VSource

from typing import Any


class Dac4DParams(SubmoduleParams):
    type: Literal["dac4D"] = "dac4D"
    slot: int
    name: str
    vsource: IVsourceAddon


class Dac4DChannel(VSource):
    """Individual channel of a Dac4D module that implements the VSource interface."""

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


class Dac4D(Submodule[Dac4DParams]):
    @property
    def mainframe_class(self) -> str:
        return "lib.instruments.dbay.dbay.DBay"

    def __init__(self, data: dict[str, Any], comm: Comm):
        super().__init__()
        self.comm = comm
        self.data = Dac4DParams(**data)
        # Construct core object from flattened data
        self.core = Core(slot=self.data.slot, type=self.data.type, name=self.data.name)

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
