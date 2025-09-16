"""
Key mapper with keyboard-like repeat behavior (initial delay before repeats).
"""

import keyboard
import time
import threading
from typing import Dict, Optional, Callable
from config_manager import RemoteProfile, KeyMapping, ActionType


class KeyMapper:
    """
    KeyMapper that mimics standard keyboard repeat behavior.
    """

    def __init__(self):
        self.running = True
        self.currently_pressed = set()
        self.last_code = None
        self.last_mapping = None
        self.last_code_time = 0
        self.mappings = {}
        self.stop_callback = None
        self.status_callback = None
        
        self.initial_repeat_delay = 0.3
        self.repeat_rate = 0.009 
        self.release_timeout = 0.12
        
        self.first_repeat_time = None
        self.last_repeat_action_time = 0
        self.repeat_started = False
        
        self.ghost_key_enabled = False
        self.single_tapping_enabled = False
        self.repeat_enabled = True
        self.debug = False
        
        self.release_timer = None
        
    def disable(self):
        self.running = False
    
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
            if self.debug:
                self._log(f"Releasing {len(self.currently_pressed)} keys")
            for key in list(self.currently_pressed):
                try:
                    keyboard.release(key)
                except:
                    pass
            self.currently_pressed.clear()
            
        keyboard.unhook_all()
    
    def _schedule_release(self):
        """Schedule automatic key release after timeout."""
        if self.release_timer:
            self.release_timer.cancel()
        
        self.release_timer = threading.Timer(
            self.release_timeout, 
            self._auto_release
        )
        self.release_timer.daemon = True
        self.release_timer.start()
    
    def _auto_release(self):
        """Automatically release keys when no signal received."""
        current_time = time.time()
        if (current_time - self.last_code_time) >= (self.release_timeout - 0.01):
            if self.debug:
                self._log("Auto-releasing (timeout)")
            self._release_all()
            self._reset_repeat_state()
    
    def _reset_repeat_state(self):
        """Reset all repeat-related state."""
        self.first_repeat_time = None
        self.repeat_started = False
        self.last_repeat_action_time = 0
        self.last_code = None
        self.last_mapping = None
    
    def process_code(self, ir_code: str) -> bool:
        """
        Process IR code or REPEAT signal with keyboard-like repeat behavior.
        """
        if not self.running:
            return False
        current_time = time.time()
        
        if ir_code == "REPEAT":
            return self._handle_repeat(current_time)
        
        mapping = self.mappings.get(ir_code)
        if not mapping:
            if self.debug:
                self._log(f"No mapping for: {ir_code}")
            return False
        
        if mapping.action_type == ActionType.SPECIAL:
            return self._handle_special(mapping.keys)
        
        is_new_button = (ir_code != self.last_code)
        is_after_timeout = (current_time - self.last_code_time) > self.release_timeout
        
        if is_new_button or is_after_timeout:
            if is_new_button and self.currently_pressed:
                self._release_all()
            
            self._reset_repeat_state()
            
            if self.debug:
                self._log(f"New press: {mapping.description or ir_code}")
            
            self._execute_initial_press(mapping)
            
            self.last_code = ir_code
            self.last_mapping = mapping
            self.last_code_time = current_time
            
            self._schedule_release()
            
            return True
        else:
            if self.debug:
                self._log(f"Ignoring bounce for {ir_code}")
            return False
    
    def _handle_repeat(self, current_time: float) -> bool:
        """
        Handle REPEAT signal with keyboard-like delay behavior.
        """
        if not self.last_code or not self.last_mapping:
            if self.debug:
                self._log("REPEAT received but no last code")
            return False
        
        self.last_code_time = current_time
        self._schedule_release()
        
        if not self.repeat_enabled:
            return True
        
        if self.first_repeat_time is None:
            self.first_repeat_time = current_time
            if self.debug:
                self._log(f"First REPEAT - waiting {self.initial_repeat_delay}s")
            return True
        
        time_since_first_repeat = current_time - self.first_repeat_time
        
        if not self.repeat_started:
            if time_since_first_repeat >= self.initial_repeat_delay:
                self.repeat_started = True
                if self.debug:
                    self._log("Repeat delay passed - starting repeats")
                self._execute_repeat_action(self.last_mapping)
                self.last_repeat_action_time = current_time
            return True
        
        time_since_last_action = current_time - self.last_repeat_action_time
        
        if time_since_last_action >= self.repeat_rate:
            self._execute_repeat_action(self.last_mapping)
            self.last_repeat_action_time = current_time
        
        return True
    
    def _execute_initial_press(self, mapping: KeyMapping):
        """Execute the initial key press."""
        try:
            if self.single_tapping_enabled:
                self._execute_tap(mapping)
            else:
                if mapping.action_type == ActionType.SINGLE:
                    keyboard.press(mapping.keys)
                    self.currently_pressed.add(mapping.keys)
                    
                elif mapping.action_type == ActionType.COMBO:
                    if isinstance(mapping.keys, list):
                        for key in mapping.keys:
                            keyboard.press(key)
                            self.currently_pressed.add(key)
                    else:
                        keyboard.press(mapping.keys)
                        self.currently_pressed.add(mapping.keys)
                        
                elif mapping.action_type == ActionType.SEQUENCE:
                    self._execute_sequence(mapping)
                    
        except Exception as e:
            if self.debug:
                self._log(f"Error executing initial press: {e}")
    
    def _execute_repeat_action(self, mapping: KeyMapping):
        """Execute a repeat action after the initial delay."""
        try:
            action_type = mapping.action_type
            
            if self.single_tapping_enabled:
                self._execute_tap(mapping)
                if self.debug:
                    self._log(f"Repeat tap: {mapping.keys}")
                    
            else:
                if action_type == ActionType.SINGLE:
                    keyboard.release(mapping.keys)
                    keyboard.press(mapping.keys)
                    if self.debug:
                        self._log(f"Repeat key: {mapping.keys}")
                        
                elif action_type == ActionType.COMBO:
                    if isinstance(mapping.keys, list):
                        for key in mapping.keys:
                            keyboard.release(key)
                        for key in mapping.keys:
                            keyboard.press(key)
                    else:
                        keyboard.release(mapping.keys)
                        keyboard.press(mapping.keys)
                    if self.debug:
                        self._log(f"Repeat combo: {mapping.keys}")
                        
                elif action_type == ActionType.SEQUENCE:
                    self._execute_sequence(mapping)
                    if self.debug:
                        self._log(f"Repeat sequence: {mapping.keys}")
                        
        except Exception as e:
            if self.debug:
                self._log(f"Error executing repeat: {e}")
    
    def _execute_tap(self, mapping: KeyMapping):
        """Execute a tap (press and release) action."""
        if mapping.action_type == ActionType.SINGLE:
            keyboard.press_and_release(mapping.keys)
        elif mapping.action_type == ActionType.COMBO:
            if isinstance(mapping.keys, list):
                keyboard.press_and_release('+'.join(mapping.keys))
            else:
                keyboard.press_and_release(mapping.keys)
        elif mapping.action_type == ActionType.SEQUENCE:
            self._execute_sequence(mapping)
    
    def _execute_sequence(self, mapping: KeyMapping):
        """Execute a sequence of key presses."""
        if isinstance(mapping.keys, list):
            for key in mapping.keys:
                keyboard.press_and_release(key)
                time.sleep(0.02)
        else:
            keyboard.press_and_release(mapping.keys)
    
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
        elif action == "toggle_repeat":
            self.repeat_enabled = not self.repeat_enabled
            self._log(f"Keyboard repeat: {'ON' if self.repeat_enabled else 'OFF'}")
            return True
        return False
    
    def cleanup(self):
        """Clean up and release all keys."""
        
        if self.release_timer:
            self.release_timer.cancel()
        self._reset_repeat_state()
        self._release_all()
        
        if self.debug:
            self._log("Cleanup complete")