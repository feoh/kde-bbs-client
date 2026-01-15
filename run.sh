#!/bin/bash
# Run script for KDE BBS Client

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is required but not installed."
    echo "Please run ./setup.sh first"
    exit 1
fi

# Run the application with uv
uv run python kdebbsclient.py
