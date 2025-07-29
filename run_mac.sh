#!/bin/bash

# Webcomic Downloader - macOS Launcher
# This script checks for dependencies and runs the application

echo "🧽 Webcomic Downloader - macOS Launcher"
echo "========================================"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Homebrew if not found
install_homebrew() {
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for current session
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        export PATH="/opt/homebrew/bin:$PATH"
    elif [[ -f "/usr/local/bin/brew" ]]; then
        export PATH="/usr/local/bin:$PATH"
    fi
}

# Function to install Python using Homebrew
install_python_brew() {
    echo "Installing Python via Homebrew..."
    brew install python@3.11
    
    # Add Python to PATH
    if [[ -f "/opt/homebrew/bin/python3" ]]; then
        export PATH="/opt/homebrew/bin:$PATH"
    elif [[ -f "/usr/local/bin/python3" ]]; then
        export PATH="/usr/local/bin:$PATH"
    fi
}

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is designed for macOS only."
    exit 1
fi

# Check macOS version
MACOS_VERSION=$(sw_vers -productVersion)
echo "📱 macOS version: $MACOS_VERSION"

# Check if Python is installed
if ! command_exists python3; then
    echo "❌ Python 3 not found."
    
    # Try to install via Homebrew
    if command_exists brew; then
        echo "✅ Homebrew found. Installing Python..."
        install_python_brew
    else
        echo "❌ Homebrew not found."
        install_homebrew
        install_python_brew
    fi
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "❌ Python 3.8+ required. Found version $PYTHON_VERSION"
    echo "Upgrading Python..."
    if command_exists brew; then
        brew upgrade python@3.11
    else
        echo "Please install Python 3.8+ manually from https://www.python.org/downloads/"
        exit 1
    fi
fi

echo "✅ Python $PYTHON_VERSION found"

# Check if pip is installed
if ! command_exists pip3; then
    echo "❌ pip3 not found. Installing..."
    if command_exists brew; then
        brew install python@3.11
    else
        echo "Please install pip manually."
        exit 1
    fi
fi

echo "✅ pip3 found"

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
echo "📋 Checking dependencies..."
if ! python -c "import PySide6, requests, beautifulsoup4, Pillow" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies. Please check your internet connection and try again."
        exit 1
    fi
    echo "✅ Dependencies installed successfully"
else
    echo "✅ All dependencies already installed"
fi

# Check for GUI dependencies
echo "🔍 Checking for GUI dependencies..."

# Check if we're in a GUI environment
if [[ -z "$DISPLAY" && -z "$WAYLAND_DISPLAY" ]]; then
    # On macOS, check if we're running in a terminal that can display GUI
    if [[ -n "$TERM_PROGRAM" ]]; then
        echo "✅ Terminal environment detected"
    else
        echo "⚠️  Make sure you're running this in a terminal that supports GUI applications"
    fi
fi

# Check for Xcode Command Line Tools (needed for some Python packages)
if ! command_exists xcode-select; then
    echo "⚠️  Xcode Command Line Tools not found. Some packages may fail to install."
    echo "To install: xcode-select --install"
fi

# Check for Qt libraries (PySide6 dependency)
if ! python -c "from PySide6.QtCore import QCoreApplication" 2>/dev/null; then
    echo "⚠️  Qt libraries may be missing. If the app doesn't start, try:"
    echo "  brew install qt@6"
fi

# Run the application
echo ""
echo "🚀 Starting Webcomic Downloader..."
echo "========================================"
python main.py

# Deactivate virtual environment when done
deactivate 