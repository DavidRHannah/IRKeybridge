"""
Main controller module for the IR Remote Controller application.

This module contains the IRRemoteController class which orchestrates the entire
IR remote control system, managing the IR receiver, key mapper, and configuration.
"""

import time
import signal
import sys
from typing import Optional
from config_manager import ActionType, ConfigManager, KeyMapping, RemoteProfile
from ir_receiver import IRReceiver
from key_mapper import KeyMapper


class IRRemoteController:
    """
    Main controller class for the IR Remote Controller application.

    This class orchestrates the entire IR remote control system by managing:
    - IR receiver for serial communication with Arduino
    - Key mapper for translating IR codes to keyboard actions
    - Configuration manager for settings and profiles
    - Main control loop and signal handling

    Attributes:
        config_manager (ConfigManager): Manages application settings and profiles
        receiver (IRReceiver): Handles IR code reception from Arduino
        mapper (KeyMapper): Maps IR codes to keyboard actions
        running (bool): Flag indicating if the controller is active
        current_profile (Optional[RemoteProfile]): Currently loaded remote profile
    """

    def __init__(self, port="COM4", profile_path=None):
        self.receiver = IRReceiver(port=port)
        self.config_manager = ConfigManager("config")
        self.mapper = KeyMapper()
        self.running = False
        
        if profile_path:
            self.load_profile(profile_path)
        
        signal.signal(signal.SIGINT, lambda s, f: self.stop())
        
    def load_profile(self, profile_path):
        """Load and optimize profile."""
        import json
        with open(profile_path, 'r') as f:
            profile_data = json.load(f)
        
        optimized_mappings = {}
        for ir_code, mapping_data in profile_data.get("mappings", {}).items():
            optimized_mappings[ir_code] = KeyMapping(
                action_type=ActionType(mapping_data["action_type"]),
                keys=mapping_data["keys"],
                description=mapping_data.get("description", "")
            )
        
        self.mapper.set_mappings(optimized_mappings)
        self.mapper.stop_callback = self.stop
    
    def start(self) -> bool:
        """Start the controller."""
        if not self.receiver.connect():
            print("Failed to connect to receiver")
            return False
        
        if not self.receiver.start_receiving():
            print("Failed to start receiving")
            return False
        
        self.running = True
        print("Controller started")
        return True
    
    def run(self):
        """Optimized main loop with minimal overhead."""
        if not self.running:
            return
        
        last_release_check = time.time()
        release_interval = 0.5
        
        get_code = self.receiver.get_code
        process_code = self.mapper.process_code
        release_all = self.mapper._release_all
        
        try:
            while self.running:
                ir_code = get_code()
                
                if ir_code:
                    start = time.time()  # Uncomment for profiling
                    process_code(ir_code)
                    last_release_check = time.time()
                    print(f"TTE: {time.time() - start:.6f}")  # Uncomment for profiling
                else:
                    current = time.time()
                    if (current - last_release_check) > release_interval:
                        release_all()
                        self.mapper.last_code = None
                        last_release_check = current
                    else:
                        time.sleep(0.0001)  # 0.1ms
                        
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def stop(self):
        """Stop the controller."""
        if self.running:
            self.running = False
            self.mapper._release_all()
            self.receiver.disconnect()
            print("Controller stopped")
            
    def list_available_profiles(self) -> list[str]:
        """
        Get list of available profiles.

        Returns:
            list[str]: List of profile filenames
        """
        return self.config_manager.list_profiles()
    
    def get_status(self) -> dict:
        """
        Get current controller status.

        Returns:
            dict: Dictionary containing current status information including
                running state, connection status, active profile, and mode settings
        """
        return {
            "running": self.running,
            "connected": self.receiver.is_connected() if self.receiver else False,
            "profile": self.current_profile.name if self.current_profile else None,
            "ghost_key_enabled": self.mapper.ghost_key_enabled,
            "single_tap_enabled": self.mapper.single_tapping_enabled,
        }
        
    def load_profile(self, profile_name: str) -> bool:
        """
        Load a remote profile by filename.

        Args:
            profile_name (str): Name of the profile file to load

        Returns:
            bool: True if profile loaded successfully, False otherwise
        """
        profile = self.config_manager.load_profile(profile_name)
        if profile:
            self.current_profile = profile
            self.mapper.set_mappings(profile.mappings)
            self.config_manager.set_setting("last_used_profile", profile_name)
            return True
        return False
    
    def _log_message(self, message: str):
        """
        Log messages with timestamp.

        Args:
            message (str): Message to log
        """
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        