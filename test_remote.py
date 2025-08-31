#!/usr/bin/env python3
"""
Quick test script for IR Remote Controller
"""

import sys
import os
from pathlib import Path

src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from main_controller import IRRemoteController

def main():
    print("=== IR Remote Controller Test ===")
    print("This will test your IR remote setup.")
    print("Make sure your Arduino is connected to COM4.")
    print()
    
    profile_name = "Vizio_Generic_TV_Remote.json"
    controller = IRRemoteController(port="COM4", profile_path=profile_name)

    print(f"Starting with profile: {profile_name}")
    
    if controller.start():
        print("Press remote buttons to test...")
        print("Measuring Time To Execution (TTE)")
        controller.run()
    else:
        print("Failed to start controller")
        
    controller.stop()
    print("Controller stopped.")

if __name__ == "__main__":
    main()