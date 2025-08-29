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
        self.auto_connect= True,
        self.debug_mode= True,
        self.timeout= 0.1,
        self.ghost_key= "f10",
        self.ghost_delay= 0.2,
        self.repeat_threshold= 0.2

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


class ConfigManager:
    """Manages JSON configuration files"""

    def __init__(self, config_dir="config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        self.default_config = {
            "system": {
                "arduino_port": "",
                "serial_port": "COM4",
                "baud_rate": 9600,
                "auto_connect": True,
                "debug_mode": True,
                "timeout": 0.1,
                "ghost_key": "f10",
                "ghost_delay": 0.2,
                "repeat_threshold": 0.2
            },
            "remotes": {},
            "profiles": {},
        }

        self.config_file = self.config_dir / "ir_config.json"
        self.load_config()

    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    self.config = json.load(f)
            else:
                self.config = self.default_config.copy()
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = self.default_config.copy()

    def save_config(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get_remotes(self):
        return self.config.get("remotes", {})

    def add_remote(self, name, remote_data):
        if "remotes" not in self.config:
            self.config["remotes"] = {}
        self.config["remotes"][name] = remote_data
        self.save_config()

    def delete_remote(self, name):
        if name in self.config.get("remotes", {}):
            del self.config["remotes"][name]
            self.save_config()

    def get_system_config(self):
        return self.config.get("system", self.default_config["system"])

    def update_system_config(self, updates):
        if "system" not in self.config:
            self.config["system"] = {}
        self.config["system"].update(updates)
        self.save_config()


class RemoteConfigWidget(QWidget):
    """Widget for configuring individual remotes"""

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.current_remote = None
        self.learning_mode = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        remote_group = QGroupBox("Remote Selection")
        remote_layout = QHBoxLayout()

        self.remote_combo = QComboBox()
        self.refresh_remotes()

        self.new_remote_btn = QPushButton("New Remote")
        self.delete_remote_btn = QPushButton("Delete Remote")
        self.save_remote_btn = QPushButton("Save Remote")

        remote_layout.addWidget(QLabel("Remote:"))
        remote_layout.addWidget(self.remote_combo)
        remote_layout.addWidget(self.new_remote_btn)
        remote_layout.addWidget(self.delete_remote_btn)
        remote_layout.addWidget(self.save_remote_btn)
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

        learn_layout = QHBoxLayout()
        self.learn_btn = QPushButton("Start Learning Mode")
        self.stop_learn_btn = QPushButton("Stop Learning")
        self.stop_learn_btn.setEnabled(False)

        learn_layout.addWidget(self.learn_btn)
        learn_layout.addWidget(self.stop_learn_btn)
        learn_layout.addStretch()

        self.buttons_table = QTableWidget()
        self.buttons_table.setColumnCount(4)
        self.buttons_table.setHorizontalHeaderLabels(
            ["Button Name", "IR Code", "Protocol", "Actions"]
        )
        self.buttons_table.horizontalHeader().setStretchLastSection(True)

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
        self.remote_combo.currentTextChanged.connect(self.load_remote)
        self.learn_btn.clicked.connect(self.start_learning)
        self.stop_learn_btn.clicked.connect(self.stop_learning)

    def refresh_remotes(self):
        self.remote_combo.clear()
        remotes = self.config_manager.get_remotes()
        self.remote_combo.addItems(list(remotes.keys()))

    def new_remote(self):
        name, ok = QInputDialog.getText(self, "New Remote", "Enter remote name:")
        if ok and name:
            self.current_remote = {
                "name": name,
                "brand": "",
                "model": "",
                "notes": "",
                "buttons": {},
                "created": datetime.now().isoformat(),
            }
            self.remote_combo.addItem(name)
            self.remote_combo.setCurrentText(name)
            self.load_remote_data()

    def delete_remote(self):
        current_name = self.remote_combo.currentText()
        if current_name:
            reply = QMessageBox.question(
                self, "Delete Remote", f"Delete remote '{current_name}'?"
            )
            if reply == QMessageBox.Yes:
                self.config_manager.delete_remote(current_name)
                self.refresh_remotes()

    def save_remote(self):
        if self.current_remote:
            name = self.remote_name_edit.text()
            if name:
                self.current_remote.update(
                    {
                        "name": name,
                        "brand": self.remote_brand_edit.text(),
                        "model": self.remote_model_edit.text(),
                        "notes": self.remote_notes_edit.toPlainText(),
                        "modified": datetime.now().isoformat(),
                    }
                )
                self.config_manager.add_remote(name, self.current_remote)
                self.refresh_remotes()
                QMessageBox.information(self, "Success", "Remote saved successfully!")

    def load_remote(self, name):
        if name:
            remotes = self.config_manager.get_remotes()
            self.current_remote = remotes.get(name, {})
            self.load_remote_data()

    def load_remote_data(self):
        if self.current_remote:
            self.remote_name_edit.setText(self.current_remote.get("name", ""))
            self.remote_brand_edit.setText(self.current_remote.get("brand", ""))
            self.remote_model_edit.setText(self.current_remote.get("model", ""))
            self.remote_notes_edit.setPlainText(self.current_remote.get("notes", ""))

            self.load_buttons_table()

    def load_buttons_table(self):
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

            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(
                lambda checked, name=button_name: self.delete_button(name)
            )
            self.buttons_table.setCellWidget(row, 3, delete_btn)

    def start_learning(self):
        button_name, ok = QInputDialog.getText(
            self, "Learn Button", "Enter button name:"
        )
        if ok and button_name:
            self.learning_mode = True
            self.learning_button_name = button_name
            self.learn_btn.setEnabled(False)
            self.stop_learn_btn.setEnabled(True)
            self.learn_btn.setText(
                f"Learning '{button_name}'... Press the button on remote"
            )

    def stop_learning(self):
        self.learning_mode = False
        self.learn_btn.setEnabled(True)
        self.stop_learn_btn.setEnabled(False)
        self.learn_btn.setText("Start Learning Mode")

    def process_ir_code(self, ir_code, protocol):
        """Called when IR code is received during learning mode"""
        if self.learning_mode and hasattr(self, "learning_button_name"):
            if "buttons" not in self.current_remote:
                self.current_remote["buttons"] = {}

            self.current_remote["buttons"][self.learning_button_name] = {
                "code": ir_code,
                "protocol": protocol,
                "learned": datetime.now().isoformat(),
            }

            self.load_buttons_table()
            self.stop_learning()
            QMessageBox.information(
                self,
                "Success",
                f"Button '{self.learning_button_name}' learned successfully!",
            )

    def delete_button(self, button_name):
        if (
            "buttons" in self.current_remote
            and button_name in self.current_remote["buttons"]
        ):
            del self.current_remote["buttons"][button_name]
            self.load_buttons_table()


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
        config = {
            "auto_connect": self.auto_connect_cb.isChecked(),
            "debug_mode": self.debug_mode_cb.isChecked(),
            "arduino_port": (
                self.port_combo.currentText().split(" - ")[0]
                if self.port_combo.currentText()
                else ""
            ),
            "baud_rate": int(self.baud_combo.currentText()),
        }
        self.config_manager.update_system_config(config)


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
        self.config_manager = ConfigManager()
        self.serial_monitor = SerialMonitor()

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

        self.remote_widget = RemoteConfigWidget(self.config_manager)
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

        self.system_widget.append_serial_data(data)

        if "Protocol:" in data and "Raw Value:" in data:
            try:

                lines = data.split("\n") if "\n" in data else [data]
                for line in lines:
                    if "Raw Value:" in line and "Protocol:" in line:
                        parts = line.split()
                        protocol_idx = -1
                        raw_idx = -1

                        for i, part in enumerate(parts):
                            if part == "Protocol:":
                                protocol_idx = i + 1
                            elif part == "Value:" and i > 0 and parts[i - 1] == "Raw":
                                raw_idx = i + 1

                        if protocol_idx < len(parts) and raw_idx < len(parts):
                            protocol = parts[protocol_idx]
                            ir_code = parts[raw_idx]
                            self.remote_widget.process_ir_code(ir_code, protocol)
            except (ValueError, IndexError):
                pass

        elif "RAW:" in data and "Protocol:" in data:
            try:
                parts = data.split()
                protocol_idx = parts.index("Protocol:") + 1
                raw_idx = parts.index("RAW:") + 1

                if protocol_idx < len(parts) and raw_idx < len(parts):
                    protocol = parts[protocol_idx]
                    ir_code = parts[raw_idx]
                    self.remote_widget.process_ir_code(ir_code, protocol)
            except (ValueError, IndexError):
                pass

    def update_connection_status(self, connected, message):
        if connected:
            self.status_bar.showMessage(f"Connected: {message}")
        else:
            self.status_bar.showMessage(f"Disconnected: {message}")

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
