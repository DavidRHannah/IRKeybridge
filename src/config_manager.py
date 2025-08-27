import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class ActionType(Enum):
    SINGLE = "single"
    COMBO = "combo" 
    SEQUENCE = "sequence"
    SPECIAL = "special"

@dataclass
class KeyMapping:
    action_type: ActionType
    keys: list[str] | str
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_type': self.action_type.value,
            'keys': self.keys,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeyMapping':
        return cls(
            action_type=ActionType(data['action_type']),
            keys=data['keys'],
            description=data.get('description', '')
        )

@dataclass
class RemoteProfile:
    name: str
    brand: str
    model: str
    mappings: Dict[str, KeyMapping]
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'brand': self.brand,
            'model': self.model,
            'description': self.description,
            'mappings': {code: mapping.to_dict() for code, mapping in self.mappings.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RemoteProfile':
        mappings = {
            code: KeyMapping.from_dict(mapping_data) 
            for code, mapping_data in data['mappings'].items()
        }
        return cls(
            name=data['name'],
            brand=data['brand'],
            model=data['model'],
            description=data.get('description', ''),
            mappings=mappings
        )

class ConfigManager:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.profiles_dir = self.config_dir / "profiles"
        self.profiles_dir.mkdir(exist_ok=True)
        
        self.settings_file = self.config_dir / "settings.json"
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load application settings"""
        default_settings = {
            'serial_port': 'COM5',
            'baud_rate': 9600,
            'timeout': 0.1,
            'ghost_key': 'f10',
            'ghost_delay': 0.2,
            'repeat_threshold': 0.2,
            'last_used_profile': None
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to handle new settings
                    default_settings.update(loaded_settings)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading settings: {e}")
        
        return default_settings
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except IOError as e:
            print(f"Error saving settings: {e}")
    
    def get_setting(self, key: str, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a setting value"""
        self.settings[key] = value
        self.save_settings()
    
    def save_profile(self, profile: RemoteProfile) -> bool:
        """Save a remote profile to file"""
        filename = f"{profile.brand}_{profile.model}.json".replace(" ", "_")
        filepath = self.profiles_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving profile: {e}")
            return False
    
    def load_profile(self, filename: str) -> Optional[RemoteProfile]:
        """Load a remote profile from file"""
        filepath = self.profiles_dir / filename
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return RemoteProfile.from_dict(data)
        except (json.JSONDecodeError, IOError, KeyError) as e:
            print(f"Error loading profile {filename}: {e}")
            return None
    
    def list_profiles(self) -> list[str]:
        """List all available profile files"""
        return [f.name for f in self.profiles_dir.glob("*.json")]
    
    def create_default_vizio_profile(self) -> RemoteProfile:
        """Create the default Vizio profile from your existing mappings"""
        mappings = {
            '0x8': KeyMapping(ActionType.COMBO, ['ctrl', 'a'], 'Power button'),
            '0x2F': KeyMapping(ActionType.COMBO, ['ctrl', 'a'], 'Input button'),
            '0xEA': KeyMapping(ActionType.SEQUENCE, ['windows', 'a'], 'Amazon button'),
            '0xEB': KeyMapping(ActionType.COMBO, ['n'], 'Netflix button'),
            '0xEE': KeyMapping(ActionType.COMBO, ['i'], 'iHeart button'),
            '0x35': KeyMapping(ActionType.COMBO, ['ctrl', 'backspace'], 'Rewind'),
            '0x37': KeyMapping(ActionType.COMBO, ['ctrl', 'a'], 'Pause'),
            '0x33': KeyMapping(ActionType.COMBO, ['ctrl', 'a'], 'Play'),
            '0x36': KeyMapping(ActionType.COMBO, ['ctrl', 'a'], 'Fast Forward'),
            '0x30': KeyMapping(ActionType.SPECIAL, 'stop', 'Stop controller'),
            '0x45': KeyMapping(ActionType.COMBO, ['ctrl', 'up'], 'Up arrow'),
            '0x46': KeyMapping(ActionType.COMBO, ['ctrl', 'down'], 'Down arrow'),
            '0x47': KeyMapping(ActionType.COMBO, ['ctrl', 'left'], 'Left arrow'),
            '0x48': KeyMapping(ActionType.COMBO, ['ctrl', 'right'], 'Right arrow'),
            '0x44': KeyMapping(ActionType.COMBO, ['ctrl', 'enter'], 'Select/OK'),
            '0x2': KeyMapping(ActionType.COMBO, ['volume up'], 'Volume Up'),
            '0x3': KeyMapping(ActionType.COMBO, ['volume down'], 'Volume Down'),
            '0x2D': KeyMapping(ActionType.COMBO, ['ctrl', 'home'], 'Home'),
            '0x0': KeyMapping(ActionType.COMBO, ['ctrl', 'page up'], 'Channel Up'),
            '0x1': KeyMapping(ActionType.COMBO, ['ctrl', 'page down'], 'Channel Down'),
            '0x9': KeyMapping(ActionType.COMBO, ['ctrl', 'f'], 'Mute'),
            '0x11': KeyMapping(ActionType.SINGLE, '1', 'Number 1'),
            '0x12': KeyMapping(ActionType.SINGLE, '2', 'Number 2'),
            '0x13': KeyMapping(ActionType.SINGLE, '3', 'Number 3'),
            '0x14': KeyMapping(ActionType.SINGLE, '4', 'Number 4'),
            '0x15': KeyMapping(ActionType.SINGLE, '5', 'Number 5'),
            '0x16': KeyMapping(ActionType.SINGLE, '6', 'Number 6'),
            '0x17': KeyMapping(ActionType.SINGLE, '7', 'Number 7'),
            '0x18': KeyMapping(ActionType.SINGLE, '8', 'Number 8'),
            '0x19': KeyMapping(ActionType.SINGLE, '9', 'Number 9'),
            '0x10': KeyMapping(ActionType.SINGLE, '0', 'Number 0'),
            '0x3A': KeyMapping(ActionType.SINGLE, 'enter', 'Enter'),
            '0x1A': KeyMapping(ActionType.SPECIAL, 'toggle_tap', 'Toggle single tap mode'),
            '0xFF': KeyMapping(ActionType.SPECIAL, 'toggle_ghost', 'Toggle ghost key'),
        }
        
        return RemoteProfile(
            name="Default Vizio Remote",
            brand="Vizio",
            model="Generic TV Remote",
            description="Default configuration for Vizio TV remote",
            mappings=mappings
        )