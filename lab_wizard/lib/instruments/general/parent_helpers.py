"""
Helper functions for common Parent class patterns.

These functions provide reusable implementations for common Parent method patterns,
reducing code duplication across instrument modules.
"""

from typing import TypeVar, cast, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lab_wizard.lib.instruments.general.parent_child import Parent, Child, ChildParams

TChild = TypeVar("TChild", bound="Child[Any, Any]")


def standard_add_child(parent: "Parent[Any, Any]", params: "ChildParams[Any]", key: str) -> "Child[Any, Any]":
    """
    Standard implementation of add_child method.
    
    Usage in your Parent class:
    ```python
    def add_child(self, params: ChildParams[TChild], key: str) -> TChild:
        return standard_add_child(self, params, key)  # type: ignore[return-value]
    ```
    """
    parent.params.children[key] = params  # type: ignore[assignment, attr-defined]
    child_cls = params.inst
    child = child_cls.from_params_with_dep(parent.dep, key, params)
    parent.children[key] = cast("Child[Any, Any]", child)
    return child


def standard_init_children(parent: "Parent[Any, Any]") -> None:
    """
    Standard implementation of init_children method.
    
    Usage in your Parent class:
    ```python
    def init_children(self) -> None:
        standard_init_children(self)
    ```
    """
    for key in list(parent.params.children.keys()):  # type: ignore[attr-defined]
        parent.init_child_by_key(key)


def standard_init_child_by_key(parent: "Parent[Any, Any]", key: str) -> "Child[Any, Any]":
    """
    Standard implementation of init_child_by_key method.
    
    Usage in your Parent class:
    ```python  
    def init_child_by_key(self, key: str) -> Child[DepType, Any]:
        return standard_init_child_by_key(self, key)  # type: ignore[return-value]
    ```
    """
    params = parent.params.children[key]  # type: ignore[attr-defined]
    child_cls = params.inst
    child = child_cls.from_params_with_dep(parent.dep, key, params)
    parent.children[key] = child
    return child