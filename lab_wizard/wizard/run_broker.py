from __future__ import annotations

"""Launch the Pyro5 channel broker.

Usage (server side). Run inside snspd_measure folder:
    uv run python -m wizard.run_broker --host 127.0.0.1 --port 9100 

Clients then set ComputerParams(mode="remote", server_uri="PYRO:objid@host:port") after
copying the printed URI (or you can compute it if you fix a name server strategy).

This minimal launcher runs a raw daemon loop; CTRL+C to exit.
"""
import argparse

from lib.instruments.general.broker import ChannelBroker

try:
    import Pyro5.api as pyro  # type: ignore
except Exception as e:  # pragma: no cover
    raise SystemExit("Pyro5 not installed; add pyro5 to dependencies") from e


def main():  # pragma: no cover - manual usage
    ap = argparse.ArgumentParser(description="Run channel broker")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=0, help="TCP port (0 = ephemeral)")
    args = ap.parse_args()

    broker = ChannelBroker()
    daemon = pyro.Daemon(host=args.host, port=args.port)
    uri = daemon.register(broker)  # type: ignore[arg-type]
    print(f"ChannelBroker running at {uri}")
    print("Press Ctrl+C to stop.")
    try:
        daemon.requestLoop()
    except KeyboardInterrupt:
        print("\nBroker shutting down...")
    finally:
        daemon.close()


if __name__ == "__main__":  # pragma: no cover
    main()
