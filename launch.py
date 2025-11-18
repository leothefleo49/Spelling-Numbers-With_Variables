#!/usr/bin/env python3
"""
Universal Launcher for Spelling Numbers Calculator
Auto-installs dependencies and runs on any platform
"""

import sys
import subprocess
import os
import platform

def print_header():
    """Print colorful header"""
    print("\n" + "="*60)
    print("✨ SPELLING NUMBERS CALCULATOR - MODERN EDITION ✨")
    print("="*60 + "\n")

def check_python_version():
    """Check if Python version is sufficient"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 7):
        print("❌ ERROR: Python 3.7 or higher is required!")
        print(f"   You are using Python {version.major}.{version.minor}.{version.micro}")
        print("\n📥 Please install Python 3.7+ from:")
        print("   https://www.python.org/downloads/")
        return False
    
    print("✅ Python version OK")
    return True

def check_and_install_numpy():
    """Check if NumPy is installed; tolerate absence by continuing."""
    print("\n🔍 Checking NumPy installation...")
    try:
        import numpy  # type: ignore  # noqa: F401
        print("✅ NumPy is installed")
        return True
    except ImportError:
        print("⚠️  NumPy not found. Attempting lightweight install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy", "--quiet"])
            import numpy  # type: ignore  # noqa: F401
            print("✅ NumPy installed successfully")
            return True
        except Exception as e:
            print(f"⚠️  NumPy install failed: {e}")
            print("➡️  Continuing without NumPy (fallback logic will be used).")
            return False

def check_tkinter():
    """Check if tkinter is available"""
    print("\n🔍 Checking tkinter (GUI library)...")
    
    try:
        import tkinter
        print("✅ tkinter is available")
        return True
    except ImportError:
        print("❌ tkinter not found!")
        print("\n📥 Please install tkinter:")
        
        system = platform.system()
        if system == "Linux":
            print("   Ubuntu/Debian: sudo apt-get install python3-tk")
            print("   Fedora: sudo dnf install python3-tkinter")
            print("   Arch: sudo pacman -S tk")
        elif system == "Darwin":  # macOS
            print("   tkinter should be included with Python")
            print("   If not, reinstall Python from python.org")
        elif system == "Windows":
            print("   tkinter should be included with Python")
            print("   If not, reinstall Python and check 'tcl/tk' option")
        
        return False

def find_app_file():
    """Find the correct app file to run"""
    # Try modern version first
    if os.path.exists('app_modern.py'):
        return 'app_modern.py'
    elif os.path.exists('app.py'):
        return 'app.py'
    else:
        return None

def run_application():
    """Run the main application"""
    app_file = find_app_file()
    
    if not app_file:
        print("\n❌ ERROR: Application file not found!")
        print("   Expected: app_modern.py or app.py")
        return False
    
    print(f"\n🚀 Launching {app_file}...")
    print("="*60 + "\n")
    
    try:
        # Import and run the main function
        if app_file == 'app_modern.py':
            from app_modern import main
        else:
            from app import main
        
        main()
        return True
        
    except Exception as e:
        print(f"\n❌ Error launching application: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_system_info():
    """Show system information"""
    print("\n📊 System Information:")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Python: {sys.version}")
    print(f"   Executable: {sys.executable}")

def main():
    """Main launcher function"""
    print_header()
    
    # Check Python version
    if not check_python_version():
        input("\nPress Enter to exit...")
        return 1
    
    # Show system info
    show_system_info()
    
    # Check and install dependencies
    if not check_and_install_numpy():
        input("\nPress Enter to exit...")
        return 1
    
    if not check_tkinter():
        input("\nPress Enter to exit...")
        return 1
    
    # All checks passed
    print("\n" + "="*60)
    print("✅ All requirements satisfied!")
    print("="*60)
    
    # Run the application
    if not run_application():
        input("\nPress Enter to exit...")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
