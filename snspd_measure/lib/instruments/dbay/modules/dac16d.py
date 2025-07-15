from snspd_measure.lib.instruments.dbay.comm import Http
from dbay.addons.vsource import VsourceChange, SharedVsourceChange
from dbay.state import IModule, Core
from typing import Literal, Union, List
from dbay.addons.vsource import IVsourceAddon, ChSourceState
from dbay.addons.vsense import ChSenseState

from lib.instruments.general.submodule import Submodule
from lib.instruments.dbay.dbay import DBay
from lib.instruments.dbay.comm import Comm

from dataclasses import dataclass


class dac16D_spec(IModule):
    module_type: Literal["dac16D"] = "dac16D"
    core: Core
    vsource: IVsourceAddon
    vsb: dict  # Assuming vsb structure from backend
    vr: dict  # Assuming vr structure from backend


@dataclass
class dac16DParams:
    core: Core
    vsource: IVsourceAddon
    vsb: ChSourceState
    vr: ChSenseState


class dac16D(Submodule):
    def __init__(self, data, comm: Comm):
        self.comm = comm
        self.data = dac16D_spec(**data)

    @property
    def mainframe_class(self) -> type[DBay]:
        return DBay

    def __del__(self):
        print("Cleaning up dac16D instance.")

        # Reverting to previous config
        for idx in range(16):
            change = VsourceChange(
                module_index=self.data.core.slot,
                index=idx,
                bias_voltage=self.data.vsource.channels[idx].bias_voltage,
                activated=self.data.vsource.channels[idx].activated,
                heading_text=self.data.vsource.channels[idx].heading_text,
                measuring=False,
            )

            self.comm.put("dac16D/vsource/", data=change.model_dump())

    def __str__(self):
        """Return a pretty string representation of the dac16D module."""
        slot = self.data.core.slot
        active_channels = sum(1 for ch in self.data.vsource.channels if ch.activated)
        return f"dac16D (Slot {slot}): {active_channels}/16 channels active"

    def voltage_set(
        self, index: int, voltage: float, activated: Union[bool, None] = None
    ):
        if activated is None:
            activated = self.data.vsource.channels[index].activated
        change = VsourceChange(
            module_index=self.data.core.slot,
            index=index,
            bias_voltage=voltage,
            activated=activated,
            heading_text=self.data.vsource.channels[index].heading_text,
            measuring=True,
        )

        self.comm.put("dac16D/vsource/", data=change.model_dump())

    def voltage_set_shared(
        self, voltage: float, activated: bool = True, channels: List[bool] | None = None
    ):
        """
        Set same voltage to multiple channels at once
        """
        if channels is None:
            # Default to all channels
            channels = [True] * 16

        change = VsourceChange(
            module_index=self.data.core.slot,
            index=0,  # Index doesn't matter for shared changes
            bias_voltage=voltage,
            activated=activated,
            heading_text=self.data.vsource.channels[0].heading_text,
            measuring=True,
        )

        shared_change = SharedVsourceChange(change=change, link_enabled=channels)

        self.comm.put("dac16D/vsource_shared/", data=shared_change.model_dump())

    def set_vsb(self, voltage: float, activated: bool = True):
        """
        Set VSB voltage
        """
        change = VsourceChange(
            module_index=self.data.core.slot,
            index=0,
            bias_voltage=voltage,
            activated=activated,
            heading_text="VSB",
            measuring=True,
        )

        self.comm.put("dac16D/vsb/", data=change.model_dump())
