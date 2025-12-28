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

ANT+ Device Data Display
Main application that reads from heart rate monitor and bike sensor,
with device configuration and scanning capabilities.
"""

import json
import os
import sys
import time

import colorama
import yaml
from colorama import Back, Fore, Style

from .bike_sensor import BikeSensor
from .device_scanner import DeviceScanner
from .heart_rate_monitor import HeartRateMonitor
from .usb_detector import ANTUSBDetector

colorama.init()


class ANTPlusDisplay:
    def __init__(self, config_file: str = "config/config.yaml"):
        self.config_file = config_file
        self.config = self.load_config()
        self.running = False

        # Device instances
        self.hr_monitor = None
        self.bike_sensor = None
        self.scanner = None
        self.usb_detector = ANTUSBDetector()

        # Latest data
        self.hr_data = {}
        self.bike_data = {}

        # Found devices
        self.found_devices = {}

        # USB stick status
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

    def load_config(self) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(self.config_file, "r") as f:
                config = yaml.safe_load(f)
            print(f"{Fore.GREEN}Loaded configuration from {self.config_file}{Style.RESET_ALL}")
            return config
        except FileNotFoundError:
            print(f"{Fore.RED}Configuration file {self.config_file} not found{Style.RESET_ALL}")
            sys.exit(1)
        except Exception as e:
            print(f"{Fore.RED}Error loading configuration: {e}{Style.RESET_ALL}")
            sys.exit(1)

    def save_config(self):
        """Save current configuration to YAML file."""
        try:
            with open(self.config_file, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            print(f"{Fore.GREEN}Configuration saved to {self.config_file}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error saving configuration: {e}{Style.RESET_ALL}")

    def scan_for_devices(self):
        """Scan for ANT+ devices and save to file."""
        print(f"\n{Fore.CYAN}=== ANT+ Device Scanner ==={Style.RESET_ALL}")

        # Check if USB stick is available
        if not self.usb_stick_available:
            print(f"{Fore.RED}Cannot scan for devices: No ANT+ USB stick detected.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please connect your ANT+ USB stick and restart the application.{Style.RESET_ALL}")
            return {}

        network_key = self.config["ant_network"]["key"]
        scan_timeout = self.config["app"]["scan_timeout"]
        backend_pref = self.config.get("app", {}).get("backend", None)

        # Keep scanner output concise unless explicitly debugging
        self.scanner = DeviceScanner(network_key, scan_timeout, debug=False, backend_preference=backend_pref)

        print("Make sure your ANT+ devices are active and transmitting...")
        print("Starting scan...")

        # Load previously found devices
        devices_file = self.config["app"]["found_devices_file"]
        self.found_devices = self.scanner.load_found_devices(devices_file)

        # Scan for new devices
        new_devices = self.scanner.scan_for_devices()

        # Merge with existing devices
        self.found_devices.update(new_devices)

        # Save updated device list
        self.scanner.save_found_devices(devices_file)

        return self.found_devices

    def list_found_devices(self):
        """Display list of found devices."""
        devices_file = self.config["app"]["found_devices_file"]

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

    def configure_devices(self):
        """Interactive device configuration."""
        print(f"\n{Fore.CYAN}=== Device Configuration ==={Style.RESET_ALL}")

        # Load found devices
        devices_file = self.config["app"]["found_devices_file"]
        try:
            with open(devices_file, "r") as f:
                found_devices = json.load(f)
        except FileNotFoundError:
            print(f"{Fore.YELLOW}No found devices file. Run scan first.{Style.RESET_ALL}")
            return

        if not found_devices:
            print(f"{Fore.YELLOW}No devices found. Run scan first.{Style.RESET_ALL}")
            return

        # Configure heart rate monitor
        print(f"\n{Fore.GREEN}Heart Rate Monitors:{Style.RESET_ALL}")
        hr_devices = {k: v for k, v in found_devices.items() if v["device_type"] == 120}

        if hr_devices:
            for i, (key, device) in enumerate(hr_devices.items(), 1):
                print(f"  {i}. {device['device_name']} (ID: {device['device_id']})")

            try:
                choice = input(f"\nSelect heart rate monitor (1-{len(hr_devices)}, 0 to skip): ")
                if choice != "0" and 1 <= int(choice) <= len(hr_devices):
                    selected_device = list(hr_devices.values())[int(choice) - 1]
                    self.config["devices"]["heart_rate"]["device_id"] = selected_device["device_id"]
                    print(
                        f"{Fore.GREEN}Selected heart rate monitor ID: {selected_device['device_id']}{Style.RESET_ALL}"
                    )
            except (ValueError, IndexError):
                print(f"{Fore.YELLOW}Invalid selection{Style.RESET_ALL}")
        else:
            print(f"  {Fore.YELLOW}No heart rate monitors found{Style.RESET_ALL}")

        # Configure bike sensor
        print(f"\n{Fore.GREEN}Bike Sensors:{Style.RESET_ALL}")
        bike_devices = {k: v for k, v in found_devices.items() if v["device_type"] in [121, 122, 123]}

        if bike_devices:
            for i, (key, device) in enumerate(bike_devices.items(), 1):
                print(f"  {i}. {device['device_name']} (ID: {device['device_id']})")

            try:
                choice = input(f"\nSelect bike sensor (1-{len(bike_devices)}, 0 to skip): ")
                if choice != "0" and 1 <= int(choice) <= len(bike_devices):
                    selected_device = list(bike_devices.values())[int(choice) - 1]
                    self.config["devices"]["bike_data"]["device_id"] = selected_device["device_id"]
                    print(f"{Fore.GREEN}Selected bike sensor ID: {selected_device['device_id']}{Style.RESET_ALL}")
            except (ValueError, IndexError):
                print(f"{Fore.YELLOW}Invalid selection{Style.RESET_ALL}")
        else:
            print(f"  {Fore.YELLOW}No bike sensors found{Style.RESET_ALL}")

        # Save configuration
        self.save_config()

    def connect_devices(self):
        """Connect to configured devices."""
        # Check if USB stick is available
        if not self.usb_stick_available:
            print(f"{Fore.RED}Cannot connect to devices: No ANT+ USB stick detected.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please connect your ANT+ USB stick and restart the application.{Style.RESET_ALL}")
            return

        network_key = self.config["ant_network"]["key"]

        # Connect heart rate monitor
        if self.config["devices"]["heart_rate"]["enabled"] and self.config["devices"]["heart_rate"]["device_id"]:

            hr_device_id = self.config["devices"]["heart_rate"]["device_id"]
            self.hr_monitor = HeartRateMonitor(hr_device_id, network_key)
            self.hr_monitor.on_heart_rate_data = self._on_hr_data

            if not self.hr_monitor.connect():
                print(f"{Fore.RED}Failed to connect to heart rate monitor{Style.RESET_ALL}")

        # Connect bike sensor
        if self.config["devices"]["bike_data"]["enabled"] and self.config["devices"]["bike_data"]["device_id"]:

            bike_device_id = self.config["devices"]["bike_data"]["device_id"]
            self.bike_sensor = BikeSensor(bike_device_id, network_key)
            self.bike_sensor.on_bike_data = self._on_bike_data

            if not self.bike_sensor.connect():
                print(f"{Fore.RED}Failed to connect to bike sensor{Style.RESET_ALL}")

    def _on_hr_data(self, data):
        """Callback for heart rate data."""
        self.hr_data = data

    def _on_bike_data(self, data):
        """Callback for bike sensor data."""
        self.bike_data = data

    def display_data(self):
        """Display real-time data from connected devices."""
        print(f"\n{Fore.CYAN}=== ANT+ Data Display ==={Style.RESET_ALL}")
        print("Press Ctrl+C to stop...\n")

        self.running = True

        try:
            while self.running:
                # Clear screen (works on most terminals)
                os.system("clear" if os.name == "posix" else "cls")

                # Display header
                print(f"{Back.BLUE}{Fore.WHITE} ANT+ Device Data Display {Style.RESET_ALL}")
                print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

                # Display heart rate data
                if self.hr_monitor and self.hr_monitor.connected:
                    if self.hr_data and self.hr_monitor.is_data_fresh():
                        hr_color = Fore.GREEN if self.hr_data["heart_rate"] > 0 else Fore.YELLOW
                        print(f"{Fore.CYAN}Heart Rate Monitor:{Style.RESET_ALL}")
                        print(f"  {hr_color}Heart Rate: {self.hr_data['heart_rate']} BPM{Style.RESET_ALL}")
                        if self.hr_data.get("rr_intervals"):
                            print(f"  R-R Intervals: {len(self.hr_data['rr_intervals'])} samples")
                    else:
                        print(f"{Fore.CYAN}Heart Rate Monitor:{Style.RESET_ALL}")
                        print(f"  {Fore.YELLOW}Waiting for data...{Style.RESET_ALL}")
                else:
                    print(f"{Fore.CYAN}Heart Rate Monitor:{Style.RESET_ALL}")
                    print(f"  {Fore.RED}Not connected{Style.RESET_ALL}")

                print()

                # Display bike sensor data
                if self.bike_sensor and self.bike_sensor.connected:
                    if self.bike_data and self.bike_sensor.is_data_fresh():
                        speed_color = Fore.GREEN if self.bike_data["speed"] > 0 else Fore.YELLOW
                        cadence_color = Fore.GREEN if self.bike_data["cadence"] > 0 else Fore.YELLOW
                        print(f"{Fore.CYAN}Bike Sensor:{Style.RESET_ALL}")
                        print(f"  {speed_color}Speed: {self.bike_data['speed']:.1f} km/h{Style.RESET_ALL}")
                        print(f"  {cadence_color}Cadence: {self.bike_data['cadence']} RPM{Style.RESET_ALL}")
                        print(f"  Distance: {self.bike_data['distance']:.2f} km")
                    else:
                        print(f"{Fore.CYAN}Bike Sensor:{Style.RESET_ALL}")
                        print(f"  {Fore.YELLOW}Waiting for data...{Style.RESET_ALL}")
                else:
                    print(f"{Fore.CYAN}Bike Sensor:{Style.RESET_ALL}")
                    print(f"  {Fore.RED}Not connected{Style.RESET_ALL}")

                time.sleep(self.config["app"]["data_display_interval"])

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Stopping data display...{Style.RESET_ALL}")
        finally:
            self.stop()

    def stop(self):
        """Stop the application and disconnect devices."""
        self.running = False

        if self.hr_monitor:
            self.hr_monitor.disconnect()

        if self.bike_sensor:
            self.bike_sensor.disconnect()

    def show_menu(self):
        """Show the main menu."""
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
                        print(
                            f"{Fore.YELLOW}Please connect an ANT+ USB stick and restart the application.{Style.RESET_ALL}"
                        )
                elif choice == "2":
                    self.list_found_devices()
                elif choice == "3":
                    if self.usb_stick_available:
                        self.configure_devices()
                    else:
                        print(
                            f"{Fore.YELLOW}Please connect an ANT+ USB stick and restart the application.{Style.RESET_ALL}"
                        )
                elif choice == "4":
                    if self.usb_stick_available:
                        self.connect_devices()
                        self.display_data()
                    else:
                        print(
                            f"{Fore.YELLOW}Please connect an ANT+ USB stick and restart the application.{Style.RESET_ALL}"
                        )
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


def main():
    """Main application entry point."""
    app = ANTPlusDisplay()

    # Check for USB stick on startup
    app.check_usb_on_startup()

    try:
        app.show_menu()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Application interrupted{Style.RESET_ALL}")
    finally:
        app.stop()


if __name__ == "__main__":
    main()
