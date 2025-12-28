#!/bin/bash
# Setup script for ANT+ Device Display project
# Creates a virtual environment and installs dependencies

set -e  # Exit on error

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

echo "Setting up ANT+ Device Display project..."
echo "Project directory: $PROJECT_DIR"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found. Please install Python 3.7+."
    exit 1
fi

# Check for venv module and provide helpful instructions
if ! python3 -m venv --help &> /dev/null; then
    echo "Error: python3-venv module is not available."
    echo ""
    if command -v apt &> /dev/null; then
        echo "On Ubuntu/Debian systems, install with:"
        echo "  sudo apt update"
        echo "  sudo apt install python3-venv python3-pip"
    elif command -v yum &> /dev/null; then
        echo "On CentOS/RHEL systems, install with:"
        echo "  sudo yum install python3-venv python3-pip"
    elif command -v dnf &> /dev/null; then
        echo "On Fedora systems, install with:"
        echo "  sudo dnf install python3-venv python3-pip"
    elif command -v pacman &> /dev/null; then
        echo "On Arch systems, install with:"
        echo "  sudo pacman -S python python-pip"
    else
        echo "Please install the python3-venv package for your distribution."
    fi
    echo ""
    echo "Then run this setup script again."
    exit 1
fi

# Create virtual environment if it doesn't exist or is incomplete
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    if [ -d "$VENV_DIR" ]; then
        echo "Removing incomplete virtual environment..."
        rm -rf "$VENV_DIR"
    fi
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists and is valid."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Configure Python to use hidden cache directory
export PYTHONPYCACHEPREFIX="$PROJECT_DIR/.pycache"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r "$PROJECT_DIR/requirements.txt"

# Install development dependencies
echo "Installing development dependencies..."
pip install -r "$PROJECT_DIR/requirements-dev.txt"

# Optional: install alternative ANT backend from Git repository
if [ -n "$ANT_BACKEND_GIT" ]; then
    echo "Installing alternative ANT backend from: $ANT_BACKEND_GIT"
    pip install "git+$ANT_BACKEND_GIT"
fi

# Set up pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

echo ""
echo "Setup complete!"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run the application:"
echo "  source .venv/bin/activate"
echo "  python -m pyantdisplay.main"
echo ""
echo "To deactivate the virtual environment when done:"
echo "  deactivate"