"""
System configuration widget for the IR Remote Configuration Tool.

This widget handles Arduino connection settings, serial communication,
and system-wide configuration options.
"""

import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QFormLayout,
    QPushButton,
    QComboBox,
    QTextEdit,
    QLineEdit,
    QCheckBox,
)
from PyQt5.QtGui import QFont


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
