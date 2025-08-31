"""
IR receiver module for serial communication with Arduino.

This module handles the serial communication with the Arduino IR receiver,
reading IR codes and providing them to the key mapper for processing.
"""

import serial
import time
from typing import Optional, Callable
from queue import Queue, Empty
import threading


class IRReceiver:
    """
    Handles IR code reception from Arduino via serial communication.

    This class manages the serial connection to the Arduino, reads IR codes
    from the serial port, and provides them to the controller for processing.

    Attributes:
        port (str): Serial port name (e.g., 'COM4', '/dev/ttyUSB0')
        baud_rate (int): Serial communication baud rate
        timeout (float): Serial read timeout in seconds
        serial_connection (Optional[serial.Serial]): Active serial connection
        receiving (bool): Flag indicating if receiver is actively receiving
        code_queue (Queue): Thread-safe queue for received IR codes
        receiver_thread (Optional[threading.Thread]): Background receiver thread
        error_callback (Optional[Callable]): Callback for error messages
    """

    def __init__(self, port: str = "COM4", baud_rate: int = 9600, timeout: float = 0.1):
        """
        Initialize the IR receiver.

        Args:
            port (str): Serial port to connect to
            baud_rate (int): Baud rate for serial communication
            timeout (float): Read timeout in seconds
        """
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout

        self.serial_connection: Optional[serial.Serial] = None
        self.receiving = False
        self.code_queue = Queue()
        self.receiver_thread: Optional[threading.Thread] = None
        self.error_callback: Optional[Callable[[str], None]] = None

    def set_error_callback(self, callback: Callable[[str], None]):
        """
        Set error callback function.

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
            self.error_callback(f"[IR Receiver] {message}")
        else:
            print(f"[IR Receiver Error] {message}")

    def connect(self) -> bool:
        """
        Establish serial connection to Arduino.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=self.timeout,
                rtscts=False,
                dsrdtr=False,
            )

            # Wait for Arduino to initialize
            time.sleep(2)

            # Clear any startup messages
            self.serial_connection.reset_input_buffer()

            return True

        except serial.SerialException as e:
            self._log_error(f"Failed to connect: {e}")
            return False

    def disconnect(self):
        """
        Close serial connection.
        """
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
            except:
                pass
            self.serial_connection = None

    def is_connected(self) -> bool:
        """
        Check if serial connection is active.

        Returns:
            bool: True if connected, False otherwise
        """
        return self.serial_connection is not None and self.serial_connection.is_open

    def _parse_ir_data(self, data: str) -> Optional[str]:
        """
        Parse the structured IR data from Arduino.
        
        Expected format: IR_DATA|Protocol:NEC|Raw:0x8D722287|Bits:32|Command:0x72|Address:0x2287
        
        Args:
            data (str): Raw data string from Arduino
            
        Returns:
            Optional[str]: Extracted IR code or None if not valid IR data
        """
        if not data.startswith("IR_DATA|"):
            return None
        
        try:
            # Split the data by pipe character
            parts = data.split("|")
            
            # Find the Raw value
            for part in parts:
                if part.startswith("Raw:"):
                    # Extract the hex code after "Raw:"
                    raw_code = part[4:]  # Remove "Raw:" prefix
                    return raw_code
            
            return None
            
        except Exception as e:
            self._log_error(f"Failed to parse IR data: {e}")
            return None

    def _receiver_loop(self):
        """
        Background thread loop for receiving IR codes.
        """
        while self.receiving and self.is_connected():
            try:
                if self.serial_connection.in_waiting:
                    raw_data = self.serial_connection.readline()
                    
                    if raw_data:
                        # Decode and strip whitespace
                        decoded = raw_data.decode("utf-8", errors="ignore").strip()
                        
                        # Parse the structured data to extract IR code
                        ir_code = self._parse_ir_data(decoded)
                        
                        if ir_code:
                            # Put the extracted IR code in the queue
                            self.code_queue.put(ir_code)
                            # Optional: log for debugging
                            # self._log_error(f"Parsed IR code: {ir_code}")
                        # Ignore non-IR data lines (startup messages, etc.)

            except serial.SerialException as e:
                self._log_error(f"Serial error: {e}")
                self.receiving = False
                break
            except UnicodeDecodeError as e:
                self._log_error(f"Decode error: {e}")
            except Exception as e:
                self._log_error(f"Unexpected error: {e}")

    def start_receiving(self) -> bool:
        """
        Start receiving IR codes in background thread.

        Returns:
            bool: True if receiver started successfully, False otherwise
        """
        if not self.is_connected():
            self._log_error("Cannot start receiving - not connected")
            return False

        if self.receiving:
            return True

        self.receiving = True
        self.receiver_thread = threading.Thread(target=self._receiver_loop, daemon=True)
        self.receiver_thread.start()

        return True

    def stop_receiving(self):
        """
        Stop receiving IR codes.
        """
        self.receiving = False

        if self.receiver_thread:
            self.receiver_thread.join(timeout=1)
            self.receiver_thread = None

        # Clear the queue
        while not self.code_queue.empty():
            try:
                self.code_queue.get_nowait()
            except Empty:
                break

    def get_code(self, timeout: float = 0.1) -> Optional[str]:
        """
        Get next IR code from the queue.

        Args:
            timeout (float): Maximum time to wait for a code

        Returns:
            Optional[str]: IR code if available, None otherwise
        """
        try:
            return self.code_queue.get(timeout=timeout)
        except Empty:
            return None

    def flush_buffer(self):
        """
        Clear any pending data in serial buffer and queue.
        """
        if self.is_connected():
            self.serial_connection.reset_input_buffer()

        while not self.code_queue.empty():
            try:
                self.code_queue.get_nowait()
            except Empty:
                break