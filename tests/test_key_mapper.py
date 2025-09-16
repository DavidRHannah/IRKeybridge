"""
Test suite for key_mapper module.
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch

from key_mapper import KeyMapper
from config_manager import KeyMapping, ActionType


class TestKeyMapper:
    """Test KeyMapper class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.mapper = KeyMapper()
        self.mapper.debug = True  # Enable debug for testing
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.mapper:
            self.mapper.cleanup()
    
    def test_init(self):
        """Test KeyMapper initialization."""
        assert self.mapper.running is True
        assert len(self.mapper.currently_pressed) == 0
        assert self.mapper.last_code is None
        assert self.mapper.last_mapping is None
        assert self.mapper.last_code_time == 0
        assert self.mapper.mappings == {}
        assert self.mapper.ghost_key_enabled is False
        assert self.mapper.single_tapping_enabled is False
        assert self.mapper.repeat_enabled is True
        assert self.mapper.initial_repeat_delay == 0.3
        assert self.mapper.repeat_rate == 0.009
        assert self.mapper.release_timeout == 0.12
    
    def test_disable(self):
        """Test disabling the mapper."""
        self.mapper.disable()
        assert self.mapper.running is False
    
    def test_set_mappings(self):
        """Test setting mappings."""
        mappings = {
            "0x1": KeyMapping(ActionType.SINGLE, "a", "Letter A"),
            "0x2": KeyMapping(ActionType.COMBO, ["ctrl", "c"], "Copy")
        }
        self.mapper.set_mappings(mappings)
        assert self.mapper.mappings == mappings
    
    def test_set_callbacks(self):
        """Test setting callbacks."""
        stop_callback = Mock()
        status_callback = Mock()
        
        self.mapper.set_callbacks(stop_callback, status_callback)
        assert self.mapper.stop_callback == stop_callback
        assert self.mapper.status_callback == status_callback
    
    def test_log_with_callback(self):
        """Test logging with status callback."""
        status_callback = Mock()
        self.mapper.set_callbacks(status_callback=status_callback)
        
        self.mapper._log("Test message")
        status_callback.assert_called_once_with("Test message")
    
    def test_log_without_callback(self):
        """Test logging without callback."""
        with patch('builtins.print') as mock_print:
            self.mapper._log("Test message")
            mock_print.assert_called_once_with("[Mapper] Test message")
    
    @patch('keyboard.release')
    @patch('keyboard.unhook_all')
    def test_release_all(self, mock_unhook, mock_release):
        """Test releasing all currently pressed keys."""
        self.mapper.currently_pressed = {"a", "ctrl"}
        self.mapper._release_all()
        
        assert len(self.mapper.currently_pressed) == 0
        assert mock_release.call_count == 2
        mock_unhook.assert_called_once()
    
    @patch('keyboard.release')
    def test_release_all_with_exception(self, mock_release):
        """Test releasing keys with exception."""
        mock_release.side_effect = Exception("Release failed")
        self.mapper.currently_pressed = {"a"}
        
        # Should not raise exception
        self.mapper._release_all()
        assert len(self.mapper.currently_pressed) == 0
    
    def test_schedule_release(self):
        """Test scheduling automatic release."""
        self.mapper._schedule_release()
        assert self.mapper.release_timer is not None
        assert self.mapper.release_timer.is_alive()
        
        # Cancel for cleanup
        self.mapper.release_timer.cancel()
    
    @patch('keyboard.release')
    @patch('keyboard.unhook_all')
    def test_auto_release(self, mock_unhook, mock_release):
        """Test automatic release after timeout."""
        self.mapper.currently_pressed = {"a"}
        self.mapper.last_code_time = time.time() - 1.0  # Old timestamp
        
        self.mapper._auto_release()
        
        assert len(self.mapper.currently_pressed) == 0
        assert self.mapper.last_code is None
        assert self.mapper.last_mapping is None
    
    def test_reset_repeat_state(self):
        """Test resetting repeat state."""
        self.mapper.first_repeat_time = time.time()
        self.mapper.repeat_started = True
        self.mapper.last_repeat_action_time = time.time()
        self.mapper.last_code = "0x1"
        self.mapper.last_mapping = Mock()
        
        self.mapper._reset_repeat_state()
        
        assert self.mapper.first_repeat_time is None
        assert self.mapper.repeat_started is False
        assert self.mapper.last_repeat_action_time == 0
        assert self.mapper.last_code is None
        assert self.mapper.last_mapping is None
    
    def test_process_code_disabled(self):
        """Test processing code when mapper is disabled."""
        self.mapper.running = False
        result = self.mapper.process_code("0x1")
        assert result is False
    
    def test_process_code_no_mapping(self):
        """Test processing code with no mapping."""
        result = self.mapper.process_code("0x999")
        assert result is False
    
    @patch('keyboard.press')
    def test_process_code_new_single_key(self, mock_press):
        """Test processing new single key press."""
        mappings = {
            "0x1": KeyMapping(ActionType.SINGLE, "a", "Letter A")
        }
        self.mapper.set_mappings(mappings)
        
        result = self.mapper.process_code("0x1")
        
        assert result is True
        assert self.mapper.last_code == "0x1"
        assert "a" in self.mapper.currently_pressed
        mock_press.assert_called_once_with("a")
    
    @patch('keyboard.press')
    def test_process_code_new_combo_key(self, mock_press):
        """Test processing new combo key press."""
        mappings = {
            "0x1": KeyMapping(ActionType.COMBO, ["ctrl", "c"], "Copy")
        }
        self.mapper.set_mappings(mappings)
        
        result = self.mapper.process_code("0x1")
        
        assert result is True
        assert self.mapper.last_code == "0x1"
        assert "ctrl" in self.mapper.currently_pressed
        assert "c" in self.mapper.currently_pressed
        assert mock_press.call_count == 2
    
    @patch('keyboard.press_and_release')
    def test_process_code_sequence(self, mock_press_release):
        """Test processing sequence action."""
        mappings = {
            "0x1": KeyMapping(ActionType.SEQUENCE, ["a", "b"], "Sequence")
        }
        self.mapper.set_mappings(mappings)
        
        result = self.mapper.process_code("0x1")
        
        assert result is True
        assert mock_press_release.call_count == 2
    
    def test_process_code_special_stop(self):
        """Test processing special stop action."""
        stop_callback = Mock()
        self.mapper.set_callbacks(stop_callback=stop_callback)
        
        mappings = {
            "0x1": KeyMapping(ActionType.SPECIAL, "stop", "Stop")
        }
        self.mapper.set_mappings(mappings)
        
        result = self.mapper.process_code("0x1")
        
        assert result is True
        stop_callback.assert_called_once()
    
    def test_process_code_special_toggle_ghost(self):
        """Test processing toggle ghost special action."""
        mappings = {
            "0x1": KeyMapping(ActionType.SPECIAL, "toggle_ghost", "Toggle Ghost")
        }
        self.mapper.set_mappings(mappings)
        
        initial_state = self.mapper.ghost_key_enabled
        result = self.mapper.process_code("0x1")
        
        assert result is True
        assert self.mapper.ghost_key_enabled != initial_state
    
    def test_process_code_special_toggle_tap(self):
        """Test processing toggle tap special action."""
        mappings = {
            "0x1": KeyMapping(ActionType.SPECIAL, "toggle_tap", "Toggle Tap")
        }
        self.mapper.set_mappings(mappings)
        
        initial_state = self.mapper.single_tapping_enabled
        result = self.mapper.process_code("0x1")
        
        assert result is True
        assert self.mapper.single_tapping_enabled != initial_state
    
    def test_process_code_special_toggle_repeat(self):
        """Test processing toggle repeat special action."""
        mappings = {
            "0x1": KeyMapping(ActionType.SPECIAL, "toggle_repeat", "Toggle Repeat")
        }
        self.mapper.set_mappings(mappings)
        
        initial_state = self.mapper.repeat_enabled
        result = self.mapper.process_code("0x1")
        
        assert result is True
        assert self.mapper.repeat_enabled != initial_state
    
    def test_process_code_special_unknown(self):
        """Test processing unknown special action."""
        mappings = {
            "0x1": KeyMapping(ActionType.SPECIAL, "unknown", "Unknown")
        }
        self.mapper.set_mappings(mappings)
        
        result = self.mapper.process_code("0x1")
        assert result is False
    
    @patch('keyboard.press')
    def test_process_code_bounce_protection(self, mock_press):
        """Test bounce protection for repeated codes."""
        mappings = {
            "0x1": KeyMapping(ActionType.SINGLE, "a", "Letter A")
        }
        self.mapper.set_mappings(mappings)
        
        # First press
        result1 = self.mapper.process_code("0x1")
        assert result1 is True
        
        # Immediate repeat (should be bounced)
        result2 = self.mapper.process_code("0x1")
        assert result2 is False
        
        # Only one press should have occurred
        mock_press.assert_called_once()
    
    @patch('keyboard.press')
    def test_process_code_after_timeout(self, mock_press):
        """Test processing code after timeout."""
        mappings = {
            "0x1": KeyMapping(ActionType.SINGLE, "a", "Letter A")
        }
        self.mapper.set_mappings(mappings)
        
        # First press
        result1 = self.mapper.process_code("0x1")
        assert result1 is True
        
        # Simulate timeout
        self.mapper.last_code_time = time.time() - 1.0
        
        # Should work again
        result2 = self.mapper.process_code("0x1")
        assert result2 is True
        
        assert mock_press.call_count == 2
    
    def test_handle_repeat_no_last_code(self):
        """Test handling repeat with no last code."""
        result = self.mapper._handle_repeat(time.time())
        assert result is False
    
    def test_handle_repeat_first_time(self):
        """Test handling first repeat signal."""
        mappings = {
            "0x1": KeyMapping(ActionType.SINGLE, "a", "Letter A")
        }
        self.mapper.set_mappings(mappings)
        self.mapper.last_code = "0x1"
        self.mapper.last_mapping = mappings["0x1"]
        
        current_time = time.time()
        result = self.mapper._handle_repeat(current_time)
        
        assert result is True
        assert self.mapper.first_repeat_time == current_time
        assert self.mapper.repeat_started is False
    
    @patch('keyboard.release')
    @patch('keyboard.press')
    def test_handle_repeat_after_delay(self, mock_press, mock_release):
        """Test handling repeat after initial delay."""
        mappings = {
            "0x1": KeyMapping(ActionType.SINGLE, "a", "Letter A")
        }
        self.mapper.set_mappings(mappings)
        self.mapper.last_code = "0x1"
        self.mapper.last_mapping = mappings["0x1"]
        self.mapper.first_repeat_time = time.time() - 0.5  # Past delay threshold
        
        result = self.mapper._handle_repeat(time.time())
        
        assert result is True
        assert self.mapper.repeat_started is True
        mock_release.assert_called_once_with("a")
        mock_press.assert_called_once_with("a")
    
    def test_handle_repeat_disabled(self):
        """Test handling repeat when repeat is disabled."""
        mappings = {
            "0x1": KeyMapping(ActionType.SINGLE, "a", "Letter A")
        }
        self.mapper.set_mappings(mappings)
        self.mapper.last_code = "0x1"
        self.mapper.last_mapping = mappings["0x1"]
        self.mapper.repeat_enabled = False
        
        result = self.mapper._handle_repeat(time.time())
        assert result is True
        assert self.mapper.first_repeat_time is None
    
    @patch('keyboard.press_and_release')
    def test_execute_tap_single(self, mock_press_release):
        """Test executing tap for single key."""
        mapping = KeyMapping(ActionType.SINGLE, "a", "Letter A")
        self.mapper._execute_tap(mapping)
        mock_press_release.assert_called_once_with("a")
    
    @patch('keyboard.press_and_release')
    def test_execute_tap_combo_list(self, mock_press_release):
        """Test executing tap for combo with list."""
        mapping = KeyMapping(ActionType.COMBO, ["ctrl", "c"], "Copy")
        self.mapper._execute_tap(mapping)
        mock_press_release.assert_called_once_with("ctrl+c")
    
    @patch('keyboard.press_and_release')
    def test_execute_tap_combo_string(self, mock_press_release):
        """Test executing tap for combo with string."""
        mapping = KeyMapping(ActionType.COMBO, "ctrl", "Ctrl")
        self.mapper._execute_tap(mapping)
        mock_press_release.assert_called_once_with("ctrl")
    
    @patch('keyboard.press_and_release')
    def test_execute_sequence_list(self, mock_press_release):
        """Test executing sequence with list."""
        mapping = KeyMapping(ActionType.SEQUENCE, ["a", "b"], "Sequence")
        self.mapper._execute_sequence(mapping)
        assert mock_press_release.call_count == 2
    
    @patch('keyboard.press_and_release')
    def test_execute_sequence_string(self, mock_press_release):
        """Test executing sequence with string."""
        mapping = KeyMapping(ActionType.SEQUENCE, "a", "Single")
        self.mapper._execute_sequence(mapping)
        mock_press_release.assert_called_once_with("a")
    
    @patch('keyboard.press')
    def test_execute_initial_press_single_tap_mode(self, mock_press):
        """Test executing initial press in single tap mode."""
        self.mapper.single_tapping_enabled = True
        mapping = KeyMapping(ActionType.SINGLE, "a", "Letter A")
        
        with patch.object(self.mapper, '_execute_tap') as mock_tap:
            self.mapper._execute_initial_press(mapping)
            mock_tap.assert_called_once_with(mapping)
            mock_press.assert_not_called()
    
    @patch('keyboard.press')
    def test_execute_initial_press_exception(self, mock_press):
        """Test executing initial press with exception."""
        mock_press.side_effect = Exception("Press failed")
        mapping = KeyMapping(ActionType.SINGLE, "a", "Letter A")
        
        # Should not raise exception
        self.mapper._execute_initial_press(mapping)
    
    @patch('keyboard.release')
    @patch('keyboard.press')
    def test_execute_repeat_action_single_tap_mode(self, mock_press, mock_release):
        """Test executing repeat action in single tap mode."""
        self.mapper.single_tapping_enabled = True
        mapping = KeyMapping(ActionType.SINGLE, "a", "Letter A")
        
        with patch.object(self.mapper, '_execute_tap') as mock_tap:
            self.mapper._execute_repeat_action(mapping)
            mock_tap.assert_called_once_with(mapping)
            mock_press.assert_not_called()
            mock_release.assert_not_called()
    
    @patch('keyboard.release')
    @patch('keyboard.press')
    def test_execute_repeat_action_exception(self, mock_press, mock_release):
        """Test executing repeat action with exception."""
        mock_release.side_effect = Exception("Release failed")
        mapping = KeyMapping(ActionType.SINGLE, "a", "Letter A")
        
        # Should not raise exception
        self.mapper._execute_repeat_action(mapping)
    
    def test_cleanup(self):
        """Test cleanup method."""
        self.mapper.release_timer = Mock()
        self.mapper.first_repeat_time = time.time()
        self.mapper.repeat_started = True
        self.mapper.last_code = "0x1"
        
        with patch.object(self.mapper, '_release_all') as mock_release:
            self.mapper.cleanup()
            
            self.mapper.release_timer.cancel.assert_called_once()
            assert self.mapper.first_repeat_time is None
            assert self.mapper.repeat_started is False
            assert self.mapper.last_code is None
            mock_release.assert_called_once()
    
    def test_cleanup_no_timer(self):
        """Test cleanup with no active timer."""
        self.mapper.release_timer = None
        
        # Should not raise exception
        self.mapper.cleanup()


if __name__ == "__main__":
    pytest.main([__file__])