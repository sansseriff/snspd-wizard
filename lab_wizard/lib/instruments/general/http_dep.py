from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

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
    """Local HTTP dependency using requests library."""

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
