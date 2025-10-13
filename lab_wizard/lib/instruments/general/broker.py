"""Typed transport broker service (Pyro5).

One daemon, per-descriptor server objects with typed APIs:
    - SerialChannelServer: write/read/line/query
    - VisaChannelServer: write/read/read_bytes/query/clear/timeout
    - HttpChannelServer: get/put/post/delete

Broker returns per-channel URIs via get_or_create_* so clients bind once and
avoid sending descriptors on every call.

Security: no auth; run only on a trusted network.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Any
import base64
from lib.utilities.codec import ensure_bytes

from .comm import (
    parse_descriptor,
    LocalSerialBackend,
    VisaBackend,
    HttpBackend,
    DummyBackend,
)

try:  # Optional Pyro5
    import Pyro5.api as pyro  # type: ignore
    from Pyro5.api import expose  # type: ignore
except Exception:  # pragma: no cover
    pyro = None  # type: ignore

    def expose(obj):  # type: ignore
        return obj


@expose
class SerialChannelServer:  # pragma: no cover - network usage
    def __init__(self, backend: LocalSerialBackend):
        self._b = backend
        self._b.open()

    def write(self, data: bytes | dict | str) -> int:
        try:
            # Support serpent base64 dicts and regular bytes/str seamlessly
            if isinstance(data, dict) and "data" in data and isinstance(data.get("data"), str):
                return self._b.write(base64.b64decode(data["data"]))
            return self._b.write(ensure_bytes(data))
        except Exception:
            # Last resort representation
            return self._b.write(repr(data).encode())

    def read(self, size: Optional[int] = None) -> bytes:
        return self._b.read(size)

    def readline(self) -> bytes:
        return self._b.readline()

    def close(self) -> None:
        self._b.close()


@expose
class VisaChannelServer:  # pragma: no cover - network usage
    def __init__(self, backend: VisaBackend):
        self._b = backend
        self._b.open()

    def write(self, cmd: str) -> None:
        self._b.write(cmd.encode())

    def read(self) -> str:
        return self._b.read().decode()

    def read_bytes(self, n: int) -> bytes:
        return self._b.read(n)

    def query(self, cmd: str) -> str:
        self.write(cmd)
        return self.read()

    def clear(self) -> None:
        try:
            inst = self._b._inst  # type: ignore[attr-defined]
            if inst is not None:
                inst.clear()
        except Exception:
            pass

    def set_timeout(self, s: float) -> None:
        try:
            inst = self._b._inst  # type: ignore[attr-defined]
            if inst is not None:
                inst.timeout = int(s * 1000)
        except Exception:
            pass

    def close(self) -> None:
        self._b.close()


@expose
class HttpChannelServer:  # pragma: no cover - network usage
    def __init__(self, backend: HttpBackend):
        self._b = backend

    def get(self, path: str) -> bytes:
        self._b.write(path.encode())
        return self._b.read()

    def put(self, path: str, data: bytes | dict) -> bytes:
        # Minimal placeholder – treat as GET for demo purposes
        return self.get(path)

    def post(self, path: str, data: bytes | dict) -> bytes:
        return self.get(path)

    def delete(self, path: str) -> bytes:
        return self.get(path)

    def close(self) -> None:
        self._b.close()


@expose
class DummyChannelServer:  # pragma: no cover - network usage
    def __init__(self, backend: DummyBackend):
        self._b = backend

    def write(self, data: bytes | dict | str) -> int:
        try:
            if isinstance(data, dict) and "data" in data and isinstance(data.get("data"), str):
                return self._b.write(base64.b64decode(data["data"]))
            return self._b.write(ensure_bytes(data))
        except Exception:
            return self._b.write(repr(data).encode())

    def read(self, size: Optional[int] = None) -> bytes:
        return self._b.read(size)

    def readline(self) -> bytes:
        return self._b.readline()

    def close(self) -> None:
        self._b.close()


@expose
class ChannelBroker:  # pragma: no cover - network usage
    def __init__(self, daemon: Any | None = None) -> None:
        # descriptor -> (uri, server instance)
        self._serial: Dict[str, tuple[str, Any]] = {}
        self._visa: Dict[str, tuple[str, Any]] = {}
        self._http: Dict[str, tuple[str, Any]] = {}
        self._dummy: Dict[str, tuple[str, Any]] = {}
        self._daemon: Any | None = daemon

    def _ensure_daemon(self):
        if self._daemon is None:
            # Fallback: create a daemon if not injected
            import Pyro5.api as pyro  # type: ignore
            self._daemon = pyro.Daemon()
        return self._daemon

    def _register(self, obj: Any) -> str:
        daemon = self._ensure_daemon()
        uri = daemon.register(obj)
        return str(uri)

    def get_or_create_serial(self, descriptor: str) -> str:
        if descriptor in self._serial:
            return self._serial[descriptor][0]
        info = parse_descriptor(descriptor)
        backend = LocalSerialBackend(
            port=info["port"], baudrate=info["baudrate"], timeout=info["timeout"]
        )
        server = SerialChannelServer(backend)
        uri = self._register(server)
        self._serial[descriptor] = (uri, server)
        return uri

    def get_or_create_visa(self, descriptor: str) -> str:
        if descriptor in self._visa:
            return self._visa[descriptor][0]
        info = parse_descriptor(descriptor)
        backend = VisaBackend(resource=info["resource"], timeout=info["timeout"])  # type: ignore[arg-type]
        server = VisaChannelServer(backend)
        uri = self._register(server)
        self._visa[descriptor] = (uri, server)
        return uri

    def get_or_create_http(self, descriptor: str) -> str:
        if descriptor in self._http:
            return self._http[descriptor][0]
        info = parse_descriptor(descriptor)
        backend = HttpBackend(base_url=info["base_url"])  # type: ignore[arg-type]
        server = HttpChannelServer(backend)
        uri = self._register(server)
        self._http[descriptor] = (uri, server)
        return uri

    def get_or_create_dummy(self, descriptor: str) -> str:
        if descriptor in self._dummy:
            return self._dummy[descriptor][0]
        info = parse_descriptor(descriptor)
        backend = DummyBackend(name=info["name"])  # type: ignore[arg-type]
        server = DummyChannelServer(backend)
        uri = self._register(server)
        self._dummy[descriptor] = (uri, server)
        return uri

    def close(self, descriptor: str) -> bool:
        for store in (self._serial, self._visa, self._http, self._dummy):
            entry = store.pop(descriptor, None)
            if entry is not None:
                try:
                    entry[1].close()
                except Exception:
                    pass
                return True
        return False

    def list_descriptors(self) -> list[str]:
        return list(self._serial.keys()) + list(self._visa.keys()) + list(self._http.keys()) + list(self._dummy.keys())


def serve(host: str = "127.0.0.1", port: int = 0) -> str:  # pragma: no cover - network
    """Start a Pyro5 daemon serving the broker; returns URI string."""
    if pyro is None:
        raise RuntimeError("Pyro5 not available; install Pyro5 to use remote broker")
    daemon = pyro.Daemon(host=host, port=port)
    broker = ChannelBroker(daemon)
    uri = daemon.register(broker)  # type: ignore[arg-type]
    print(f"ChannelBroker serving at {uri}")
    try:
        daemon.requestLoop()
    finally:
        daemon.close()
    return str(uri)


__all__ = [
    "ChannelBroker",
    "SerialChannelServer",
    "VisaChannelServer",
    "HttpChannelServer",
    "serve",
]
