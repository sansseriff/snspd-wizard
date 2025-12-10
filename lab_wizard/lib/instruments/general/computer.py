from __future__ import annotations

"""Computer root parent providing channel allocation.

Minimal local-only implementation; remote mode scaffolding included.
"""
from typing import Any, Dict, Literal, TypeVar, cast, overload
from pydantic import Field

from lab_wizard.lib.instruments.general.parent_child import (
    Parent,
    ParentParams,
    ParentFactory,
    Child,
    ChildParams,
    Dependency,
)
from lab_wizard.lib.instruments.general.comm import (
    SerialChannelRequest,
    VisaChannelRequest,
    HttpChannelRequest,
    DummyChannelRequest,
)
from lab_wizard.lib.instruments.general.serial import LocalSerialDep, RemoteSerialDep, SerialDep
from lab_wizard.lib.instruments.general.visa import LocalVisaDep, RemoteVisaDep, VisaDep
from lab_wizard.lib.instruments.general.http_dep import LocalHttpDep, RemoteHttpDep, HttpDep
from lab_wizard.lib.instruments.general.dummy_dep import LocalDummyDep, RemoteDummyDep, DummyDep

# Type variables
TChild = TypeVar("TChild", bound=Child[Any, Any])

ChannelRequest = (
    SerialChannelRequest | VisaChannelRequest | HttpChannelRequest | DummyChannelRequest
)


class ComputerParams(ParentParams["Computer", "ComputerDep", ChildParams[Any]]):  # type: ignore[type-arg]
    type: Literal["computer"] = "computer"
    mode: Literal["local", "remote"] = "local"
    server_uri: str | None = None
    children: dict[str, ChildParams[Any]] = Field(default_factory=dict)  # type: ignore[assignment]

    @property
    def inst(self):  # type: ignore[override]
        return Computer

    # convenience for symmetry with other Params types
    def create_inst(self) -> "Computer":
        return Computer.from_params(self)

    def __call__(self) -> "Computer":  # pragma: no cover simple convenience
        return self.create_inst()


class ComputerDep(Dependency):
    def __init__(self, params: ComputerParams):
        self.params = params
        self._channels: Dict[str, Any] = {}

    @overload
    def get_channel(self, req: SerialChannelRequest) -> SerialDep: ...

    @overload
    def get_channel(self, req: VisaChannelRequest) -> VisaDep: ...

    @overload
    def get_channel(self, req: HttpChannelRequest) -> HttpDep: ...

    @overload
    def get_channel(self, req: DummyChannelRequest) -> DummyDep: ...

    def get_channel(self, req: ChannelRequest):
        descriptor = req.descriptor()
        if descriptor in self._channels:
            return self._channels[descriptor]

        remote = self.params.mode == "remote" and self.params.server_uri is not None
        if isinstance(req, SerialChannelRequest):
            if remote:
                # ask broker for typed URI
                uri = self._broker_get_uri("serial", descriptor)
                dep = RemoteSerialDep(uri)
            else:
                dep = LocalSerialDep(req.port, req.baudrate, float(req.timeout))
        elif isinstance(req, VisaChannelRequest):
            if remote:
                uri = self._broker_get_uri("visa", descriptor)
                dep = RemoteVisaDep(uri)
            else:
                dep = LocalVisaDep(req.resource, float(req.timeout))
        elif isinstance(req, HttpChannelRequest):
            if remote:
                uri = self._broker_get_uri("http", descriptor)
                dep = RemoteHttpDep(uri)
            else:
                dep = LocalHttpDep(req.descriptor())
        elif isinstance(req, DummyChannelRequest):
            if remote:
                uri = self._broker_get_uri("dummy", descriptor)
                dep = RemoteDummyDep(uri)
            else:
                dep = LocalDummyDep(req.name)
        else:  # pragma: no cover
            raise TypeError(f"Unsupported request type: {type(req)}")

        self._channels[descriptor] = dep
        return dep

    def _broker_get_uri(self, kind: Literal["serial", "visa", "http", "dummy"], descriptor: str) -> str:
        # Lazy import to avoid Pyro dependency unless in remote mode
        try:
            import Pyro5.api as pyro  # type: ignore
        except Exception as e:  # noqa: BLE001
            raise RuntimeError("Remote mode requires Pyro5 installed") from e
        assert self.params.server_uri is not None
        with pyro.Proxy(self.params.server_uri) as broker:  # type: ignore
            if kind == "serial":
                return str(broker.get_or_create_serial(descriptor))
            if kind == "visa":
                return str(broker.get_or_create_visa(descriptor))
            if kind == "http":
                return str(broker.get_or_create_http(descriptor))
            if kind == "dummy":
                return str(broker.get_or_create_dummy(descriptor))
        raise ValueError(f"Unknown broker kind: {kind}")


class Computer(Parent[ComputerDep, ChildParams[Any]], ParentFactory[ComputerParams, "Computer"]):  # type: ignore[type-arg]
    def __init__(self, dep: ComputerDep, params: ComputerParams):
        self._dep = dep
        self.params = params
        self.children: dict[str, Child[Any, Any]] = {}

    @property
    def dep(self) -> ComputerDep:
        return self._dep

    @classmethod
    def from_params(cls, params: ComputerParams) -> "Computer":
        dep = ComputerDep(params)
        inst = cls(dep, params)
        inst.init_children()
        return inst

    def init_child_by_key(self, key: str):
        child_params = self.params.children[key]
        child_cls = child_params.inst
        child = child_cls.from_params_with_dep(self.dep, key, child_params)  # type: ignore[attr-defined]
        self.children[key] = cast(Child[Any, Any], child)
        return child

    def init_children(self) -> None:
        for key in list(self.params.children.keys()):
            self.init_child_by_key(key)

    def add_child(self, params: ChildParams[TChild], key: str) -> TChild:  # type: ignore[type-var]
        self.params.children[key] = params  # type: ignore[assignment]
        child_cls = params.inst
        child = child_cls.from_params_with_dep(self.dep, key, params)  # type: ignore[attr-defined]
        self.children[key] = cast(Child[Any, Any], child)
        return child

    def get_child(self, key: str):  # simple accessor similar to other parents
        return self.children.get(key)

    def list_children(self):  # pragma: no cover simple IO
        print("Computer Children:")
        for name, child in self.children.items():
            print(f"{name}: {child}")


__all__ = [
    "ComputerParams",
    "Computer",
    "ComputerDep",
]
