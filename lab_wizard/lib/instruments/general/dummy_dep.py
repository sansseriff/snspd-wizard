from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any

from lab_wizard.lib.instruments.general.comm import DummyBackend
from lab_wizard.lib.utilities.codec import coerce_bytes, ensure_bytes


class DummyDep(ABC):
    @property
    @abstractmethod
    def is_open(self) -> bool: ...

    @abstractmethod
    def write(self, data: bytes | str) -> int: ...

    @abstractmethod
    def read(self, size: Optional[int] = None) -> bytes: ...

    @abstractmethod
    def readline(self) -> bytes: ...

    @abstractmethod
    def close(self) -> None: ...


@dataclass
class LocalDummyDep(DummyDep):
    name: str
    _backend: DummyBackend | None = None

    def _ensure(self) -> DummyBackend:
        if self._backend is None:
            self._backend = DummyBackend(self.name)
        return self._backend

    @property
    def is_open(self) -> bool:
        return True

    def write(self, data: bytes | str) -> int:
        if isinstance(data, str):
            data = data.encode()
        return self._ensure().write(data)

    def read(self, size: Optional[int] = None) -> bytes:
        return self._ensure().read(size)

    def readline(self) -> bytes:
        return self._ensure().readline()

    def close(self) -> None:
        return None


class RemoteDummyDep(DummyDep):  # pragma: no cover - network usage
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
