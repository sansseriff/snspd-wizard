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
)

from lib.instruments.general.serial import SerialComm, SerialDep

# TypeVar for method-level inference
TChild = TypeVar("TChild", bound=Child[SerialDep, Any])


# Union of possible child param types on a serial bus (extend as needed)
PrologixChildParams = Annotated[Sim900Params, Field(discriminator="type")]


class PrologixControllerParams(ParentParams[SerialDep, PrologixChildParams]):
    port: str = "/dev/ttyUSB0"
    baudrate: int = 9600
    timeout: int = 1
    # Override defaults for ParentParams
    children: dict[str, PrologixChildParams] = Field(default_factory=dict)
    num_children: int = 1600  # arbitrary bus capacity

    @property
    def corresponding_inst(self):
        return PrologixController

    # Allow calling the params instance to construct its corresponding instrument
    # so user code / tests can do: PrologixControllerParams(...).corresponding_inst().add_child(...)
    # which matches the chaining style requested.
    def __call__(self) -> "PrologixController":  # type: ignore[name-defined]
        inst = PrologixController(self.port, self.baudrate, self.timeout)
        return inst


class PrologixController(
    Parent[SerialDep, PrologixChildParams],
    ParentFactory[PrologixControllerParams, "PrologixController"],
):
    """
    PrologixController now implements the new Parent + ParentFactory interfaces.
    Children (e.g., Sim900) receive a SerialDep containing the shared SerialComm.
    """

    def __init__(
        self, port: str = "/dev/ttyUSB0", baudrate: int = 9600, timeout: int = 1
    ):
        self.params = PrologixControllerParams(
            port=port, baudrate=baudrate, timeout=timeout
        )
        self._comm = SerialComm(
            self.params.port, self.params.baudrate, self.params.timeout
        )
        self._comm.connect()
        self._dep = SerialDep(self._comm)
        self.children: dict[str, Child[SerialDep, PrologixChildParams]] = {}

    # Parent requirement
    @property
    def dep(self) -> SerialDep:
        return self._dep

    # Factory for pure parent
    @classmethod
    def from_params(
        cls, params: PrologixControllerParams
    ) -> tuple["PrologixController", PrologixControllerParams]:
        inst = cls(**params.model_dump())
        return inst, params

    def disconnect(self):
        self._comm.disconnect()

    # Child initialization
    def init_child_by_key(self, key: str) -> Child[SerialDep, PrologixChildParams]:
        child_params = self.params.children[key]
        child_cls = child_params.corresponding_inst
        # See sim900.init_child_by_key for explanation of this cast.
        child_typed = cast(type[Child[SerialDep, PrologixChildParams]], child_cls)
        child, _ = child_typed.from_params(self.dep, child_params)
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
        child_cls = params.corresponding_inst
        child, _ = child_cls.from_params(self.dep, params)
        self.children[key] = cast(Child[SerialDep, PrologixChildParams], child)
        return child

    def get_child(self, key: str) -> Child[SerialDep, PrologixChildParams] | None:
        return self.children.get(key)

    def list_children(self):
        print(f"Prologix Connection ({self.params.port}) Children:")
        print("=" * 50)
        for name, child in self.children.items():
            print(f"{name}: {child}")
        print("=" * 50)
        return self.children
