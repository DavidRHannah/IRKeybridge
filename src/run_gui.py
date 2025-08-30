"""
Launcher script for IR Remote Configuration Tool
"""

import sys
import os
from pathlib import Path


def main():
    """Launch the GUI application with proper error handling"""

    src_dir = Path(__file__).parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    try:
        try:
            import PyQt5
        except ImportError:
            print("Error: PyQt5 not installed")
            print("\nTo install PyQt5:")
            print("  pip install PyQt5")
            print("\nOr install all dependencies:")
            print("  pip install -r requirements.txt")
            sys.exit(1)

        try:
            import serial
        except ImportError:
            print("Error: pyserial not installed")
            print("\nTo install dependencies:")
            print("  pip install pyserial keyboard")
            print("\nOr install all dependencies:")
            print("  pip install -r requirements.txt")
            sys.exit(1)

        print("Starting IR Remote Configuration Tool...")
        from gui_app import main as gui_main

        gui_main()

    except ImportError as e:
        print(f"Error: Required modules not found")
        print(f"Details: {e}")
        print("\nPlease install dependencies:")
        print("  pip install PyQt5 pyserial keyboard")
        print("\nOr run the complete setup:")
        print("  python run_app.py --install-deps")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
