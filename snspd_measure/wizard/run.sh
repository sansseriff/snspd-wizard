#!/bin/bash

# Forward all CLI args to the backend (supports --debug, --no-ui, --port, etc.)
uv run ./backend/main.py "$@"