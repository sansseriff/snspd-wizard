"""Remote channel broker service.

Provides a Pyro5-exposed object that manages a cache of backend instances
identified by canonical descriptors (e.g., serial:/dev/ttyUSB0?baud=9600&timeout=1.0).

Responsibilities:
- Accept descriptor strings from clients.
- Parse descriptor and create appropriate backend (serial, visa, http) lazily.
- Provide simple byte-oriented read / write / readline operations.
- Keep backends open for reuse until explicit close or process shutdown.

Security: This minimal version performs no authentication and should only be
used in a trusted lab network segment. Add ACL / auth hooks before broader use.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Any
import base64

from .comm import (
    parse_descriptor,
    LocalSerialBackend,
    VisaBackend,
    HttpBackend,
    BackendProtocol,
    DummyBackend,
)

try:  # Optional Pyro5
    import Pyro5.api as pyro  # type: ignore
    from Pyro5.api import expose  # type: ignore
except Exception:  # pragma: no cover
    pyro = None  # type: ignore

    def expose(obj):  # type: ignore
        return obj


@dataclass
class _Entry:
    backend: BackendProtocol


@expose
class ChannelBroker:  # pragma: no cover - network usage
    def __init__(self) -> None:
        self._cache: Dict[str, _Entry] = {}

    # ------- helpers -------
    def _coerce_bytes(self, payload: Any) -> bytes:
        if isinstance(payload, bytes):
            return payload
        if isinstance(payload, dict) and "data" in payload:
            data_field = payload.get("data")
            if isinstance(data_field, str):
                try:
                    return base64.b64decode(data_field)
                except Exception:
                    pass
        if isinstance(payload, str):
            return payload.encode()
        return repr(payload).encode()

    # ------- backend factory -------
    def _get_backend(self, descriptor: str) -> BackendProtocol:
        e = self._cache.get(descriptor)
        if e is not None:
            return e.backend
        info = parse_descriptor(descriptor)
        t = info["type"]
        if t == "serial":
            backend = LocalSerialBackend(
                port=info["port"],
                baudrate=info["baudrate"],
                timeout=info["timeout"],
            )
        elif t == "visa":
            backend = VisaBackend(
                resource=info["resource"],
                timeout=info["timeout"],
            )
        elif t == "http":
            backend = HttpBackend(base_url=info["base_url"])  # type: ignore[arg-type]
        elif t == "dummy":
            backend = DummyBackend(name=info["name"])  # type: ignore[arg-type]
        else:
            raise ValueError(f"Unsupported descriptor type: {t}")
        backend.open()
        self._cache[descriptor] = _Entry(backend=backend)
        return backend

    # ------- exposed operations -------
    @expose
    def write(self, descriptor: str, data: bytes) -> int:
        backend = self._get_backend(descriptor)
        coerced = self._coerce_bytes(data)
        return backend.write(coerced)

    @expose
    def read(self, descriptor: str, size: Optional[int] = None) -> bytes:
        backend = self._get_backend(descriptor)
        return backend.read(size)

    @expose
    def readline(self, descriptor: str) -> bytes:
        backend = self._get_backend(descriptor)
        return backend.readline()

    @expose
    def close(self, descriptor: str) -> bool:
        e = self._cache.pop(descriptor, None)
        if e is None:
            return False
        try:
            e.backend.close()
        except Exception:
            pass
        return True

    @expose
    def list_descriptors(self) -> list[str]:  # management helper
        return list(self._cache.keys())


def serve(host: str = "127.0.0.1", port: int = 0) -> str:
    """Start a Pyro5 daemon serving the broker; returns URI string.

    If port=0 an ephemeral port is chosen. Caller is responsible for keeping
    the program alive (daemon.requestLoop()). For simple usage you can call
    this and then call daemon.requestLoop() manually; we return URI for clients.
    """
    if pyro is None:  # pragma: no cover
        raise RuntimeError("Pyro5 not available; install Pyro5 to use remote broker")
    broker = ChannelBroker()
    daemon = pyro.Daemon(host=host, port=port)
    uri = daemon.register(broker)  # type: ignore[arg-type]
    print(f"ChannelBroker serving at {uri}")
    try:
        daemon.requestLoop()
    finally:
        daemon.close()
    return str(uri)


__all__ = ["ChannelBroker", "serve"]
