from __future__ import annotations

"""Unified communication abstraction layer.

Initial minimal implementation providing:
- Descriptor builder for serial resources
- SerialChannelRequest pydantic model
- LocalSerialBackend wrapping pyserial (on-demand open)
- CommChannel facade used by higher-level deps (e.g., SerialDep.from_channel)

Remote / VISA backends can be added later by implementing the BackendProtocol.
"""
from dataclasses import dataclass
from typing import Protocol, Optional, Union, Any, Dict
from urllib.parse import parse_qs

try:  # VISA optional
    import pyvisa  # type: ignore
except Exception:  # pragma: no cover
    pyvisa = None  # type: ignore
import requests  # type: ignore

try:
    import serial  # type: ignore
except Exception:  # pragma: no cover - tests patch serial anyway
    serial = None  # type: ignore


# ---------------- Descriptor Helpers -----------------


def build_serial_descriptor(
    port: str, *, baudrate: int, timeout: Union[int, float]
) -> str:
    return f"serial:{port}?baud={baudrate}&timeout={timeout}"


def parse_descriptor(descriptor: str) -> Dict[str, Any]:
    """Parse a descriptor string back into its components.

    Supported forms:
      serial:PORT?baud=9600&timeout=1.0
      visa:RESOURCE?timeout=5.0
      http[s]://host:port/path

    Returns a dict with keys: type (serial|visa|http), plus parameters needed
    to reconstruct an appropriate backend or request.
    """
    if descriptor.startswith("serial:"):
        body = descriptor[len("serial:") :]
        if "?" in body:
            port, query = body.split("?", 1)
            params = {k: v[0] for k, v in parse_qs(query).items()}
        else:
            port, params = body, {}
        return {
            "type": "serial",
            "port": port,
            "baudrate": int(params.get("baud", 9600)),
            "timeout": float(params.get("timeout", 1.0)),
        }
    if descriptor.startswith("visa:"):
        body = descriptor[len("visa:") :]
        if "?" in body:
            resource, query = body.split("?", 1)
            params = {k: v[0] for k, v in parse_qs(query).items()}
        else:
            resource, params = body, {}
        return {
            "type": "visa",
            "resource": resource,
            "timeout": float(params.get("timeout", 5.0)),
        }
    if descriptor.startswith("http://") or descriptor.startswith("https://"):
        # Treat the whole descriptor as base_url; we do not currently parse further
        return {"type": "http", "base_url": descriptor.rstrip("/")}
    if descriptor.startswith("dummy:"):
        name = descriptor[len("dummy:") :]
        return {"type": "dummy", "name": name}
    raise ValueError(f"Unrecognized descriptor format: {descriptor}")


# ---------------- Request Models ---------------------
try:
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover
    BaseModel = object  # type: ignore
    Field = lambda *a, **k: None  # type: ignore
    Literal = str  # type: ignore


class SerialChannelRequest(BaseModel):  # type: ignore[misc]
    type: str = "serial"  # discriminator value
    port: str
    baudrate: int = 9600
    timeout: float = 1.0

    def descriptor(self) -> str:
        return build_serial_descriptor(
            self.port, baudrate=self.baudrate, timeout=self.timeout
        )


class VisaChannelRequest(BaseModel):  # type: ignore[misc]
    type: str = "visa"
    resource: str
    timeout: float = 5.0

    def descriptor(self) -> str:
        return f"visa:{self.resource}?timeout={self.timeout}"


class HttpChannelRequest(BaseModel):  # type: ignore[misc]
    type: str = "http"
    host: str
    port: int = 80
    base_path: str = ""

    def descriptor(self) -> str:
        return f"http://{self.host}:{self.port}{self.base_path}".rstrip("/")


class DummyChannelRequest(BaseModel):  # type: ignore[misc]
    type: str = "dummy"
    name: str

    def descriptor(self) -> str:
        return f"dummy:{self.name}"


ChannelRequest = Union[
    SerialChannelRequest, VisaChannelRequest, HttpChannelRequest, DummyChannelRequest
]


# ---------------- Backend Protocol -------------------
class BackendProtocol(Protocol):
    def open(self) -> None: ...
    def close(self) -> None: ...
    @property
    def is_open(self) -> bool: ...

    def write(self, data: bytes) -> int: ...
    def read(self, size: Optional[int] = None) -> bytes: ...
    def readline(self) -> bytes: ...


# ---------------- Serial Backend ---------------------
@dataclass
class LocalSerialBackend:
    port: str
    baudrate: int
    timeout: float
    _serial: Any | None = None  # treat as Any to avoid partial unknown complaints

    def open(self) -> None:
        if self._serial is None:
            if serial is None:  # pragma: no cover
                raise RuntimeError("serial module not available")
            self._serial = serial.Serial(
                port=self.port, baudrate=self.baudrate, timeout=self.timeout
            )

    def close(self) -> None:
        if self._serial and getattr(self._serial, "is_open", False):  # type: ignore[truthy-bool]
            self._serial.close()

    @property
    def is_open(self) -> bool:
        return bool(self._serial and getattr(self._serial, "is_open", False))

    def write(self, data: bytes) -> int:
        self.open()
        assert self._serial is not None
        try:
            self._serial.flush()
        except Exception:  # pragma: no cover
            pass
        return self._serial.write(data)  # type: ignore[no-any-return]

    def read(self, size: Optional[int] = None) -> bytes:
        self.open()
        assert self._serial is not None
        if size is None:
            try:
                return self._serial.read_all()
            except Exception:  # pragma: no cover
                return self._serial.read(9999)
        return self._serial.read(size)

    def readline(self) -> bytes:
        self.open()
        assert self._serial is not None
        return self._serial.readline()


# ---------------- VISA Backend ----------------------
@dataclass
class VisaBackend:
    resource: str
    timeout: float
    _inst: Any | None = None

    def open(self) -> None:
        if self._inst is None:
            if pyvisa is None:  # pragma: no cover
                raise RuntimeError("pyvisa not available")
            rm = pyvisa.ResourceManager("@py")
            self._inst = rm.open_resource(self.resource)
            self._inst.timeout = int(self.timeout * 1000)

    def close(self) -> None:
        if self._inst is not None:
            try:
                self._inst.close()
            except Exception:
                pass

    @property
    def is_open(self) -> bool:
        return self._inst is not None

    def write(self, data: bytes) -> int:
        self.open()
        assert self._inst is not None
        s = data.decode()
        self._inst.write(s)
        return len(data)

    def read(self, size: Optional[int] = None) -> bytes:
        self.open()
        assert self._inst is not None
        if size is not None:  # VISA read length hint not always supported
            resp = self._inst.read_bytes(size)
        else:
            resp = self._inst.read()
        if isinstance(resp, str):
            resp = resp.encode()
        return resp

    def readline(self) -> bytes:
        return self.read()


# ---------------- HTTP Backend ----------------------
@dataclass
class HttpBackend:
    base_url: str  # e.g., http://host:port
    _buffer: bytes = b""

    def open(self) -> None:  # HTTP is stateless; nothing to do
        return None

    def close(self) -> None:
        return None

    @property
    def is_open(self) -> bool:
        return True

    def write(self, data: bytes) -> int:
        # Interpret data as a GET path for simplicity in this minimal backend
        path = data.decode().strip()
        try:
            r = requests.get(f"{self.base_url}/{path.lstrip('/')}")
            self._buffer = r.content
        except Exception:
            self._buffer = b""
        return len(data)

    def read(self, size: Optional[int] = None) -> bytes:
        if size is None:
            return self._buffer
        return self._buffer[:size]

    def readline(self) -> bytes:
        return self.read()


# ---------------- Remote Backend Skeleton -----------
@dataclass
class _BaseRemoteBackend:
    descriptor: str
    uri: str  # pyro URI of remote broker
    _proxy: Any | None = None

    def open(self) -> None:  # pragma: no cover
        if self._proxy is None:
            try:
                import Pyro5.api as pyro  # type: ignore
            except Exception as e:  # noqa: BLE001
                raise RuntimeError("Pyro5 not installed") from e
            self._proxy = pyro.Proxy(self.uri)

    def close(self) -> None:
        if self._proxy is not None:
            try:
                self._proxy._pyroRelease()
            except Exception:
                pass

    @property
    def is_open(self) -> bool:
        return self._proxy is not None

    # Common remote operations delegating to broker
    def write(self, data: bytes) -> int:  # pragma: no cover
        self.open()
        assert self._proxy is not None
        return self._proxy.write(self.descriptor, data)

    def read(self, size: Optional[int] = None) -> bytes:  # pragma: no cover
        self.open()
        assert self._proxy is not None
        payload = self._proxy.read(self.descriptor, size)
        return self._coerce_bytes(payload)

    def readline(self) -> bytes:  # pragma: no cover
        self.open()
        assert self._proxy is not None
        payload = self._proxy.readline(self.descriptor)
        return self._coerce_bytes(payload)

    # --- local helper mirroring broker normalization ---
    def _coerce_bytes(self, payload: Any) -> bytes:
        import base64

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


@dataclass
class RemoteSerialBackend(_BaseRemoteBackend):
    """Remote backend for serial descriptors.

    Exists mainly for future serial-specific remote behaviors (e.g., line-ending normalization,
    latency compensation heuristics, flow control negotiation). Currently identical to base.
    """


@dataclass
class RemoteVisaBackend(_BaseRemoteBackend):
    """Remote backend for VISA descriptors.

    Placeholder for VISA-specific remote logic (e.g., chunked read policies, SRQ handling later).
    """


@dataclass
class RemoteHttpBackend(_BaseRemoteBackend):
    """Remote backend for HTTP descriptors (rare but keeps symmetry)."""


# ---------------- Dummy Backend (test/demo) ---------
@dataclass
class DummyBackend:
    name: str
    _buffer: bytes = b""

    def open(self) -> None:  # no-op
        return None

    def close(self) -> None:  # no-op
        return None

    @property
    def is_open(self) -> bool:
        return True

    def write(self, data: bytes) -> int:
        text = data.decode().strip()
        if text.upper() in {"MEAS:VOLT?", "VOLT?", "MEAS?"}:
            import random, time

            value = random.uniform(0.0, 1.0)
            print(
                f"[DummyBackend:{self.name} server] voltage measurement requested -> {value:.6f} V"
            )
            # Simulate hardware latency
            time.sleep(0.01)
            self._buffer = f"{value:.6f}".encode()
        else:
            self._buffer = b""
        return len(data)

    def read(self, size: Optional[int] = None) -> bytes:
        if size is None:
            return self._buffer
        return self._buffer[:size]

    def readline(self) -> bytes:
        return self.read()


@dataclass
class RemoteDummyBackend(_BaseRemoteBackend):
    """Remote backend for dummy descriptors."""


# ---------------- CommChannel Facade -----------------
class CommChannel:
    def __init__(self, backend: BackendProtocol, descriptor: str):
        self._backend = backend
        self._descriptor = descriptor

    @property
    def descriptor(self) -> str:
        return self._descriptor

    def write(self, data: str | bytes) -> int:
        if isinstance(data, str):
            data = data.encode()
        return self._backend.write(data)

    def read(self, size: Optional[int] = None) -> bytes:
        return self._backend.read(size)

    def readline(self) -> bytes:
        return self._backend.readline()

    def query(self, cmd: str) -> bytes:
        self.write(cmd)
        return self.readline()

    def close(self) -> None:
        self._backend.close()


__all__ = [
    "SerialChannelRequest",
    "VisaChannelRequest",
    "HttpChannelRequest",
    "DummyChannelRequest",
    "build_serial_descriptor",
    "parse_descriptor",
    "CommChannel",
    "LocalSerialBackend",
    "VisaBackend",
    "HttpBackend",
    "RemoteSerialBackend",
    "RemoteVisaBackend",
    "RemoteHttpBackend",
    "DummyBackend",
    "RemoteDummyBackend",
]
