#!/usr/bin/env python3
"""
Debug script to see raw IR codes from Arduino
"""

import serial
import time
import json
from pathlib import Path

def test_raw_serial():
    """Test raw serial communication"""
    print("=== Testing Raw Serial Communication ===")
    print("Connecting to COM4...")
    
    try:
        ser = serial.Serial('COM4', 9600, timeout=0.1)
        time.sleep(2)  # Wait for Arduino reset
        
        print("Connected! Press buttons on your IR remote:")
        print("-" * 40)
        
        received_codes = set()
        
        while True:
            if ser.in_waiting:
                data = ser.readline().decode('utf-8').strip()
                if data:
                    print(f"Received: '{data}' (length: {len(data)})")
                    
                    # Try different format interpretations
                    if data not in received_codes:
                        received_codes.add(data)
                        print(f"  -> New unique code #{len(received_codes)}")
                        
                        # Check if it's hex without 0x prefix
                        if all(c in '0123456789ABCDEFabcdef' for c in data):
                            print(f"  -> As hex with 0x: 0x{data}")
                            print(f"  -> As decimal: {int(data, 16)}")
                    else:
                        print(f"  -> Repeat of previous code")
                    
                    print()
                    
    except serial.SerialException as e:
        print(f"Serial Error: {e}")
    except KeyboardInterrupt:
        print("\n\nStopped by user")
        print(f"\nTotal unique codes received: {len(received_codes)}")
        print("Unique codes:", list(received_codes))

def test_with_profile():
    """Test with profile comparison"""
    print("\n=== Testing with Profile Comparison ===")
    
    # Try to load the profile
    profile_path = Path("config/profiles/Sanyo_NC092.json")  # Adjust path as needed
    
    if not profile_path.exists():
        print(f"Profile not found at {profile_path}")
        print("Available profiles:")
        profiles_dir = Path("profiles")
        if profiles_dir.exists():
            for p in profiles_dir.glob("*.json"):
                print(f"  - {p.name}")
        return
    
    with open(profile_path, 'r') as f:
        profile = json.load(f)
    
    print(f"Loaded profile: {profile['name']}")
    print(f"Profile has {len(profile['mappings'])} mappings")
    print("Sample codes from profile:")
    for code in list(profile['mappings'].keys())[:5]:
        print(f"  - {code}")
    
    print("\nNow testing serial...")
    try:
        ser = serial.Serial('COM4', 9600, timeout=0.1)
        time.sleep(2)
        
        print("Press buttons on your remote to compare with profile:")
        print("-" * 40)
        
        while True:
            if ser.in_waiting:
                data = ser.readline().decode('utf-8').strip()
                if data:
                    print(f"Received: '{data}'")
                    
                    # Try different formats
                    variations = [
                        data,                    # As-is
                        f"0x{data}",            # Add 0x prefix
                        f"0x{data.upper()}",    # Add 0x and uppercase
                        data.upper(),           # Just uppercase
                        hex(int(data, 16)) if all(c in '0123456789ABCDEFabcdef' for c in data) else None
                    ]
                    
                    found = False
                    for var in variations:
                        if var and var in profile['mappings']:
                            print(f"  ✓ MATCH FOUND: {var}")
                            print(f"    Action: {profile['mappings'][var]['description']}")
                            print(f"    Type: {profile['mappings'][var]['action_type']}")
                            print(f"    Keys: {profile['mappings'][var]['keys']}")
                            found = True
                            break
                    
                    if not found:
                        print(f"  ✗ No match in profile")
                        print(f"    Tried: {[v for v in variations if v]}")
                    
                    print()
                    
    except Exception as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\nStopped by user")

def main():
    print("IR Remote Debug Tool")
    print("=" * 40)
    print("1. Test raw serial communication")
    print("2. Test with profile comparison")
    print()
    
    choice = input("Choose test mode (1 or 2): ").strip()
    
    if choice == "1":
        test_raw_serial()
    elif choice == "2":
        test_with_profile()
    else:
        print("Invalid choice, running raw serial test...")
        test_raw_serial()

if __name__ == "__main__":
    main()