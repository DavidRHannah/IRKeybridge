#!/usr/bin/env python3
"""
Quick test script for IR Remote Controller
"""

import sys
import os
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from main_controller import IRRemoteController

def main():
    print("=== IR Remote Controller Test ===")
    print("This will test your IR remote setup.")
    print("Make sure your Arduino is connected to COM4.")
    print()
    
    controller = IRRemoteController()
    
    profiles = controller.list_available_profiles()
    print(f"Available profiles: {profiles}")
    
    profile_name = "Sanyo_NC092.json"
    print(f"Starting with profile: {profile_name}")
    
    if controller.start(profile_name):
        print("Controller started successfully!")
        print("Connected to Arduino on COM4")
        print("Profile loaded with IR code mappings")
        print()
        print("TEST YOUR REMOTE NOW:")
        print("  - Press any button on your IR remote")
        print("  - You should see the action being executed")
        print("  - Press the 'Function/Stop' button to exit")
        print("  - Or press Ctrl+C to stop")
        print()
        
        try:
            controller.run()
        except KeyboardInterrupt:
            print("\n  Stopped by user")
    else:
        print("Failed to start controller")
        print("Check:")
        print("  1. Arduino is connected to COM4")
        print("  2. Arduino is running the IR receiver firmware")
        print("  3. No other programs are using COM4")
        
    controller.stop()
    print("Controller stopped.")

if __name__ == "__main__":
    main()