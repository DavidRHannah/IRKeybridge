"""
Serial communication module for Arduino integration.

This module handles all serial communication with Arduino devices,
including connection management and data parsing.
"""

import serial
import serial.tools.list_ports
from PyQt5.QtCore import QThread, pyqtSignal


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
