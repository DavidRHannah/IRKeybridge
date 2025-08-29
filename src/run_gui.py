"""
Launcher script for IR Remote Configuration Tool
"""

import sys
import os
from pathlib import Path

src_dir = Path(__file__).parent / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))

try:
    from gui import main

    main()
except ImportError as e:
    print("Error: Required modules not found")
    print(f"Details: {e}")
    print("\nPlease install dependencies:")
    print("  pip install PyQt5 pyserial")
    print("\nOr run the setup script:")
    print("  python setup.py")
    sys.exit(1)
except Exception as e:
    print(f"Error starting application: {e}")
    sys.exit(1)
