"""
Widgets package for the IR Remote Configuration Tool.

This package contains all the specialized UI widgets used in the application.
Each widget is organized into its own module for better maintainability.
"""

from .remote_config_widget import RemoteConfigWidget
from .system_config_widget import SystemConfigWidget
from .profile_widget import ProfileWidget

__all__ = [
    'RemoteConfigWidget',
    'SystemConfigWidget',
    'ProfileWidget'
]