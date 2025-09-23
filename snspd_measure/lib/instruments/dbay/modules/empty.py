from typing import Literal, Any

from lib.instruments.dbay.state import Core
from lib.instruments.general.parent_child import Child, ChildParams
from lib.instruments.dbay.comm import Comm


class EmptyParams(ChildParams["Empty"]):
    type: Literal["empty"] = "empty"
    slot: int
    name: str

    @property
    def inst(self):  # type: ignore[override]
        return Empty


class Empty(Child[Comm, EmptyParams]):
    def __init__(self, data: dict[str, Any] | None = None):
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

    @classmethod
    def from_params_with_dep(
        cls,
        parent_dep: Comm,
        key: str,
        params: EmptyParams,
    ) -> "Empty":
        # There is no real hardware behavior; return a simple placeholder instance
        return cls()
