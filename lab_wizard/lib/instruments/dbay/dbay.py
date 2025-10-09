from typing import Any, Annotated, TypeVar, cast
from pydantic import Field

from lib.instruments.dbay.comm import Comm
from lib.instruments.general.parent_child import (
    Parent,
    ParentParams,
    ParentFactory,
    Child,
    ChildParams,
    CanInstantiate,
)
from lib.instruments.dbay.modules.dac4d import Dac4DParams, Dac4D
from lib.instruments.dbay.modules.dac16d import Dac16DParams, Dac16D
from lib.instruments.dbay.modules.empty import EmptyParams, Empty
from typing import Literal
from lib.instruments.general.computer import ComputerDep
from lib.instruments.general.comm import HttpChannelRequest


# For now, restrict to Dac4D until other modules are migrated to the new generics.
DBayChildParams = Annotated[
    Dac4DParams | Dac16DParams | EmptyParams, Field(discriminator="type")
]


# TypeVar for method-level inference
TChild = TypeVar("TChild", bound=Child[Comm, Any])


class DBayParams(
    ParentParams["DBay", Comm, DBayChildParams],
    ChildParams["DBay"],
    CanInstantiate["DBay"],
):
    """Params for DBay controller.

    Hybrid usage:
      - Top-level (legacy): provide server_address/port (defaults retained) and call .create_inst().
      - As a child of Computer: omit server_address (or leave default) and add via
        computer.add_child(DBayParams(), "host" or "host:port"). The key supplies host (and optional port).
    """

    type: Literal["dbay"] = "dbay"
    server_address: str | None = "10.7.0.4"
    port: int = 8345
    children: dict[str, DBayChildParams] = Field(default_factory=dict)

    @property
    def inst(self):  # type: ignore[override]
        return DBay

    def create_inst(self) -> "DBay":
        return DBay.from_params(self)

    def __call__(self) -> "DBay":  # convenience
        return self.create_inst()


class DBay(
    Parent[Comm, DBayChildParams],
    ParentFactory[DBayParams, "DBay"],
    Child[ComputerDep, Any],
):
    def __init__(
        self, server_address: str, port: int = 8345, params: DBayParams | None = None
    ):
        self.server_address = server_address
        self.port = port
        self.comm = Comm(server_address, port)
        self.children: dict[str, Child[Comm, DBayChildParams]] = {}
        self._module_snapshot: list[Any] | None = None
        if params is not None:
            self.params = params  # type: ignore[attr-defined]

    # Child interface
    @property
    def parent_class(self) -> str:
        return "lib.instruments.general.computer.Computer"

    @property
    def dep(self) -> Comm:
        return self.comm

    def init_child_by_key(self, key: str) -> Child[Comm, Any]:
        params = self.params.children[key]  # type: ignore[attr-defined]
        child_cls = params.inst
        child = child_cls.from_params_with_dep(self.dep, key, params)  # type: ignore[arg-type]
        # Store with broad typing; precise generic variance not critical at runtime here
        self.children[key] = cast(Child[Comm, Any], child)
        return child

    def init_children(self) -> None:
        for key in list(getattr(self.params, "children", {}).keys()):  # type: ignore[attr-defined]
            self.init_child_by_key(key)

    def add_child(
        self,
        params: ChildParams[TChild],
        key: str,
    ) -> TChild:
        # Ensure params container exists
        if not hasattr(self, "params"):
            # Create minimal params holder if not present
            self.params = DBayParams(server_address=self.server_address, port=self.port)
        self.params.children[key] = params  # type: ignore[assignment]
        child_cls = params.inst
        child = child_cls.from_params_with_dep(self.dep, key, params)  # type: ignore[arg-type]
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
                # Normalize minimal test data to required structure
                core = module_info.setdefault("core", {})
                core.setdefault("slot", 0)
                core.setdefault("name", "dac4D-0")
                if "vsource" not in module_info:
                    module_info["vsource"] = {"channels": []}
                channels = module_info["vsource"].setdefault("channels", [])
                if not channels:
                    for i in range(4):
                        channels.append(
                            {
                                "index": i,
                                "bias_voltage": 0.0,
                                "activated": False,
                                "heading_text": f"CH{i}",
                                "measuring": False,
                            }
                        )
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
        if params.server_address is None:
            raise ValueError(
                "server_address must be provided for top-level DBay instantiation"
            )
        inst = cls(params.server_address, params.port, params)
        inst.init_children()
        return inst

    @classmethod
    def from_params_with_dep(
        cls,
        parent_dep: ComputerDep,
        key: str,
        params: DBayParams,
    ) -> "DBay":
        # Key can be host or host:port
        host = key
        port = params.port
        if ":" in key:
            host_part, port_part = key.rsplit(":", 1)
            host = host_part
            try:
                port = int(port_part)
            except ValueError:  # keep params.port if parse fails
                pass
        # Channel request for caching (not yet wired into Comm operations)
        req = HttpChannelRequest(host=host, port=port)

        # Based on the internal configuration of paretn_dep, this may return a direct channel (control the local computer)
        # or it may return a remote channel proxy (for controlling a remote computer over network).
        parent_dep.get_channel(req)
        # Ensure params reflect actual runtime host/port (helpful for debugging / serialization)
        params.server_address = host
        params.port = port
        inst = cls(host, port, params)
        inst.init_children()
        return inst
