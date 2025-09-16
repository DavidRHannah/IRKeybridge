"""
Pytest configuration and shared fixtures for IR Remote Controller tests.
Fixed for src/ directory structure.
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

# Verify imports work
try:
    from config_manager import ConfigManager, RemoteProfile, KeyMapping, ActionType
    import cli
    import ir_receiver
    import key_mapper
    import main_controller
    print(f"✓ Successfully imported modules from {src_dir}")
except ImportError as e:
    print(f"✗ Failed to import modules: {e}")
    print(f"✓ Project root: {project_root}")
    print(f"✓ Source directory: {src_dir}")
    print(f"✓ Available source files: {list(src_dir.glob('*.py'))}")


@pytest.fixture
def temp_config_dir():
    """Create a temporary configuration directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def config_manager(temp_config_dir):
    """Create a ConfigManager instance with temporary directory."""
    return ConfigManager(temp_config_dir)


@pytest.fixture
def sample_key_mapping():
    """Create a sample KeyMapping for testing."""
    return KeyMapping(
        action_type=ActionType.SINGLE,
        keys="a",
        description="Letter A"
    )


@pytest.fixture
def sample_remote_profile(sample_key_mapping):
    """Create a sample RemoteProfile for testing."""
    mappings = {
        "0x1": sample_key_mapping,
        "0x2": KeyMapping(ActionType.COMBO, ["ctrl", "c"], "Copy"),
        "0x3": KeyMapping(ActionType.SEQUENCE, ["a", "b"], "Sequence"),
        "0x4": KeyMapping(ActionType.SPECIAL, "stop", "Stop")
    }
    
    return RemoteProfile(
        name="Test Remote",
        brand="TestBrand",
        model="TestModel",
        mappings=mappings,
        description="Test profile for unit tests"
    )


@pytest.fixture
def mock_ir_receiver():
    """Create a mock IRReceiver."""
    receiver = Mock()
    receiver.port = "TEST_PORT"
    receiver.baud_rate = 9600
    receiver.serial_connection = None
    receiver.receiving = False
    receiver.codes_received = 0
    receiver.codes_dropped = 0
    receiver.connect.return_value = True
    receiver.start_receiving.return_value = True
    receiver.is_connected.return_value = True
    receiver.get_code.return_value = None
    receiver.get_statistics.return_value = {
        "codes_received": 0,
        "codes_dropped": 0,
        "queue_size": 0,
        "connected": True,
        "receiving": True
    }
    return receiver


@pytest.fixture
def mock_key_mapper():
    """Create a mock KeyMapper."""
    mapper = Mock()
    mapper.running = True
    mapper.currently_pressed = set()
    mapper.last_code = None
    mapper.last_mapping = None
    mapper.mappings = {}
    mapper.ghost_key_enabled = False
    mapper.single_tapping_enabled = False
    mapper.repeat_enabled = True
    mapper.debug = False
    mapper.process_code.return_value = True
    return mapper


@pytest.fixture
def mock_controller(mock_ir_receiver, mock_key_mapper, config_manager):
    """Create a mock IRRemoteController."""
    controller = Mock()
    controller.receiver = mock_ir_receiver
    controller.mapper = mock_key_mapper
    controller.config_manager = config_manager
    controller.running = False
    controller.current_profile = None
    
    controller.start.return_value = True
    controller.load_profile.return_value = True
    controller.list_available_profiles.return_value = ["test.json"]
    controller.get_status.return_value = {
        "running": False,
        "connected": True,
        "profile": None,
        "ghost_key_enabled": False,
        "single_tap_enabled": False,
    }
    
    return controller


@pytest.fixture(autouse=True)
def disable_keyboard_hooks():
    """Disable actual keyboard hooks during testing."""
    # Mock keyboard module if it's imported
    try:
        import keyboard
        keyboard.press = Mock()
        keyboard.release = Mock()
        keyboard.press_and_release = Mock()
        keyboard.unhook_all = Mock()
    except ImportError:
        pass  # keyboard module not available, which is fine for testing


@pytest.fixture
def sample_profile_data():
    """Sample profile data in dictionary format."""
    return {
        "name": "Test Remote",
        "brand": "TestBrand",
        "model": "TestModel",
        "description": "Test profile",
        "mappings": {
            "0x1": {
                "action_type": "single",
                "keys": "a",
                "description": "Letter A"
            },
            "0x2": {
                "action_type": "combo",
                "keys": ["ctrl", "c"],
                "description": "Copy"
            },
            "0x3": {
                "action_type": "sequence",
                "keys": ["a", "b"],
                "description": "Sequence"
            },
            "0x4": {
                "action_type": "special",
                "keys": "stop",
                "description": "Stop"
            }
        }
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add unit marker to all tests by default
        if not any(marker.name in ['integration', 'slow'] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)
        
        # Add slow marker to tests that might be slow
        if any(keyword in item.name.lower() for keyword in ['integration', 'workflow', 'full']):
            item.add_marker(pytest.mark.slow)


# Custom assertions
def assert_key_mapping_equal(mapping1, mapping2):
    """Assert that two KeyMapping objects are equal."""
    assert mapping1.action_type == mapping2.action_type
    assert mapping1.keys == mapping2.keys
    assert mapping1.description == mapping2.description


def assert_profile_equal(profile1, profile2):
    """Assert that two RemoteProfile objects are equal."""
    assert profile1.name == profile2.name
    assert profile1.brand == profile2.brand
    assert profile1.model == profile2.model
    assert profile1.description == profile2.description
    assert len(profile1.mappings) == len(profile2.mappings)
    
    for code, mapping1 in profile1.mappings.items():
        assert code in profile2.mappings
        assert_key_mapping_equal(mapping1, profile2.mappings[code])


# Make custom assertions available globally
pytest.assert_key_mapping_equal = assert_key_mapping_equal
pytest.assert_profile_equal = assert_profile_equal