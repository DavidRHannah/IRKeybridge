"""
GUI script for configuring new remotes and developing profiles.

This module contains the SerialMonitor, ConfigManager, RemoteConfigWidget,
SystemConfigWidget, ProfileWidget, and IRRemoteGUI classes which work together
to allow the user to configure new remotes and profiles.
"""

import sys
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QSpinBox,
    QCheckBox,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QFormLayout,
    QSlider,
    QProgressBar,
    QStatusBar,
    QToolBar,
    QAction,
    QInputDialog,
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor
import ctypes


class SerialMonitor(QThread):
    """Thread for monitoring Arduino serial communication"""

    data_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.running = False
        self.port_name = ""
        self.baud_rate = 9600
        self.auto_connect = (True,)
        self.debug_mode = (True,)
        self.timeout = (0.1,)
        self.ghost_key = ("f10",)
        self.ghost_delay = (0.2,)
        self.repeat_threshold = 0.2

    def connect_arduino(self, port, baud_rate=9600):
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()

            self.port_name = port
            self.baud_rate = baud_rate
            self.serial_port = serial.Serial(port, baud_rate, timeout=1)
            self.connection_status.emit(True, f"Connected to {port}")
            return True
        except Exception as e:
            self.connection_status.emit(False, f"Failed to connect: {str(e)}")
            return False

    def disconnect_arduino(self):
        self.running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.connection_status.emit(False, "Disconnected")

    def send_command(self, command):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(f"{command}\n".encode())
                return True
            except Exception as e:
                self.connection_status.emit(False, f"Send error: {str(e)}")
                return False
        return False

    def run(self):
        self.running = True
        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting:
                    data = (
                        self.serial_port.readline()
                        .decode("utf-8", errors="ignore")
                        .strip()
                    )
                    if data:
                        self.data_received.emit(data)
                self.msleep(50)
            except Exception as e:
                self.connection_status.emit(False, f"Read error: {str(e)}")
                break


class GUIConfigManager:
    """GUI-specific configuration manager that integrates with the main application"""

    def __init__(self, config_dir="config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        sys.path.insert(0, str(Path(__file__).parent))
        from config_manager import (
            ConfigManager as MainConfigManager,
            RemoteProfile,
            KeyMapping,
            ActionType,
        )

        self.main_config = MainConfigManager(config_dir=str(self.config_dir))

        self.RemoteProfile = RemoteProfile
        self.KeyMapping = KeyMapping
        self.ActionType = ActionType

        self.gui_config_file = self.config_dir / "gui_config.json"
        self.gui_config = self.load_gui_config()

        self.temp_remotes = {}

    def load_gui_config(self):
        """Load GUI-specific configuration (window settings, etc.)"""
        default_gui_config = {
            "window_geometry": None,
            "last_tab": 0,
            "arduino_port": "",
            "baud_rate": 9600,
            "auto_connect": False,
            "debug_mode": False,
        }

        try:
            if self.gui_config_file.exists():
                with open(self.gui_config_file, "r") as f:
                    config = json.load(f)
                    default_gui_config.update(config)
            return default_gui_config
        except Exception as e:
            print(f"Error loading GUI config: {e}")
            return default_gui_config

    def save_gui_config(self):
        """Save GUI-specific configuration"""
        try:
            with open(self.gui_config_file, "w") as f:
                json.dump(self.gui_config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving GUI config: {e}")
            return False

    def save_config(self):
        """Save all configurations (for compatibility with main window)"""
        return self.save_gui_config()

    def get_profiles(self):
        """Get all available profiles from the main config manager"""
        return self.main_config.list_profiles()

    def load_profile(self, filename):
        """Load a profile using the main config manager"""
        return self.main_config.load_profile(filename)

    def save_profile(self, profile):
        """Save a profile using the main config manager"""
        return self.main_config.save_profile(profile)

    def get_remotes(self):
        """Get remotes - combination of temp remotes and existing profiles converted back"""
        remotes = {}

        remotes.update(self.temp_remotes)

        profile_files = self.main_config.list_profiles()
        for filename in profile_files:
            profile = self.main_config.load_profile(filename)
            if profile:

                gui_remote = self.profile_to_gui_format(profile)
                remotes[profile.name] = gui_remote

        return remotes

    def profile_to_gui_format(self, profile):
        """Convert a RemoteProfile to GUI format"""
        gui_remote = {
            "name": profile.name,
            "brand": profile.brand,
            "model": profile.model,
            "notes": profile.description,
            "buttons": {},
            "created": "",
            "modified": "",
        }

        for code, mapping in profile.mappings.items():

            button_name = mapping.description.replace(" button", "").replace(" ", "_")
            if not button_name or button_name == "":
                button_name = f"button_{code}"

            gui_remote["buttons"][button_name] = {
                "code": code,
                "protocol": "NEC",
                "action_type": mapping.action_type.value,
                "keys": mapping.keys,
                "description": mapping.description,
            }

        return gui_remote

    def add_remote(self, name, remote_data):
        """Add a remote - store temporarily and create profile"""

        self.temp_remotes[name] = remote_data

        try:
            profile = self.create_profile_from_remote(remote_data)
            success = self.save_profile(profile)
            if success:
                print(f"Successfully saved profile for remote '{name}'")

                if name in self.temp_remotes:
                    del self.temp_remotes[name]
            return success
        except Exception as e:
            print(f"Error creating profile from remote: {e}")
            return False

    def delete_remote(self, name):
        """Delete a remote - remove from temp storage and delete profile"""

        if name in self.temp_remotes:
            del self.temp_remotes[name]

        profile_files = self.main_config.list_profiles()
        for filename in profile_files:
            profile = self.main_config.load_profile(filename)
            if profile and profile.name == name:

                try:
                    profile_path = self.main_config.profiles_dir / filename
                    if profile_path.exists():
                        profile_path.unlink()
                        print(f"Deleted profile file: {filename}")
                except Exception as e:
                    print(f"Error deleting profile file: {e}")
                break

    def create_profile_from_remote(self, remote_data):
        """Create a profile from remote button data"""

        action_type_map = {
            "single": self.ActionType.SINGLE,
            "combo": self.ActionType.COMBO,
            "sequence": self.ActionType.SEQUENCE,
            "special": self.ActionType.SPECIAL,
        }

        mappings = {}
        for button_name, button_data in remote_data.get("buttons", {}).items():
            action_type = action_type_map.get(
                button_data.get("action_type", "single"), self.ActionType.SINGLE
            )
            keys = button_data.get("keys", "")
            description = button_data.get("description", button_name)

            ir_code = button_data.get("code", button_name)
            mappings[ir_code] = self.KeyMapping(action_type, keys, description)

        profile = self.RemoteProfile(
            name=remote_data.get("name", "Unnamed Remote"),
            brand=remote_data.get("brand", "Unknown"),
            model=remote_data.get("model", "Unknown"),
            description=remote_data.get("notes", ""),
            mappings=mappings,
        )

        return profile

    def get_system_config(self):
        """Get system configuration"""
        return self.gui_config

    def update_system_config(self, updates):
        """Update system configuration"""
        self.gui_config.update(updates)
        self.save_gui_config()

        main_settings = {}
        if "arduino_port" in updates:
            main_settings["serial_port"] = updates["arduino_port"]
        if "baud_rate" in updates:
            main_settings["baud_rate"] = updates["baud_rate"]

        if main_settings:
            for key, value in main_settings.items():
                self.main_config.set_setting(key, value)


class RemoteConfigWidget(QWidget):
    """Widget for configuring individual remotes"""

    def __init__(self, config_manager, serial_monitor=None):
        super().__init__()
        self.config_manager = config_manager
        self.serial_monitor = serial_monitor
        self.current_remote = None
        self.learning_mode = False
        self.setup_ui()
        self.refresh_remotes()
        remotes = self.config_manager.get_remotes()
        print(
            f"RemoteConfigWidget initialized with {len(remotes)} remotes: {list(remotes.keys())}"
        )

    def setup_ui(self):
        layout = QVBoxLayout()

        remote_group = QGroupBox("Remote Selection")
        remote_layout = QHBoxLayout()

        self.remote_combo = QComboBox()
        self.remote_combo.setMinimumWidth(200)

        self.new_remote_btn = QPushButton("New Remote")
        self.delete_remote_btn = QPushButton("Delete Remote")
        self.save_remote_btn = QPushButton("Save Remote")
        self.export_profile_btn = QPushButton("Export Profile")

        remote_layout.addWidget(QLabel("Remote:"))
        remote_layout.addWidget(self.remote_combo)
        remote_layout.addWidget(self.new_remote_btn)
        remote_layout.addWidget(self.delete_remote_btn)
        remote_layout.addWidget(self.save_remote_btn)
        remote_layout.addWidget(self.export_profile_btn)
        remote_group.setLayout(remote_layout)

        details_group = QGroupBox("Remote Details")
        details_layout = QFormLayout()

        self.remote_name_edit = QLineEdit()
        self.remote_brand_edit = QLineEdit()
        self.remote_model_edit = QLineEdit()
        self.remote_notes_edit = QTextEdit()
        self.remote_notes_edit.setMaximumHeight(80)

        details_layout.addRow("Name:", self.remote_name_edit)
        details_layout.addRow("Brand:", self.remote_brand_edit)
        details_layout.addRow("Model:", self.remote_model_edit)
        details_layout.addRow("Notes:", self.remote_notes_edit)
        details_group.setLayout(details_layout)

        buttons_group = QGroupBox("Button Configuration")
        buttons_layout = QVBoxLayout()

        instructions = QLabel(
            "Instructions:\n"
            "1. Connect Arduino and start serial monitor in System Config\n"
            "2. Click 'Start Learning Mode' and enter a button name\n"
            "3. Press the button on your remote control\n"
            "4. Configure the action type and keys in the table\n"
            "5. Save the remote (profile is created automatically)"
        )
        instructions.setStyleSheet(
            "QLabel { background-color: #f0f0f0; padding: 8px; border-radius: 4px; "
            "font-size: 11px; color: #333; }"
        )
        buttons_layout.addWidget(instructions)

        learn_layout = QHBoxLayout()
        self.learn_btn = QPushButton("Start Learning Mode")
        self.stop_learn_btn = QPushButton("Stop Learning")
        self.stop_learn_btn.setEnabled(False)

        learn_layout.addWidget(self.learn_btn)
        learn_layout.addWidget(self.stop_learn_btn)
        learn_layout.addStretch()

        self.buttons_table = QTableWidget()
        self.buttons_table.setColumnCount(6)
        self.buttons_table.setHorizontalHeaderLabels(
            ["Button Name", "IR Code", "Protocol", "Action Type", "Keys", "Actions"]
        )
        self.buttons_table.horizontalHeader().setStretchLastSection(True)

        self.buttons_table.setColumnWidth(0, 120)
        self.buttons_table.setColumnWidth(1, 80)
        self.buttons_table.setColumnWidth(2, 80)
        self.buttons_table.setColumnWidth(3, 100)
        self.buttons_table.setColumnWidth(4, 150)

        buttons_layout.addLayout(learn_layout)
        buttons_layout.addWidget(self.buttons_table)
        buttons_group.setLayout(buttons_layout)

        layout.addWidget(remote_group)
        layout.addWidget(details_group)
        layout.addWidget(buttons_group)

        self.setLayout(layout)

        self.new_remote_btn.clicked.connect(self.new_remote)
        self.delete_remote_btn.clicked.connect(self.delete_remote)
        self.save_remote_btn.clicked.connect(self.save_remote)
        self.export_profile_btn.clicked.connect(self.export_profile)
        self.remote_combo.currentTextChanged.connect(self.load_remote)
        self.learn_btn.clicked.connect(self.start_learning)
        self.stop_learn_btn.clicked.connect(self.stop_learning)

    def refresh_remotes(self):
        """Refresh the remote combo box with all available remotes"""
        current_text = self.remote_combo.currentText()
        self.remote_combo.clear()

        remotes = self.config_manager.get_remotes()
        remote_names = list(remotes.keys())

        print(f"Available remotes: {remote_names}")

        if remote_names:
            self.remote_combo.addItems(remote_names)

            if current_text and current_text in remote_names:
                index = self.remote_combo.findText(current_text)
                if index >= 0:
                    self.remote_combo.setCurrentIndex(index)

    def new_remote(self):
        """Create a new remote"""
        name, ok = QInputDialog.getText(self, "New Remote", "Enter remote name:")
        if ok and name.strip():
            name = name.strip()

            existing_remotes = self.config_manager.get_remotes()
            if name in existing_remotes:
                reply = QMessageBox.question(
                    self,
                    "Remote Exists",
                    f"Remote '{name}' already exists. Do you want to edit it?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    return

                index = self.remote_combo.findText(name)
                if index >= 0:
                    self.remote_combo.setCurrentIndex(index)
                return

            self.current_remote = {
                "name": name,
                "brand": "",
                "model": "",
                "notes": "",
                "buttons": {},
                "created": datetime.now().isoformat(),
            }

            self.load_remote_data()

            self.remote_name_edit.setFocus()
            print(f"Created new remote: {name}")

    def save_remote(self):
        """Save the current remote"""
        if not self.current_remote:
            QMessageBox.warning(self, "Warning", "No remote data to save!")
            return

        name = self.remote_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Please enter a remote name!")
            return

        self.current_remote.update(
            {
                "name": name,
                "brand": self.remote_brand_edit.text().strip(),
                "model": self.remote_model_edit.text().strip(),
                "notes": self.remote_notes_edit.toPlainText(),
                "modified": datetime.now().isoformat(),
            }
        )

        print(f"Saving remote '{name}' with data: {self.current_remote}")

        success = self.config_manager.add_remote(name, self.current_remote)

        if success:

            self.refresh_remotes()

            index = self.remote_combo.findText(name)
            if index >= 0:
                self.remote_combo.setCurrentIndex(index)

            QMessageBox.information(
                self,
                "Success",
                f"Remote '{name}' saved successfully!\nProfile automatically created for main application.",
            )
        else:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to save remote '{name}'. Check the console for error details.",
            )

    def load_remote(self, name):
        """Load a remote by name"""
        print(f"Loading remote: '{name}'")

        if not name:
            self.current_remote = None
            self.clear_remote_data()
            return

        remotes = self.config_manager.get_remotes()
        print(f"Available remotes for loading: {list(remotes.keys())}")

        if name in remotes:

            import copy

            self.current_remote = copy.deepcopy(remotes[name])
            self.load_remote_data()
            print(f"Successfully loaded remote: {name}")
        else:
            print(f"Remote '{name}' not found in available remotes")
            self.current_remote = None
            self.clear_remote_data()

    def load_remote_data(self):
        """Load the current remote data into the form fields"""
        if self.current_remote:
            self.remote_name_edit.setText(self.current_remote.get("name", ""))
            self.remote_brand_edit.setText(self.current_remote.get("brand", ""))
            self.remote_model_edit.setText(self.current_remote.get("model", ""))
            self.remote_notes_edit.setPlainText(self.current_remote.get("notes", ""))

            self.load_buttons_table()
            print(
                f"Loaded remote data for: {self.current_remote.get('name', 'Unknown')}"
            )
        else:
            self.clear_remote_data()
            print("No remote data to load - cleared form")

    def clear_remote_data(self):
        """Clear all remote data fields"""
        self.remote_name_edit.clear()
        self.remote_brand_edit.clear()
        self.remote_model_edit.clear()
        self.remote_notes_edit.clear()
        self.buttons_table.setRowCount(0)

    def delete_remote(self):
        """Delete the currently selected remote"""
        current_name = self.remote_combo.currentText()
        if not current_name:
            QMessageBox.warning(self, "Warning", "No remote selected to delete!")
            return

        reply = QMessageBox.question(
            self,
            "Delete Remote",
            f"Are you sure you want to delete remote '{current_name}'?\n\n"
            f"This will also delete the corresponding profile file.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:

            self.config_manager.delete_remote(current_name)

            self.current_remote = None
            self.clear_remote_data()

            self.refresh_remotes()

            QMessageBox.information(
                self,
                "Success",
                f"Remote '{current_name}' and its profile have been deleted.",
            )

    def load_buttons_table(self):
        """Load buttons into the table with proper widgets"""
        buttons = self.current_remote.get("buttons", {})
        self.buttons_table.setRowCount(len(buttons))

        for row, (button_name, button_data) in enumerate(buttons.items()):

            self.buttons_table.setItem(row, 0, QTableWidgetItem(button_name))

            self.buttons_table.setItem(
                row, 1, QTableWidgetItem(button_data.get("code", ""))
            )

            self.buttons_table.setItem(
                row, 2, QTableWidgetItem(button_data.get("protocol", ""))
            )

            action_combo = QComboBox()
            action_combo.addItems(["single", "combo", "sequence", "special"])
            action_combo.setCurrentText(button_data.get("action_type", "single"))

            action_combo.currentTextChanged.connect(
                lambda text, name=button_name: self.update_button_action_type(
                    name, text
                )
            )
            self.buttons_table.setCellWidget(row, 3, action_combo)

            keys_edit = QLineEdit()
            keys_value = button_data.get("keys", "")
            if isinstance(keys_value, list):
                keys_edit.setText(", ".join(str(k) for k in keys_value))
            else:
                keys_edit.setText(str(keys_value))

            keys_edit.textChanged.connect(
                lambda text, name=button_name: self.update_button_keys(name, text)
            )
            self.buttons_table.setCellWidget(row, 4, keys_edit)

            delete_btn = QPushButton("Delete")
            delete_btn.setMaximumWidth(60)

            delete_btn.clicked.connect(
                lambda checked, name=button_name: self.delete_button(name)
            )
            self.buttons_table.setCellWidget(row, 5, delete_btn)

    def update_button_action_type(self, button_name, action_type):
        """Update button action type"""
        if self.current_remote and "buttons" in self.current_remote:
            if button_name in self.current_remote["buttons"]:
                self.current_remote["buttons"][button_name]["action_type"] = action_type
                print(f"Updated {button_name} action type to {action_type}")

    def update_button_keys(self, button_name, keys_text):
        """Update button keys"""
        if self.current_remote and "buttons" in self.current_remote:
            if button_name in self.current_remote["buttons"]:

                if "," in keys_text:
                    keys = [k.strip() for k in keys_text.split(",") if k.strip()]
                else:
                    keys = keys_text.strip()
                self.current_remote["buttons"][button_name]["keys"] = keys
                print(f"Updated {button_name} keys to {keys}")

    def start_learning(self):
        """Start learning mode for a new button"""

        if not (
            self.serial_monitor
            and self.serial_monitor.serial_port
            and self.serial_monitor.serial_port.is_open
        ):
            QMessageBox.warning(
                self,
                "Arduino Not Connected",
                "Please connect to Arduino in System Config first!\n\n"
                "Steps:\n"
                "1. Go to System Config tab\n"
                "2. Select your Arduino port\n"
                "3. Click Connect\n"
                "4. Verify you see serial output",
            )
            return

        if not self.current_remote:
            QMessageBox.warning(
                self, "No Remote", "Please create or select a remote first!"
            )
            return

        button_name, ok = QInputDialog.getText(
            self, "Learn Button", "Enter button name:"
        )
        if ok and button_name.strip():
            button_name = button_name.strip()

            if button_name in self.current_remote.get("buttons", {}):
                reply = QMessageBox.question(
                    self,
                    "Button Exists",
                    f"Button '{button_name}' already exists. Replace it?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    return

            self.learning_mode = True
            self.learning_button_name = button_name
            self.learn_btn.setEnabled(False)
            self.stop_learn_btn.setEnabled(True)
            self.learn_btn.setText(
                f"Learning '{button_name}'... Press button on remote now!"
            )

            learning_msg = QMessageBox(self)
            learning_msg.setWindowTitle("Learning Mode Active")
            learning_msg.setText(f"Learning button: {button_name}")
            learning_msg.setInformativeText(
                "1. Point your remote at the Arduino IR receiver\n"
                "2. Press the button you want to learn\n"
                "3. Wait for confirmation\n\n"
                "Click 'Stop Learning' to cancel."
            )
            learning_msg.setStandardButtons(QMessageBox.Cancel)
            learning_msg.show()

            self.learning_dialog = learning_msg

    def stop_learning(self):
        """Stop learning mode"""
        self.learning_mode = False
        self.learn_btn.setEnabled(True)
        self.stop_learn_btn.setEnabled(False)
        self.learn_btn.setText("Start Learning Mode")

    def process_ir_code(self, ir_code, protocol):
        """Called when IR code is received during learning mode"""
        if self.learning_mode and hasattr(self, "learning_button_name"):
            if not self.current_remote:
                QMessageBox.warning(self, "Error", "No remote selected!")
                self.stop_learning()
                return

            if "buttons" not in self.current_remote:
                self.current_remote["buttons"] = {}

            self.current_remote["buttons"][self.learning_button_name] = {
                "code": ir_code,
                "protocol": protocol,
                "action_type": "single",
                "keys": "space",
                "description": f"Button {self.learning_button_name}",
                "learned": datetime.now().isoformat(),
            }

            self.load_buttons_table()
            self.stop_learning()

            QMessageBox.information(
                self,
                "Button Learned Successfully",
                f"Button '{self.learning_button_name}' learned successfully!\n\n"
                f"IR Code: {ir_code}\n"
                f"Protocol: {protocol}\n\n"
                f"You can now configure the key action by editing the button in the table.\n"
                f"Don't forget to save the remote when you're done!",
            )

    def delete_button(self, button_name):
        """Delete a button from the current remote"""
        if (
            self.current_remote
            and "buttons" in self.current_remote
            and button_name in self.current_remote["buttons"]
        ):
            reply = QMessageBox.question(
                self,
                "Delete Button",
                f"Delete button '{button_name}'?",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                del self.current_remote["buttons"][button_name]
                self.load_buttons_table()
                print(f"Deleted button: {button_name}")

    def export_profile(self):
        """Export the current remote as a profile (shows status since it's automatic on save)"""
        current_name = self.remote_combo.currentText()
        if not current_name:
            QMessageBox.warning(self, "Warning", "No remote selected!")
            return

        profile_files = self.config_manager.get_profiles()
        profile_found = False
        profile_filename = ""

        for filename in profile_files:
            profile = self.config_manager.load_profile(filename)
            if profile and profile.name == current_name:
                profile_found = True
                profile_filename = filename
                break

        if profile_found:
            QMessageBox.information(
                self,
                "Profile Available",
                f"Profile for '{current_name}' is available!\n\n"
                f"Profile file: {profile_filename}\n"
                f"Location: {self.config_manager.main_config.profiles_dir}\n\n"
                f"The profile is automatically created when you save the remote.\n"
                f"You can now use this profile in the main application.",
            )
        else:
            QMessageBox.warning(
                self,
                "No Profile Found",
                f"No profile found for '{current_name}'.\n\n"
                f"Make sure you've saved the remote first.\n"
                f"Profiles are automatically created when you save a remote.",
            )

    def validate_remote_data(self):
        """Validate that current remote has required data"""
        if not self.current_remote:
            return False, "No remote data"

        name = self.remote_name_edit.text().strip()
        if not name:
            return False, "Remote name is required"

        buttons = self.current_remote.get("buttons", {})
        if not buttons:
            return False, "Remote has no buttons configured"

        return True, "Valid"


class SystemConfigWidget(QWidget):
    """Widget for system configuration"""

    def __init__(self, config_manager, serial_monitor):
        super().__init__()
        self.config_manager = config_manager
        self.serial_monitor = serial_monitor
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout()

        arduino_group = QGroupBox("Arduino Connection")
        arduino_layout = QFormLayout()

        self.port_combo = QComboBox()
        self.refresh_ports()

        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")

        self.connect_btn = QPushButton("Connect")
        self.disconnect_btn = QPushButton("Disconnect")
        self.refresh_btn = QPushButton("Refresh Ports")

        arduino_layout.addRow("Port:", self.port_combo)
        arduino_layout.addRow("Baud Rate:", self.baud_combo)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.disconnect_btn)
        button_layout.addWidget(self.refresh_btn)
        arduino_layout.addRow("Actions:", button_layout)

        arduino_group.setLayout(arduino_layout)

        system_group = QGroupBox("System Settings")
        system_layout = QFormLayout()

        self.auto_connect_cb = QCheckBox("Auto-connect on startup")
        self.debug_mode_cb = QCheckBox("Enable debug mode")

        system_layout.addRow(self.auto_connect_cb)
        system_layout.addRow(self.debug_mode_cb)

        system_group.setLayout(system_layout)

        monitor_group = QGroupBox("Serial Monitor")
        monitor_layout = QVBoxLayout()

        self.serial_output = QTextEdit()
        self.serial_output.setFont(QFont("Consolas", 9))
        self.serial_output.setReadOnly(True)

        self.serial_input = QLineEdit()
        self.send_btn = QPushButton("Send")
        self.clear_btn = QPushButton("Clear")

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.serial_input)
        input_layout.addWidget(self.send_btn)
        input_layout.addWidget(self.clear_btn)

        monitor_layout.addWidget(self.serial_output)
        monitor_layout.addLayout(input_layout)
        monitor_group.setLayout(monitor_layout)

        layout.addWidget(arduino_group)
        layout.addWidget(system_group)
        layout.addWidget(monitor_group)

        self.setLayout(layout)

        self.connect_btn.clicked.connect(self.connect_arduino)
        self.disconnect_btn.clicked.connect(self.disconnect_arduino)
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.send_btn.clicked.connect(self.send_command)
        self.clear_btn.clicked.connect(self.serial_output.clear)
        self.serial_input.returnPressed.connect(self.send_command)

        self.auto_connect_cb.stateChanged.connect(self.save_system_config)
        self.debug_mode_cb.stateChanged.connect(self.save_system_config)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(f"{port.device} - {port.description}")

    def connect_arduino(self):
        port_text = self.port_combo.currentText()
        if port_text:
            port = port_text.split(" - ")[0]
            baud_rate = int(self.baud_combo.currentText())

            if self.serial_monitor.connect_arduino(port, baud_rate):
                self.serial_monitor.start()
                self.connect_btn.setEnabled(False)
                self.disconnect_btn.setEnabled(True)

    def disconnect_arduino(self):
        self.serial_monitor.disconnect_arduino()
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)

    def send_command(self):
        command = self.serial_input.text()
        if command:
            self.serial_monitor.send_command(command)
            self.serial_output.append(f"> {command}")
            self.serial_input.clear()

    def append_serial_data(self, data):
        self.serial_output.append(data)

        scrollbar = self.serial_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def load_config(self):
        config = self.config_manager.get_system_config()
        self.auto_connect_cb.setChecked(config.get("auto_connect", True))
        self.debug_mode_cb.setChecked(config.get("debug_mode", True))

        saved_port = config.get("arduino_port", "")
        if saved_port:
            for i in range(self.port_combo.count()):
                if saved_port in self.port_combo.itemText(i):
                    self.port_combo.setCurrentIndex(i)
                    break

    def save_system_config(self):
        port_text = self.port_combo.currentText()
        arduino_port = port_text.split(" - ")[0] if port_text else ""

        config = {
            "auto_connect": self.auto_connect_cb.isChecked(),
            "debug_mode": self.debug_mode_cb.isChecked(),
            "arduino_port": arduino_port,
            "baud_rate": int(self.baud_combo.currentText()),
        }
        self.config_manager.update_system_config(config)

        print(f"System config saved: {config}")


class ProfileWidget(QWidget):
    """Widget for managing profiles"""

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        profile_group = QGroupBox("Profile Management")
        profile_layout = QHBoxLayout()

        self.profile_combo = QComboBox()
        self.new_profile_btn = QPushButton("New Profile")
        self.delete_profile_btn = QPushButton("Delete Profile")
        self.save_profile_btn = QPushButton("Save Profile")

        profile_layout.addWidget(QLabel("Profile:"))
        profile_layout.addWidget(self.profile_combo)
        profile_layout.addWidget(self.new_profile_btn)
        profile_layout.addWidget(self.delete_profile_btn)
        profile_layout.addWidget(self.save_profile_btn)
        profile_group.setLayout(profile_layout)

        details_group = QGroupBox("Profile Details")
        details_layout = QFormLayout()

        self.profile_name_edit = QLineEdit()
        self.profile_description_edit = QTextEdit()
        self.profile_description_edit.setMaximumHeight(80)

        details_layout.addRow("Name:", self.profile_name_edit)
        details_layout.addRow("Description:", self.profile_description_edit)
        details_group.setLayout(details_layout)

        remotes_group = QGroupBox("Active Remotes")
        remotes_layout = QVBoxLayout()

        self.remotes_list = QTableWidget()
        self.remotes_list.setColumnCount(3)
        self.remotes_list.setHorizontalHeaderLabels(["Remote Name", "Brand", "Actions"])

        remotes_layout.addWidget(self.remotes_list)
        remotes_group.setLayout(remotes_layout)

        layout.addWidget(profile_group)
        layout.addWidget(details_group)
        layout.addWidget(remotes_group)

        self.setLayout(layout)


class IRRemoteGUI(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.config_manager = GUIConfigManager()
        self.serial_monitor = SerialMonitor()

        self.ir_data_buffer = ""
        self.collecting_ir_data = False

        self.setup_ui()
        self.setup_connections()

        if self.config_manager.get_system_config().get("auto_connect", False):
            QTimer.singleShot(1000, self.auto_connect)

    def setup_ui(self):
        self.setWindowTitle("IR Remote Configuration Tool")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        self.tabs = QTabWidget()

        self.system_widget = SystemConfigWidget(
            self.config_manager, self.serial_monitor
        )
        self.tabs.addTab(self.system_widget, "System Config")

        self.remote_widget = RemoteConfigWidget(
            self.config_manager, self.serial_monitor
        )
        self.tabs.addTab(self.remote_widget, "Remote Config")

        self.profile_widget = ProfileWidget(self.config_manager)
        self.tabs.addTab(self.profile_widget, "Profiles")

        layout.addWidget(self.tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        self.create_toolbar()

    def create_toolbar(self):
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        save_action = QAction("Save All", self)
        save_action.triggered.connect(self.save_all_configs)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        import_action = QAction("Import Config", self)
        import_action.triggered.connect(self.import_config)
        toolbar.addAction(import_action)

        export_action = QAction("Export Config", self)
        export_action.triggered.connect(self.export_config)
        toolbar.addAction(export_action)

        toolbar.addSeparator()

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)

    def setup_connections(self):

        self.serial_monitor.data_received.connect(self.process_serial_data)
        self.serial_monitor.connection_status.connect(self.update_connection_status)

    def process_serial_data(self, data):
        """Process incoming serial data and handle IR code detection"""
        self.system_widget.append_serial_data(data)

        if data.startswith("IR_DATA|"):
            try:
                parts = data.split("|")
                protocol = ""
                raw_value = ""

                for part in parts:
                    if part.startswith("Protocol:"):
                        protocol = part.split(":", 1)[1]
                    elif part.startswith("Raw:"):
                        raw_value = part.split(":", 1)[1]

                if raw_value and protocol:
                    print(f"Parsed IR: {protocol} - {raw_value}")
                    self.remote_widget.process_ir_code(raw_value, protocol)

            except Exception as e:
                print(f"Error parsing IR data: {e}")

    def update_connection_status(self, connected, message):
        """Handle connection status updates and UI state"""
        if connected:
            self.status_bar.showMessage(f"Connected: {message}")
            self.status_bar.setStyleSheet("QStatusBar { color: green; }")

            if hasattr(self.remote_widget, "learn_btn"):
                self.remote_widget.learn_btn.setEnabled(True)

        else:
            self.status_bar.showMessage(f"Disconnected: {message}")
            self.status_bar.setStyleSheet("QStatusBar { color: red; }")

            if hasattr(self.remote_widget, "learn_btn"):
                if self.remote_widget.learning_mode:
                    self.remote_widget.stop_learning()
                self.remote_widget.learn_btn.setEnabled(False)

    def auto_connect(self):

        config = self.config_manager.get_system_config()
        if config.get("arduino_port"):
            self.system_widget.connect_arduino()

    def save_all_configs(self):
        if self.config_manager.save_config():
            QMessageBox.information(self, "Success", "All configurations saved!")
        else:
            QMessageBox.warning(self, "Error", "Failed to save configurations!")

    def import_config(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Configuration", "", "JSON Files (*.json)"
        )
        if filename:
            try:
                with open(filename, "r") as f:
                    imported_config = json.load(f)

                self.config_manager.config.update(imported_config)
                self.config_manager.save_config()

                self.system_widget.load_config()
                self.remote_widget.refresh_remotes()

                QMessageBox.information(
                    self, "Success", "Configuration imported successfully!"
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to import config: {str(e)}")

    def export_config(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Configuration", "ir_config.json", "JSON Files (*.json)"
        )
        if filename:
            try:
                with open(filename, "w") as f:
                    json.dump(self.config_manager.config, f, indent=2)
                QMessageBox.information(
                    self, "Success", "Configuration exported successfully!"
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export config: {str(e)}")

    def show_about(self):
        about_text = """
        <h2>IR Remote Configuration Tool</h2>
        <p>Version 1.0</p>
        <p>A comprehensive tool for managing IR remote configurations with Arduino.</p>
        
        <h3>Features:</h3>
        <ul>
        <li>Arduino integration with real-time serial monitoring</li>
        <li>IR code learning from physical remotes</li>
        <li>Multiple remote configuration management</li>
        <li>JSON-based persistent storage</li>
        <li>Import/Export functionality</li>
        </ul>
        
        <h3>Supported Protocols:</h3>
        <p>NEC, Sony, RC5, RC6, Samsung, LG, JVC, Panasonic</p>
        
        <p><b>Hardware Requirements:</b><br>
        Arduino with IR receiver module (TSOP38238, VS1838B, etc.)</p>
        """

        QMessageBox.about(self, "About IR Remote Tool", about_text)

    def closeEvent(self, event):
        """Handle application close"""
        if self.serial_monitor.running:
            self.serial_monitor.disconnect_arduino()
            self.serial_monitor.wait()

        self.config_manager.save_config()
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    app.setApplicationName("IR Remote Configuration Tool")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("IR Remote Tools")

    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    window = IRRemoteGUI()
    window.show()

    sys.exit(app.exec_())


def is_admin():
    """Check for UAC Privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if __name__ == "__main__":
    if is_admin():
        main()
    else:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
