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

import json
import time

from colorama import Back, Fore, Style

from ..core.device_scanner import DeviceScanner


class MenuManager:
    """Manages the interactive menu system."""
    
    def __init__(self, config_manager, device_manager, usb_detector):
        self.config_manager = config_manager
        self.device_manager = device_manager
        self.usb_detector = usb_detector
        self.usb_stick_available = False

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
            return True
        else:
            print(f"{Fore.YELLOW}❌ No ANT+ USB stick found{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}   Connect your ANT+ USB stick to enable device scanning{Style.RESET_ALL}")
            self.usb_stick_available = False
            return False

    def scan_for_devices(self):
        """Scan for ANT+ devices and save to file."""
        print(f"\n{Fore.CYAN}=== ANT+ Device Scanner ==={Style.RESET_ALL}")

        # Check if USB stick is available
        if not self.usb_stick_available:
            print(f"{Fore.RED}Cannot scan for devices: No ANT+ USB stick detected.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please connect your ANT+ USB stick and restart the application.{Style.RESET_ALL}")
            return {}

        config = self.config_manager.config
        network_key = config["ant_network"]["key"]
        scan_timeout = config["app"]["scan_timeout"]
        backend_pref = config.get("app", {}).get("backend", None)

        # Keep scanner output concise unless explicitly debugging
        scanner = DeviceScanner(network_key, scan_timeout, debug=False, backend_preference=backend_pref)

        print("Make sure your ANT+ devices are active and transmitting...")
        print("Starting scan...")

        # Load previously found devices
        devices_file = config["app"]["found_devices_file"]
        found_devices = scanner.load_found_devices(devices_file)

        # Scan for new devices
        new_devices = scanner.scan_for_devices()

        # Merge with existing devices
        found_devices.update(new_devices)

        # Save updated device list
        scanner.save_found_devices(devices_file)

        return found_devices

    def list_found_devices(self):
        """Display list of found devices."""
        devices_file = self.config_manager.config["app"]["found_devices_file"]

        try:
            with open(devices_file, "r") as f:
                devices = json.load(f)
        except FileNotFoundError:
            print(f"{Fore.YELLOW}No found devices file. Run scan first.{Style.RESET_ALL}")
            return
        except Exception as e:
            print(f"{Fore.RED}Error loading found devices: {e}{Style.RESET_ALL}")
            return

        if not devices:
            print(f"{Fore.YELLOW}No devices found in {devices_file}{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}=== Found ANT+ Devices ==={Style.RESET_ALL}")
        print(f"{'ID':<8} {'Type':<6} {'Name':<25} {'Last Seen':<20}")
        print("-" * 70)

        for key, device in devices.items():
            last_seen = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(device["last_seen"]))
            print(f"{device['device_id']:<8} {device['device_type']:<6} " f"{device['device_name']:<25} {last_seen}")

    def show_menu(self):
        """Show the main menu and handle user interactions."""
        while True:
            print(f"\n{Back.BLUE}{Fore.WHITE} ANT+ Device Manager {Style.RESET_ALL}")

            # Show USB stick status
            if self.usb_stick_available:
                print(f"USB Status: {Fore.GREEN}✓ ANT+ USB stick connected{Style.RESET_ALL}")
            else:
                print(f"USB Status: {Fore.YELLOW}❌ No ANT+ USB stick detected{Style.RESET_ALL}")

            print(f"\n{Fore.CYAN}Available options:{Style.RESET_ALL}")

            if self.usb_stick_available:
                print("1. Scan for ANT+ devices")
                print("2. List found devices")
                print("3. Configure devices")
                print("4. Start data display")
            else:
                print(f"1. {Fore.YELLOW}Scan for ANT+ devices (USB stick required){Style.RESET_ALL}")
                print(f"2. {Fore.YELLOW}List found devices{Style.RESET_ALL}")
                print(f"3. {Fore.YELLOW}Configure devices (USB stick required){Style.RESET_ALL}")
                print(f"4. {Fore.YELLOW}Start data display (USB stick required){Style.RESET_ALL}")

            print("5. Show USB setup instructions")
            print("6. Exit")

            try:
                choice = input(f"\n{Fore.YELLOW}Select option (1-6): {Style.RESET_ALL}")

                if choice == "1":
                    if self.usb_stick_available:
                        self.scan_for_devices()
                    else:
                        print(f"{Fore.YELLOW}Please connect an ANT+ USB stick and restart the application.{Style.RESET_ALL}")
                        
                elif choice == "2":
                    self.list_found_devices()
                    
                elif choice == "3":
                    if self.usb_stick_available:
                        self.config_manager.configure_devices_interactive()
                        # Update device manager with new config
                        self.device_manager.config = self.config_manager.config
                    else:
                        print(f"{Fore.YELLOW}Please connect an ANT+ USB stick and restart the application.{Style.RESET_ALL}")
                        
                elif choice == "4":
                    if self.usb_stick_available:
                        self.device_manager.connect_devices()
                        self.device_manager.display_data()
                    else:
                        print(f"{Fore.YELLOW}Please connect an ANT+ USB stick and restart the application.{Style.RESET_ALL}")
                        
                elif choice == "5":
                    self.usb_detector.print_setup_instructions()
                    
                elif choice == "6":
                    print(f"{Fore.GREEN}Goodbye!{Style.RESET_ALL}")
                    break
                    
                else:
                    print(f"{Fore.RED}Invalid option. Please choose 1-6.{Style.RESET_ALL}")

            except KeyboardInterrupt:
                print(f"\n{Fore.GREEN}Goodbye!{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")