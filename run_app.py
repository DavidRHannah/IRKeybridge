#!/usr/bin/env python3
"""
Production launcher for IR Remote Controller application.

This is the main entry point for running the IR Remote Controller in production.
It handles dependency checking, environment setup, and provides multiple launch modes.
"""

import sys
import os
import subprocess
from pathlib import Path
import argparse


def main():
    """Main application launcher."""
    parser = argparse.ArgumentParser(
        prog="IR Remote Controller",
        description="Universal IR Remote Controller with Arduino Integration"
    )
    
    parser.add_argument(
        "--gui", "-g",
        action="store_true",
        help="Launch GUI configuration tool"
    )
    
    parser.add_argument(
        "--cli", "-c",
        action="store_true",
        help="Launch CLI interface (default)"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install required dependencies"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test suite"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage report"
    )
    
    args, remaining = parser.parse_known_args()
    
    project_root = Path(__file__).parent
    src_dir = project_root / "src"
    
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    
    if args.install_deps:
        print("Installing dependencies...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", 
                str(project_root / "requirements.txt")
            ])
            print("Dependencies installed successfully!")
            return 0
        except subprocess.CalledProcessError as e:
            print(f"Failed to install dependencies: {e}")
            return 1
    
    if args.test or args.coverage:
        print("Running tests...")
        try:
            cmd = [sys.executable, "-m", "pytest", "tests/"]
            if args.coverage:
                cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term-missing"])
            
            subprocess.check_call(cmd, cwd=project_root)
            print("Tests completed successfully!")
            return 0
        except subprocess.CalledProcessError as e:
            print(f"Tests failed: {e}")
            return 1
    
    try:
        import serial
        import keyboard
    except ImportError as e:
        print(f"Missing required dependency: {e}")
        print("Install dependencies with: python run_app.py --install-deps")
        return 1
    
    if args.gui:
        try:
            import PyQt5
            from gui import main as gui_main
            print("Launching GUI...")
            gui_main()
        except ImportError:
            print("GUI dependencies not available. Install with: pip install PyQt5")
            return 1
        except Exception as e:
            print(f"Error launching GUI: {e}")
            return 1
    else:
        try:
            from main import main as app_main
            app_main()
        except Exception as e:
            print(f"Error launching application: {e}")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())