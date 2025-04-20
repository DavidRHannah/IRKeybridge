import serial
import keyboard
import time
from ir_codes import *

class IRRemoteController:
    def __init__(self):
        self.ser = serial.Serial('COM5', 9600)
        self.last_pressed = {}
        self.held_keys = {}
        self.running = True
        self.action_log = []
        self.ACTION_LOG_LIMIT = 20

        # Ghost key configuration
        self.GHOST_KEY = 'f10'  # A key most games don't use
        self.GHOST_DELAY = 0.2 # Very short press duration

        self.KEY_RELEASE_TIMEOUT = 0.2

        # Key bindings configuration
        self.ir_to_action = {
            INPUT: ('combo', ['ctrl', 'a']),
            POWER: ('combo', ['shift', 'a']),
            AMAZON: ('sequence', ['windows', 'a']),
            NETFLIX: ('single', 'n'),
            IHEART: ('single', 'i'),
            REWIND: ('single', 'backspace'),
            PAUSE: ('single', 'space'),
            PLAY: ('single', 'space'),
            FAST_FORWARD: ('single', 'right'),
            CC: ('single', 'c'),
            RECORD: ('single', 'r'),
            STOP: ('single', 's'),
            MENU: ('single', 'esc'),
            UP: ('single', 'up'),
            DOWN: ('single', 'down'),
            LEFT: ('single', 'left'),
            RIGHT: ('single', 'right'),
            SELECT: ('single', 'enter'),
            VOLUME_UP: ('single', 'volume up'),
            VOLUME_DOWN: ('single', 'volume down'),
            HOME: ('single', 'home'),
            CHANNEL_UP: ('single', 'page up'),
            CHANNEL_DOWN: ('single', 'page down'),
            MUTE: ('single', 'f'),
            DISPLAY: ('single', 'd'),
            PIC: ('single', 'p'),
            REVERT: ('single', 'b'),
            NUM_1: ('single', '1'),
            NUM_2: ('single', '2'),
            NUM_3: ('single', '3'),
            NUM_4: ('single', '4'),
            NUM_5: ('single', '5'),
            NUM_6: ('single', '6'),
            NUM_7: ('single', '7'),
            NUM_8: ('single', '8'),
            NUM_9: ('single', '9'),
            ENTER_BTN: ('single', 'enter'),
            NUM_0: ('single', '0'),
            BAR: ('single', '.')  
        }
        
    def _press_ghost_key(self):
        """Quickly press and release a neutral key"""
        keyboard.press(self.GHOST_KEY)
        time.sleep(self.GHOST_DELAY)
        keyboard.release(self.GHOST_KEY)

    def handle_action(self, action_type, keys):
        """Handle actions with verification logging"""
        action_str = f"{action_type.upper()}: {keys}"
        timestamp = time.strftime("%H:%M:%S")

        try:
            if action_type == 'single':
                if isinstance(keys, list):
                    for key in keys:
                        keyboard.press_and_release(key)
                        self._log_action(f"{timestamp} | {key} (single)")
                else:
                    keyboard.press_and_release(keys)
                    self._log_action(f"{timestamp} | {keys} (single)")

                self._press_ghost_key()

            elif action_type == 'sequence':
                for key in keys:
                    keyboard.press_and_release(key)
                    self._log_action(f"{timestamp} | {keys} (sequence)")
                    time.sleep(self.SEQUENCE_DELAY)
                self._press_ghost_key()

            elif action_type == 'combo':
                combo_str = '+'.join(keys)
                keyboard.send(combo_str)
                self._log_action(f"{timestamp} | {combo_str} (combo)")
                self._press_ghost_key()

            else:
                print(f"⚠️ Unknown action type: {action_type}")

            print(f"✅ Executed: {action_str}")
            return True
        
        except Exception as e:
            error_msg = f"⚠️ Failed {action_str} - {str(e)}"
            self._log_action(f"{timestamp} | ERROR: {error_msg}")
            print(error_msg)
            return False

    def _log_action(self, message):
        """Maintain an action log"""
        self.action_log.append(message)
        if len(self.action_log) > self.ACTION_LOG_LIMIT:
            self.action_log.pop(0)
        self.last_action_time = time.time()

    def get_recent_actions(self):
        """Return formatted action log"""
        return "\n".join(self.action_log[-5:]) if self.action_log else "No actions yet"

    def process_ir_code(self, ir_code):
        """Process a single IR code"""
        if not self.running:
            return
        if not ir_code:
            return
        now = time.time()

        print(f"🔹 Received IR code: {ir_code}")

        if ir_code == STOP:
            print("🛑 STOP button pressed - initiating shutdown...")
            self.running = False
            return
        
        if ir_code in self.ir_to_action:
            action_type, keys = self.ir_to_action[ir_code]
            self.handle_action(action_type, keys)
            self.last_pressed[ir_code] = now

        time.sleep(0.2)

    def release_inactive_keys(self):
        """Release keys that haven't been pressed recently"""
        now = time.time()
        for code in list(self.held_keys):
            last_time = self.last_pressed.get(code, 0)
            if now - last_time > self.KEY_RELEASE_TIMEOUT:
                keys = self.held_keys.pop(code)
                if isinstance(keys, list):
                    for key in keys:
                        keyboard.release(key)
                else:
                    keyboard.release(keys)

    def is_valid_ir_code(self, code):
        """Validate the IR code format"""
        return isinstance(code, str) and code.isalnum() and len(code) <= 10

    def get_ir_code(self):
        """Safely read from serial port"""
        try:
            line = self.ser.readline()
            return line.decode('utf-8').strip().upper()
        except UnicodeDecodeError:
            return None
        except serial.SerialException as e:
            print(f"Serial port error: {e}")
            return None

    def run(self):
        """Main execution loop with better error handling"""
        print("🎮 IR Remote Game Control Running... (Press Ctrl+C to stop)")
        
        try:
            while self.running:
                ir_code = self.get_ir_code()
                if ir_code and self.is_valid_ir_code(ir_code):
                    self.process_ir_code(ir_code)
                self.release_inactive_keys()
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n🛑 Exiting program.")
        except Exception as e:
            print(f"\n⚠️ Critical error occurred: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
            time.sleep(0.5)

    def cleanup(self):
        """Comprehensive cleanup of all resources"""
        print("\n🔌 Performing cleanup...")
        
        # Release all held keys
        if hasattr(self, 'held_keys'):
            for code, keys in self.held_keys.items():
                try:
                    if isinstance(keys, list):
                        for key in keys:
                            keyboard.release(key)
                    else:
                        keyboard.release(keys)
                    print(f"  ⌨️ Released keys for code: {code}")
                except Exception as e:
                    print(f"  ⚠️ Error releasing keys for {code}: {e}")
            self.held_keys.clear()
        
        # Close serial port
        if hasattr(self, 'ser') and self.ser and self.ser.is_open:
            try:
                self.ser.close()
                print("  🔌 Serial port closed")
            except Exception as e:
                print(f"  ⚠️ Error closing serial port: {e}")
        
        # Reset keyboard state (just in case)
        try:
            keyboard.unhook_all()
            print("  ⌨️ Keyboard hooks reset")
        except Exception as e:
            print(f"  ⚠️ Error resetting keyboard: {e}")
        
        # Clear any remaining state
        if hasattr(self, 'last_pressed'):
            self.last_pressed.clear()
        
        print("✅ Cleanup complete")
        return

if __name__ == "__main__":
    controller = IRRemoteController()
    controller.run()
    print("🪓 Terminating Process")