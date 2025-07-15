from dbay.modules.dac4d import dac4D
from dbay.modules.dac16d import dac16D
from dbay.modules.empty import Empty
from dbay.http import Http
import time
from typing import List, Union

from lib.instruments.general.genericMainframe import GenericMainframe
from lib.instruments.general.submodule import Submodule
from typing import Any


@dataclass
class DBayParams:
    server_address: str = "10.7.0.4"
    port: int = 8345


@dataclass
class ChSourceState:
    index: int
    bias_voltage: float
    activated: bool
    heading_text: str
    measuring: bool


@dataclass
class IVsourceAddon:
    channels: list[ChSourceState]


@dataclass
class Core:
    slot: int
    type: str
    name: str


@dataclass
class dac4DParams:
    core: Core
    vsource: IVsourceAddon


@dataclass
class ChSenseState:
    index: int
    voltage: float
    measuring: bool
    name: str


@dataclass
class dac16DParams:
    core: Core
    vsource: IVsourceAddon
    vsb: ChSourceState
    vr: ChSenseState


class DBay(GenericMainframe):
    def __init__(self, server_address: str, port: int = 8345):
        self.server_address = server_address
        self.port = port
        self.modules: List[Union[dac4D, dac16D, Empty]] = [None] * 8
        self.comm = Http(server_address, port)
        self.load_full_state()

    def load_full_state(self):
        response = self.comm.get("full-state")
        self.instantiate_modules(response["data"])

    def instantiate_modules(self, module_data: list[dict[str, dict[str, Any]]]) -> None:
        for i, module_info in enumerate(module_data):
            module_type = module_info["core"]["type"]
            if module_type == "dac4D":
                self.modules[i] = dac4D(module_info, self.comm)
            elif module_type == "dac16D":
                self.modules[i] = dac16D(module_info, self.comm)
            else:
                self.modules[i] = Empty()

    def create_submodule(self, params: dac4DParams | dac16DParams) -> Submodule:
        slot = params.core.slot
        module_type = params.core.type

        # get handle to already-instantiated module

        return self.modules[slot] if self.modules[slot] else Empty()

    def get_modules(self):
        return self.modules

    def list_modules(self):
        """
        Pretty-print a list of all modules and their basic status.
        """
        print("DBay Modules:")
        print("-------------")
        for i, module in enumerate(self.modules):
            print(f"Slot {i}: {module}")
        print("-------------")
        return self.modules

    # Additional methods to interact with the modules can be added here.
