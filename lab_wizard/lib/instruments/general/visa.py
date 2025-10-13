from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

try:  # pragma: no cover
    import pyvisa  # type: ignore
except Exception:  # pragma: no cover
    pyvisa = None  # type: ignore

from lib.utilities.codec import coerce_str, coerce_bytes


class VisaDep(ABC):
    @property
    @abstractmethod
    def is_open(self) -> bool: ...

    @abstractmethod
    def write(self, cmd: str) -> None: ...

    @abstractmethod
    def read(self) -> str: ...

    @abstractmethod
    def read_bytes(self, n: int) -> bytes: ...

    @abstractmethod
    def query(self, cmd: str) -> str: ...

    @abstractmethod
    def clear(self) -> None: ...

    @abstractmethod
    def set_timeout(self, s: float) -> None: ...

    @abstractmethod
    def close(self) -> None: ...


@dataclass
class LocalVisaDep(VisaDep):
    resource: str
    timeout: float = 5.0
    _inst: Any | None = None

    def _ensure(self):
        if self._inst is None:
            if pyvisa is None:  # pragma: no cover
                raise RuntimeError("pyvisa not available")
            rm = pyvisa.ResourceManager("@py")
            self._inst = rm.open_resource(self.resource)
            self._inst.timeout = int(self.timeout * 1000)
        return self._inst

    @property
    def is_open(self) -> bool:
        return self._inst is not None

    def write(self, cmd: str) -> None:
        self._ensure().write(cmd)

    def read(self) -> str:
        payload = self._ensure().read()
        return coerce_str(payload)

    def read_bytes(self, n: int) -> bytes:
        return coerce_bytes(self._ensure().read_bytes(n))

    def query(self, cmd: str) -> str:
        self.write(cmd)
        return self.read()

    def clear(self) -> None:
        inst = self._ensure()
        try:
            inst.clear()
        except Exception:
            pass

    def set_timeout(self, s: float) -> None:
        self._ensure().timeout = int(s * 1000)

    def close(self) -> None:
        if self._inst is not None:
            try:
                self._inst.close()
            except Exception:
                pass


class RemoteVisaDep(VisaDep):  # pragma: no cover - network usage
    def __init__(self, uri: str) -> None:
        self._uri = uri
        self._proxy: Any | None = None

    def _ensure(self):
        if self._proxy is None:
            try:
                import Pyro5.api as pyro  # type: ignore
            except Exception as e:  # noqa: BLE001
                raise RuntimeError("Pyro5 not installed") from e
            self._proxy = pyro.Proxy(self._uri)
        return self._proxy

    @property
    def is_open(self) -> bool:
        return self._proxy is not None

    def write(self, cmd: str) -> None:
        self._ensure().write(cmd)

    def read(self) -> str:
        return str(self._ensure().read())

    def read_bytes(self, n: int) -> bytes:
        payload = self._ensure().read_bytes(n)
        return coerce_bytes(payload)

    def query(self, cmd: str) -> str:
        return str(self._ensure().query(cmd))

    def clear(self) -> None:
        self._ensure().clear()

    def set_timeout(self, s: float) -> None:
        self._ensure().set_timeout(float(s))

    def close(self) -> None:
        if self._proxy is not None:
            try:
                self._proxy.close()
            except Exception:
                pass
