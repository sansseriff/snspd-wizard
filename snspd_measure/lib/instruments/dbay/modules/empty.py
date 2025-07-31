from lib.instruments.general.child import Child, ChildParams
from lib.instruments.dbay.state import Core
from typing import Literal


class EmptyParams(ChildParams):
    type: Literal["empty"] = "empty"
    slot: int
    name: str


class Empty(Child[EmptyParams]):
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
    def parent_class(self) -> str:
        return "lib.instruments.dbay.dbay.DBay"
