"""
IR receiver module for serial communication with Arduino.

This module handles serial communication with an Arduino-based IR receiver,
managing the connection, receiving IR codes in a background thread, and
providing a queue-based interface for code retrieval.
"""

import serial
import time
import threading
from typing import Optional, Callable
from queue import Queue, Empty


class IRReceiver:
    """
    Handles serial communication with Arduino IR receiver.

    This class manages the serial connection to an Arduino-based IR receiver,
    processes incoming IR codes in a background thread, and provides a
    thread-safe queue interface for retrieving codes.

    Attributes:
        port (str): Serial port name (e.g., 'COM5', '/dev/ttyUSB0')
        baud_rate (int): Serial communication baud rate
        timeout (float): Serial read timeout in seconds
        serial_conn (Optional[serial.Serial]): Active serial connection
        running (bool): Flag indicating if receiver thread is active
        receive_thread (Optional[threading.Thread]): Background receiver thread
        code_queue (Queue): Thread-safe queue for IR codes
        error_callback (Optional[Callable]): Callback for error reporting
    """

    def __init__(self, port: str, baud_rate: int = 9600, timeout: float = 0.1):
        """
        Initialize the IR receiver.

        Args:
            port (str): Serial port name (e.g., 'COM5', '/dev/ttyUSB0')
            baud_rate (int, optional): Serial baud rate. Defaults to 9600.
            timeout (float, optional): Serial read timeout. Defaults to 0.1.
        """
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.running = False
        self.receive_thread: Optional[threading.Thread] = None
        self.code_queue = Queue()
        self.error_callback: Optional[Callable[[str], None]] = None

    def set_error_callback(self, callback: Callable[[str], None]):
        """
        Set callback for error handling.

        Args:
            callback (Callable[[str], None]): Function to call with error messages
        """
        self.error_callback = callback

    def _log_error(self, message: str):
        """
        Log error using callback or print.

        Args:
            message (str): Error message to log
        """
        if self.error_callback:
            self.error_callback(f"IRReceiver: {message}")
        else:
            print(f"IRReceiver Error: {message}")

    def connect(self) -> bool:
        """
        Connect to the serial port.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.serial_conn = serial.Serial(
                port=self.port, baudrate=self.baud_rate, timeout=self.timeout
            )
            return True
        except serial.SerialException as e:
            self._log_error(f"Failed to connect to {self.port}: {e}")
            return False

    def disconnect(self):
        """
        Disconnect from serial port.

        Closes the serial connection if it's open.
        """
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

    def start_receiving(self):
        """
        Start receiving IR codes in background thread.

        Returns:
            bool: True if receiver started successfully, False otherwise
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            self._log_error("Serial connection not established")
            return False

        self.running = True
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()
        return True

    def stop_receiving(self):
        """
        Stop receiving IR codes.

        Stops the background receiver thread and waits for it to finish.
        """
        self.running = False
        if self.receive_thread:
            self.receive_thread.join(timeout=1.0)

    def _receive_loop(self):
        """
        Background thread for receiving serial data.

        Continuously reads from serial port, filters and processes IR codes,
        and adds valid codes to the queue.
        """
        while self.running and self.serial_conn and self.serial_conn.is_open:
            try:
                line = self.serial_conn.readline()
                if line:
                    code = line.decode("utf-8").strip().upper()
                    if code and code.startswith("0X"):
                        clean_code = code[2:]
                        self.code_queue.put(clean_code)

            except UnicodeDecodeError:
                continue
            except serial.SerialException as e:
                self._log_error(f"Serial communication error: {e}")
                break
            except Exception as e:
                self._log_error(f"Unexpected error: {e}")

            time.sleep(0.01)

    def get_code(self, timeout: float = 0) -> Optional[str]:
        """
        Get next IR code from queue.

        Args:
            timeout (float, optional): Maximum time to wait for code. Defaults to 0.

        Returns:
            Optional[str]: IR code if available, None if timeout or queue empty
        """
        try:
            return self.code_queue.get(timeout=timeout)
        except Empty:
            return None

    def is_connected(self) -> bool:
        """
        Check if serial connection is active.

        Returns:
            bool: True if connected and port is open, False otherwise
        """
        return self.serial_conn is not None and self.serial_conn.is_open
