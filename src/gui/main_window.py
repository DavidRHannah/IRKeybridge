"""
Main window module for the IR Remote Configuration Tool.

This module contains the main application window that brings together
all the widgets and handles the overall application flow.
"""

import json
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QStatusBar,
    QToolBar,
    QAction,
    QMessageBox,
    QFileDialog,
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPalette, QColor

from .config_manager import GUIConfigManager
from .serial_monitor import SerialMonitor
from .widgets import RemoteConfigWidget, SystemConfigWidget, ProfileWidget


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
        """Setup signal connections between components"""
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
        """Automatically connect to Arduino if configured"""
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

                self.config_manager.gui_config.update(imported_config)
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
                    json.dump(self.config_manager.gui_config, f, indent=2)
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
