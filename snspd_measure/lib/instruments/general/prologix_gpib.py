from __future__ import annotations

from typing import Annotated, TypeVar, cast, Any
from pydantic import Field, model_validator

from lib.instruments.sim900.sim900 import (
    Sim900Params,
)  # for typing
from lib.instruments.general.parent_child import (
    Parent,
    ParentParams,
    ParentFactory,
    Child,
    ChildParams,
    CanInstantiate,
)
from lib.instruments.general.computer import ComputerDep
from lib.instruments.general.comm import SerialChannelRequest, build_serial_descriptor

from lib.instruments.general.serial import SerialDep
from typing import Literal

# TypeVar for method-level inference
TChild = TypeVar("TChild", bound=Child[SerialDep, Any])


# Union of possible child param types on a serial bus (extend as needed)
PrologixChildParams = Annotated[Sim900Params, Field(discriminator="type")]


class PrologixGPIBParams(
    ParentParams["PrologixGPIB", SerialDep, PrologixChildParams],
    ChildParams["PrologixGPIB"],
    CanInstantiate["PrologixGPIB"],
):
    """Params for Prologix controller.

    When used as a child of `Computer`, the USB/serial device path is supplied
    as the key (e.g. add_child(PrologixGPIBParams(), "/dev/ttyUSB0")). In that
    case `port` may be omitted (None). When instantiated top-level via
    .create_inst(), `port` must be provided or defaults to /dev/ttyUSB0.
    """

    type: Literal["prologix_gpib"] = "prologix_gpib"
    # Optional when nested under Computer (key supplies it); retained for backward compatibility.
    port: str | None = "/dev/ttyUSB0"
    baudrate: int = 9600
    timeout: int = 1
    children: dict[str, PrologixChildParams] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate(self):  # simple placeholder; could cross-check later
        return self

    @property
    def inst(self) -> type["PrologixGPIB"]:  # type: ignore[override]
        return PrologixGPIB

    def create_inst(self) -> "PrologixGPIB":
        # legacy top-level path still builds its own SerialDep
        return PrologixGPIB.from_params(self)

    def __call__(self) -> "PrologixGPIB":
        return self.create_inst()


class PrologixGPIB(
    Parent[SerialDep, PrologixChildParams],
    ParentFactory[PrologixGPIBParams, "PrologixGPIB"],
    Child[ComputerDep, Any],
):
    """
    PrologixGPIB now implements the new Parent + ParentFactory interfaces.
    Children (e.g., Sim900) receive the shared SerialDep serial connection.
    """

    def __init__(self, serial_dep: SerialDep, params: PrologixGPIBParams):
        self.params = params
        self._dep = serial_dep
        self.children: dict[str, Child[SerialDep, Any]] = {}

    # Child interface requirement
    @property
    def parent_class(self) -> str:
        return "lib.instruments.general.computer.Computer"

    @property
    def dep(self) -> SerialDep:
        return self._dep

    @classmethod
    def from_params(cls, params: PrologixGPIBParams) -> "PrologixGPIB":
        # legacy constructor path (no Computer parent)
        if params.port is None:
            raise ValueError(
                "port must be provided when creating PrologixGPIB top-level"
            )
        serial_dep = SerialDep(params.port, params.baudrate, params.timeout)
        inst = cls(serial_dep, params)
        inst.init_children()
        return inst

    @classmethod
    def from_params_with_dep(
        cls,
        parent_dep: ComputerDep,
        key: str,
        params: PrologixGPIBParams,
    ) -> "PrologixGPIB":
        # key supplies the port
        port = key
        # build descriptor (currently unused but kept for future caching / logging)
        _descriptor = build_serial_descriptor(
            port, baudrate=params.baudrate, timeout=params.timeout
        )
        # request channel from computer (channel currently unused inside SerialDep legacy path)
        req = SerialChannelRequest(
            port=port, baudrate=params.baudrate, timeout=params.timeout
        )
        parent_dep.get_channel(req)
        # For now we still create a fresh SerialDep (future: integrate channel to avoid reopen)
        serial_dep = SerialDep.from_channel(port, params.baudrate, params.timeout, None)
        inst = cls(serial_dep, params)
        inst.init_children()
        return inst

    def disconnect(self):
        self._dep.disconnect()

    def init_child_by_key(self, key: str) -> Child[SerialDep, Any]:
        child_params = self.params.children[key]
        child_cls = child_params.inst
        child = child_cls.from_params_with_dep(self.dep, key, child_params)
        self.children[key] = child
        return child

    def init_children(self) -> None:
        for key in list(self.params.children.keys()):
            self.init_child_by_key(key)

    def add_child(self, params: ChildParams[TChild], key: str) -> TChild:
        self.params.children[key] = params  # type: ignore[assignment]
        child_cls = params.inst
        child = child_cls.from_params_with_dep(self.dep, key, params)
        self.children[key] = cast(Child[SerialDep, Any], child)
        return child

    def get_child(self, key: str) -> Child[SerialDep, Any] | None:
        return self.children.get(key)

    def list_children(self):
        port_display = self.params.port or "<injected>"
        print(f"Prologix Connection ({port_display}) Children:")
        print("=" * 50)
        for name, child in self.children.items():
            print(f"{name}: {child}")
        print("=" * 50)


if __name__ == "__main__":
    # Legacy top-level usage
    prologix = PrologixGPIBParams(port="/dev/ttyUSB0").create_inst()
    sim900 = prologix.add_child(Sim900Params(), "3")
