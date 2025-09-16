"""
Test suite for config_manager module.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open

from config_manager import (
    ConfigManager, RemoteProfile, KeyMapping, ActionType
)


class TestActionType:
    """Test ActionType enum."""
    
    def test_action_type_values(self):
        """Test ActionType enum values."""
        assert ActionType.SINGLE.value == "single"
        assert ActionType.COMBO.value == "combo"
        assert ActionType.SEQUENCE.value == "sequence"
        assert ActionType.SPECIAL.value == "special"


class TestKeyMapping:
    """Test KeyMapping dataclass."""
    
    def test_key_mapping_creation(self):
        """Test KeyMapping creation."""
        mapping = KeyMapping(
            action_type=ActionType.SINGLE,
            keys="a",
            description="Test key"
        )
        assert mapping.action_type == ActionType.SINGLE
        assert mapping.keys == "a"
        assert mapping.description == "Test key"
    
    def test_key_mapping_default_description(self):
        """Test KeyMapping with default description."""
        mapping = KeyMapping(ActionType.COMBO, ["ctrl", "a"])
        assert mapping.description == ""
    
    def test_to_dict(self):
        """Test KeyMapping to_dict conversion."""
        mapping = KeyMapping(
            action_type=ActionType.COMBO,
            keys=["ctrl", "a"],
            description="Select all"
        )
        result = mapping.to_dict()
        expected = {
            "action_type": "combo",
            "keys": ["ctrl", "a"],
            "description": "Select all"
        }
        assert result == expected
    
    def test_from_dict(self):
        """Test KeyMapping from_dict creation."""
        data = {
            "action_type": "single",
            "keys": "space",
            "description": "Space key"
        }
        mapping = KeyMapping.from_dict(data)
        assert mapping.action_type == ActionType.SINGLE
        assert mapping.keys == "space"
        assert mapping.description == "Space key"
    
    def test_from_dict_no_description(self):
        """Test KeyMapping from_dict without description."""
        data = {
            "action_type": "combo",
            "keys": ["alt", "tab"]
        }
        mapping = KeyMapping.from_dict(data)
        assert mapping.description == ""


class TestRemoteProfile:
    """Test RemoteProfile dataclass."""
    
    def test_remote_profile_creation(self):
        """Test RemoteProfile creation."""
        mappings = {
            "0x1": KeyMapping(ActionType.SINGLE, "a", "Letter A")
        }
        profile = RemoteProfile(
            name="Test Remote",
            brand="TestBrand",
            model="TestModel",
            mappings=mappings,
            description="Test profile"
        )
        assert profile.name == "Test Remote"
        assert profile.brand == "TestBrand"
        assert profile.model == "TestModel"
        assert profile.description == "Test profile"
        assert len(profile.mappings) == 1
    
    def test_to_dict(self):
        """Test RemoteProfile to_dict conversion."""
        mappings = {
            "0x1": KeyMapping(ActionType.SINGLE, "a", "Letter A")
        }
        profile = RemoteProfile(
            name="Test Remote",
            brand="TestBrand",
            model="TestModel",
            mappings=mappings
        )
        result = profile.to_dict()
        assert result["name"] == "Test Remote"
        assert result["brand"] == "TestBrand"
        assert result["model"] == "TestModel"
        assert "0x1" in result["mappings"]
        assert result["mappings"]["0x1"]["action_type"] == "single"
    
    def test_from_dict(self):
        """Test RemoteProfile from_dict creation."""
        data = {
            "name": "Test Remote",
            "brand": "TestBrand",
            "model": "TestModel",
            "description": "Test profile",
            "mappings": {
                "0x1": {
                    "action_type": "single",
                    "keys": "a",
                    "description": "Letter A"
                }
            }
        }
        profile = RemoteProfile.from_dict(data)
        assert profile.name == "Test Remote"
        assert profile.brand == "TestBrand"
        assert profile.model == "TestModel"
        assert profile.description == "Test profile"
        assert len(profile.mappings) == 1
        assert isinstance(profile.mappings["0x1"], KeyMapping)


class TestConfigManager:
    """Test ConfigManager class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_creates_directories(self):
        """Test ConfigManager initialization creates directories."""
        assert Path(self.temp_dir).exists()
        assert (Path(self.temp_dir) / "profiles").exists()
    
    def test_load_default_settings(self):
        """Test loading default settings."""
        settings = self.config_manager._load_settings()
        assert "serial_port" in settings
        assert "baud_rate" in settings
        assert "ghost_key" in settings
        assert settings["serial_port"] == "COM4"
        assert settings["baud_rate"] == 115200
    
    @patch("builtins.open", mock_open(read_data='{"custom_setting": "value"}'))
    def test_load_existing_settings(self):
        """Test loading existing settings file."""
        # Create a mock settings file
        settings_file = Path(self.temp_dir) / "settings.json"
        settings_file.write_text('{"custom_setting": "value", "serial_port": "COM5"}')
        
        # Create new config manager to load the settings
        config_manager = ConfigManager(self.temp_dir)
        assert config_manager.get_setting("custom_setting") == "value"
        assert config_manager.get_setting("serial_port") == "COM5"
    
    def test_load_corrupted_settings(self):
        """Test loading corrupted settings file."""
        settings_file = Path(self.temp_dir) / "settings.json"
        settings_file.write_text('invalid json{')
        
        # Should fall back to defaults
        config_manager = ConfigManager(self.temp_dir)
        assert config_manager.get_setting("serial_port") == "COM4"
    
    def test_save_settings(self):
        """Test saving settings."""
        self.config_manager.set_setting("test_key", "test_value")
        
        # Check file was created
        settings_file = Path(self.temp_dir) / "settings.json"
        assert settings_file.exists()
        
        # Check content
        with open(settings_file, 'r') as f:
            data = json.load(f)
        assert data["test_key"] == "test_value"
    
    @patch("builtins.open", side_effect=IOError("Write error"))
    def test_save_settings_error(self, mock_file):
        """Test save settings with IO error."""
        # Mock open to raise IOError
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with patch('builtins.print') as mock_print:
                # This should not raise an exception
                self.config_manager.save_settings()
                # Verify error was printed
                mock_print.assert_called_once()
    
    def test_get_setting(self):
        """Test getting setting values."""
        assert self.config_manager.get_setting("serial_port") == "COM4"
        assert self.config_manager.get_setting("nonexistent") is None
        assert self.config_manager.get_setting("nonexistent", "default") == "default"
    
    def test_set_setting(self):
        """Test setting values."""
        self.config_manager.set_setting("test_key", "test_value")
        assert self.config_manager.get_setting("test_key") == "test_value"
    
    def test_save_profile(self):
        """Test saving a profile."""
        mappings = {
            "0x1": KeyMapping(ActionType.SINGLE, "a", "Letter A")
        }
        profile = RemoteProfile(
            name="Test Remote",
            brand="TestBrand",
            model="TestModel",
            mappings=mappings
        )
        
        result = self.config_manager.save_profile(profile)
        assert result is True
        
        # Check file was created
        expected_filename = "TestBrand_TestModel.json"
        profile_file = Path(self.temp_dir) / "profiles" / expected_filename
        assert profile_file.exists()
    
    @patch("builtins.open", side_effect=IOError("Write error"))
    def test_save_profile_error(self, mock_file):
        """Test save profile with IO error."""
        mappings = {
            "0x1": KeyMapping(ActionType.SINGLE, "a", "Letter A")
        }
        profile = RemoteProfile(
            name="Test Remote",
            brand="TestBrand",
            model="TestModel",
            mappings=mappings
        )
        
        result = self.config_manager.save_profile(profile)
        assert result is False
    
    def test_load_profile(self):
        """Test loading a profile."""
        # First save a profile
        mappings = {
            "0x1": KeyMapping(ActionType.SINGLE, "a", "Letter A")
        }
        profile = RemoteProfile(
            name="Test Remote",
            brand="TestBrand",
            model="TestModel",
            mappings=mappings
        )
        self.config_manager.save_profile(profile)
        
        # Then load it
        filename = "TestBrand_TestModel.json"
        loaded_profile = self.config_manager.load_profile(filename)
        
        assert loaded_profile is not None
        assert loaded_profile.name == "Test Remote"
        assert loaded_profile.brand == "TestBrand"
        assert len(loaded_profile.mappings) == 1
    
    def test_load_nonexistent_profile(self):
        """Test loading a non-existent profile."""
        result = self.config_manager.load_profile("nonexistent.json")
        assert result is None
    
    def test_load_corrupted_profile(self):
        """Test loading a corrupted profile."""
        profile_file = Path(self.temp_dir) / "profiles" / "corrupted.json"
        profile_file.write_text('invalid json{')
        
        result = self.config_manager.load_profile("corrupted.json")
        assert result is None
    
    def test_list_profiles(self):
        """Test listing profiles."""
        # Initially empty
        profiles = self.config_manager.list_profiles()
        assert profiles == []
        
        # Add a profile
        mappings = {
            "0x1": KeyMapping(ActionType.SINGLE, "a", "Letter A")
        }
        profile = RemoteProfile(
            name="Test Remote",
            brand="TestBrand",
            model="TestModel",
            mappings=mappings
        )
        self.config_manager.save_profile(profile)
        
        # Should now have one profile
        profiles = self.config_manager.list_profiles()
        assert len(profiles) == 1
        assert "TestBrand_TestModel.json" in profiles
    
    def test_create_default_vizio_profile(self):
        """Test creating default Vizio profile."""
        profile = self.config_manager.create_default_vizio_profile()
        
        assert profile.name == "Default Vizio Remote"
        assert profile.brand == "Vizio"
        assert profile.model == "Generic TV Remote"
        assert len(profile.mappings) > 0
        
        # Check some specific mappings
        assert "0x8" in profile.mappings
        assert "0x11" in profile.mappings  # Number 1
        assert "0x30" in profile.mappings  # Stop
        
        # Check action types
        assert profile.mappings["0x11"].action_type == ActionType.SINGLE
        assert profile.mappings["0x8"].action_type == ActionType.COMBO
        assert profile.mappings["0x30"].action_type == ActionType.SPECIAL


if __name__ == "__main__":
    pytest.main([__file__])