import os
import sys
import subprocess

def install_requirements():
    print(f"Using Python: {sys.executable}")
    print("Checking dependencies...")
    try:
        import customtkinter
        import scipy
        import numpy
        import psutil
        import packaging
        print("Dependencies found.")
    except ImportError as e:
        print(f"Missing dependency ({e}). Installing from requirements.txt...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("Dependencies installed successfully.")
        except subprocess.CalledProcessError:
            print("Error: Failed to install dependencies. Please install them manually.")
            sys.exit(1)

if __name__ == "__main__":
    install_requirements()
    
    # Add src to path
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    
    try:
        from src.ui.app import App
        app = App()
        app.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

