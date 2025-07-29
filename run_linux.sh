#!/bin/bash

# Webcomic Downloader - Linux Launcher
# This script checks for dependencies and runs the application

echo "🧽 Webcomic Downloader - Linux Launcher"
echo "========================================"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Python if not found
install_python() {
    echo "Python not found. Attempting to install..."
    
    if command_exists apt-get; then
        echo "Detected Debian/Ubuntu system. Installing Python..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv
    elif command_exists dnf; then
        echo "Detected Fedora system. Installing Python..."
        sudo dnf install -y python3 python3-pip
    elif command_exists yum; then
        echo "Detected CentOS/RHEL system. Installing Python..."
        sudo yum install -y python3 python3-pip
    elif command_exists pacman; then
        echo "Detected Arch Linux system. Installing Python..."
        sudo pacman -S --noconfirm python python-pip
    elif command_exists zypper; then
        echo "Detected openSUSE system. Installing Python..."
        sudo zypper install -y python3 python3-pip
    else
        echo "❌ Could not detect package manager. Please install Python 3.8+ manually."
        echo "Visit https://www.python.org/downloads/ for installation instructions."
        exit 1
    fi
}

# Function to install pip if not found
install_pip() {
    echo "pip not found. Attempting to install..."
    
    if command_exists apt-get; then
        sudo apt-get install -y python3-pip
    elif command_exists dnf; then
        sudo dnf install -y python3-pip
    elif command_exists yum; then
        sudo yum install -y python3-pip
    elif command_exists pacman; then
        sudo pacman -S --noconfirm python-pip
    elif command_exists zypper; then
        sudo zypper install -y python3-pip
    else
        echo "❌ Could not install pip automatically. Please install it manually."
        exit 1
    fi
}

# Check if Python is installed
if ! command_exists python3; then
    echo "❌ Python 3 not found."
    install_python
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "❌ Python 3.8+ required. Found version $PYTHON_VERSION"
    echo "Please upgrade Python to version 3.8 or higher."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"

# Check if pip is installed
if ! command_exists pip3; then
    echo "❌ pip3 not found."
    install_pip
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

# Check for additional system dependencies (for GUI)
echo "🔍 Checking for system GUI dependencies..."

# Check for X11/Wayland display
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo "⚠️  No display detected. Make sure you're running this in a graphical environment."
    echo "If you're using SSH, make sure X11 forwarding is enabled."
fi

# Check for common GUI libraries
MISSING_LIBS=""
if ! ldconfig -p | grep -q libQt6Core; then
    MISSING_LIBS="$MISSING_LIBS qt6-base"
fi

if ! ldconfig -p | grep -q libX11; then
    MISSING_LIBS="$MISSING_LIBS libx11-6"
fi

if [ -n "$MISSING_LIBS" ]; then
    echo "⚠️  Some system libraries may be missing: $MISSING_LIBS"
    echo "If the application doesn't start, you may need to install these packages:"
    echo "  Ubuntu/Debian: sudo apt-get install $MISSING_LIBS"
    echo "  Fedora: sudo dnf install $MISSING_LIBS"
    echo "  Arch: sudo pacman -S $MISSING_LIBS"
fi

# Run the application
echo ""
echo "🚀 Starting Webcomic Downloader..."
echo "========================================"
python main.py

# Deactivate virtual environment when done
deactivate 