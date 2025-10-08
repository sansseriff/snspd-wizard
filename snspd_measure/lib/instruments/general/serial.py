from typing import Optional, Any

try:  # pragma: no cover
    import serial  # type: ignore
except Exception:  # pragma: no cover
    serial = None  # type: ignore

from lib.instruments.general.parent_child import Dependency


class SerialDep(Dependency):
    """Serial dependency wrapping either a CommChannel or a direct pyserial connection.

    Preferred path: constructed via from_channel() when a CommChannel already
    exists (e.g. provided by Computer). Backward-compatible path: direct
    construction with port/baudrate/timeout still opens pyserial.
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        timeout: int = 1,
        *,
        channel: Any | None = None,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._channel = channel  # CommChannel or None
        self.serial: Optional[Any] = None  # underlying serial.Serial if locally opened
        self.offline: bool = False

        if self._channel is None:
            self._open_local()

    @classmethod
    def from_channel(
        cls, port: str, baudrate: int, timeout: int, channel_obj: Any
    ) -> "SerialDep":
        return cls(port, baudrate, timeout, channel=channel_obj)

    def _open_local(self) -> bool:
        if serial is None:  # pragma: no cover
            self.offline = True
            return False
        try:
            self.serial = serial.Serial(
                port=self.port, baudrate=self.baudrate, timeout=self.timeout
            )
            return True
        except Exception as e:  # pragma: no cover (handled by fakes in tests)
            print(f"Failed to connect to {self.port}: {e}")
            self.offline = True
            return False

    # Backward name for existing callers
    connect = _open_local

    def disconnect(self) -> bool:
        if self._channel is not None:
            try:
                self._channel.close()
            except Exception:
                pass
            return True
        if self.serial and getattr(self.serial, "is_open", False):
            try:
                self.serial.close()
            except Exception:
                pass
        return True

    def __del__(self):  # pragma: no cover
        try:
            self.disconnect()
        except Exception:
            pass

    def _write_bytes(self, data: bytes) -> int | None:
        if self._channel is not None:
            return self._channel.write(data)
        if self.offline:
            return len(data)
        if not self.serial or not getattr(self.serial, "is_open", False):
            raise RuntimeError("Serial connection not open")
        try:
            self.serial.flush()
        except Exception:
            pass
        return self.serial.write(data)

    def write(self, cmd: str) -> int | None:
        return self._write_bytes(cmd.encode())

    def _read_line(self) -> bytes:
        if self._channel is not None:
            # Prefer readline if available; fallback to read
            if hasattr(self._channel, "readline"):
                return self._channel.readline()
            return self._channel.read()
        if self.offline:
            return b""
        if not self.serial or not getattr(self.serial, "is_open", False):
            raise RuntimeError("Serial connection not open")
        return self.serial.readline()

    def read(self) -> bytes:
        return self._read_line()

    def query(self, cmd: str) -> bytes:
        self.write(cmd)
        return self.read()
