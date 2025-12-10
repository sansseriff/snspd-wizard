from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any

from lab_wizard.lib.instruments.general.parent_child import Dependency
from lab_wizard.lib.instruments.general.comm import LocalSerialBackend
from lab_wizard.lib.utilities.codec import ensure_bytes, coerce_bytes


class SerialDep(Dependency, ABC):
    """Abstract serial-like dependency API.

    Concrete implementations: LocalSerialDep, RemoteSerialDep
    """

    @property
    @abstractmethod
    def is_open(self) -> bool:  # pragma: no cover - interface
        ...

    @abstractmethod
    def write(self, data: bytes | str) -> int: ...  # returns bytes written

    @abstractmethod
    def read(self, size: Optional[int] = None) -> bytes: ...

    @abstractmethod
    def readline(self) -> bytes: ...

    def query(self, cmd: str) -> bytes:
        self.write(cmd)
        return self.readline()

    @abstractmethod
    def close(self) -> None: ...


@dataclass
class LocalSerialDep(SerialDep):
    port: str
    baudrate: int = 9600
    timeout: float = 1.0
    _backend: LocalSerialBackend | None = None

    def _ensure(self) -> LocalSerialBackend:
        if self._backend is None:
            self._backend = LocalSerialBackend(
                port=self.port, baudrate=self.baudrate, timeout=self.timeout
            )
        return self._backend

    @property
    def is_open(self) -> bool:
        b = self._ensure()
        return b.is_open

    def write(self, data: bytes | str) -> int:
        return self._ensure().write(ensure_bytes(data))

    def read(self, size: Optional[int] = None) -> bytes:
        return self._ensure().read(size)

    def readline(self) -> bytes:
        return self._ensure().readline()

    def close(self) -> None:
        if self._backend is not None:
            self._backend.close()


class RemoteSerialDep(SerialDep):  # pragma: no cover - network usage
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

    def write(self, data: bytes | str) -> int:
        return int(self._ensure().write(ensure_bytes(data)))

    def read(self, size: Optional[int] = None) -> bytes:
        payload = self._ensure().read(size)
        return coerce_bytes(payload)

    def readline(self) -> bytes:
        payload = self._ensure().readline()
        return coerce_bytes(payload)

    def close(self) -> None:
        if self._proxy is not None:
            try:
                self._proxy.close()
            except Exception:
                pass
