from __future__ import annotations

"""Computer root parent providing channel allocation.

Minimal local-only implementation; remote mode scaffolding included.
"""
from typing import Any, Dict, Literal, TypeVar, cast
from pydantic import Field

from lib.instruments.general.parent_child import (
    Parent,
    ParentParams,
    ParentFactory,
    Child,
    ChildParams,
    Dependency,
)
from lib.instruments.general.comm import (
    SerialChannelRequest,
    VisaChannelRequest,
    HttpChannelRequest,
    DummyChannelRequest,
    CommChannel,
    LocalSerialBackend,
    VisaBackend,
    HttpBackend,
    RemoteSerialBackend,
    RemoteVisaBackend,
    RemoteHttpBackend,
    DummyBackend,
    RemoteDummyBackend,
)

# Type variables
TChild = TypeVar("TChild", bound=Child[Any, Any])

ChannelRequest = SerialChannelRequest | VisaChannelRequest | HttpChannelRequest


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
        self._channels: Dict[str, CommChannel] = {}

    def get_channel(self, req: ChannelRequest) -> CommChannel:
        descriptor = req.descriptor()
        if descriptor in self._channels:
            return self._channels[descriptor]
        # Backend selection (local or remote)
        remote = self.params.mode == "remote" and self.params.server_uri is not None
        if isinstance(req, SerialChannelRequest):
            if remote:
                backend = RemoteSerialBackend(descriptor, self.params.server_uri)  # type: ignore[arg-type]
            else:
                sreq = cast(SerialChannelRequest, req)
                backend = LocalSerialBackend(sreq.port, sreq.baudrate, sreq.timeout)  # type: ignore[arg-type]
        elif isinstance(req, VisaChannelRequest):
            if remote:
                backend = RemoteVisaBackend(descriptor, self.params.server_uri)  # type: ignore[arg-type]
            else:
                vreq = cast(VisaChannelRequest, req)
                backend = VisaBackend(vreq.resource, vreq.timeout)  # type: ignore[arg-type]
        elif isinstance(req, HttpChannelRequest):
            if remote:
                backend = RemoteHttpBackend(descriptor, self.params.server_uri)  # type: ignore[arg-type]
            else:
                hreq = cast(HttpChannelRequest, req)
                backend = HttpBackend(hreq.descriptor())
        elif isinstance(req, DummyChannelRequest):
            if remote:
                backend = RemoteDummyBackend(descriptor, self.params.server_uri)  # type: ignore[arg-type]
            else:
                dreq = cast(DummyChannelRequest, req)
                backend = DummyBackend(dreq.name)
        else:  # pragma: no cover
            raise TypeError(f"Unsupported request type: {type(req)}")
        chan = CommChannel(backend, descriptor)
        self._channels[descriptor] = chan
        return chan


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
