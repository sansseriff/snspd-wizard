from lib.instruments.general.parent_child import Dependency
from lib.instruments.general.serial import SerialDep


class Sim900Dep(Dependency):
    """Lightweight dependency object passed to SIM900 modules.

    Holds shared SerialDep and the mainframe GPIB address.
    Safe to import at runtime (no circular deps).
    """

    def __init__(self, parent_dep: SerialDep, gpibAddr: int):
        self.serial = parent_dep
        self.gpibAddr = gpibAddr
