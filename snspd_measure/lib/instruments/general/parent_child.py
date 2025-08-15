from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic
from pydantic import BaseModel, model_validator, Field


# Move base classes above TypeVar declarations so bounds use real types (not strings)
class Dependency(ABC):
    pass


I_co = TypeVar("I_co", bound="Child[Any]", covariant=True)

P_co = TypeVar("P_co", bound="Parent[Any, Any]", covariant=True)


class RequiresDepsToInstantiate(Generic[I_co], ABC):
    """
    Has a corresponding instrument instance, but that instance may require resources not
    included in the params object. Like a comm object from a parent.
    """

    @property
    @abstractmethod
    def inst(self) -> type[I_co]: ...


class RequiresNoDepsToInstantiate(Generic[P_co], ABC):
    """
    An instrument can be created with the params object. No other dependencies are required.
    """

    @abstractmethod
    def create_inst(self) -> P_co:
        pass


# hmm I want ParentParams to have a method create_inst() IFF it is a top parent.
# if its not a top parent then it presumably needs to pass down a resource like a comm object


# and I want


class ChildParams(BaseModel, Generic[I_co], RequiresDepsToInstantiate[I_co]):
    """Base class for all child parameter objects.

    Generic over the concrete Child instrument type (I_co). This lets APIs
    accepting a ChildParams[I] return an I without ad-hoc overloads.
    """

    @model_validator(mode="after")
    def validate_type_exists(self) -> ChildParams[I_co]:
        """
        Validate that the type field is set. This is used by pydantic to figure out
        how to discriminate a union of possible pydantic models
        """
        if not hasattr(self, "type") or getattr(self, "type") is None:
            raise ValueError("Missing required 'type' field")
        return self


class ChannelChildParams(ChildParams[I_co], Generic[I_co]):
    """
    A submodule that a fixed number of channels.

    The validator checks that the channels dict is consistent with num_channels.
    """

    children: dict[str, Any] = Field(default_factory=dict)
    num_children: int

    @model_validator(mode="after")
    def validate_channels(self) -> ChannelChildParams[I_co]:
        """Validate that channels dict is consistent with num_children."""
        # Check if we have too many channels
        if len(self.children) > self.num_children:
            raise ValueError(
                f"Too many channels: found {len(self.children)} channels but num_children is {self.num_children}"
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


R = TypeVar("R", bound=Dependency)
P = TypeVar("P", bound=ChildParams[Any])

"""NOTE ON VARIANCE & FACTORY SIGNATURE

The earlier design attempted to use contravariance on the dependency / params
TypeVars in the Child interface so that a subclass could accept *broader*
inputs. In practice, what we want is the opposite: subclasses almost always
need to *narrow* the dependency + params types (e.g. Sim928 needs Sim900Dep
and Sim928Params). Pylance (and mypy) then reported override incompatibility
because a method cannot narrow a contravariant parameter type.

To make subclass factories ergonomically type-safe we switch to a simpler
pattern:
    class Child[R, P]:
            @classmethod
            def from_params(cls: type[C], dep: R, params: P) -> tuple[C, P]

Where C is a TypeVar bound to Child[Any, Any]. This lets each subclass bind C
to itself (Sim928) and R/P to its concrete dependency/param types with no
override complaints and precise return typing.
"""


PR_co = TypeVar("PR_co", bound="Parent[Any, Any]")


class ParentParams(BaseModel, Generic[R, P]):
    """A submodule that is a limited subset of the full module."""

    # Use Field to avoid shared mutable default
    children: dict[str, P] = Field(default_factory=dict)
    num_children: int  # should be given default value in subclasses

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

    children: dict[str, "Child[R]"]

    @property
    @abstractmethod
    def dep(self) -> R:
        """
        A dep is some object that childen require to operate, such as a Comm object.
        This should return the same type as the first type expected by the Child.from_params method.
        """
        pass

    @abstractmethod
    def init_child_by_key(self, key: str) -> "Child[R]":
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


PP = TypeVar("PP", bound=ParentParams[Any, Any])  # any concrete ParentParams subtype
PR = TypeVar("PR", bound="Parent[Any, Any]")  # any concrete Parent subtype


class ParentFactory(ABC, Generic[PP, PR]):
    """
    Factory for creating a Parent (or subtype) from its concrete ParentParams (or subtype).

    PP: concrete ParentParams subtype (any R/P specialization)
    PR: resulting Parent subtype

    from_params:
      Accepts a params instance (PP) and returns (parent_instance, same_params_object).
    """

    @classmethod
    @abstractmethod
    def from_params(cls, params: PP) -> PR:
        pass


C = TypeVar("C", bound="Child[Any]")


class Child(ABC, Generic[R]):
    """Generic child instrument / module interface.

    R: dependency type needed to build / operate this child (e.g., a Comm wrapper)
    P: concrete ChildParams subtype describing configuration for this child

    Subclasses implement from_params with their concrete (R, P) and return their
    own class type. The generic signature with the "cls: type[C]" pattern allows
    precise return typing while remaining friendly to static type checkers.
    """

    @property
    @abstractmethod
    def parent_class(self) -> str:
        """Fully-qualified (or uniquely identifying) name of the expected parent class."""
        pass

    @classmethod
    @abstractmethod
    def from_params_with_dep(
        cls: type[C],
        dep: R,
        params: ChildParams[Any],
    ) -> C:
        """Factory constructing the child from dependency + params."""


# New ChannelChild base class
R_dep = TypeVar("R_dep", bound=Dependency)


class ChannelChild(Child[R_dep]):
    """
    Base class for children whose params are ChannelChildParams (fixed number of channels).

    Subclass responsibilities:
      - implement parent_class property (name of expected parent class)
      - add any channel-specific behavior

    Provided:
      - dep / params storage
      - from_params factory matching current Child API
      - convenience helpers for channels
    """

    params: ChannelChildParams[Any]
    _dep: R_dep

    def __init__(self, dep: R_dep, params: ChannelChildParams[Any]):
        self._dep = dep
        self.params = params

    # Convenience helpers
    def child_keys(self) -> list[int]:
        return sorted(int(k) for k in self.params.children.keys())

    def get_child(self, idx: int) -> Any:
        return self.params.children[str(idx)]
