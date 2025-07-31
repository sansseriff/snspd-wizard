from lib.instruments.dbay.comm import Comm
from typing import List
from lib.instruments.general.parent import Parent, ParentParams
from typing import Any, Annotated, Union
from pydantic import Field

from lib.instruments.dbay.modules.dac4d import Dac4DParams, Dac4D
from lib.instruments.dbay.modules.dac16d import Dac16DParams, Dac16D
from lib.instruments.dbay.modules.empty import Empty, EmptyParams

DBayChildParams = Annotated[
    Dac4DParams | Dac16DParams | EmptyParams, Field(discriminator="type")
]


class DBayParams(ParentParams[DBayChildParams]):
    server_address: str = "10.7.0.4"
    port: int = 8345
    num_modules: int = 4
    modules: dict[str, DBayChildParams] = {}

    def promote(self) -> "DBay":
        """
        Promote the parameters to a DBay instance.
        :return: An instance of DBay
        """
        return DBay.from_params(self)


class DBay(Parent[DBayParams]):
    def __init__(self, server_address: str, port: int = 8345):
        self.server_address = server_address
        self.port = port
        self.modules: List[Dac4D | Dac16D | Empty] = [Empty() for _ in range(16)]
        self.comm = Comm(server_address, port)
        self.load_full_state()

    def load_full_state(self):
        response = self.comm.get("full-state")
        self.instantiate_modules(response["data"])

    def instantiate_modules(self, module_data: list[dict[str, dict[str, Any]]]) -> None:
        for i, module_info in enumerate(module_data):
            module_type = module_info["core"]["type"]
            if module_type == "dac4D":
                self.modules[i] = Dac4D(module_info, self.comm)
            elif module_type == "dac16D":
                self.modules[i] = Dac16D(module_info, self.comm)
            else:
                self.modules[i] = Empty()

    @classmethod
    def from_params(cls, params: DBayParams) -> "DBay":
        """
        Create a DBay instance from parameters
        :param params: Parameters for the DBay mainframe
        :return: An instance of DBay
        """
        return cls(server_address=params.server_address, port=params.port)

    def create_submodule(self, params: DBayChildParams) -> Union[Dac4D, Dac16D, Empty]:
        slot = params.slot

        # modules should already be instantiated. Return an existing one
        # other classes that use create_submodule might init the submodule here

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
