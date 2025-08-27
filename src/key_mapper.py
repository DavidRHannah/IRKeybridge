import keyboard
import time
from typing import Dict, Any, Optional, Callable
from collections import defaultdict
from .config_manager import RemoteProfile, KeyMapping, ActionType

class KeyMapper:
    def __init__(self):
        self.currently_pressed = defaultdict(bool)
        self.last_received_code: Optional[str] = None
        self.last_code_time = 0
        self.repeat_threshold = 0.2
        
        
        self.ghost_key_enabled = False
        self.single_tapping_enabled = False
        self.ghost_key = 'f10'
        self.ghost_delay = 0.2
        
        
        self.stop_callback: Optional[Callable] = None
        self.status_callback: Optional[Callable[[str], None]] = None
        
        self.profile: Optional[RemoteProfile] = None
    
    def set_profile(self, profile: RemoteProfile):
        """Set the active remote profile"""
        self.profile = profile
        self._log_status(f"Loaded profile: {profile.name}")
    
    def set_callbacks(self, stop_callback: Callable = None, status_callback: Callable[[str], None] = None):
        """Set callback functions"""
        self.stop_callback = stop_callback
        self.status_callback = status_callback
    
    def _log_status(self, message: str):
        """Log status using callback or print"""
        if self.status_callback:
            self.status_callback(message)
        else:
            print(message)
    
    def configure(self, **settings):
        """Configure mapper settings"""
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def _ghost_press(self):
        """Execute ghost key press"""
        if self.ghost_key_enabled:
            try:
                keyboard.press(self.ghost_key)
                time.sleep(self.ghost_delay)
                keyboard.release(self.ghost_key)
            except Exception:
                pass
    
    def _release_all_keys(self):
        """Release all currently pressed keys"""
        for key in list(self.currently_pressed.keys()):
            if self.currently_pressed[key]:
                try:
                    keyboard.release(key)
                    self.currently_pressed[key] = False
                except Exception:
                    pass
    
    def _handle_special_action(self, action: str) -> bool:
        """Handle special actions, return True if handled"""
        if action == 'toggle_ghost':
            self.ghost_key_enabled = not self.ghost_key_enabled
            status = "ENABLED" if self.ghost_key_enabled else "DISABLED"
            self._log_status(f"Ghost key {status}")
            return True
            
        elif action == 'toggle_tap':
            self.single_tapping_enabled = not self.single_tapping_enabled
            status = "ENABLED" if self.single_tapping_enabled else "DISABLED"
            self._log_status(f"Single tapping {status}")
            return True
            
        elif action == 'stop':
            if self.stop_callback:
                self.stop_callback()
            return True
            
        return False
    
    def _execute_key_action(self, mapping: KeyMapping, is_new_press: bool):
        """Execute the key action based on mapping type"""
        action_type = mapping.action_type
        keys = mapping.keys
        
        try:
            if action_type == ActionType.COMBO:
                if self.single_tapping_enabled:
                    
                    if isinstance(keys, list):
                        for key in keys:
                            keyboard.press(key)
                            time.sleep(0.01)
                        time.sleep(0.05)
                        for key in reversed(keys):
                            keyboard.release(key)
                            time.sleep(0.01)
                    else:
                        keyboard.press_and_release(keys)
                    return
                
                
                if is_new_press:
                    self._release_all_keys()
                    if isinstance(keys, list):
                        for key in keys:
                            keyboard.press(key)
                            self.currently_pressed[key] = True
                    else:
                        keyboard.press(keys)
                        self.currently_pressed[keys] = True
            
            elif action_type == ActionType.SEQUENCE:
                if is_new_press:
                    self._release_all_keys()
                    if isinstance(keys, list):
                        for key in keys:
                            keyboard.press_and_release(key)
                            time.sleep(0.1)
                    else:
                        keyboard.press_and_release(keys)
            
            elif action_type == ActionType.SINGLE:
                if self.single_tapping_enabled:
                    self._release_all_keys()
                    keyboard.press_and_release(keys)
                    return
                
                if is_new_press:
                    if not self.currently_pressed.get(keys, False):
                        self._release_all_keys()
                        keyboard.press(keys)
                        self.currently_pressed[keys] = True
                        
        except Exception as e:
            self._log_status(f"Key execution error: {e}")
    
    def process_code(self, ir_code: str):
        """Process an IR code and execute corresponding action"""
        if not self.profile or not ir_code:
            return
        
        
        if ir_code not in self.profile.mappings:
            return
        
        mapping = self.profile.mappings[ir_code]
        current_time = time.time()
        
        
        if mapping.action_type == ActionType.SPECIAL:
            if self._handle_special_action(mapping.keys):
                return
        
        
        is_new_press = (
            self.last_received_code != ir_code or 
            (current_time - self.last_code_time) > self.repeat_threshold
        )
        
        
        if (self.last_received_code == ir_code and 
            (current_time - self.last_code_time) < 0.1):
            return
        
        
        if is_new_press:
            self._log_status(f"Executing: {mapping.description or ir_code}")
            self._execute_key_action(mapping, True)
            self._ghost_press()
        
        
        self.last_received_code = ir_code
        self.last_code_time = current_time
    
    def cleanup(self):
        """Clean up resources and release keys"""
        self._release_all_keys()