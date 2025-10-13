from __future__ import annotations

from typing import Any
import base64


def coerce_bytes(payload: Any) -> bytes:
    """Normalize various payload shapes into raw bytes.

    Supports:
    - bytes -> bytes
    - {"data": base64str, ...} -> base64-decoded bytes
    - str -> UTF-8 encoded bytes
    - other -> repr(payload).encode()
    """
    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, dict) and "data" in payload:
        v = payload.get("data")
        if isinstance(v, str):
            try:
                return base64.b64decode(v)
            except Exception:
                return v.encode()
    if isinstance(payload, str):
        return payload.encode()
    return repr(payload).encode()


def coerce_str(payload: Any, *, encoding: str = "utf-8", errors: str = "strict") -> str:
    """Normalize to text, decoding bytes or base64 dict payloads to string.

    If decoding fails, falls back to str(payload).
    """
    try:
        if isinstance(payload, bytes):
            return payload.decode(encoding, errors)
        if isinstance(payload, dict) and "data" in payload:
            v = payload.get("data")
            if isinstance(v, str):
                try:
                    return base64.b64decode(v).decode(encoding, errors)
                except Exception:
                    return v
        return str(payload)
    except Exception:
        return str(payload)


def ensure_bytes(data: Any) -> bytes:
    """Accept bytes | str | {data: base64} | Any and return bytes.

    Useful for server-side write handlers.
    """
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return data.encode()
    if isinstance(data, dict) and "data" in data:
        v = data.get("data")
        if isinstance(v, str):
            try:
                return base64.b64decode(v)
            except Exception:
                return v.encode()
    return repr(data).encode()
