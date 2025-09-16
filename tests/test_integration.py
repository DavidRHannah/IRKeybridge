"""
Integration tests for the IR Remote Controller application.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import json
import time

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from main_controller import IRRemoteController
from config_manager import ConfigManager, RemoteProfile, KeyMapping, ActionType


@pytest.fixture
def mock_keyboard():
    """Mock keyboard module for testing."""
    with patch('keyboard.press') as mock_press:
        with patch('keyboard.release') as mock_release:
            with patch('keyboard.press_and_release') as mock_press_release:
                with patch('keyboard.unhook_all') as mock_unhook:
                    yield Mock(
                        press=mock_press,
                        release=mock_release,
                        press_and_release=mock_press_release,
                        unhook_all=mock_unhook
                    )


class TestIntegration:
    """Integration test cases."""

    def test_full_application_flow(self, temp_config_dir):
        """Test complete application flow from start to finish."""
        # Create controller with mocked dependencies
        with patch('main_controller.IRReceiver') as mock_receiver_class:
            with patch('main_controller.KeyMapper') as mock_mapper_class:
                mock_receiver = mock_receiver_class.return_value
                mock_mapper = mock_mapper_class.return_value
                
                # Configure mocks
                mock_receiver.connect.return_value = True
                mock_receiver.start_receiving.return_value = True
                mock_receiver.is_connected.return_value = True
                
                controller = IRRemoteController()
                controller.config_manager = ConfigManager(config_dir=temp_config_dir)
                
                # Create and save a test profile
                test_mapping = KeyMapping(ActionType.SINGLE, "a", "Test key A")
                test_profile = RemoteProfile(
                    name="Integration Test Remote",
                    brand="Test_Brand",
                    model="Test_Model",
                    description="Integration test profile",
                    mappings={"0xFF": test_mapping}
                )
                
                # Save the profile
                assert controller.config_manager.save_profile(test_profile)
                
                # Verify profile was saved
                profiles = controller.list_available_profiles()
                assert len(profiles) > 0
                
                # Load the profile (use correct method signature)
                profile_filename = profiles[0]
                assert controller.load_profile(profile_filename)
                assert controller.current_profile is not None
                assert controller.current_profile.name == test_profile.name
                
                # Start controller (no profile argument needed)
                assert controller.start()
                assert controller.running
                
                # Test status
                status = controller.get_status()
                assert status['running']
                assert status['connected']
                assert status['profile'] == test_profile.name
                
                # Stop controller
                controller.stop()
                assert not controller.running

    def test_config_persistence(self, temp_config_dir):
        """Test configuration persistence across instances."""
        # Create first config manager instance
        config1 = ConfigManager(config_dir=temp_config_dir)
        config1.set_setting("test_setting", "test_value")
        
        # Create test profile
        test_mapping = KeyMapping(ActionType.COMBO, ["ctrl", "a"], "Select all")
        test_profile = RemoteProfile(
            name="Persistence Test",
            brand="Test_Brand",
            model="Test_Model",
            mappings={"0xAA": test_mapping}
        )
        
        # Save profile
        assert config1.save_profile(test_profile)
        
        # Create second config manager instance
        config2 = ConfigManager(config_dir=temp_config_dir)
        
        # Verify settings persisted
        assert config2.get_setting("test_setting") == "test_value"
        
        # Verify profile persisted
        profiles = config2.list_profiles()
        assert len(profiles) > 0
        
        loaded_profile = config2.load_profile(profiles[0])
        assert loaded_profile is not None
        assert loaded_profile.name == test_profile.name
        assert "0xAA" in loaded_profile.mappings

    def test_error_handling_chain(self, temp_config_dir):
        """Test error handling throughout the application chain."""
        with patch('main_controller.IRReceiver') as mock_receiver_class:
            with patch('main_controller.KeyMapper') as mock_mapper_class:
                mock_receiver = mock_receiver_class.return_value
                mock_mapper = mock_mapper_class.return_value
                
                controller = IRRemoteController()
                controller.config_manager = ConfigManager(config_dir=temp_config_dir)
                
                # Test loading non-existent profile
                assert not controller.load_profile("nonexistent.json")
                
                # Test receiver connection failure
                mock_receiver.connect.return_value = False
                assert not controller.start()
                
                # Test receiver start failure
                mock_receiver.connect.return_value = True
                mock_receiver.start_receiving.return_value = False
                assert not controller.start()

    def test_key_mapping_execution_chain(self, temp_config_dir, mock_keyboard):
        """Test complete key mapping execution chain."""
        with patch('main_controller.IRReceiver') as mock_receiver_class:
            with patch('main_controller.KeyMapper') as mock_mapper_class:
                # Use the real KeyMapper for this test
                from key_mapper import KeyMapper
                real_mapper = KeyMapper()
                mock_mapper_class.return_value = real_mapper
                
                controller = IRRemoteController()
                controller.config_manager = ConfigManager(config_dir=temp_config_dir)
                
                # Create profile with different action types
                mappings = {
                    "0x01": KeyMapping(ActionType.SINGLE, "a", "Single key"),
                    "0x02": KeyMapping(ActionType.COMBO, ["ctrl", "c"], "Copy"),
                    "0x03": KeyMapping(ActionType.SEQUENCE, ["a", "b"], "Sequence"),
                    "0x04": KeyMapping(ActionType.SPECIAL, "toggle_ghost", "Toggle ghost"),
                }
                
                # Set up mapper with mappings (correct method)
                real_mapper.set_mappings(mappings)
                
                # Test single key
                real_mapper.process_code("0x01")
                mock_keyboard.press.assert_called_with("a")
                
                # Test combo key
                mock_keyboard.reset_mock()
                real_mapper.process_code("0x02")
                mock_keyboard.press.assert_any_call("ctrl")
                mock_keyboard.press.assert_any_call("c")
                
                # Test sequence
                mock_keyboard.reset_mock()
                real_mapper.process_code("0x03")
                mock_keyboard.press_and_release.assert_any_call("a")
                mock_keyboard.press_and_release.assert_any_call("b")
                
                # Test special action
                assert not real_mapper.ghost_key_enabled
                real_mapper.process_code("0x04")
                assert real_mapper.ghost_key_enabled

    def test_default_profile_creation_and_usage(self, temp_config_dir):
        """Test default profile creation and usage."""
        with patch('main_controller.IRReceiver') as mock_receiver_class:
            with patch('main_controller.KeyMapper') as mock_mapper_class:
                controller = IRRemoteController()
                controller.config_manager = ConfigManager(config_dir=temp_config_dir)
                
                # Create default profile using config manager (correct method)
                default_profile = controller.config_manager.create_default_vizio_profile()
                assert controller.config_manager.save_profile(default_profile)
                
                # Verify profile was created
                profiles = controller.list_available_profiles()
                assert len(profiles) > 0
                
                # Load and verify default profile
                profile = controller.config_manager.load_profile(profiles[0])
                assert profile is not None
                assert profile.brand == "Vizio"
                assert len(profile.mappings) > 0
                
                # Verify specific mappings exist
                assert "0x8" in profile.mappings  # Power button
                assert "0x30" in profile.mappings  # Stop button
                assert profile.mappings["0x30"].action_type == ActionType.SPECIAL

    @patch('time.sleep')
    @patch('time.time')
    def test_ir_code_processing_flow(self, mock_time, mock_sleep, temp_config_dir, mock_keyboard):
        """Test complete IR code processing flow."""
        with patch('main_controller.IRReceiver') as mock_receiver_class:
            with patch('main_controller.KeyMapper') as mock_mapper_class:
                # Use real KeyMapper for realistic timing behavior
                from key_mapper import KeyMapper
                real_mapper = KeyMapper()
                mock_mapper_class.return_value = real_mapper
                
                controller = IRRemoteController()
                controller.config_manager = ConfigManager(config_dir=temp_config_dir)
                
                # Set up profile
                test_mapping = KeyMapping(ActionType.SINGLE, "space", "Space key")
                mappings = {"0xFF": test_mapping}
                
                real_mapper.set_mappings(mappings)
                mock_time.return_value = 1.0
                
                # Simulate IR code reception and processing
                real_mapper.process_code("0xFF")
                
                # Verify key was pressed
                mock_keyboard.press.assert_called_with("space")
                
                # Test repeat threshold - same code within timeout should be ignored
                mock_time.return_value = 1.05  # 0.05 seconds later
                mock_keyboard.reset_mock()
                result = real_mapper.process_code("0xFF")
                
                # Should be ignored due to bounce protection
                assert result is False
                mock_keyboard.press.assert_not_called()

    def test_configuration_validation(self, temp_config_dir):
        """Test configuration validation and error handling."""
        config_manager = ConfigManager(config_dir=temp_config_dir)
        
        # Test invalid profile data
        invalid_profile_data = {
            "name": "Invalid Profile",
            "brand": "Test",
            "model": "Test",
            "mappings": {
                "0xFF": {
                    "action_type": "invalid_type",  # Invalid action type
                    "keys": "a",
                    "description": "Invalid"
                }
            }
        }
        
        # Should handle invalid action type gracefully
        with pytest.raises(ValueError):
            RemoteProfile.from_dict(invalid_profile_data)
        
        # Test valid profile data
        valid_profile_data = {
            "name": "Valid Profile",
            "brand": "Test",
            "model": "Test",
            "mappings": {
                "0xFF": {
                    "action_type": "single",
                    "keys": "a",
                    "description": "Valid"
                }
            }
        }
        
        # Should create profile successfully
        profile = RemoteProfile.from_dict(valid_profile_data)
        assert profile.name == "Valid Profile"
        assert "0xFF" in profile.mappings

    def test_profile_loading_integration(self, temp_config_dir):
        """Test profile loading integration between components."""
        with patch('main_controller.IRReceiver') as mock_receiver_class:
            with patch('main_controller.KeyMapper') as mock_mapper_class:
                mock_receiver = mock_receiver_class.return_value
                mock_mapper = mock_mapper_class.return_value
                
                controller = IRRemoteController()
                controller.config_manager = ConfigManager(config_dir=temp_config_dir)
                
                # Create and save test profile
                test_mappings = {
                    "0x01": KeyMapping(ActionType.SINGLE, "a", "Key A"),
                    "0x02": KeyMapping(ActionType.COMBO, ["ctrl", "c"], "Copy")
                }
                
                test_profile = RemoteProfile(
                    name="Integration Profile",
                    brand="Integration_Brand",
                    model="Integration_Model",
                    mappings=test_mappings
                )
                
                assert controller.config_manager.save_profile(test_profile)
                
                # Load profile through controller
                profiles = controller.list_available_profiles()
                assert len(profiles) > 0
                
                profile_name = profiles[0]
                assert controller.load_profile(profile_name)
                
                # Verify mapper received the mappings
                mock_mapper.set_mappings.assert_called_once()
                called_mappings = mock_mapper.set_mappings.call_args[0][0]
                assert "0x01" in called_mappings
                assert "0x02" in called_mappings
                
                # Verify profile is set as current
                assert controller.current_profile is not None
                assert controller.current_profile.name == test_profile.name

    def test_controller_lifecycle_integration(self, temp_config_dir):
        """Test complete controller lifecycle."""
        with patch('main_controller.IRReceiver') as mock_receiver_class:
            with patch('main_controller.KeyMapper') as mock_mapper_class:
                mock_receiver = mock_receiver_class.return_value
                mock_mapper = mock_mapper_class.return_value
                
                # Configure successful mocks
                mock_receiver.connect.return_value = True
                mock_receiver.start_receiving.return_value = True
                mock_receiver.is_connected.return_value = True
                
                controller = IRRemoteController()
                controller.config_manager = ConfigManager(config_dir=temp_config_dir)
                
                # Create and load profile
                test_profile = controller.config_manager.create_default_vizio_profile()
                assert controller.config_manager.save_profile(test_profile)
                
                profiles = controller.list_available_profiles()
                assert controller.load_profile(profiles[0])
                
                # Start controller
                assert controller.start()
                assert controller.running
                
                # Verify all components were initialized
                mock_receiver.connect.assert_called_once()
                mock_receiver.start_receiving.assert_called_once()
                mock_mapper.set_mappings.assert_called_once()
                
                # Get status
                status = controller.get_status()
                assert status['running']
                assert status['connected']
                assert status['profile'] is not None
                
                # Stop controller
                controller.stop()
                assert not controller.running
                
                # Verify cleanup
                mock_receiver.disconnect.assert_called_once()
                mock_mapper.disable.assert_called_once()
                mock_mapper.cleanup.assert_called_once()