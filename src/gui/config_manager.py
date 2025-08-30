"""
Configuration management module for the GUI application.

This module handles all configuration-related operations including
loading, saving, and converting between GUI and profile formats.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


class GUIConfigManager:
    """GUI-specific configuration manager that integrates with the main application"""

    def __init__(self, config_dir="config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config_manager import (
            ConfigManager as MainConfigManager,
            RemoteProfile,
            KeyMapping,
            ActionType,
        )

        self.main_config = MainConfigManager(config_dir=str(self.config_dir))

        self.RemoteProfile = RemoteProfile
        self.KeyMapping = KeyMapping
        self.ActionType = ActionType

        self.gui_config_file = self.config_dir / "gui_config.json"
        self.gui_config = self.load_gui_config()

        self.temp_remotes = {}

    def load_gui_config(self):
        """Load GUI-specific configuration (window settings, etc.)"""
        default_gui_config = {
            "window_geometry": None,
            "last_tab": 0,
            "arduino_port": "",
            "baud_rate": 9600,
            "auto_connect": False,
            "debug_mode": False,
        }

        try:
            if self.gui_config_file.exists():
                with open(self.gui_config_file, "r") as f:
                    config = json.load(f)
                    default_gui_config.update(config)
            return default_gui_config
        except Exception as e:
            print(f"Error loading GUI config: {e}")
            return default_gui_config

    def save_gui_config(self):
        """Save GUI-specific configuration"""
        try:
            with open(self.gui_config_file, "w") as f:
                json.dump(self.gui_config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving GUI config: {e}")
            return False

    def save_config(self):
        """Save all configurations (for compatibility with main window)"""
        return self.save_gui_config()

    def get_profiles(self):
        """Get all available profiles from the main config manager"""
        return self.main_config.list_profiles()

    def load_profile(self, filename):
        """Load a profile using the main config manager"""
        return self.main_config.load_profile(filename)

    def save_profile(self, profile):
        """Save a profile using the main config manager"""
        return self.main_config.save_profile(profile)

    def get_remotes(self):
        """Get remotes - combination of temp remotes and existing profiles converted back"""
        remotes = {}

        remotes.update(self.temp_remotes)

        profile_files = self.main_config.list_profiles()
        for filename in profile_files:
            profile = self.main_config.load_profile(filename)
            if profile:
                gui_remote = self.profile_to_gui_format(profile)
                remotes[profile.name] = gui_remote

        return remotes

    def profile_to_gui_format(self, profile):
        """Convert a RemoteProfile to GUI format"""
        gui_remote = {
            "name": profile.name,
            "brand": profile.brand,
            "model": profile.model,
            "notes": profile.description,
            "buttons": {},
            "created": "",
            "modified": "",
        }

        for code, mapping in profile.mappings.items():
            button_name = mapping.description.replace(" button", "").replace(" ", "_")
            if not button_name or button_name == "":
                button_name = f"button_{code}"

            gui_remote["buttons"][button_name] = {
                "code": code,
                "protocol": "NEC",
                "action_type": mapping.action_type.value,
                "keys": mapping.keys,
                "description": mapping.description,
            }

        return gui_remote

    def add_remote(self, name, remote_data):
        """Add a remote - store temporarily and create profile"""
        self.temp_remotes[name] = remote_data

        try:
            profile = self.create_profile_from_remote(remote_data)
            success = self.save_profile(profile)
            if success:
                print(f"Successfully saved profile for remote '{name}'")
                # Clean up temp storage
                if name in self.temp_remotes:
                    del self.temp_remotes[name]
            return success
        except Exception as e:
            print(f"Error creating profile from remote: {e}")
            return False

    def delete_remote(self, name):
        """Delete a remote - remove from temp storage and delete profile"""
        if name in self.temp_remotes:
            del self.temp_remotes[name]

        profile_files = self.main_config.list_profiles()
        for filename in profile_files:
            profile = self.main_config.load_profile(filename)
            if profile and profile.name == name:
                try:
                    profile_path = self.main_config.profiles_dir / filename
                    if profile_path.exists():
                        profile_path.unlink()
                        print(f"Deleted profile file: {filename}")
                except Exception as e:
                    print(f"Error deleting profile file: {e}")
                break

    def create_profile_from_remote(self, remote_data):
        """Create a profile from remote button data"""
        action_type_map = {
            "single": self.ActionType.SINGLE,
            "combo": self.ActionType.COMBO,
            "sequence": self.ActionType.SEQUENCE,
            "special": self.ActionType.SPECIAL,
        }

        mappings = {}
        for button_name, button_data in remote_data.get("buttons", {}).items():
            action_type = action_type_map.get(
                button_data.get("action_type", "single"), self.ActionType.SINGLE
            )
            keys = button_data.get("keys", "")
            description = button_data.get("description", button_name)

            ir_code = button_data.get("code", button_name)
            mappings[ir_code] = self.KeyMapping(action_type, keys, description)

        profile = self.RemoteProfile(
            name=remote_data.get("name", "Unnamed Remote"),
            brand=remote_data.get("brand", "Unknown"),
            model=remote_data.get("model", "Unknown"),
            description=remote_data.get("notes", ""),
            mappings=mappings,
        )

        return profile

    def get_system_config(self):
        """Get system configuration"""
        return self.gui_config

    def update_system_config(self, updates):
        """Update system configuration"""
        self.gui_config.update(updates)
        self.save_gui_config()

        main_settings = {}
        if "arduino_port" in updates:
            main_settings["serial_port"] = updates["arduino_port"]
        if "baud_rate" in updates:
            main_settings["baud_rate"] = updates["baud_rate"]

        if main_settings:
            for key, value in main_settings.items():
                self.main_config.set_setting(key, value)
