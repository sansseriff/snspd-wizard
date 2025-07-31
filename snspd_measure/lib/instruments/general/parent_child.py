from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic
from pydantic import BaseModel, model_validator
from lib.instruments.general.child import ChildParams


P = TypeVar("P", bound=ChildParams, covariant=True)


class ParentParams(BaseModel, Generic[P]):
    """A submodule that is a limited subset of the full module."""

    modules: dict[str, P] = {}
    num_modules: int

    @model_validator(mode="after")
    def validate_modules(self) -> "ParentParams[P]":
        """Validate that modules dict is consistent with num_modules."""
        # Check if we have too many modules
        if len(self.modules) > self.num_modules:
            raise ValueError(
                f"Too many modules: found {len(self.modules)} modules but num_modules is {self.num_modules}"
            )

        # Check that all string keys can be converted to valid channel numbers
        for key in self.modules.keys():
            try:
                channel_num = int(key)
            except ValueError:
                raise ValueError(
                    f"Channel key '{key}' cannot be converted to an integer"
                )

            if channel_num < 0 or channel_num >= self.num_modules:
                raise ValueError(
                    f"Channel number {channel_num} is out of range. "
                    f"Valid range is 0 to {self.num_modules - 1} (num_modules = {self.num_modules})"
                )

        return self


M = TypeVar("M", bound=ParentParams[ChildParams])
R = TypeVar("R")  # Resource type

# exp = Exp()

# gpib_controlled = GPIBControlled.from_params(exp.instruments["gpib_controlled"])

# mainfram_params = exp.instruments["mainframe"]
# mainframe_sim900 = Sim900.from_params(mainfram_params, comm = gpib_controlled.get_comm())

# sim928_params = mainframe_params.modules["sim928"]
# sim928 = Sim928.from_params(sim928_params, comm=mainframe_sim900.get_comm())

# sim970_params = mainframe_params.modules["sim970"]
# sim970 = Sim970.from_params(sim970_params, comm=mainframe_sim900.get_comm())


class Parent(ABC, Generic[M, R]):
    """
    M Should be the params object that corresponds to the mainframe

    for example, 'MyParent(Parent[MyParentParams])'
    """

    @property
    @abstractmethod
    def resource(self) -> R:
        pass

    @abstractmethod
    def create_submodule(self, params: Any) -> Any:  # Changed dataclass to Any
        """
        Create a submodule with the given parameters.

        Args:
            params: Parameters for the submodule, typically a dataclass instance

        Returns:
            The created submodule instance
        """
        pass


if __name__ == "__main__":
    # Test the ParentParams validator

    class TestChildParams(ChildParams):
        value: int = 0

    class TestParentParams(ParentParams[TestChildParams]):
        pass

    print("Testing ParentParams validator...")

    # Test 1: Valid configuration
    try:
        valid_params = TestParentParams(
            num_modules=3,
            modules={
                "0": TestChildParams(value=10),
                "1": TestChildParams(value=20),
                "2": TestChildParams(value=30),
            },
        )
        print("✓ Test 1 passed: Valid configuration accepted")
    except Exception as e:
        print(f"✗ Test 1 failed: {e}")

    # Test 2: Too many modules
    try:
        invalid_params = TestParentParams(
            num_modules=2,
            modules={
                "0": TestChildParams(value=10),
                "1": TestChildParams(value=20),
                "2": TestChildParams(value=30),  # This should fail
            },
        )
        print("✗ Test 2 failed: Should have raised ValueError for too many modules")
    except ValueError as e:
        print(f"✓ Test 2 passed: {e}")

    # Test 3: Invalid module key (non-numeric)
    try:
        invalid_params = TestParentParams(
            num_modules=3,
            modules={
                "0": TestChildParams(value=10),
                "abc": TestChildParams(value=20),  # This should fail
            },
        )
        print("✗ Test 3 failed: Should have raised ValueError for non-numeric key")
    except ValueError as e:
        print(f"✓ Test 3 passed: {e}")

    # Test 4: Module number out of range
    try:
        invalid_params = TestParentParams(
            num_modules=2,
            modules={
                "0": TestChildParams(value=10),
                "5": TestChildParams(value=20),  # This should fail (5 >= 2)
            },
        )
        print("✗ Test 4 failed: Should have raised ValueError for out-of-range module")
    except ValueError as e:
        print(f"✓ Test 4 passed: {e}")

    # Test 5: Negative module number
    try:
        invalid_params = TestParentParams(
            num_modules=3,
            modules={
                "-1": TestChildParams(value=10)  # This should fail
            },
        )
        print("✗ Test 5 failed: Should have raised ValueError for negative module")
    except ValueError as e:
        print(f"✓ Test 5 passed: {e}")

    # Test 6: Empty modules dict (should be valid)
    try:
        empty_params = TestParentParams(
            num_modules=3,
            modules={},
        )
        print("✓ Test 6 passed: Empty modules dict accepted")
    except Exception as e:
        print(f"✗ Test 6 failed: {e}")

    print("\nAll mainframe tests completed!")
