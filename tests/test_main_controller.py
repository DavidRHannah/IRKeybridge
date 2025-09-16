"""
Test suite for main_controller module.
"""

import pytest
import json
import tempfile
import time
import signal
import threading
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open
import sys

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from main_controller import IRRemoteController
    from config_manager import KeyMapping, ActionType
except ImportError as e:
    pytest.skip(f"Cannot import modules: {e}", allow_module_level=True)


class TestIRRemoteController:
    """IRRemoteController tests with timeout protection."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment with proper mocking."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Patch all imports at class level
        self.config_patcher = patch('main_controller.ConfigManager')
        self.receiver_patcher = patch('main_controller.IRReceiver')
        self.mapper_patcher = patch('main_controller.KeyMapper')
        
        self.mock_config_class = self.config_patcher.start()
        self.mock_receiver_class = self.receiver_patcher.start()
        self.mock_mapper_class = self.mapper_patcher.start()
        
        # Setup return values
        self.mock_config = self.mock_config_class.return_value
        self.mock_receiver = self.mock_receiver_class.return_value
        self.mock_mapper = self.mock_mapper_class.return_value
        
        # Configure mocks
        self.mock_receiver.connect.return_value = True
        self.mock_receiver.start_receiving.return_value = True
        self.mock_receiver.is_connected.return_value = True
        self.mock_receiver.get_code.return_value = None
        
        # Create controller
        self.controller = IRRemoteController(port="TEST_PORT")
        
        yield
        
        # Cleanup
        self.config_patcher.stop()
        self.receiver_patcher.stop()
        self.mapper_patcher.stop()
        
        if hasattr(self, 'controller'):
            self.controller.stop()
    
    def test_init_default_port(self):
        """Test initialization with default port."""
        with patch('main_controller.ConfigManager'):
            with patch('main_controller.IRReceiver') as mock_receiver:
                with patch('main_controller.KeyMapper'):
                    controller = IRRemoteController()
                    mock_receiver.assert_called_once_with(port="COM4")
    
    def test_init_custom_port(self):
        """Test initialization with custom port."""
        # This is already tested in setup, verify the mock was called correctly
        self.mock_receiver_class.assert_called_with(port="TEST_PORT")
    
    @patch('builtins.open', mock_open(read_data='{"mappings": {"0x1": {"action_type": "single", "keys": "a"}}}'))
    def test_load_profile_from_file(self):
        """Test loading profile from file."""
        # This should not timeout
        with patch('json.load') as mock_json_load:
            mock_json_load.return_value = {
                "mappings": {
                    "0x1": {"action_type": "single", "keys": "a"}
                }
            }
            
            # This should complete quickly
            self.controller.load_profile("test.json")
            
            # Verify the mapper was configured
            self.mock_mapper.set_mappings.assert_called()
    
    def test_signal_handler_no_actual_exit(self):
        """Test signal handler without actual system exit."""
        with patch.object(self.controller, 'stop') as mock_stop:
            with patch('sys.exit') as mock_exit:
                self.controller._signal_handler(signal.SIGINT, None)
                mock_stop.assert_called_once()
                mock_exit.assert_called_once_with(0)
    
    def test_start_success(self):
        """Test successful controller start."""
        self.mock_receiver.connect.return_value = True
        self.mock_receiver.start_receiving.return_value = True
        
        result = self.controller.start()
        
        assert result is True
        assert self.controller.running is True
        self.mock_receiver.connect.assert_called_once()
        self.mock_receiver.start_receiving.assert_called_once()
    
    def test_start_connect_failure(self):
        """Test controller start with connection failure."""
        self.mock_receiver.connect.return_value = False
        
        with patch('builtins.print'):
            result = self.controller.start()
            
            assert result is False
            assert self.controller.running is False
    
    def test_start_receiving_failure(self):
        """Test controller start with receiving failure."""
        self.mock_receiver.connect.return_value = True
        self.mock_receiver.start_receiving.return_value = False
        
        with patch('builtins.print'):
            result = self.controller.start()
            
            assert result is False
            assert self.controller.running is False
    
    def test_run_not_running(self):
        """Test run method when controller is not running."""
        self.controller.running = False
        
        # Should return immediately without calling get_code
        start_time = time.time()
        self.controller.run()
        duration = time.time() - start_time
        
        # Should complete almost instantly
        assert duration < 0.1
        self.mock_receiver.get_code.assert_not_called()
    
    def test_run_with_limited_iterations(self):
        """Test run method with controlled iteration count."""
        self.controller.running = True
        
        # Mock get_code to return None a few times then stop the controller
        call_count = 0
        def mock_get_code():
            nonlocal call_count
            call_count += 1
            if call_count >= 3:  # Stop after 3 calls
                self.controller.running = False
            return None
        
        self.mock_receiver.get_code.side_effect = mock_get_code
        
        start_time = time.time()
        self.controller.run()
        duration = time.time() - start_time
        
        # Should complete quickly
        assert duration < 1.0
        assert call_count == 3
    
    def test_run_with_ir_codes_limited(self):
        """Test run method processing IR codes with limited iterations."""
        self.controller.running = True
        
        # Mock a sequence of codes then stop
        codes = ["0x1", "0x2", None, None]
        call_count = 0
        
        def mock_get_code():
            nonlocal call_count
            if call_count < len(codes):
                code = codes[call_count]
                call_count += 1
                if call_count >= len(codes):
                    self.controller.running = False
                return code
            return None
        
        self.mock_receiver.get_code.side_effect = mock_get_code
        
        start_time = time.time()
        self.controller.run()
        duration = time.time() - start_time
        
        # Should complete quickly
        assert duration < 1.0
        # Should have processed the IR codes
        assert self.mock_mapper.process_code.call_count == 2
    
    def test_run_with_keyboard_interrupt(self):
        """Test run method handles KeyboardInterrupt properly."""
        self.controller.running = True
        
        # Mock get_code to raise KeyboardInterrupt
        self.mock_receiver.get_code.side_effect = KeyboardInterrupt()
        
        with patch.object(self.controller, 'stop') as mock_stop:
            # Should not raise exception
            self.controller.run()
            mock_stop.assert_called_once()
    
    def test_stop(self):
        """Test stopping the controller."""
        self.controller.running = True
        
        with patch('builtins.print'):
            self.controller.stop()
            
            assert self.controller.running is False
            self.mock_receiver.disconnect.assert_called_once()
            self.mock_mapper.disable.assert_called_once()
            self.mock_mapper.cleanup.assert_called_once()
    
    def test_list_available_profiles(self):
        """Test listing available profiles."""
        expected_profiles = ["profile1.json", "profile2.json"]
        self.mock_config.list_profiles.return_value = expected_profiles
        
        result = self.controller.list_available_profiles()
        
        assert result == expected_profiles
        self.mock_config.list_profiles.assert_called_once()
    
    def test_get_status_complete(self):
        """Test getting controller status."""
        self.controller.running = True
        self.controller.current_profile = Mock()
        self.controller.current_profile.name = "Test Profile"
        self.mock_receiver.is_connected.return_value = True
        self.mock_mapper.ghost_key_enabled = True
        self.mock_mapper.single_tapping_enabled = False
        
        status = self.controller.get_status()
        
        expected_status = {
            "running": True,
            "connected": True,
            "profile": "Test Profile",
            "ghost_key_enabled": True,
            "single_tap_enabled": False,
        }
        assert status == expected_status
    
    def test_get_status_no_profile(self):
        """Test getting status with no active profile."""
        self.controller.running = False
        self.controller.current_profile = None
        self.mock_receiver.is_connected.return_value = False
        
        status = self.controller.get_status()
        
        assert status["profile"] is None
        assert status["running"] is False
        assert status["connected"] is False
    
    def test_get_status_no_receiver(self):
        """Test getting status with no receiver."""
        self.controller.receiver = None
        
        status = self.controller.get_status()
        
        assert status["connected"] is False
    
    def test_load_profile_method_success(self):
        """Test load_profile method success."""
        mock_profile = Mock()
        mock_profile.name = "Test Profile"
        mock_profile.mappings = {"0x1": "mapping"}
        
        self.mock_config.load_profile.return_value = mock_profile
        
        result = self.controller.load_profile("test.json")
        
        assert result is True
        assert self.controller.current_profile == mock_profile
        self.mock_config.load_profile.assert_called_once_with("test.json")
        self.mock_mapper.set_mappings.assert_called_once_with(mock_profile.mappings)
        self.mock_config.set_setting.assert_called_once_with("last_used_profile", "test.json")
    
    def test_load_profile_method_failure(self):
        """Test load_profile method with failure."""
        self.mock_config.load_profile.return_value = None
        
        result = self.controller.load_profile("invalid.json")
        
        assert result is False
        self.mock_config.load_profile.assert_called_once_with("invalid.json")
    
    def test_log_message(self):
        """Test log message method."""
        with patch('time.strftime', return_value="12:34:56"):
            with patch('builtins.print') as mock_print:
                self.controller._log_message("Test message")
                mock_print.assert_called_once_with("[12:34:56] Test message")
    
    def test_run_timeout_protection(self):
        """Test that run method has built-in timeout protection."""
        self.controller.running = True
        
        # Set up a scenario that could potentially run forever
        self.mock_receiver.get_code.return_value = None
        
        # Start run in a separate thread with timeout
        import threading
        
        def run_with_timeout():
            self.controller.run()
        
        thread = threading.Thread(target=run_with_timeout, daemon=True)
        start_time = time.time()
        thread.start()
        
        # Let it run for a short time, then force stop
        time.sleep(0.1)
        self.controller.running = False
        
        # Wait for thread to complete
        thread.join(timeout=1.0)
        duration = time.time() - start_time
        
        # Should not have taken too long
        assert duration < 2.0
        assert not thread.is_alive()


class TestIRRemoteControllerIntegration:
    """Integration tests that are timeout-safe."""
    
    def test_full_workflow_quick(self):
        """Test complete workflow with timeout protection."""
        with patch('main_controller.ConfigManager') as mock_config_class:
            with patch('main_controller.IRReceiver') as mock_receiver_class:
                with patch('main_controller.KeyMapper') as mock_mapper_class:
                    
                    # Setup mocks
                    mock_receiver = mock_receiver_class.return_value
                    mock_mapper = mock_mapper_class.return_value
                    mock_config = mock_config_class.return_value
                    
                    mock_receiver.connect.return_value = True
                    mock_receiver.start_receiving.return_value = True
                    mock_receiver.is_connected.return_value = True
                    mock_receiver.get_code.return_value = None
                    
                    mock_config.list_profiles.return_value = ["test.json"]
                    
                    mock_profile = Mock()
                    mock_profile.name = "Test Profile"
                    mock_profile.mappings = {}
                    mock_config.load_profile.return_value = mock_profile
                    
                    # Create and test controller
                    controller = IRRemoteController(port="TEST_PORT")
                    
                    # Test workflow without running the main loop
                    assert controller.start() is True
                    assert controller.load_profile("test.json") is True
                    assert controller.list_available_profiles() == ["test.json"]
                    
                    status = controller.get_status()
                    assert status["running"] is True
                    assert status["connected"] is True
                    assert status["profile"] == "Test Profile"
                    
                    controller.stop()
                    assert controller.running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])