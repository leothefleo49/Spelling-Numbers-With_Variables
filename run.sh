#!/bin/bash
# Universal launcher script for Linux/macOS

echo "============================================"
echo " Spelling Numbers Calculator - MODERN"
echo "============================================"
echo ""

# Try to find Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ ERROR: Python not found!"
    echo "Please install Python 3.7 or higher"
    exit 1
fi

# Run the launcher
$PYTHON launch.py

exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo ""
    echo "Application exited with an error."
    read -p "Press Enter to exit..."
fi

exit $exit_code
