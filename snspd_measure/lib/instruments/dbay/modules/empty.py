from lib.instruments.general.submodule import Submodule, SubmoduleParams
from lib.instruments.dbay.state import Core
from typing import Literal


class EmptyParams(SubmoduleParams):
    type: Literal["empty"] = "empty"
    slot: int
    name: str


class Empty(Submodule[EmptyParams]):
    def __init__(self, data: dict = None):
        """Initialize an empty module."""
        if data:
            self.data = EmptyParams(**data)
            # Construct core object from flattened data
            self.core = Core(
                slot=self.data.slot, type=self.data.type, name=self.data.name
            )

    def __str__(self):
        """Return a pretty string representation of the Empty module."""
        return "Empty slot"

    @property
    def mainframe_class(self) -> str:
        return "lib.instruments.dbay.dbay.DBay"
