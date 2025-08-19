from typing import Annotated, TypeVar, cast
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
    params_alignment,
)

from lib.instruments.general.serial import SerialDep

# TypeVar for method-level inference
TChild = TypeVar("TChild", bound=Child[SerialDep])


# Union of possible child param types on a serial bus (extend as needed)
PrologixChildParams = Annotated[Sim900Params, Field(discriminator="type")]


class PrologixGPIBParams(
    ParentParams[SerialDep, PrologixChildParams],
    CanInstantiate["PrologixGPIB"],
):
    port: str = "/dev/ttyUSB0"
    baudrate: int = 9600
    timeout: int = 1
    # Override defaults for ParentParams
    children: dict[str, PrologixChildParams] = Field(default_factory=dict)

    def create_inst(self):
        return PrologixGPIB.from_params(self)

    # Allow calling the params instance to construct its corresponding instrument
    # so user code / tests can do: PrologixGPIBParams(...).inst().add_child(...)
    # which matches the chaining style requested.
    def __call__(self) -> "PrologixGPIB":  # type: ignore[name-defined]
        inst = PrologixGPIB(self.port, self.baudrate, self.timeout)
        return inst


@params_alignment(PrologixGPIBParams)
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
        self.children: dict[str, Child[SerialDep]] = {}

    # Parent requirement
    @property
    def dep(self) -> SerialDep:
        return self._dep

    # Factory for pure parent
    @classmethod
    def from_params(cls, params: PrologixGPIBParams) -> "PrologixGPIB":
        inst = cls(port=params.port, baudrate=params.baudrate, timeout=params.timeout)
        inst.params.children.update(params.children)
        return inst

    def disconnect(self):
        self._dep.disconnect()

    # Child initialization
    def init_child_by_key(self, key: str) -> Child[SerialDep]:
        child_params = self.params.children[key]
        child_cls = child_params.inst
        # See sim900.init_child_by_key for explanation of this cast.
        # child_typed = cast(type[Child[SerialDep, PrologixChildParams]], child_cls)

        # the child takes whatever dep the parent can provide
        child = child_cls.from_params_with_dep(self.dep, child_params)
        self.children[key] = child
        return child

    def init_children(self) -> None:
        for key in list(self.params.children.keys()):
            self.init_child_by_key(key)

    # Convenience helpers
    def add_child(self, key: str, params: ChildParams[TChild]) -> TChild:
        """Add and instantiate a child, returning the precise instrument type."""
        # Store strongly-typed params (erased in params dict for runtime use)
        self.params.children[key] = params  # type: ignore[assignment]
        # Instantiate
        child_cls = params.inst
        child = child_cls.from_params_with_dep(self.dep, params)
        self.children[key] = cast(Child[SerialDep], child)
        return child

    def get_child(self, key: str) -> Child[SerialDep] | None:
        return self.children.get(key)

    def list_children(self):
        print(f"Prologix Connection ({self.params.port}) Children:")
        print("=" * 50)
        for name, child in self.children.items():
            print(f"{name}: {child}")
        print("=" * 50)


if __name__ == "__main__":
    # Example usage
    prologix = PrologixGPIBParams(port="/dev/ttyUSB0").create_inst()
    sim900 = prologix.add_child("3", Sim900Params())
