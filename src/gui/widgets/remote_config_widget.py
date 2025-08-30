"""
Remote configuration widget for the IR Remote Configuration Tool.

This widget handles all remote-related operations including creating new remotes,
learning IR codes from physical remotes, and managing button configurations.
"""

import copy
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QFormLayout,
    QMessageBox,
    QInputDialog,
)


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
