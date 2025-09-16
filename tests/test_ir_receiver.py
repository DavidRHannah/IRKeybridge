"""
Test suite for ir_receiver module.
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from queue import Queue, Empty

from ir_receiver import IRReceiver


class TestIRReceiver:
    """Test IRReceiver class."""
    
    def setup_method(self):
        """Set up test environment."""
        from ir_receiver import IRReceiver
        self.receiver = IRReceiver(port="TEST_PORT", baud_rate=9600)
    
    def teardown_method(self):
        """Clean up test environment."""
        if hasattr(self, 'receiver') and self.receiver:
            self.receiver.disconnect()
    
    def test_init(self):
        """Test IRReceiver initialization."""
        assert self.receiver.port == "TEST_PORT"
        assert self.receiver.baud_rate == 9600
        assert self.receiver.serial_connection is None
        assert self.receiver.receiving is False
        assert not self.receiver.code_queue.empty() or self.receiver.code_queue.empty()  # Queue exists
        assert self.receiver.receiver_thread is None
        assert self.receiver.codes_received == 0
        assert self.receiver.codes_dropped == 0
    
    def test_set_error_callback(self):
        """Test setting error callback."""
        callback = Mock()
        self.receiver.set_error_callback(callback)
        assert self.receiver.error_callback == callback
    
    def test_log_error_with_callback(self):
        """Test logging error with callback."""
        callback = Mock()
        self.receiver.set_error_callback(callback)
        self.receiver._log_error("Test error")
        callback.assert_called_once_with("[IR Receiver] Test error")
    
    def test_log_error_without_callback(self):
        """Test logging error without callback."""
        with patch('builtins.print') as mock_print:
            self.receiver._log_error("Test error")
            mock_print.assert_called_once_with("[IR Receiver Error] Test error")
    
    @patch('serial.Serial')
    def test_connect_success(self, mock_serial):
        """Test successful connection."""
        mock_connection = MagicMock()
        mock_connection.in_waiting = False
        mock_serial.return_value = mock_connection
        
        result = self.receiver.connect()
        assert result is True
        assert self.receiver.serial_connection == mock_connection
        
        # Verify serial configuration
        mock_serial.assert_called_once_with(
            port="TEST_PORT",
            baudrate=9600,
            timeout=0,
            write_timeout=0,
            inter_byte_timeout=None,
            rtscts=False,
            dsrdtr=False,
        )
    
    @patch('serial.Serial')
    def test_connect_with_ready_signal(self, mock_serial):
        """Test connection with READY signal from Arduino."""
        mock_connection = MagicMock()
        mock_connection.in_waiting = True
        mock_connection.readline.return_value = b"READY\n"
        mock_serial.return_value = mock_connection
        
        result = self.receiver.connect()
        assert result is True
    
    @patch('serial.Serial')
    def test_connect_failure(self, mock_serial):
        """Test connection failure."""
        mock_serial.side_effect = Exception("Connection failed")
        
        result = self.receiver.connect()
        assert result is False
        assert self.receiver.serial_connection is None
    
    def test_process_line_ir_code(self):
        """Test processing IR code line."""
        self.receiver._process_line(b"0x8D722287")
        
        assert self.receiver.codes_received == 1
        assert not self.receiver.code_queue.empty()
        code = self.receiver.code_queue.get_nowait()
        assert code == "0x8D722287"
    
    def test_process_line_repeat(self):
        """Test processing REPEAT signal."""
        self.receiver._process_line(b"REPEAT")
        
        assert self.receiver.codes_received == 1
        assert not self.receiver.code_queue.empty()
        code = self.receiver.code_queue.get_nowait()
        assert code == "REPEAT"
    
    def test_process_line_status_response(self):
        """Test processing status response."""
        self.receiver._process_line(b"OK:8D722287")
        # Should not add to queue or increment counter
        assert self.receiver.codes_received == 0
        assert self.receiver.code_queue.empty()
    
    def test_process_line_ready_signal(self):
        """Test processing READY signal."""
        self.receiver._process_line(b"READY")
        # Should not add to queue or increment counter
        assert self.receiver.codes_received == 0
        assert self.receiver.code_queue.empty()
    
    def test_process_line_reset_signal(self):
        """Test processing RST signal."""
        self.receiver._process_line(b"RST")
        # Should not add to queue or increment counter
        assert self.receiver.codes_received == 0
        assert self.receiver.code_queue.empty()
    
    def test_process_line_invalid_unicode(self):
        """Test processing line with invalid unicode."""
        # Should not raise exception
        self.receiver._process_line(b'\xff\xfe\x00')
        assert self.receiver.codes_received == 0
    
    def test_process_line_queue_full(self):
        """Test processing line when queue is full."""
        # Fill the queue to maxsize
        for i in range(100):  # maxsize is 100
            self.receiver.code_queue.put_nowait(f"0x{i}")
        
        # This should drop the oldest and add the new one
        self.receiver._process_line(b"0xNEW")
        
        assert self.receiver.codes_received == 1
        assert self.receiver.codes_dropped == 1
    
    def test_start_receiving_no_connection(self):
        """Test starting receiver without connection."""
        result = self.receiver.start_receiving()
        assert result is False
    
    @patch('serial.Serial')
    def test_start_receiving_success(self, mock_serial):
        """Test starting receiver successfully."""
        mock_connection = MagicMock()
        mock_serial.return_value = mock_connection
        self.receiver.connect()
        
        result = self.receiver.start_receiving()
        assert result is True
        assert self.receiver.receiving is True
        assert self.receiver.receiver_thread is not None
        assert self.receiver.receiver_thread.is_alive()
        
        # Clean up
        self.receiver.stop_receiving()
    
    @patch('serial.Serial')
    def test_start_receiving_already_receiving(self, mock_serial):
        """Test starting receiver when already receiving."""
        mock_connection = MagicMock()
        mock_serial.return_value = mock_connection
        self.receiver.connect()
        
        # Start once
        result1 = self.receiver.start_receiving()
        assert result1 is True
        
        # Start again
        result2 = self.receiver.start_receiving()
        assert result2 is True
        
        # Clean up
        self.receiver.stop_receiving()
    
    @patch('serial.Serial')
    def test_stop_receiving(self, mock_serial):
        """Test stopping receiver."""
        mock_connection = MagicMock()
        mock_serial.return_value = mock_connection
        self.receiver.connect()
        self.receiver.start_receiving()
        
        # Stop receiving
        self.receiver.stop_receiving()
        assert self.receiver.receiving is False
    
    def test_stop_receiving_not_started(self):
        """Test stopping receiver that wasn't started."""
        # Should not raise exception
        self.receiver.stop_receiving()
        assert self.receiver.receiving is False
    
    def test_get_code_immediate(self):
        """Test getting code immediately."""
        self.receiver.code_queue.put_nowait("0x123")
        code = self.receiver.get_code(timeout=0)
        assert code == "0x123"
    
    def test_get_code_empty_queue(self):
        """Test getting code from empty queue."""
        code = self.receiver.get_code(timeout=0)
        assert code is None
    
    def test_get_code_with_timeout(self):
        """Test getting code with timeout."""
        # This should timeout and return None
        start_time = time.time()
        code = self.receiver.get_code(timeout=0.1)
        elapsed = time.time() - start_time
        
        assert code is None
        assert elapsed >= 0.1
    
    def test_get_statistics(self):
        """Test getting receiver statistics."""
        self.receiver.codes_received = 5
        self.receiver.codes_dropped = 2
        self.receiver.code_queue.put_nowait("0x123")
        
        stats = self.receiver.get_statistics()
        
        assert stats["codes_received"] == 5
        assert stats["codes_dropped"] == 2
        assert stats["queue_size"] == 1
        assert stats["connected"] is False  # Not connected in test
        assert stats["receiving"] is False
    
    @patch('serial.Serial')
    def test_send_command(self, mock_serial):
        """Test sending command to Arduino."""
        mock_connection = MagicMock()
        mock_serial.return_value = mock_connection
        self.receiver.connect()
        
        self.receiver.send_command("S")
        mock_connection.write.assert_called_once_with(b"S")
    
    def test_send_command_not_connected(self):
        """Test sending command when not connected."""
        # Should not raise exception
        self.receiver.send_command("S")
    
    @patch('serial.Serial')
    def test_send_command_exception(self, mock_serial):
        """Test sending command with exception."""
        mock_connection = MagicMock()
        mock_connection.write.side_effect = Exception("Write failed")
        mock_serial.return_value = mock_connection
        self.receiver.connect()
        
        # Should not raise exception
        self.receiver.send_command("S")
    
    def test_is_connected_false(self):
        """Test is_connected when not connected."""
        assert self.receiver.is_connected() is False
    
    @patch('serial.Serial')
    def test_is_connected_true(self, mock_serial):
        """Test is_connected when connected."""
        mock_connection = MagicMock()
        mock_connection.is_open = True
        mock_serial.return_value = mock_connection
        self.receiver.connect()
        
        assert self.receiver.is_connected() is True
    
    @patch('serial.Serial')
    def test_disconnect(self, mock_serial):
        """Test disconnection."""
        mock_connection = MagicMock()
        mock_serial.return_value = mock_connection
        self.receiver.connect()
        self.receiver.start_receiving()
        
        self.receiver.disconnect()
        
        assert self.receiver.receiving is False
        assert self.receiver.serial_connection is None
        mock_connection.close.assert_called_once()
    
    def test_disconnect_not_connected(self):
        """Test disconnection when not connected."""
        # Should not raise exception
        self.receiver.disconnect()
    
    @patch('serial.Serial')
    def test_disconnect_close_exception(self, mock_serial):
        """Test disconnection with close exception."""
        mock_connection = MagicMock()
        mock_connection.close.side_effect = Exception("Close failed")
        mock_serial.return_value = mock_connection
        self.receiver.connect()
        
        # Should not raise exception
        self.receiver.disconnect()
        assert self.receiver.serial_connection is None
    
    @patch('serial.Serial')
    def test_flush_buffer(self, mock_serial):
        """Test buffer flushing."""
        mock_connection = MagicMock()
        mock_serial.return_value = mock_connection
        self.receiver.connect()
        
        # Add some items to queue
        self.receiver.code_queue.put_nowait("0x1")
        self.receiver.code_queue.put_nowait("0x2")
        
        self.receiver.flush_buffer()
        
        assert self.receiver.code_queue.empty()
        mock_connection.reset_input_buffer.assert_called_once()
    
    def test_flush_buffer_not_connected(self):
        """Test buffer flushing when not connected."""
        # Add some items to queue
        self.receiver.code_queue.put_nowait("0x1")
        self.receiver.code_queue.put_nowait("0x2")
        
        self.receiver.flush_buffer()
        
        # Queue should still be cleared
        assert self.receiver.code_queue.empty()
    
    def test_receiver_loop_with_timeout_fixed(self):
        """Test receiver loop doesn't hang."""
        # Mock serial connection
        mock_connection = Mock()
        mock_connection.in_waiting = False
        self.receiver.serial_connection = mock_connection
        
        # Start receiving with a very short timeout
        self.receiver.receiving = True
        
        import threading
        import time
        
        # Start receiver in separate thread with timeout
        thread = threading.Thread(target=self.receiver._receiver_loop, daemon=True)
        thread.start()
        
        # Let it run briefly then stop
        time.sleep(0.1)
        self.receiver.receiving = False
        
        # Wait for thread to finish with timeout
        thread.join(timeout=1.0)
        
        # Thread should have stopped
        assert not thread.is_alive()
    
    @patch('serial.Serial')
    def test_receiver_loop_integration(self, mock_serial):
        """Test receiver loop with mock data."""
        mock_connection = MagicMock()
        mock_connection.in_waiting = True
        mock_connection.read.return_value = b"0x123\n0x456\nREPEAT\n"
        mock_serial.return_value = mock_connection
        
        self.receiver.connect()
        self.receiver.start_receiving()
        
        # Give some time for processing
        time.sleep(0.1)
        
        # Stop and check results
        self.receiver.stop_receiving()
        
        # Should have processed the codes
        assert self.receiver.codes_received >= 2  # At least 0x123 and 0x456


if __name__ == "__main__":
    pytest.main([__file__])