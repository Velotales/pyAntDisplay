#!/usr/bin/env python3
"""
PyANTDisplay - Main Application

Copyright (c) 2025 Velotales

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Main entry point for the ANT+ Device Data Display application.
Coordinates the menu system, configuration, and device management.
"""

import colorama
from colorama import Fore, Style

from .config_manager import ConfigManager
from .device_manager import DeviceManager
from .menu_manager import MenuManager
from .usb_detector import ANTUSBDetector

colorama.init()


def main():
    """Main application entry point."""
    try:
        # Initialize components
        config_manager = ConfigManager()
        device_manager = DeviceManager(config_manager.config)
        usb_detector = ANTUSBDetector()
        menu_manager = MenuManager(config_manager, device_manager, usb_detector)

        # Check for USB stick on startup
        menu_manager.check_usb_on_startup()

        # Show interactive menu
        menu_manager.show_menu()
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Application interrupted{Style.RESET_ALL}")
    finally:
        # Cleanup
        if 'device_manager' in locals():
            device_manager.stop()


if __name__ == "__main__":
    main()
