import argparse
import os
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser("wizard")
    parser.add_argument(
        "--projects",
        default=os.getcwd(),
        help="Path to projects root (default: current directory)",
    )
    parser.add_argument("--port", type=int, default=8884, help="Port for the server")
    parser.add_argument("--no-ui", action="store_true", help="Run without desktop UI")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args, extra = parser.parse_known_args()

    environment = os.environ.copy()
    environment["LAB_WIZARD_PROJECTS_DIR"] = os.path.abspath(args.projects)

    command = [
        sys.executable,
        "-m",
        "lab_wizard.wizard.backend.main",
        "--port",
        str(args.port),
    ]
    if args.no_ui:
        command.append("--no-ui")
    if args.debug:
        command.append("--debug")
    command += extra

    raise SystemExit(subprocess.call(command, env=environment))





