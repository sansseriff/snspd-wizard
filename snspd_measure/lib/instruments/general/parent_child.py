from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic
from pydantic import BaseModel, model_validator, Field


# Move base classes above TypeVar declarations so bounds use real types (not strings)
class Dependency(ABC):
    pass


class ChildParams(BaseModel):
    """There's non-trivial rules for how ABC and pydantic interact."""

    @model_validator(mode="after")
    def validate_type_exists(self) -> ChildParams:
        """Validate that the type field is set."""
        if not hasattr(self, "type") or getattr(self, "type") is None:
            raise ValueError("Missing required 'type' field")
        return self

    @property
    @abstractmethod
    def corresponding_inst(self) -> "type[Child[Dependency, ChildParams]]":
        """
        A property that returns the corresponding instrument class for this child.
        """
        pass


class ChannelChildParams(ChildParams):
    """
    A submodule that a fixed number of channels.

    The validator checks that the channels dict is consistent with num_channels.
    """

    channels: dict[str, Any] = Field(default_factory=dict)
    num_channels: int

    @model_validator(mode="after")
    def validate_channels(self) -> ChannelChildParams:
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


# TypeVars now bind to already-declared classes (fixes the previous forward-ref error)
R = TypeVar("R", bound=Dependency)
P = TypeVar("P", bound=ChildParams)

# Variance-expressive TypeVars for Child interface only
R_co = TypeVar("R_co", bound=Dependency, covariant=True)
P_co = TypeVar("P_co", bound=ChildParams, covariant=True)
R_contra = TypeVar("R_contra", bound=Dependency, contravariant=True)
P_contra = TypeVar("P_contra", bound=ChildParams, contravariant=True)


class ParentParams(BaseModel, Generic[R, P]):
    """A submodule that is a limited subset of the full module."""

    # Use Field to avoid shared mutable default
    children: dict[str, P] = Field(default_factory=dict)
    num_children: int  # should be given default value in subclasses

    # @classmethod
    # @abstractmethod
    # def init(
    #     cls, params: "ParentParams[R, P_contra]"
    # ) -> tuple[
    #     "Parent[ParentParams[R, P_contra], R, P_contra]", "ParentParams[R, P_contra]"
    # ]:
    #     """
    #     inside here you'd typically call my_parent.from_params(params)
    #     """

    #     pass

    @property
    @abstractmethod
    def corresponding_inst(self) -> "type[Parent[R, P]]":
        """
        A property that returns the corresponding instrument class for this child.
        """
        pass

    @model_validator(mode="after")
    def validate_children(self) -> ParentParams[R, P]:
        """Validate that children dict is consistent with num_children."""
        # Check if we have too many children
        if len(self.children) > self.num_children:
            raise ValueError(
                f"Too many children: found {len(self.children)} children but num_children is {self.num_children}"
            )

        # Check that all string keys can be converted to valid channel numbers
        for key in self.children.keys():
            try:
                channel_num = int(key)
            except ValueError:
                raise ValueError(
                    f"Channel key '{key}' cannot be converted to an integer"
                )

            if channel_num < 0 or channel_num >= self.num_children:
                raise ValueError(
                    f"Channel number {channel_num} is out of range. "
                    f"Valid range is 0 to {self.num_children - 1} (num_children = {self.num_children})"
                )

        return self


class Parent(ABC, Generic[R, P]):
    """
    R: dependency type (e.g., Comm)
    P: ChildParams subtype for children

    Note:
      The factory method for creating a Parent from only ParentParams has been
      split out into ParentFactory. This avoids a signature clash when a class
      is both a Parent and a Child (hybrid). Hybrid classes now only need to
      implement the Child.from_params(dep, params) factory.
    """

    children: dict[str, "Child[R, P]"]

    @property
    @abstractmethod
    def dep(self) -> R:
        """
        A dep is some object that childen require to operate, such as a Comm object.
        This should return the same type as the first type expected by the Child.from_params method.
        """
        pass

    @abstractmethod
    def init_child_by_key(self, key: str) -> "Child[R, P]":
        """
        Create for a key 'my_key', init a child from this.params.children['my_key'],
        and place it in self.children['my_key'].
        """
        pass

    @abstractmethod
    def init_children(self) -> None:
        """
        This is intended to enable the 'automatic' creation of all children by
        iterating over the self.params.children dict. And therefore filling
        the self.children dict.
        """


class ParentFactory(ABC, Generic[R, P]):
    """
    Optional mixin-style ABC for pure parent factories. Parents that are not also children.

    Use this when a class is only a parent (not a child) and you want the
    parent-style factory: from_params(cls, params) -> (instance, params).

    Do NOT inherit this in classes that are also Children; implement only the
    Child.from_params(dep, params) in those hybrid cases.
    """

    @classmethod
    @abstractmethod
    def from_params(
        cls, params: ParentParams[R, P]
    ) -> tuple["Parent[R, P]", ParentParams[R, P]]:
        """
        Create a parent from the given params (no dep argument).
        Only implement in non-hybrid parent classes.
        """
        pass


class Child(ABC, Generic[R_co, P_co]):
    """
    Public interface is covariant (Child[DerivedDep, DerivedParams] is a subtype of Child[BaseDep, BaseParams]).
    Construction uses contravariant TypeVars so factories can accept broader (base) types.
    """

    @property
    @abstractmethod
    def parent_class(self) -> str:
        """Subclasses must override this property to specify the parent class."""
        pass

    @classmethod
    @abstractmethod
    def from_params(
        cls,
        dep: R_contra,
        params: P_contra,
    ) -> tuple["Child[R_contra, P_contra]", P_contra]:
        """
        Factory method: accepts base (contravariant) dependency / params types
        and returns a Child specialized to those concrete types.
        """
