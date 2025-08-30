"""
Main entry point for the IR Remote Controller application.

This module provides the main entry point that delegates to the CLI module
for comprehensive command-line interface functionality.
"""

import sys
import os
from pathlib import Path

src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


def main():
    """Main application entry point."""
    try:
        from cli import main as cli_main

        cli_main()
    except ImportError as e:
        print(f"Error: Failed to import required modules: {e}")
        print("Please ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
