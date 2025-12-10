from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from lab_wizard.lib.utilities.codec import coerce_bytes

try:  # pragma: no cover
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore


class HttpDep(ABC):
    @property
    @abstractmethod
    def is_open(self) -> bool: ...

    @abstractmethod
    def get(self, path: str) -> bytes: ...

    @abstractmethod
    def put(self, path: str, data: bytes | dict) -> bytes: ...

    @abstractmethod
    def post(self, path: str, data: bytes | dict) -> bytes: ...

    @abstractmethod
    def delete(self, path: str) -> bytes: ...

    @abstractmethod
    def close(self) -> None: ...


@dataclass
class LocalHttpDep(HttpDep):
    base_url: str

    @property
    def is_open(self) -> bool:
        return True

    def _req(self, method: str, path: str, data: bytes | dict | None = None) -> bytes:
        if requests is None:  # pragma: no cover
            raise RuntimeError("requests not available")
        url = f"{self.base_url}/{path.lstrip('/')}"
        if isinstance(data, bytes):
            resp = requests.request(method, url, data=data)
        elif isinstance(data, dict):
            resp = requests.request(method, url, json=data)
        else:
            resp = requests.request(method, url)
        return resp.content

    def get(self, path: str) -> bytes:
        return self._req("GET", path)

    def put(self, path: str, data: bytes | dict) -> bytes:
        return self._req("PUT", path, data)

    def post(self, path: str, data: bytes | dict) -> bytes:
        return self._req("POST", path, data)

    def delete(self, path: str) -> bytes:
        return self._req("DELETE", path)

    def close(self) -> None:
        return None


class RemoteHttpDep(HttpDep):  # pragma: no cover - network usage
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

    def get(self, path: str) -> bytes:
        payload = self._ensure().get(path)
        return coerce_bytes(payload)

    def put(self, path: str, data: bytes | dict) -> bytes:
        payload = self._ensure().put(path, data)
        return coerce_bytes(payload)

    def post(self, path: str, data: bytes | dict) -> bytes:
        payload = self._ensure().post(path, data)
        return coerce_bytes(payload)

    def delete(self, path: str) -> bytes:
        payload = self._ensure().delete(path)
        return coerce_bytes(payload)

    def close(self) -> None:
        if self._proxy is not None:
            try:
                self._proxy.close()
            except Exception:
                pass
