import serial
import pyautogui
import time
from ir_codes import *
# Open the serial port
ser = serial.Serial('COM5', 9600)

# ========================================
# 🛠 Key Bindings: Customize Your Mappings
# ========================================
# Format: 'IR_CODE': ('action_type', key(s))
# - 'single'   → one key press
# - 'combo'    → multiple keys held (e.g., ['ctrl', 'f4'])
# - 'sequence' → series of individual presses (e.g., ['a', 'b', 'c'])
ir_to_action = {
    INPUT: ('combo', ['ctrl', 'a']),     
    POWER:  ('combo', ['shift', 'ctrl', 'a']),             
    AMAZON: ('sequence', ['win', 'a']),    
    NETFLIX: ('single', 'n'),               
    IHEART: ('single', 'i'),               
    REWIND: ('single', 'left'),            
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
    VOLUME_UP:  ('single', 'volumeup'),        
    VOLUME_DOWN:  ('single', 'volumedown'),      
    HOME: ('single', 'home'),            
    CHANNEL_UP:  ('single', 'pageup'),          
    CHANNEL_DOWN:  ('single', 'pagedown'),        
    MUTE:  ('single', 'f'),               
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

# ========================================
# 🕒 Cooldown (Debounce) Per IR Code
# Keys here will NOT trigger more than once per X seconds
# ========================================
cooldown_keys = {
    POWER:  0.15,   
    PLAY: 0.15,   
    PAUSE: 0.15,   
    SELECT: 0.15,   
    INPUT: 0.15,   
    AMAZON: 0.15,   
    NETFLIX: 0.15,   
    CC: 0.15,   
    RECORD: 0.15,    
    MUTE: 0.15,
    LEFT: 0.15,
    RIGHT: 0.15,
}

# Track last press time per code
last_pressed = {}

# ========================================
# 🔄 Action Handler
# ========================================
def handle_action(action_type, keys):
    if action_type == 'single':
        pyautogui.press(keys)
    elif action_type == 'sequence':
        for key in keys:
            pyautogui.press(key)
            time.sleep(0.1)
    elif action_type == 'combo':
        pyautogui.hotkey(*keys)
    else:
        print(f"⚠️ Unknown action type: {action_type}")

# ========================================
# ▶️ Main Loop
# ========================================
print("🎮 IR Remote Control Running... (Ctrl+C to exit)")

try:
    while True:
        ir_code = ser.readline().decode('utf-8').strip().upper()
        now = time.time()

        if ir_code:
            print(f"🔹 Received IR code: {ir_code}")

            # Debounce logic
            if ir_code in cooldown_keys:
                cooldown = cooldown_keys[ir_code]
                last_time = last_pressed.get(ir_code, 0)
                if now - last_time < cooldown:
                    print(f"⏳ Cooldown active for {ir_code} ({cooldown:.1f}s)")
                    continue
                last_pressed[ir_code] = now

            # Handle mapped actions
            if ir_code in ir_to_action:
                action_type, keys = ir_to_action[ir_code]
                handle_action(action_type, keys)
            else:
                print(f"❌ Unmapped IR code: {ir_code}")

except KeyboardInterrupt:
    print("\n🛑 Exiting program.")
    ser.close()