#!/bin/bash

# Check if the --debug argument is passed to the script
DEBUG_FLAG=""
if [[ "$1" == "--debug" ]]; then
  DEBUG_FLAG="--debug"
fi

# Navigate to the backend directory and run the Python script with the debug flag if provided
uv run ./backend/main.py $DEBUG_FLAG