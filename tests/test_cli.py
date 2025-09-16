"""
Test suite for cli module.
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from argparse import Namespace

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import cli module directly - we'll mock the dependencies
import cli

class TestCreateParser:
    """Test create_parser function."""
    
    def test_create_parser(self):
        """Test parser creation and basic arguments."""
        parser = cli.create_parser()
        
        assert parser.prog == "ir-remote"
        assert "IR Remote Controller" in parser.description
        
        # Test parsing with no arguments
        args = parser.parse_args([])
        assert args.profile is None
        assert args.list_profiles is False
        assert args.verbose is False
    
    def test_parser_all_arguments(self):
        """Test all parser arguments."""
        parser = cli.create_parser()
        
        # Test with all arguments
        test_args = [
            "--profile", "test.json",
            "--list-profiles",
            "--create-default", 
            "--gui",
            "--status",
            "--port", "COM5",
            "--baud-rate", "115200",
            "--ghost-key", "f11",
            "--enable-ghost",
            "--enable-tap",
            "--verbose",
            "--debug"
        ]
        
        args = parser.parse_args(test_args)
        assert args.profile == "test.json"
        assert args.list_profiles is True
        assert args.create_default is True
        assert args.gui is True
        assert args.status is True
        assert args.port == "COM5"
        assert args.baud_rate == 115200
        assert args.ghost_key == "f11"
        assert args.enable_ghost is True
        assert args.enable_tap is True
        assert args.verbose is True
        assert args.debug is True


class TestMain:
    """Main function tests."""
    
    @patch('cli.launch_gui')
    @patch('sys.argv', ['cli.py', '--gui'])
    def test_main_gui_mode(self, mock_launch_gui):
        """Test main function in GUI mode."""
        cli.main()
        mock_launch_gui.assert_called_once()
    
    @patch('cli.list_profiles')
    @patch('sys.argv', ['cli.py', '--list-profiles'])
    def test_main_list_profiles(self, mock_list_profiles):
        """Test main function with list profiles."""
        # Mock the IRRemoteController import and class
        with patch('cli.main_controller') as mock_module:
            mock_controller_class = Mock()
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_module.IRRemoteController = mock_controller_class
            
            cli.main()
            
            mock_list_profiles.assert_called_once_with(mock_controller.config_manager)
    
    @patch('cli.create_default_profile')
    @patch('sys.argv', ['cli.py', '--create-default'])
    def test_main_create_default(self, mock_create_default):
        """Test main function with create default."""
        with patch('cli.main_controller') as mock_module:
            mock_controller_class = Mock()
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_module.IRRemoteController = mock_controller_class
            
            cli.main()
            
            mock_create_default.assert_called_once_with(mock_controller.config_manager)
    
    @patch('cli.show_status')
    @patch('sys.argv', ['cli.py', '--status'])
    def test_main_show_status(self, mock_show_status):
        """Test main function with show status."""
        with patch('cli.main_controller') as mock_module:
            mock_controller_class = Mock()
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_module.IRRemoteController = mock_controller_class
            
            cli.main()
            
            mock_show_status.assert_called_once_with(mock_controller)
    
    @patch('cli.interactive_profile_selection', return_value=None)
    @patch('sys.argv', ['cli.py'])
    def test_main_no_profile_exits(self, mock_selection):
        """Test main function exits when no profile selected."""
        with patch('cli.main_controller') as mock_module:
            mock_controller_class = Mock()
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            mock_module.IRRemoteController = mock_controller_class
            
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            
            assert exc_info.value.code == 1
    
    @patch('sys.argv', ['cli.py', '--profile', 'test.json'])
    def test_main_start_failure(self):
        """Test main function when start fails."""
        with patch('cli.main_controller') as mock_module:
            mock_controller_class = Mock()
            mock_controller = Mock()
            mock_controller.start.return_value = False
            mock_controller_class.return_value = mock_controller
            mock_module.IRRemoteController = mock_controller_class
            
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            
            assert exc_info.value.code == 1
    
    @patch('builtins.print')
    @patch('sys.argv', ['cli.py', '--profile', 'test.json'])
    def test_main_successful_run(self, mock_print):
        """Test successful main execution."""
        with patch('cli.main_controller') as mock_module:
            mock_controller_class = Mock()
            mock_controller = Mock()
            mock_controller.start.return_value = True
            mock_controller.run.side_effect = KeyboardInterrupt()  # Simulate Ctrl+C
            mock_controller_class.return_value = mock_controller
            mock_module.IRRemoteController = mock_controller_class
            
            cli.main()  # Should not raise exception
            
            mock_controller.start.assert_called_once_with('test.json')
            mock_controller.run.assert_called_once()
            mock_controller.stop.assert_called_once()
    
    @patch('builtins.print')
    @patch('sys.argv', ['cli.py', '--profile', 'test.json', '--enable-ghost', '--enable-tap'])
    def test_main_with_options(self, mock_print):
        """Test main with ghost and tap options."""
        with patch('cli.main_controller') as mock_module:
            mock_controller_class = Mock()
            mock_controller = Mock()
            mock_controller.start.return_value = True
            mock_controller.run.side_effect = KeyboardInterrupt()
            mock_controller.mapper = Mock()
            mock_controller_class.return_value = mock_controller
            mock_module.IRRemoteController = mock_controller_class
            
            cli.main()
            
            assert mock_controller.mapper.ghost_key_enabled is True
            assert mock_controller.mapper.single_tapping_enabled is True
    
    @patch('sys.argv', ['cli.py', '--profile', 'test.json', '--port', 'COM5', '--baud-rate', '115200', '--ghost-key', 'f11'])
    def test_main_with_settings(self):
        """Test main with custom settings."""
        with patch('cli.main_controller') as mock_module:
            mock_controller_class = Mock()
            mock_controller = Mock()
            mock_controller.start.return_value = True
            mock_controller.run.side_effect = KeyboardInterrupt()
            mock_controller_class.return_value = mock_controller
            mock_module.IRRemoteController = mock_controller_class
            
            with patch('builtins.print'):
                cli.main()
            
            # Verify settings were applied
            mock_controller.config_manager.set_setting.assert_any_call("serial_port", "COM5")
            mock_controller.config_manager.set_setting.assert_any_call("baud_rate", 115200)
            mock_controller.config_manager.set_setting.assert_any_call("ghost_key", "f11")


class TestUtilityFunctions:
    """Test utility functions with proper mocking."""
    
    def test_list_profiles_empty(self):
        """Test listing profiles when none exist."""
        mock_config = Mock()
        mock_config.list_profiles.return_value = []
        
        with patch('builtins.print') as mock_print:
            cli.list_profiles(mock_config)
            
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("No profiles found" in str(call) for call in print_calls)
    
    def test_list_profiles_with_data(self):
        """Test listing profiles with data."""
        mock_profile = Mock()
        mock_profile.brand = "Vizio"
        mock_profile.model = "TV"
        mock_profile.mappings = {"0x1": "test"}
        
        mock_config = Mock()
        mock_config.list_profiles.return_value = ["vizio.json"]
        mock_config.load_profile.return_value = mock_profile
        
        with patch('builtins.print') as mock_print:
            cli.list_profiles(mock_config)
            
            # Check that profile information was printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("vizio.json" in str(call) for call in print_calls)
            assert any("Vizio" in str(call) for call in print_calls)
    
    def test_list_profiles_load_error(self):
        """Test listing profiles when loading fails."""
        mock_config = Mock()
        mock_config.list_profiles.return_value = ["bad.json"]
        mock_config.load_profile.side_effect = Exception("Load error")
        
        with patch('builtins.print') as mock_print:
            cli.list_profiles(mock_config)
            
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("Unable to load profile details" in str(call) for call in print_calls)
    
    def test_create_default_profile_success(self):
        """Test successful default profile creation."""
        mock_profile = Mock()
        mock_profile.name = "Test Profile"
        mock_profile.brand = "Vizio"
        mock_profile.model = "TV"
        mock_profile.mappings = {"0x1": "test"}
        
        mock_config = Mock()
        mock_config.create_default_vizio_profile.return_value = mock_profile
        mock_config.save_profile.return_value = True
        
        with patch('builtins.print'):
            result = cli.create_default_profile(mock_config)
            assert result is True
    
    def test_create_default_profile_save_failure(self):
        """Test default profile creation with save failure."""
        mock_profile = Mock()
        mock_profile.name = "Test Profile"
        mock_profile.brand = "Vizio"
        mock_profile.model = "TV"
        mock_profile.mappings = {"0x1": "test"}
        
        mock_config = Mock()
        mock_config.create_default_vizio_profile.return_value = mock_profile
        mock_config.save_profile.return_value = False
        
        with patch('builtins.print') as mock_print:
            result = cli.create_default_profile(mock_config)
            assert result is False
            
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("Failed to save" in str(call) for call in print_calls)
    
    def test_create_default_profile_exception(self):
        """Test default profile creation with exception."""
        mock_config = Mock()
        mock_config.create_default_vizio_profile.side_effect = Exception("Error")
        
        with patch('builtins.print') as mock_print:
            result = cli.create_default_profile(mock_config)
            assert result is False
            
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("Error creating default profile" in str(call) for call in print_calls)
    
    def test_show_status_complete(self):
        """Test show status with all information."""
        mock_controller = Mock()
        mock_controller.get_status.return_value = {
            'running': True,
            'connected': True,
            'profile': 'test.json',
            'ghost_key_enabled': True,
            'single_tap_enabled': False
        }
        
        # Mock the config manager's get_setting method
        def mock_get_setting(key, default=None):
            settings = {
                'serial_port': 'COM4',
                'baud_rate': 9600,
                'ghost_key': 'f10',
                'repeat_threshold': 0.11
            }
            return settings.get(key, default)
        
        mock_controller.config_manager.get_setting = mock_get_setting
        
        with patch('builtins.print') as mock_print:
            cli.show_status(mock_controller)
            
            # Verify status information was printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("Running: Yes" in str(call) for call in print_calls)
            assert any("Connected: Yes" in str(call) for call in print_calls)
            assert any("test.json" in str(call) for call in print_calls)
    
    def test_interactive_profile_selection_by_number(self):
        """Test interactive selection by number."""
        mock_controller = Mock()
        mock_controller.list_available_profiles.return_value = ['test1.json', 'test2.json']
        
        with patch('builtins.input', return_value='1'):
            with patch('builtins.print'):
                result = cli.interactive_profile_selection(mock_controller)
                assert result == 'test1.json'
    
    def test_interactive_profile_selection_by_name(self):
        """Test interactive selection by filename."""
        mock_controller = Mock()
        mock_controller.list_available_profiles.return_value = ['test1.json', 'test2.json']
        
        with patch('builtins.input', return_value='test2.json'):
            with patch('builtins.print'):
                result = cli.interactive_profile_selection(mock_controller)
                assert result == 'test2.json'
    
    def test_interactive_profile_selection_invalid_number(self):
        """Test interactive selection with invalid number."""
        mock_controller = Mock()
        mock_controller.list_available_profiles.return_value = ['test1.json']
        
        # First invalid, then valid
        with patch('builtins.input', side_effect=['5', '1']):
            with patch('builtins.print'):
                result = cli.interactive_profile_selection(mock_controller)
                assert result == 'test1.json'
    
    def test_interactive_profile_selection_invalid_name(self):
        """Test interactive selection with invalid name."""
        mock_controller = Mock()
        mock_controller.list_available_profiles.return_value = ['test1.json']
        
        # First invalid, then valid
        with patch('builtins.input', side_effect=['nonexistent.json', '1']):
            with patch('builtins.print'):
                result = cli.interactive_profile_selection(mock_controller)
                assert result == 'test1.json'
    
    def test_interactive_profile_selection_keyboard_interrupt(self):
        """Test interactive selection with keyboard interrupt."""
        mock_controller = Mock()
        mock_controller.list_available_profiles.return_value = ['test1.json']
        
        with patch('builtins.input', side_effect=KeyboardInterrupt()):
            with patch('builtins.print'):
                result = cli.interactive_profile_selection(mock_controller)
                assert result is None
    
    def test_interactive_profile_selection_eof(self):
        """Test interactive selection with EOF."""
        mock_controller = Mock()
        mock_controller.list_available_profiles.return_value = ['test1.json']
        
        with patch('builtins.input', side_effect=EOFError()):
            with patch('builtins.print'):
                result = cli.interactive_profile_selection(mock_controller)
                assert result is None
    
    def test_interactive_profile_selection_no_profiles(self):
        """Test interactive selection with no profiles and no creation."""
        mock_controller = Mock()
        mock_controller.list_available_profiles.return_value = []
        
        with patch('builtins.input', return_value='n'):
            with patch('builtins.print'):
                result = cli.interactive_profile_selection(mock_controller)
                assert result is None
    
    def test_interactive_profile_selection_create_default(self):
        """Test interactive selection with default profile creation."""
        mock_controller = Mock()
        # First call returns empty, second returns profile after creation
        mock_controller.list_available_profiles.side_effect = [[], ['default.json']]
        mock_controller.create_default_profile.return_value = True
        
        with patch('builtins.input', side_effect=['y', '1']):
            with patch('builtins.print'):
                result = cli.interactive_profile_selection(mock_controller)
                assert result == 'default.json'
                mock_controller.create_default_profile.assert_called_once()
    
    def test_interactive_profile_selection_create_fails(self):
        """Test interactive selection when creation fails."""
        mock_controller = Mock()
        mock_controller.list_available_profiles.return_value = []
        mock_controller.create_default_profile.return_value = False
        
        with patch('builtins.input', return_value='y'):
            with patch('builtins.print'):
                result = cli.interactive_profile_selection(mock_controller)
                assert result is None
    
    def test_launch_gui_success(self):
        """Test successful GUI launch."""
        mock_gui_main = Mock()
        with patch('cli.gui.main', mock_gui_main):
            with patch('builtins.print'):
                cli.launch_gui()
                mock_gui_main.assert_called_once()
    
    def test_launch_gui_import_error(self):
        """Test GUI launch with import error."""
        with patch.dict('sys.modules', {'gui': None}):
            with patch('builtins.print'):
                with pytest.raises(SystemExit) as exc_info:
                    cli.launch_gui()
                assert exc_info.value.code == 1
    
    def test_launch_gui_runtime_error(self):
        """Test GUI launch with runtime error."""
        with patch('cli.gui.main', side_effect=RuntimeError("GUI Error")):
            with patch('builtins.print'):
                with pytest.raises(SystemExit) as exc_info:
                    cli.launch_gui()
                assert exc_info.value.code == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])