import sys
import pathlib
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.instruments.general.computer import ComputerParams
from lib.instruments.dbay.dbay import DBayParams
from lib.instruments.dbay.modules.dac4d import Dac4DParams


def fake_requests_module():
    class FakeResponse:
        def __init__(self, data: dict[str, object], status_code: int = 200):
            self._data: dict[str, object] = data
            self.status_code: int = status_code
            self.content: bytes = b"{}"

        def json(self) -> dict[str, object]:
            return self._data

    def get(url: str):  # minimal endpoint parsing
        if url.endswith("full-state"):
            return FakeResponse(
                {
                    "data": [
                        {
                            "core": {"type": "dac4D"},
                            "channels": {"0": {"measuring": False}},
                        }
                    ]
                }
            )
        return FakeResponse({"data": []})

    def put(url: str, json: dict[str, object] | None = None):  # noqa: A002
        return FakeResponse({"ok": True})

    return types.SimpleNamespace(get=get, put=put)


def test_computer_dbay_child(monkeypatch):  # type: ignore[no-untyped-def]
    # Patch requests so DBay comm uses fake
    monkeypatch.setitem(sys.modules, "requests", fake_requests_module())
    import lib.instruments.dbay.comm as dbay_comm

    dbay_comm.requests = sys.modules["requests"]

    comp = ComputerParams().create_inst()
    # Add DBay as child; key supplies host (and optionally port). Use custom host for clarity.
    dbay = comp.add_child(DBayParams(), "dbay.test:9000")
    # Add a dac4D module into DBay params dynamically and init
    dac_params = Dac4DParams(type="dac4D")  # type field explicit for discrimination
    dbay.params.children["0"] = dac_params  # type: ignore[attr-defined]
    dbay.init_child_by_key("0")

    # Assertions
    assert comp.get_child("dbay.test:9000") is dbay
    assert "0" in dbay.children
    # full-state snapshot
    modules = dbay.get_modules()
    assert modules is not None
    assert len(modules) >= 1
