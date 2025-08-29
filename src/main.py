"""
Main entry point for the IR Remote Controller application.

This module provides the command-line interface for the IR Remote Controller,
handling profile selection and starting the main controller.
"""

import sys
from main_controller import IRRemoteController

if __name__ == "__main__":
    controller = IRRemoteController()

    if len(sys.argv) > 1:
        profile_name = sys.argv[1]
        if controller.start(profile_name):
            controller.run()
    else:
        profiles = controller.list_available_profiles()
        if profiles:
            print("Available profiles:")
            for i, profile in enumerate(profiles):
                print(f"  {i+1}. {profile}")

            try:
                choice = input("\nSelect profile (number or filename): ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(profiles):
                        profile_name = profiles[idx]
                    else:
                        print("Invalid selection")
                        sys.exit(1)
                else:
                    profile_name = choice

            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit(0)
        else:
            print("No profiles found, will create default")
            profile_name = None

        if controller.start(profile_name):
            controller.run()
