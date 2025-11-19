import types
import sys
import pathlib
import pytest


# Ensure project root (containing 'lib') is on path when tests run BEFORE imports
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.instruments.general.prologix_gpib import PrologixGPIBParams
from lib.instruments.sim900.sim900 import Sim900Params
from lib.instruments.sim900.modules.sim928 import Sim928Params
from lib.instruments.sim900.modules.sim970 import Sim970Params


@pytest.fixture(autouse=True)
def patch_serial(monkeypatch: pytest.MonkeyPatch):
    """Provide a fake serial.Serial so no real hardware is touched."""

    class FakeSerial:
        def __init__(self, *_, **__):  # type: ignore[no-untyped-def]
            self.is_open = True

        def close(self):
            self.is_open = False

        def flush(self):
            pass

        def write(self, data: bytes):
            return len(data)

        def readline(self):
            return b""

    # Patch both the imported 'serial' module and the already imported symbol inside our package
    fake_module = types.SimpleNamespace(Serial=FakeSerial)
    monkeypatch.setitem(sys.modules, "serial", fake_module)
    import lib.instruments.general.serial as serial_mod

    serial_mod.serial = fake_module


def test_requested_chain_expression():
    controller = PrologixGPIBParams(port="FAKE").create_inst()
    sim900 = controller.add_child(Sim900Params(), "3")

    sim928 = sim900.add_child(Sim928Params(), "1")

    _sim970 = sim900.add_child(Sim970Params(), "5")

    sim928.set_voltage(3.0)

    # Sim970 is a grandchild (child of sim900), so controller.get_child("5") should be None
    assert controller.get_child("5") is None
    assert controller.get_child("3") is sim900
    assert sim900.children.get("1") is sim928

    print(sim900.children)
