"""
genericSense.py
Author: SNSPD Library Rewrite
Date: June 4, 2025

Abstract base class for sensing instruments (multimeters, counters, oscilloscopes, etc.)
"""

from abc import ABC, abstractmethod


class VSense(ABC):
    """Abstract base class for single-channel sensing instruments.

    Rationale for simplification:
    The original interface accepted an optional channel parameter so that a single
    VSense implementation could directly represent a multi-channel instrument. We
    are moving toward a model where each physical channel is represented by its
    own Child instrument (e.g. Sim970Channel) underneath a parent module (e.g.
    Sim970). Therefore the abstract API is simplified to a single-channel
    contract. Multi-channel hardware should expose per-channel children that each
    implement this interface.
    """

    def __init__(self):
        self.connected = False

    def __del__(self):
        if hasattr(self, "connected") and self.connected:
            try:
                self.disconnect()
            except Exception:
                # Avoid raising during GC
                pass

    # ---- Abstract API ----
    @abstractmethod
    def disconnect(self) -> bool: ...

    @abstractmethod
    def get_voltage(self) -> float: ...

    # ---- Convenience wrappers ----
    def measure(self) -> float:
        """Return a voltage measurement (alias used by measurement code)."""
        return self.get_voltage()


class StandInVSense(VSense):
    """Simple stand-in implementation of VSense for tests / CLI scaffolding."""

    ignore_in_cli = True

    def __init__(self):
        super().__init__()
        self.connected = True
        self.measurement_value = 0.0
        print("Stand-in sensing instrument initialized.")

    def disconnect(self) -> bool:
        self.connected = False
        print("StandInVSense disconnected (no real hardware).")
        return True

    def get_voltage(self) -> float:
        return self.measurement_value
