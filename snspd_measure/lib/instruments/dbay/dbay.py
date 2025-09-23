from typing import Any, Annotated, TypeVar, cast
from pydantic import Field

from lib.instruments.dbay.comm import Comm
from lib.instruments.general.parent_child import Parent, ParentParams, Child, ChildParams
from lib.instruments.dbay.modules.dac4d import Dac4DParams, Dac4D
from lib.instruments.dbay.modules.dac16d import Dac16DParams, Dac16D
from lib.instruments.dbay.modules.empty import EmptyParams, Empty

# TypeVar for method-level inference
TChild = TypeVar("TChild", bound=Child[Comm, Any])

# For now, restrict to Dac4D until other modules are migrated to the new generics.
DBayChildParams = Annotated[Dac4DParams, Dac16DParams, EmptyParams, Field(discriminator="type")]


class DBay(Parent[Comm, DBayChildParams]):
    def __init__(self, server_address: str, port: int = 8345):
        self.server_address = server_address
        self.port = port
        self.comm = Comm(server_address, port)
        self.children: dict[str, Child[Comm, DBayChildParams]] = {}
        # For convenience keep a snapshot list like before (built on demand)
        self._module_snapshot: list[Any] | None = None

    @property
    def dep(self) -> Comm:
        return self.comm

    def init_child_by_key(self, key: str) -> Child[Comm, DBayChildParams]:
        params = self.params.children[key]  # type: ignore[attr-defined]
        child_cls = params.inst
        child = child_cls.from_params_with_dep(self.dep, key, params)
        self.children[key] = child
        return child

    def init_children(self) -> None:
        for key in list(getattr(self.params, "children", {}).keys()):  # type: ignore[attr-defined]
            self.init_child_by_key(key)

    def add_child(self, key: str, params: ChildParams[TChild]) -> TChild:
        # Ensure params container exists
        if not hasattr(self, "params"):
            # Create minimal params holder if not present
            self.params = DBayParams(server_address=self.server_address, port=self.port)
        self.params.children[key] = params  # type: ignore[assignment]
        child_cls = params.inst
        child = child_cls.from_params_with_dep(self.dep, key, params)
        self.children[key] = cast(Child[Comm, Any], child)
        return child

    # Back-compat helpers
    def load_full_state(self) -> None:
        response = self.comm.get("full-state")
        data: list[dict[str, dict[str, Any]]] = response.get("data", [])
        # Make a simple snapshot list so previous callers can list modules
        snapshot: list[Any] = []
        for module_info in data:
            t = module_info.get("core", {}).get("type")
            if t == "dac4D":
                snapshot.append(Dac4D(module_info, self.comm))
            elif t == "dac16D":
                snapshot.append(Dac16D(module_info, self.comm))
            else:
                snapshot.append(Empty())
        self._module_snapshot = snapshot

    def get_modules(self):
        if self._module_snapshot is None:
            self.load_full_state()
        return self._module_snapshot

    def list_modules(self):
        modules = self.get_modules() or []
        print("DBay Modules:")
        print("-------------")
        for i, module in enumerate(modules):
            print(f"Slot {i}: {module}")
        print("-------------")
        return modules
    
    @classmethod
    def from_params(cls, params: "DBayParams") -> "DBay":
        inst = cls(params.server_address, params.port)
        inst.params = params  # type: ignore[attr-defined]
        inst.init_children()
        return inst


class DBayParams(ParentParams["DBay", Comm, DBayChildParams]):
    server_address: str = "10.7.0.4"
    port: int = 8345
    # Use children dict keyed by slot strings, like "0".."15"
    children: dict[str, DBayChildParams] = {}

    @property
    def inst(self):  # type: ignore[override]
        return DBay

    def create_inst(self) -> "DBay":
        return DBay.from_params(self)
