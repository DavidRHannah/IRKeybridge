"""
IR receiver module for serial communication with optimized Arduino firmware.

This module handles the serial communication with the Arduino IR receiver,
reading IR codes and providing them to the key mapper for processing.
"""

import serial
import time
import threading
from typing import Optional, Callable
from queue import Queue, Empty

class IRReceiver:
    """
    Optimized IR code reception from Arduino via serial communication.
    Works with simplified firmware that sends just "0xHEXCODE" format.
    """

    def __init__(self, port: str = "COM4", baud_rate: int = 115200):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_connection: Optional[serial.Serial] = None
        self.receiving = False
        self.code_queue = Queue(maxsize=100)
        self.receiver_thread: Optional[threading.Thread] = None
        self.error_callback: Optional[Callable[[str], None]] = None
        
        self.codes_received = 0
        self.codes_dropped = 0
        
    def set_error_callback(self, callback: Callable[[str], None]):
        """Set error callback function."""
        self.error_callback = callback
    
    def _log_error(self, message: str):
        """Log error using callback or print."""
        if self.error_callback:
            self.error_callback(f"[IR Receiver] {message}")
        else:
            print(f"[IR Receiver Error] {message}")
    
    def connect(self) -> bool:
        """Establish serial connection with optimized settings."""
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=0,
                write_timeout=0,
                inter_byte_timeout=None,
                rtscts=False,
                dsrdtr=False,
            )
            
            if hasattr(self.serial_connection, 'set_buffer_size'):
                self.serial_connection.set_buffer_size(rx_size=4096, tx_size=4096)
            
            time.sleep(1.0)
            self.serial_connection.reset_input_buffer()
            
            start_time = time.time()
            while time.time() - start_time < 2.0:
                if self.serial_connection.in_waiting:
                    line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                    if line == "READY":
                        self._log_error("Arduino ready")
                        break
            
            return True
            
        except serial.SerialException as e:
            self._log_error(f"Connection failed: {e}")
            return False
    
    def _receiver_loop(self):
        """
        Optimized receiver loop for simple hex format.
        Expects lines like: 0xHEXVALUE
        """
        buffer = bytearray()
        
        while self.receiving and self.serial_connection:
            try:
                if self.serial_connection.in_waiting:
                    chunk = self.serial_connection.read(self.serial_connection.in_waiting)
                    buffer.extend(chunk)
                    
                    while b'\n' in buffer:
                        line_end = buffer.index(b'\n')
                        line = bytes(buffer[:line_end]).strip()
                        buffer = buffer[line_end + 1:]
                        
                        if line.endswith(b'\r'):
                            line = line[:-1]
                        
                        if line:
                            self._process_line(line)
                else:
                    time.sleep(0.0001)
                    
            except Exception as e:
                pass
    
    def _process_line(self, line: bytes):
        """
        Process a single line from Arduino.
        Expected formats:
        - 0xHEXVALUE (IR code)
        - READY (startup)
        - OK:HEXVALUE (status response)
        - RST (reset confirmation)
        - REPEAT (optional repeat signal)
        """
        try:
            decoded = line.decode('ascii').strip()
            if decoded.startswith('0x'):
                self.codes_received += 1
                try:
                    self.code_queue.put_nowait(decoded)
                except:
                    self.codes_dropped += 1
                    try:
                        self.code_queue.get_nowait()
                        self.code_queue.put_nowait(decoded)
                    except:
                        pass
            
            elif decoded == "REPEAT":
                pass
            elif decoded.startswith("OK:"):
                pass
            elif decoded in ["READY", "RST"]:
                pass
            
        except UnicodeDecodeError:
            pass
    
    def start_receiving(self) -> bool:
        """Start receiving with high-priority thread."""
        if not self.serial_connection:
            self._log_error("Cannot start - not connected")
            return False
        
        if self.receiving:
            return True
        
        self.receiving = True
        self.receiver_thread = threading.Thread(
            target=self._receiver_loop, 
            daemon=True,
            name="IR-Receiver"
        )
        self.receiver_thread.start()
        return True
    
    def stop_receiving(self):
        """Stop receiving IR codes."""
        self.receiving = False
        
        if self.receiver_thread:
            self.receiver_thread.join(timeout=0.5)
            self.receiver_thread = None
        
        while not self.code_queue.empty():
            try:
                self.code_queue.get_nowait()
            except Empty:
                break
    
    def get_code(self, timeout: float = 0) -> Optional[str]:
        """
        Get next IR code from queue.
        
        Args:
            timeout: How long to wait (0 = don't wait, None = wait forever)
            
        Returns:
            IR code string like "0x8D722287" or None
        """
        try:
            if timeout == 0:
                return self.code_queue.get_nowait()
            else:
                return self.code_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def get_statistics(self) -> dict:
        """Get receiver statistics."""
        return {
            "codes_received": self.codes_received,
            "codes_dropped": self.codes_dropped,
            "queue_size": self.code_queue.qsize(),
            "connected": self.is_connected(),
            "receiving": self.receiving
        }
    
    def send_command(self, command: str):
        """Send a command to Arduino (S=status, R=reset)."""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.write(command.encode('ascii'))
            except:
                pass
    
    def is_connected(self) -> bool:
        """Check if serial connection is active."""
        return self.serial_connection is not None and self.serial_connection.is_open
    
    def disconnect(self):
        """Clean disconnect."""
        self.stop_receiving()
        
        if self.serial_connection:
            try:
                self.serial_connection.close()
            except:
                pass
            self.serial_connection = None
    
    def flush_buffer(self):
        """Clear any pending data in serial buffer and queue."""
        if self.is_connected():
            self.serial_connection.reset_input_buffer()
        
        while not self.code_queue.empty():
            try:
                self.code_queue.get_nowait()
            except Empty:
                break