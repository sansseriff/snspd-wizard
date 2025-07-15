from abc import ABC, abstractmethod
from lib.instruments.general.genericMainframe import GenericMainframe


class Submodule(ABC):
    """ """

    @property
    @abstractmethod
    def mainframe_class(self) -> type[GenericMainframe]:
        """Subclasses must override this property to specify the mainframe class."""
        pass
