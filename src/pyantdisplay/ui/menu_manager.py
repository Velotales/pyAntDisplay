#!/usr/bin/env python3
"""
PyANTDisplay - Menu Manager

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

Manages the interactive menu system and device scanning.
"""

import time

from colorama import Back, Fore, Style

from ..services.device_scan import DeviceScanService
from ..services.device_list import DeviceListService
from ..ui.data_display import DataDisplayService


class MenuManager:
    """Manages the interactive menu system."""

    def __init__(self, config_manager, device_manager, usb_detector):
        self.config_manager = config_manager
        self.device_manager = device_manager
        self.usb_detector = usb_detector
        self.usb_stick_available = False

        # Initialize services
        self._scan_service = None
        self._list_service = None
        self._display_service = None

    def check_usb_on_startup(self) -> bool:
        """Check for ANT+ USB stick on application startup."""
        print(f"{Fore.CYAN}ANT+ Device Data Display{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Checking for ANT+ USB stick...{Style.RESET_ALL}")

        # Check USB permissions first
        if not self.usb_detector.check_usb_permissions():
            print(f"{Fore.RED}❌ USB permission error{Style.RESET_ALL}")
            return False

        # Detect ANT+ devices
        devices = self.usb_detector.detect_ant_sticks()

        if devices:
            print(f"{Fore.GREEN}✓ ANT+ USB stick detected and ready!{Style.RESET_ALL}")
            for device in devices:
                print(f"  📡 {device['name']}")
            self.usb_stick_available = True
            self._initialize_services()
            return True
        else:
            print(f"{Fore.YELLOW}❌ No ANT+ USB stick found{Style.RESET_ALL}")
            print(
                f"{Fore.YELLOW}   Connect your ANT+ USB stick to enable device scanning{Style.RESET_ALL}"
            )
            self.usb_stick_available = False
            return False

    def _initialize_services(self):
        """Initialize services when USB stick is available."""
        config = self.config_manager.config
        self._scan_service = DeviceScanService(config)
        self._list_service = DeviceListService(config)

    def _handle_device_scan(self):
        """Handle device scanning menu option."""
        if not self.usb_stick_available:
            print(
                f"{Fore.RED}Cannot scan for devices: No ANT+ USB stick detected.{Style.RESET_ALL}"
            )
            print(
                f"{Fore.YELLOW}Please connect your ANT+ USB stick and restart the application.{Style.RESET_ALL}"
            )
            return

        self._scan_service.scan_for_devices()

    def _handle_list_devices(self):
        """Handle list devices menu option."""
        if not self._list_service:
            self._list_service = DeviceListService(self.config_manager.config)
        self._list_service.list_found_devices()

    def _handle_configure_devices(self):
        """Handle configure devices menu option."""
        if not self.usb_stick_available:
            print(
                f"{Fore.YELLOW}Please connect an ANT+ USB stick and restart the application.{Style.RESET_ALL}"
            )
            return

        self.config_manager.configure_devices_interactive()
        # Update device manager with new config
        self.device_manager.config = self.config_manager.config

    def _handle_start_display(self):
        """Handle start data display menu option."""
        if not self.usb_stick_available:
            print(
                f"{Fore.YELLOW}Please connect an ANT+ USB stick and restart the application.{Style.RESET_ALL}"
            )
            return

        self.device_manager.connect_devices()
        if self.device_manager.has_connected_devices():
            if not self._display_service:
                self._display_service = DataDisplayService(
                    self.device_manager, self.device_manager.config
                )
            self._display_service.display_data()
        else:
            print(
                f"{Fore.YELLOW}No ANT+ devices connected. Connect devices first using scan/configure options.{Style.RESET_ALL}"
            )

    def show_menu(self):
        """Show the main menu and handle user interactions."""
        while True:
            print(f"\n{Back.BLUE}{Fore.WHITE} ANT+ Device Manager {Style.RESET_ALL}")

            # Show USB stick status
            if self.usb_stick_available:
                print(
                    f"USB Status: {Fore.GREEN}✓ ANT+ USB stick connected{Style.RESET_ALL}"
                )
            else:
                print(
                    f"USB Status: {Fore.YELLOW}❌ No ANT+ USB stick detected{Style.RESET_ALL}"
                )

            print(f"\n{Fore.CYAN}Available options:{Style.RESET_ALL}")

            if self.usb_stick_available:
                print("1. Scan for ANT+ devices")
                print("2. List found devices")
                print("3. Configure devices")
                print("4. Start data display")
            else:
                print(
                    f"1. {Fore.YELLOW}Scan for ANT+ devices (USB stick required){Style.RESET_ALL}"
                )
                print(f"2. {Fore.YELLOW}List found devices{Style.RESET_ALL}")
                print(
                    f"3. {Fore.YELLOW}Configure devices (USB stick required){Style.RESET_ALL}"
                )
                print(
                    f"4. {Fore.YELLOW}Start data display (USB stick required){Style.RESET_ALL}"
                )

            print("5. Show USB setup instructions")
            print("6. Exit")

            try:
                choice = input(f"\n{Fore.YELLOW}Select option (1-6): {Style.RESET_ALL}")

                if choice == "1":
                    if self.usb_stick_available:
                        self._handle_device_scan()
                    else:
                        print(
                            f"{Fore.YELLOW}Please connect an ANT+ USB stick and restart the application.{Style.RESET_ALL}"
                        )

                elif choice == "2":
                    self._handle_list_devices()

                elif choice == "3":
                    self._handle_configure_devices()

                elif choice == "4":
                    self._handle_start_display()

                elif choice == "5":
                    self.usb_detector.print_setup_instructions()

                elif choice == "6":
                    print(f"{Fore.GREEN}Goodbye!{Style.RESET_ALL}")
                    break

                else:
                    print(
                        f"{Fore.RED}Invalid option. Please choose 1-6.{Style.RESET_ALL}"
                    )

            except KeyboardInterrupt:
                print(f"\n{Fore.GREEN}Goodbye!{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
