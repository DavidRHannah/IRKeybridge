"""
GUI package for the IR Remote Configuration Tool.

This package provides a modular GUI interface for configuring IR remotes,
managing profiles, and communicating with Arduino devices.
"""

from .main_window import IRRemoteGUI
from .config_manager import GUIConfigManager
from .serial_monitor import SerialMonitor
from .widgets import RemoteConfigWidget, SystemConfigWidget, ProfileWidget

__all__ = [
    'IRRemoteGUI',
    'GUIConfigManager', 
    'SerialMonitor',
    'RemoteConfigWidget',
    'SystemConfigWidget', 
    'ProfileWidget'
]

__version__ = "0.1.0"