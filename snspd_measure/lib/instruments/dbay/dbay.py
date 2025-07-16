from lib.instruments.dbay.modules.dac4d import dac4D
from lib.instruments.dbay.modules.dac16d import dac16D
from lib.instruments.dbay.modules.empty import Empty
from lib.instruments.dbay.comm import Comm

from typing import List, Union

from lib.instruments.general.genericMainframe import GenericMainframe
from lib.instruments.general.submodule import Submodule, SubmoduleParams
from typing import Any
from dataclasses import dataclass


@dataclass
class DBayParams:
    server_address: str = "10.7.0.4"
    port: int = 8345


class DBay(GenericMainframe):
    def __init__(self, server_address: str, port: int = 8345):
        self.server_address = server_address
        self.port = port
        self.modules: List[Union[dac4D, dac16D, Empty]] = [Empty() for _ in range(16)]
        self.comm = Comm(server_address, port)
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

    def create_submodule(self, params: SubmoduleParams) -> Submodule:
        #
        slot = params.slot
        module_type = params.type

        # slot = params.core.slot
        # module_type = params.core.type

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
