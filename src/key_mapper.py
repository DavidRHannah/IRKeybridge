"""
Optimized Key mapping module for translating IR codes to keyboard actions.
"""

import keyboard
import time
import threading
from typing import Dict, Any, Optional, Callable
from collections import defaultdict
from config_manager import RemoteProfile, KeyMapping, ActionType


class KeyMapper:
    """
    KeyMapper with non-blocking operations and caching.
    """

    def __init__(self):
        self.currently_pressed = set()
        self.last_code = None
        self.last_code_time = 0
        self.last_action_time = 0 
        self.mappings = {}
        self.stop_callback = None
        self.status_callback = None
        
        # Timing configuration
        self.min_repeat_interval = 0.005  # 50ms - minimum time between held key repeats
        self.key_release_timeout = 0.005  # 150ms - time before considering key released
        self.double_click_window = 0.005   # 300ms - window for double-clicks
        
        self.min_execution_interval = 0.0002  # 200 microseconds
        self.last_execution_time = 0
        
        self.click_count = 0
        self.last_click_code = None
        self.last_click_time = 0
        
        self.ghost_key_enabled = False
        self.single_tapping_enabled = False
        self.debug = False
    
    def set_mappings(self, mappings: Dict):
        """Set the key mappings."""
        self.mappings = mappings
        if self.debug:
            print(f"[Mapper] Loaded {len(mappings)} mappings")
    
    def set_callbacks(self, stop_callback=None, status_callback=None):
        """Set callbacks."""
        self.stop_callback = stop_callback
        self.status_callback = status_callback
    
    def _log(self, message: str):
        """Log a message."""
        if self.status_callback:
            self.status_callback(message)
        elif self.debug:
            print(f"[Mapper] {message}")
    
    def _release_all(self):
        """Release all currently pressed keys."""
        if self.currently_pressed:
            for key in list(self.currently_pressed):
                try:
                    keyboard.release(key)
                except:
                    pass
            self.currently_pressed.clear()
    
    def process_code(self, ir_code: str) -> bool:
        """
        Process IR code with proper rapid press handling.
        
        This version properly handles:
        - Rapid button presses
        - Double-clicks
        - Held buttons (continuous fire)
        - Different buttons in quick succession
        """
        
        mapping = self.mappings.get(ir_code)
        if not mapping:
            if self.debug:
                self._log(f"No mapping for: {ir_code}")
            return False
        
        current_time = time.time()
        
        if mapping.action_type == ActionType.SPECIAL:
            return self._handle_special(mapping.keys)
        
        time_since_last = current_time - self.last_code_time
        is_same_code = (ir_code == self.last_code)
        
        if is_same_code:
            if time_since_last < self.min_repeat_interval:
                if self.debug:
                    self._log(f"Bounce detected ({time_since_last*1000:.1f}ms)")
                return False
            elif time_since_last < self.key_release_timeout:
                press_type = "held"
            else:
                press_type = "new"
        else:
            press_type = "new"
            self._release_all()
        
        if press_type == "new":
            if self.debug:
                self._log(f"New press: {mapping.description or ir_code}")
            
            if ir_code == self.last_click_code and \
               (current_time - self.last_click_time) < self.double_click_window:
                self.click_count += 1
                if self.debug:
                    self._log(f"Click #{self.click_count}")
            else:
                self.click_count = 1
                self.last_click_code = ir_code
            
            self.last_click_time = current_time
            
            # Execute the action
            self._execute_action(mapping, press_type="new")
            
        elif press_type == "held":
            # Held key - handle based on action type
            if mapping.action_type == ActionType.SINGLE:
                # For single keys, just keep it pressed
                if self.debug and time_since_last > 0.5:  # Log every 500ms
                    self._log(f"Holding: {mapping.keys}")
                # Key should already be pressed, no action needed
            elif mapping.action_type in [ActionType.COMBO, ActionType.SEQUENCE]:
                # For combos/sequences, might want to repeat
                if self.single_tapping_enabled:
                    # In tap mode, repeat the tap
                    self._execute_action(mapping, press_type="repeat")
            
        # Update state
        self.last_code = ir_code
        self.last_code_time = current_time
        self.last_action_time = current_time
        
        return True
    
    def _handle_special(self, action: str) -> bool:
        """Handle special actions."""
        if action == "stop" and self.stop_callback:
            self._log("Stop requested")
            self.stop_callback()
            return True
        elif action == "toggle_ghost":
            self.ghost_key_enabled = not self.ghost_key_enabled
            self._log(f"Ghost key: {'ON' if self.ghost_key_enabled else 'OFF'}")
            return True
        elif action == "toggle_tap":
            self.single_tapping_enabled = not self.single_tapping_enabled
            self._log(f"Single tap: {'ON' if self.single_tapping_enabled else 'OFF'}")
            return True
        return False
    
    def _execute_action(self, mapping: KeyMapping, press_type: str = "new"):
        """
        Execute keyboard action.
        
        Args:
            mapping: The key mapping to execute
            press_type: "new" for new press, "repeat" for held key
        """
        keys = mapping.keys
        
        try:
            if self.single_tapping_enabled:
                # Tap mode - always press and release quickly
                self._release_all()
                
                if mapping.action_type == ActionType.SINGLE:
                    keyboard.press_and_release(keys)
                elif mapping.action_type == ActionType.COMBO:
                    if isinstance(keys, list):
                        keyboard.press_and_release('+'.join(keys))
                    else:
                        keyboard.press_and_release(keys)
                elif mapping.action_type == ActionType.SEQUENCE:
                    if isinstance(keys, list):
                        for key in keys:
                            keyboard.press_and_release(key)
                            time.sleep(0.02)  # Small delay between sequence keys
                    else:
                        keyboard.press_and_release(keys)
                
            else:
                # Hold mode - press on new, keep pressed until release
                if press_type == "new":
                    if mapping.action_type == ActionType.SINGLE:
                        # Only release and re-press if it's a different key
                        if keys not in self.currently_pressed:
                            self._release_all()
                            keyboard.press(keys)
                            self.currently_pressed.add(keys)
                    
                    elif mapping.action_type == ActionType.COMBO:
                        self._release_all()
                        if isinstance(keys, list):
                            for key in keys:
                                keyboard.press(key)
                                self.currently_pressed.add(key)
                        else:
                            keyboard.press(keys)
                            self.currently_pressed.add(keys)
                    
                    elif mapping.action_type == ActionType.SEQUENCE:
                        self._release_all()
                        if isinstance(keys, list):
                            for key in keys:
                                keyboard.press_and_release(key)
                                time.sleep(0.02)
                        else:
                            keyboard.press_and_release(keys)
                
        except Exception as e:
            if self.debug:
                self._log(f"Error executing action: {e}")
    
    def cleanup(self):
        """Clean up and release all keys."""
        self._release_all()
        if self.debug:
            self._log("Cleanup complete")

# Test rapid presses
def test_rapid_fire():
    """Test rapid button press handling."""
    import random
    
    print("Testing Rapid Fire Key Mapper")
    print("-" * 40)
    
    mapper = KeyMapper()
    mapper.debug = True
    
    # Test mappings
    test_mappings = {
        "0x123": KeyMapping(ActionType.SINGLE, "space", "Fire button"),
        "0x456": KeyMapping(ActionType.SINGLE, "a", "Move left"),
        "0x789": KeyMapping(ActionType.COMBO, ["ctrl", "s"], "Save"),
    }
    
    mapper.set_mappings(test_mappings)
    
    print("\nSimulating rapid button presses...")
    print("Watch the console and keyboard output\n")
    
    time.sleep(2)
    
    print("Test 1: Rapid fire (same button)")
    for i in range(5):
        mapper.process_code("0x123")
        time.sleep(0.04)  # 80ms between presses (fast clicking)
    
    mapper._release_all()
    time.sleep(1)
    
    # Test 2: Different buttons quickly
    print("\nTest 2: Different buttons rapidly")
    codes = ["0x123", "0x456", "0x123", "0x456"]
    for code in codes:
        mapper.process_code(code)
        time.sleep(0.03)  # 60ms between different buttons
    
    mapper._release_all()
    time.sleep(1)
    
    # Test 3: Double-click simulation
    print("\nTest 3: Double-click")
    mapper.process_code("0x123")
    time.sleep(0.075)  # 150ms gap
    mapper.process_code("0x123")
    
    mapper._release_all()
    time.sleep(1)
    
    # Test 4: Held button (continuous)
    print("\nTest 4: Held button")
    for i in range(10):
        mapper.process_code("0x456")
        time.sleep(0.02)  # 20ms - simulating held button repeats
    
    mapper.cleanup()
    print("\nTest complete!")

if __name__ == "__main__":
    test_rapid_fire()