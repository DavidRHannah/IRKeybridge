
import time
import signal
import sys
from typing import Optional
from .config_manager import ConfigManager, RemoteProfile
from .ir_receiver import IRReceiver
from .key_mapper import KeyMapper

class IRRemoteController:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.receiver = IRReceiver(
            port=self.config_manager.get_setting('serial_port', 'COM5'),
            baud_rate=self.config_manager.get_setting('baud_rate', 9600),
            timeout=self.config_manager.get_setting('timeout', 0.1)
        )
        self.mapper = KeyMapper()
        
        self.running = False
        self.current_profile: Optional[RemoteProfile] = None
        
        
        self.receiver.set_error_callback(self._log_message)
        self.mapper.set_callbacks(
            stop_callback=self.stop,
            status_callback=self._log_message
        )
        
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\nShutdown signal received...")
        self.stop()
    
    def _log_message(self, message: str):
        """Log messages with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def load_profile(self, profile_name: str) -> bool:
        """Load a remote profile by filename"""
        profile = self.config_manager.load_profile(profile_name)
        if profile:
            self.current_profile = profile
            self.mapper.set_profile(profile)
            self.config_manager.set_setting('last_used_profile', profile_name)
            return True
        return False
    
    def create_default_profile(self) -> bool:
        """Create and save the default Vizio profile"""
        profile = self.config_manager.create_default_vizio_profile()
        if self.config_manager.save_profile(profile):
            self._log_message(f"Created default profile: {profile.name}")
            return True
        return False
    
    def list_available_profiles(self) -> list[str]:
        """Get list of available profiles"""
        return self.config_manager.list_profiles()
    
    def start(self, profile_name: str = None) -> bool:
        """Start the controller with specified or last used profile"""
        
        if profile_name:
            target_profile = profile_name
        else:
            target_profile = self.config_manager.get_setting('last_used_profile')
            
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
            'ghost_key': self.config_manager.get_setting('ghost_key', 'f10'),
            'ghost_delay': self.config_manager.get_setting('ghost_delay', 0.2),
            'repeat_threshold': self.config_manager.get_setting('repeat_threshold', 0.2)
        }
        self.mapper.configure(**mapper_settings)
        
        
        if not self.receiver.start_receiving():
            self.receiver.disconnect()
            return False
        
        self.running = True
        self._log_message(f"Controller started with profile: {self.current_profile.name}")
        self._log_message("Press any button on remote to test, STOP button to exit")
        return True
    
    def run(self):
        """Main control loop"""
        if not self.running:
            self._log_message("Controller not started")
            return
        
        try:
            last_release_time = time.time()
            
            while self.running:
                
                ir_code = self.receiver.get_code(timeout=0.01)
                
                if ir_code:
                    
                    self.mapper.process_code(ir_code)
                    last_release_time = time.time()
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
        finally:
            self.stop()
    
    def stop(self):
        """Stop the controller"""
        if self.running:
            self.running = False
            self._log_message("Stopping controller...")
            
            
            self.receiver.stop_receiving()
            self.receiver.disconnect()
            
            
            self.mapper.cleanup()
            
            self._log_message("Controller stopped")
    
    def get_status(self) -> dict:
        """Get current controller status"""
        return {
            'running': self.running,
            'connected': self.receiver.is_connected() if self.receiver else False,
            'profile': self.current_profile.name if self.current_profile else None,
            'ghost_key_enabled': self.mapper.ghost_key_enabled,
            'single_tap_enabled': self.mapper.single_tapping_enabled
        }