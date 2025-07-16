from lib.instruments.general.submodule import Submodule


class Empty(Submodule):
    def __init__(self):
        """Initialize an empty module."""
        pass

    def __str__(self):
        """Return a pretty string representation of the Empty module."""
        return "Empty slot"

    @property
    def mainframe_class(self) -> str:
        return "lib.instruments.dbay.dbay.DBay"

    def some_placeholder_method(self):
        pass  # This method can be implemented later if needed.
