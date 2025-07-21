from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from pydantic import BaseModel


class SubmoduleParams(BaseModel):
    """There's non-trivial rules for how ABC and pydantic interact."""


P = TypeVar("P", bound=SubmoduleParams)


class Submodule(ABC, Generic[P]):
    """ """

    @property
    @abstractmethod
    def mainframe_class(self) -> str:
        """Subclasses must override this property to specify the mainframe class."""
        pass

    # should NOT have a from_params method, and init of submodules often requires
    # something like a comm object in addition to params

    # submodule initialization should be done with Mainframe.create_submodule(params)
