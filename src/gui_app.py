#!/usr/bin/env python3
"""
Main entry point for the IR Remote Configuration Tool GUI.

This script initializes and runs the GUI application. The actual GUI components
are organized in the gui/ package for better modularity and maintainability.
"""

import sys
import ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor

from gui import IRRemoteGUI


def setup_dark_theme(app):
    """Setup dark theme for the application"""
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)


def is_admin():
    """Check for UAC Privileges on Windows"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    app.setApplicationName("IR Remote Configuration Tool")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("IR Remote Tools")

    setup_dark_theme(app)

    window = IRRemoteGUI()
    window.show()

    sys.exit(app.exec_())


def run_with_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        if is_admin():
            main()
        else:
            main()
    else:
        main()
