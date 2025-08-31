"""
Main controller module for the IR Remote Controller application.

This module contains the IRRemoteController class which orchestrates the entire
IR remote control system, managing the IR receiver, key mapper, and configuration.
"""

import time
import signal
import sys
from typing import Optional
from config_manager import ConfigManager, RemoteProfile
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

    def __init__(self):
        """
        Initialize the IR Remote Controller.

        Sets up the configuration manager, IR receiver, and key mapper with
        default settings. Also configures signal handlers for graceful shutdown.
        """
        self.config_manager = ConfigManager()
        self.receiver = IRReceiver(
            port=self.config_manager.get_setting("serial_port", "COM4"),
            baud_rate=self.config_manager.get_setting("baud_rate", 9600),
            timeout=self.config_manager.get_setting("timeout", 0.1),
        )
        self.mapper = KeyMapper()

        self.running = False
        self.current_profile: Optional[RemoteProfile] = None

        self.receiver.set_error_callback(self._log_message)
        self.mapper.set_callbacks(
            stop_callback=self.stop, status_callback=self._log_message
        )

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals (SIGINT, SIGTERM).

        Args:
            signum (int): Signal number
            frame: Current stack frame
        """
        print("\nShutdown signal received...")
        self.stop()

    def _log_message(self, message: str):
        """
        Log messages with timestamp.

        Args:
            message (str): Message to log
        """
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

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
            self.mapper.set_profile(profile)
            self.config_manager.set_setting("last_used_profile", profile_name)
            return True
        return False

    def create_default_profile(self) -> bool:
        """
        Create and save the default Vizio profile.

        Returns:
            bool: True if profile created successfully, False otherwise
        """
        profile = self.config_manager.create_default_vizio_profile()
        if self.config_manager.save_profile(profile):
            self._log_message(f"Created default profile: {profile.name}")
            return True
        return False

    def list_available_profiles(self) -> list[str]:
        """
        Get list of available profiles.

        Returns:
            list[str]: List of profile filenames
        """
        return self.config_manager.list_profiles()

    def start(self, profile_name: str = None) -> bool:
        """
        Start the controller with specified or last used profile.

        Args:
            profile_name (str, optional): Name of profile to load. If None,
                uses last used profile or creates default.

        Returns:
            bool: True if controller started successfully, False otherwise
        """

        if profile_name:
            target_profile = profile_name
        else:
            target_profile = self.config_manager.get_setting("last_used_profile")

        if target_profile and not self.load_profile(target_profile):
            self._log_message(f"Failed to load profile: {target_profile}")

        if not self.current_profile:
            available_profiles = self.list_available_profiles()
            if not available_profiles:
                self._log_message("No profiles found, creating default...")
                self.create_default_profile()
                available_profiles = self.list_available_profiles()

            if available_profiles:
                if self.load_profile(available_profiles[0]):
                    self._log_message(f"Loaded first available profile")
                else:
                    self._log_message("Failed to load any profile")
                    return False
            else:
                self._log_message("No profiles available")
                return False

        if not self.receiver.connect():
            self._log_message("Failed to connect to IR receiver")
            return False

        mapper_settings = {
            "ghost_key": self.config_manager.get_setting("ghost_key", "f10"),
            "ghost_delay": self.config_manager.get_setting("ghost_delay", 0.2),
            "repeat_threshold": self.config_manager.get_setting(
                "repeat_threshold", 0.2
            ),
        }
        self.mapper.configure(**mapper_settings)

        if not self.receiver.start_receiving():
            self.receiver.disconnect()
            return False

        self.running = True
        self._log_message(
            f"Controller started with profile: {self.current_profile.name}"
        )
        self._log_message("Press any button on remote to test, STOP button to exit")
        return True

    def run(self):
        """
        Main control loop.

        Continuously processes IR codes from the receiver and maps them to
        keyboard actions. Handles key release timing and cleanup on exit.
        """
        if not self.running:
            self._log_message("Controller not started")
            return
        
        try:
            last_release_time = time.time()

            while self.running:
                start_time = time.time()
                
                ir_code = self.receiver.get_code(timeout=0.01)

                if ir_code:
                    # self._log_message(f"Received IR code: {ir_code}")
                    
                    if self.current_profile and ir_code in self.current_profile.mappings:
                        mapping = self.current_profile.mappings[ir_code]
                        # self._log_message(f"Found mapping: {mapping.description} -> {mapping.action_type}:{mapping.keys}")
                    else:
                        # self._log_message(f"No mapping found for {ir_code}")
                        if self.current_profile and self.current_profile.mappings:
                            available = list(self.current_profile.mappings.keys())[:3]
                            # self._log_message(f"Sample available codes: {available}")
                    
                    self.mapper.process_code(ir_code)
                    
                    end_time = time.time()
                    self._log_message(f"TTE: {end_time - start_time}")
                else:
                    current_time = time.time()
                    if (current_time - last_release_time) > 0.5:
                        self.mapper._release_all_keys()
                        self.mapper.last_received_code = None
                        last_release_time = current_time

                time.sleep(0.01)

        except KeyboardInterrupt:
            self._log_message("Interrupted by user")
        except Exception as e:
            self._log_message(f"Unexpected error: {e}")
            import traceback
            self._log_message(f"Traceback: {traceback.format_exc()}")
        finally:
            self.stop()

    def stop(self):
        """
        Stop the controller.

        Gracefully shuts down the receiver, mapper, and releases all resources.
        """
        if self.running:
            self.running = False
            self._log_message("Stopping controller...")

            self.receiver.stop_receiving()
            self.receiver.disconnect()

            self.mapper.cleanup()

            self._log_message("Controller stopped")

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
