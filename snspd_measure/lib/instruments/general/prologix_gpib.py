from __future__ import annotations

from typing import Annotated, TypeVar, cast, Any
from pydantic import Field

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

from lib.instruments.general.serial import SerialDep

# TypeVar for method-level inference
TChild = TypeVar("TChild", bound=Child[SerialDep, Any])


# Union of possible child param types on a serial bus (extend as needed)
PrologixChildParams = Annotated[Sim900Params, Field(discriminator="type")]


class PrologixGPIBParams(
    ParentParams["PrologixGPIB", SerialDep, PrologixChildParams],
    CanInstantiate["PrologixGPIB"],
):
    port: str = "/dev/ttyUSB0"
    baudrate: int = 9600
    timeout: int = 1
    # Override defaults for ParentParams
    children: dict[str, PrologixChildParams] = Field(default_factory=dict)

    @property
    def inst(self) -> type["PrologixGPIB"]:
        return PrologixGPIB

    def create_inst(self) -> "PrologixGPIB":
        return PrologixGPIB.from_params(self)

    def __call__(self) -> "PrologixGPIB":
        return self.create_inst()


class PrologixGPIB(
    Parent[SerialDep, PrologixChildParams],
    ParentFactory[PrologixGPIBParams, "PrologixGPIB"],
):
    """
    PrologixGPIB now implements the new Parent + ParentFactory interfaces.
    Children (e.g., Sim900) receive the shared SerialDep serial connection.
    """

    def __init__(self, params: PrologixGPIBParams):
        self.params = params

        self._dep = SerialDep(
            self.params.port, self.params.baudrate, self.params.timeout
        )
        self._dep.connect()
        self.children: dict[str, Child[SerialDep, Any]] = {}

    @property
    def dep(self) -> SerialDep:
        return self._dep

    @classmethod
    def from_params(cls, params: PrologixGPIBParams) -> "PrologixGPIB":
        inst = cls(params)
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

    def add_child(self, key: str, params: ChildParams[TChild]) -> TChild:
        self.params.children[key] = params  # type: ignore[assignment]
        child_cls = params.inst
        child = child_cls.from_params_with_dep(self.dep, key, params)
        self.children[key] = cast(Child[SerialDep, Any], child)
        return child

    def get_child(self, key: str) -> Child[SerialDep, Any] | None:
        return self.children.get(key)

    def list_children(self):
        print(f"Prologix Connection ({self.params.port}) Children:")
        print("=" * 50)
        for name, child in self.children.items():
            print(f"{name}: {child}")
        print("=" * 50)


if __name__ == "__main__":
    prologix = PrologixGPIBParams(port="/dev/ttyUSB0").create_inst()
    sim900 = prologix.add_child("3", Sim900Params())
