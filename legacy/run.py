#!/usr/bin/env python3
"""
Startup script for Spelling Numbers Calculator
"""
import sys
import subprocess

def safe_import_numpy():
    try:
        import numpy  # type: ignore  # noqa: F401
        return True
    except ImportError:
        return False

def check_requirements():
    """Check and install requirements"""
    if safe_import_numpy():
        print("✓ NumPy is installed")
        return
    print("Installing NumPy...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
        if safe_import_numpy():
            print("✓ NumPy installed successfully")
        else:
            print("✗ NumPy installation appears to have failed")
    except Exception as e:
        print(f"✗ Failed to install NumPy: {e}")

def main():
    print("=" * 60)
    print("Spelling Numbers with Variables Calculator")
    print("=" * 60)
    print()
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7 or higher is required")
        print(f"You are using Python {sys.version}")
        sys.exit(1)
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check requirements
    check_requirements()
    
    print()
    print("Starting application...")
    print()
    
    # Import and run the app
    from app import main as run_app
    run_app()

if __name__ == "__main__":
    main()
