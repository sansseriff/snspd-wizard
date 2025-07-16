from abc import ABC, abstractmethod
from dataclasses import dataclass
from lib.instruments.general.genericMainframe import GenericMainframe
from pydantic import BaseModel, Field


class Submodule(ABC):
    """ """

    @property
    @abstractmethod
    def mainframe_class(self) -> str:
        """Subclasses must override this property to specify the mainframe class."""
        pass


@dataclass
class SubmoduleParams(BaseModel, ABC):
    @property
    @abstractmethod
    def type(self) -> str:
        """Subclasses must override this property to specify the type."""
        pass

    @property
    @abstractmethod
    def slot(self) -> int:
        """Subclasses must override this property to specify the slot number."""
        pass
