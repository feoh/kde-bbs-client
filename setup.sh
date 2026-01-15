#!/bin/bash
# Setup script for KDE BBS Client

echo "Setting up KDE BBS Client..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is required but not installed."
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Sync dependencies
echo "Syncing dependencies with uv..."
uv sync

echo ""
echo "Setup complete!"
echo ""
echo "To run the application:"
echo "  uv run python kdebbsclient.py"
echo ""
echo "Or simply run:"
echo "  ./run.sh"
