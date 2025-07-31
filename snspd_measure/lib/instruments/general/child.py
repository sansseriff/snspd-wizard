from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Literal, Any
from pydantic import BaseModel, model_validator


class ChildParams(BaseModel):
    """There's non-trivial rules for how ABC and pydantic interact."""

    @model_validator(mode="after")
    def validate_type_exists(self) -> "ChildParams":
        """Validate that the type field is set."""
        if not hasattr(self, "type") or getattr(self, "type") is None:
            raise ValueError("Missing required 'type' field")
        return self


class ChannelChildParams(ChildParams):
    """
    A slightly modified ChildParams for when a parent has a fixed number of channels.

    The validator checks that the channels dict is consistent with num_channels.
    """

    channels: dict[str, Any] = {}
    num_channels: int

    @model_validator(mode="after")
    def validate_channels(self) -> "ChannelChildParams":
        """Validate that channels dict is consistent with num_channels."""
        # Check if we have too many channels
        if len(self.channels) > self.num_channels:
            raise ValueError(
                f"Too many channels: found {len(self.channels)} channels but num_channels is {self.num_channels}"
            )

        # Check that all string keys can be converted to valid channel numbers
        for key in self.channels.keys():
            try:
                channel_num = int(key)
            except ValueError:
                raise ValueError(
                    f"Channel key '{key}' cannot be converted to an integer"
                )

            if channel_num < 0 or channel_num >= self.num_channels:
                raise ValueError(
                    f"Channel number {channel_num} is out of range. "
                    f"Valid range is 0 to {self.num_channels - 1} (num_channels = {self.num_channels})"
                )

        return self


class Child(ABC):
    """ """

    @property
    @abstractmethod
    def mainframe_class(self) -> str:
        """Subclasses must override this property to specify the mainframe class."""
        pass


    @abstractmethod
    def from_params(self, resource: ???, params: ChildParams) -> "Child":
        pass


if __name__ == "__main__":
    # Test the ChannelChild validator

    class TestParams(ChildParams):
        type: Literal["test_module"] = "test_module"
        value: int = 0

    class TestChannelChildParams(ChannelChildParams):
        type: Literal["test_channel_submodule"] = "test_channel_submodule"
        num_channels: int
        channels: dict[str, TestParams] = {}

        @property
        def mainframe_class(self) -> str:
            return "TestParent"

    print("Testing ChannelChild validator...")

    # Test 1: Valid configuration with type set
    try:
        valid_module = TestChannelChildParams(
            num_channels=3,
            channels={
                "0": TestParams(value=10),
                "1": TestParams(value=20),
                "2": TestParams(value=30),
            },
        )
        print("✓ Test 1 passed: Valid configuration with type accepted")
    except Exception as e:
        print(f"✗ Test 1 failed: {e}")

    try:
        invalid_module = TestChannelChildParams(
            num_channels=2,
            channels={
                "0": TestParams(value=10),
            },
        )
        print("✗ Test 2 failed: Should have raised ValueError for missing type")
    except ValueError as e:
        print(f"✓ Test 2 passed: {e}")

    # Test 3: Too many channels
    try:
        invalid_module = TestChannelChildParams(
            num_channels=2,
            channels={
                "0": TestParams(value=10),
                "1": TestParams(value=20),
                "2": TestParams(value=30),  # This should fail
            },
        )
        print("✗ Test 3 failed: Should have raised ValueError for too many channels")
    except ValueError as e:
        print(f"✓ Test 3 passed: {e}")

    # Test 4: Invalid channel key (non-numeric)
    try:
        invalid_module = TestChannelChildParams(
            num_channels=3,
            channels={
                "0": TestParams(value=10),
                "abc": TestParams(value=20),  # This should fail
            },
        )
        print("✗ Test 4 failed: Should have raised ValueError for non-numeric key")
    except ValueError as e:
        print(f"✓ Test 4 passed: {e}")

    # Test 5: Channel number out of range
    try:
        invalid_module = TestChannelChildParams(
            num_channels=2,
            channels={
                "0": TestParams(value=10),
                "5": TestParams(value=20),  # This should fail (5 >= 2)
            },
        )
        print("✗ Test 5 failed: Should have raised ValueError for out-of-range channel")
    except ValueError as e:
        print(f"✓ Test 5 passed: {e}")

    # Test 6: Negative channel number
    try:
        invalid_module = TestChannelChildParams(
            num_channels=3,
            channels={
                "-1": TestParams(value=10)  # This should fail
            },
        )
        print("✗ Test 6 failed: Should have raised ValueError for negative channel")
    except ValueError as e:
        print(f"✓ Test 6 passed: {e}")

        print("\nAll tests completed!")
        invalid_module = TestChannelChildParams(
            num_channels=3,
            channels={
                "-1": TestParams(value=10)  # This should fail
            },
        )
        print("✗ Test 6 failed: Should have raised ValueError for negative channel")

    print("\nAll tests completed!")
