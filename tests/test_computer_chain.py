import types
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.instruments.general.computer import ComputerParams
from lib.instruments.general.prologix_gpib import PrologixGPIBParams
from lib.instruments.sim900.sim900 import Sim900Params
from lib.instruments.sim900.modules.sim928 import Sim928Params


def fake_serial_module():
    class FakeSerial:
        def __init__(self, *_, **__):
            self.is_open = True

        def close(self):
            self.is_open = False

        def flush(self):
            pass

        def write(self, data: bytes):
            return len(data)

        def readline(self):
            return b""

        def read_all(self):
            return b""

        def read(self, size: int):
            return b""

    return types.SimpleNamespace(Serial=FakeSerial)


def test_computer_prologix_chain(monkeypatch):  # type: ignore[no-untyped-def]
    # patch serial
    monkeypatch.setitem(sys.modules, "serial", fake_serial_module())
    import lib.instruments.general.serial as serial_mod

    serial_mod.serial = sys.modules["serial"]

    comp = ComputerParams().create_inst()
    prologix = comp.add_child(PrologixGPIBParams(baudrate=19200), "/dev/ttyUSB_FAKE")
    sim900 = prologix.add_child(Sim900Params(), "3")
    sim928 = sim900.add_child(Sim928Params(), "1")

    assert comp.get_child("/dev/ttyUSB_FAKE") is prologix  # type: ignore[attr-defined]
    assert prologix.get_child("3") is sim900  # type: ignore[attr-defined]
    assert sim900.children.get("1") is sim928
