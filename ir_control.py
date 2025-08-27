import serial
import keyboard
import time
from collections import defaultdict

# Constants for IR codes
POWER        = '8'
INPUT        = '2F'
AMAZON       = 'EA'
NETFLIX      = 'EB'
IHEART       = 'EE'
REWIND       = '35'
PAUSE        = '37'
PLAY         = '33'
FAST_FORWARD = '36'
CC           = '39'
RECORD       = '34'
STOP         = '30'
MENU         = '4F'
TOP_LEFT     = '49'
TOP_RIGHT    = '1B'
BOTTOM_LEFT  = '4A'
RIGHT_LEFT   = '1C'
UP           = '45'
DOWN         = '46'
LEFT         = '47'
RIGHT        = '48'
SELECT       = '44'
VOLUME_UP    = '2'
VOLUME_DOWN  = '3'
HOME         = '2D'
CHANNEL_UP   = '0'
CHANNEL_DOWN = '1'
MUTE         = '9'
DISPLAY      = '77'
PIC          = '67'
REVERT       = '1A'
NUM_1        = '11'
NUM_2        = '12'
NUM_3        = '13'
NUM_4        = '14'
NUM_5        = '15'
NUM_6        = '16'
NUM_7        = '17'
NUM_8        = '18'
NUM_9        = '19'
NUM_0        = '10'
ENTER_BTN    = '3A'
BAR          = 'FF'

class IRRemoteController:
    def __init__(self):
        self.ser = serial.Serial('COM5', 9600, timeout=0.1)
        self.running = True
        self.ghost_key = 'f10'
        self.ghost_delay = 0.2
        self.ghost_key_enabled = False
        self.single_tapping_enabled = False
        
        # Track currently pressed keys and their state
        self.currently_pressed = defaultdict(bool)
        self.last_received_code = None
        self.last_code_time = 0
        self.repeat_threshold = 0.2  # Time before considering a held button
        
        # Key bindings configuration
        self.ir_to_action = {
            INPUT: ('combo', ['ctrl','a']),
            POWER: ('combo', ['ctrl','a']),
            AMAZON: ('sequence', ['windows', 'a']),
            NETFLIX: ('combo', 'n'),
            IHEART: ('combo', 'i'),
            REWIND: ('combo', ['ctrl','backspace']),
            PAUSE: ('combo', ['ctrl','a']),
            PLAY: ('combo', ['ctrl','a']),
            FAST_FORWARD: ('combo', ['ctrl','a']),
            CC: ('combo', ['ctrl','a']),
            RECORD: ('combo', ['ctrl','a']),
            STOP: ('combo', ['ctrl','a']),
            MENU: ('combo', ['ctrl','a']),
            TOP_LEFT: ('combo', ['ctrl','a']),
            TOP_RIGHT: ('combo', ['ctrl','a']),
            BOTTOM_LEFT: ('combo', ['ctrl','a']),
            RIGHT_LEFT: ('combo', ['ctrl','a']),
            UP: ('combo', ['ctrl','up']),
            DOWN: ('combo', ['ctrl','down']),
            LEFT: ('combo', ['ctrl','left']),
            RIGHT: ('combo', ['ctrl','right']),
            SELECT: ('combo', ['ctrl','enter']),
            VOLUME_UP: ('combo', 'volume up'),
            VOLUME_DOWN: ('combo', 'volume down'),
            HOME: ('combo', ['ctrl','home']),
            CHANNEL_UP: ('combo', ['ctrl','page up']),
            CHANNEL_DOWN: ('combo', ['ctrl', 'page down']),
            MUTE: ('combo', ['ctrl','f']),
            DISPLAY: ('combo', ['ctrl','a']),
            PIC: ('combo', ['ctrl','a']),
            REVERT: ('special', 'toggle_tap'),
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
            BAR: ('special', 'toggle_ghost')  
        }

    def _ghost_press(self):
        """Quick neutral key press"""
        if self.ghost_key_enabled:
            try:
                keyboard.press(self.ghost_key)
                time.sleep(self.ghost_delay)
                keyboard.release(self.ghost_key)
            except:
                pass
    
    def toggle_ghost_key(self):
        """Toggle ghost key functionality"""
        self.ghost_key_enabled = not self.ghost_key_enabled
        status = "ENABLED" if self.ghost_key_enabled else "DISABLED"
        print(f"Ghost key {status}")
    
    def toggle_tap(self):
        """Toggle single tap functionality"""
        self.single_tapping_enabled = not self.single_tapping_enabled
        status = "ENABLED" if self.single_tapping_enabled else "DISABLED"
        print(f"Single tapping {status}")

    def _release_all_keys(self):
        """Release any currently pressed keys"""
        for key in list(self.currently_pressed.keys()):
            if self.currently_pressed[key]:
                keyboard.release(key)
                self.currently_pressed[key] = False

    def handle_key(self, action_type, keys):
        """Handle key press based on current state"""
        current_time = time.time()
        
        # Special case for ghost key toggle
        if action_type == 'special' and keys == 'toggle_ghost':
            self.toggle_ghost_key()
            return
        
        if action_type == 'special' and keys == 'toggle_tap':
            self.toggle_tap()
            return

        # Check if this is a new button press
        is_new_press = (self.last_received_code is None or 
                       (current_time - self.last_code_time) > self.repeat_threshold)
        
        try:
            if action_type == 'combo':
                if self.single_tapping_enabled:
                    for key in keys:
                        keyboard.press(key)
                        time.sleep(0.01)
                    time.sleep(0.05)
                    for key in keys:
                        keyboard.release(keys)
                        time.sleep(0.01)
                    return
                if is_new_press:
                    self._release_all_keys()
                    for key in keys:
                        keyboard.press(key)
                        self.currently_pressed[key] = True
                # Keep combo keys pressed until new command
                
            elif action_type == 'sequence':
                if is_new_press:
                    self._release_all_keys()
                    for key in keys:
                        keyboard.press(key)
                        time.sleep(0.1)
                        keyboard.release(key)
                        time.sleep(0.1)
                
            elif action_type == 'single':
                if self.single_tapping_enabled:
                  self._release_all_keys()
                  keyboard.press(keys)
                  time.sleep(0.05)
                  keyboard.release(keys)
                  return

                if is_new_press:
                    # If this key wasn't already pressed
                    if not self.currently_pressed.get(keys, False):
                        self._release_all_keys()
                        keyboard.press(keys)
                        self.currently_pressed[keys] = True
                    # If it was pressed, we keep it pressed
                # Keep single key pressed until new command
            
            if is_new_press:
                self._ghost_press()
                
        except Exception as e:
            print(f"Key press error: {e}")

    def process_code(self, ir_code):
        """Process IR code with button holding support"""
        if not self.running or not ir_code:
            return
            
        if ir_code == STOP:
            self.running = False
            self._release_all_keys()
            return
            
        if ir_code in self.ir_to_action:
            current_time = time.time()
            
            # Check if this is a repeat of the last code (button held down)
            if ir_code == self.last_received_code:
                time_since_last = current_time - self.last_code_time
                if time_since_last < 0.1:  # Very rapid repeats are probably noise
                    return
            else:
                # New button pressed - process it
                action = self.ir_to_action[ir_code]
                print(f"Action: {ir_code} -> {action}")
                self.handle_key(action[0], action[1])
            
            self.last_received_code = ir_code
            self.last_code_time = current_time

    def run(self):
        """Main loop with proper cleanup"""
        print("Controller ready (Press STOP to exit)")
        print(f"Initial ghost key state: {'ENABLED' if self.ghost_key_enabled else 'DISABLED'}")
        print(f"Initial single tap state: {'ENABLED' if self.single_tapping_enabled else 'DISABLED'}")

        try:
            while self.running:
                try:
                    line = self.ser.readline()
                    if line:
                        code = line.decode('utf-8').strip().upper()
                        if code:
                            self.process_code(code)
                    else:
                        # If no code received for a while, release keys
                        if (time.time() - self.last_code_time) > 0.01:
                            self._release_all_keys()
                            self.last_received_code = None
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"Serial error: {e}")
                    time.sleep(1)
                
                time.sleep(0.01)
        finally:
            self._release_all_keys()
            self.ser.close()
            print("Controller stopped")

if __name__ == "__main__":
    IRRemoteController().run()