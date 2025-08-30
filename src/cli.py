"""
Command-line interface for the IR Remote Controller application.

This module provides a comprehensive CLI for managing IR remote configurations,
profiles, and running the controller with various options.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional
import json

from main_controller import IRRemoteController
from config_manager import ConfigManager


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.

    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        prog="ir-remote",
        description="IR Remote Controller - Control your computer with any IR remote",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ir-remote                          # Interactive profile selection
  ir-remote --profile vizio.json     # Run with specific profile
  ir-remote --list-profiles          # List available profiles
  ir-remote --create-default         # Create default Vizio profile
  ir-remote --gui                    # Launch GUI configuration tool
  ir-remote --status                 # Show controller status
        """,
    )

    # Main operation modes
    parser.add_argument(
        "--profile", "-p", type=str, help="Profile file to use (e.g., vizio.json)"
    )

    parser.add_argument(
        "--list-profiles", "-l", action="store_true", help="List all available profiles"
    )

    parser.add_argument(
        "--create-default", action="store_true", help="Create default Vizio profile"
    )

    parser.add_argument(
        "--gui", "-g", action="store_true", help="Launch GUI configuration tool"
    )

    parser.add_argument(
        "--status", "-s", action="store_true", help="Show controller status"
    )

    # Configuration options
    parser.add_argument(
        "--port", type=str, help="Serial port (e.g., COM5, /dev/ttyUSB0)"
    )

    parser.add_argument(
        "--baud-rate", type=int, default=9600, help="Serial baud rate (default: 9600)"
    )

    parser.add_argument(
        "--ghost-key", type=str, help="Ghost key for maintaining focus (default: f10)"
    )

    parser.add_argument(
        "--enable-ghost", action="store_true", help="Enable ghost key mode"
    )

    parser.add_argument(
        "--enable-tap", action="store_true", help="Enable single tap mode"
    )

    # Debugging and verbosity
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    parser.add_argument(
        "--version", action="version", version="IR Remote Controller 1.0.0"
    )

    return parser


def list_profiles(config_manager: ConfigManager) -> None:
    """
    List all available profiles.

    Args:
        config_manager (ConfigManager): Configuration manager instance
    """
    profiles = config_manager.list_profiles()

    if not profiles:
        print("No profiles found.")
        print("Use --create-default to create a default Vizio profile.")
        return

    print("Available profiles:")
    for i, profile in enumerate(profiles, 1):
        print(f"  {i}. {profile}")

        # Try to load and show profile details
        try:
            profile_obj = config_manager.load_profile(profile)
            if profile_obj:
                print(f"     Brand: {profile_obj.brand}, Model: {profile_obj.model}")
                print(f"     Mappings: {len(profile_obj.mappings)} buttons")
        except Exception:
            print("     (Unable to load profile details)")
        print()


def create_default_profile(config_manager: ConfigManager) -> bool:
    """
    Create and save the default Vizio profile.

    Args:
        config_manager (ConfigManager): Configuration manager instance

    Returns:
        bool: True if profile created successfully
    """
    try:
        profile = config_manager.create_default_vizio_profile()
        if config_manager.save_profile(profile):
            print(f"Created default profile: {profile.name}")
            print(f"Brand: {profile.brand}, Model: {profile.model}")
            print(f"Mappings: {len(profile.mappings)} buttons")
            return True
        else:
            print("Error: Failed to save default profile")
            return False
    except Exception as e:
        print(f"Error creating default profile: {e}")
        return False


def show_status(controller: IRRemoteController) -> None:
    """
    Show controller status information.

    Args:
        controller (IRRemoteController): Controller instance
    """
    status = controller.get_status()

    print("IR Remote Controller Status:")
    print(f"  Running: {'Yes' if status['running'] else 'No'}")
    print(f"  Connected: {'Yes' if status['connected'] else 'No'}")
    print(f"  Active Profile: {status['profile'] or 'None'}")
    print(f"  Ghost Key Enabled: {'Yes' if status['ghost_key_enabled'] else 'No'}")
    print(f"  Single Tap Enabled: {'Yes' if status['single_tap_enabled'] else 'No'}")

    # Show configuration
    config = controller.config_manager.get_setting
    print(f"\nConfiguration:")
    print(f"  Serial Port: {config('serial_port', 'Not set')}")
    print(f"  Baud Rate: {config('baud_rate', 'Not set')}")
    print(f"  Ghost Key: {config('ghost_key', 'Not set')}")
    print(f"  Repeat Threshold: {config('repeat_threshold', 'Not set')}s")


def interactive_profile_selection(controller: IRRemoteController) -> Optional[str]:
    """
    Interactive profile selection menu.

    Args:
        controller (IRRemoteController): Controller instance

    Returns:
        Optional[str]: Selected profile name or None
    """
    profiles = controller.list_available_profiles()

    if not profiles:
        print("No profiles found.")
        create = input("Create default Vizio profile? (y/N): ").strip().lower()
        if create in ["y", "yes"]:
            if controller.create_default_profile():
                profiles = controller.list_available_profiles()
            else:
                return None
        else:
            return None

    if not profiles:
        return None

    print("\nAvailable profiles:")
    for i, profile in enumerate(profiles, 1):
        print(f"  {i}. {profile}")

    while True:
        try:
            choice = input(
                f"\nSelect profile (1-{len(profiles)}) or filename: "
            ).strip()

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(profiles):
                    return profiles[idx]
                else:
                    print(f"Invalid selection. Please choose 1-{len(profiles)}")
            else:
                if choice in profiles:
                    return choice
                elif choice.endswith(".json") and choice in profiles:
                    return choice
                else:
                    print(f"Profile '{choice}' not found")

        except KeyboardInterrupt:
            print("\nCancelled.")
            return None
        except EOFError:
            return None


def launch_gui() -> None:
    """Launch the GUI configuration tool."""
    try:
        from gui import main as gui_main

        print("Launching GUI configuration tool...")
        gui_main()
    except ImportError as e:
        print("Error: GUI dependencies not available")
        print("Please install PyQt5: pip install PyQt5")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching GUI: {e}")
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle GUI launch first
    if args.gui:
        launch_gui()
        return

    # Create controller
    controller = IRRemoteController()

    # Apply configuration overrides
    if args.port:
        controller.config_manager.set_setting("serial_port", args.port)

    if args.baud_rate != 9600:
        controller.config_manager.set_setting("baud_rate", args.baud_rate)

    if args.ghost_key:
        controller.config_manager.set_setting("ghost_key", args.ghost_key)

    # Handle different operation modes
    if args.list_profiles:
        list_profiles(controller.config_manager)
        return

    if args.create_default:
        create_default_profile(controller.config_manager)
        return

    if args.status:
        show_status(controller)
        return

    # Determine profile to use
    profile_name = None
    if args.profile:
        profile_name = args.profile
    else:
        profile_name = interactive_profile_selection(controller)

    if not profile_name:
        print("No profile selected. Exiting.")
        sys.exit(1)

    # Configure mapper options
    if args.enable_ghost:
        controller.mapper.ghost_key_enabled = True
        print("Ghost key mode enabled")

    if args.enable_tap:
        controller.mapper.single_tapping_enabled = True
        print("Single tap mode enabled")

    # Start the controller
    print(f"Starting IR Remote Controller with profile: {profile_name}")

    if not controller.start(profile_name):
        print("Failed to start controller")
        sys.exit(1)

    try:
        print("Controller started successfully!")
        print("Press Ctrl+C to stop, or use the STOP button on your remote")
        controller.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        controller.stop()
        print("Controller stopped.")


if __name__ == "__main__":
    main()
