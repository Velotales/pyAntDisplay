#!/usr/bin/env python3
"""
PyANTDisplay - Configuration Manager

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

Handles configuration loading, saving, and device configuration.
"""

import json
import sys

import yaml
from colorama import Fore, Style


class ConfigManager:
    """Manages application configuration and device setup."""
    
    def __init__(self, config_file: str = "config/config.yaml"):
        self.config_file = config_file
        self.config = self.load_config()
    
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

    def configure_devices_interactive(self):
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
        self._configure_heart_rate_monitor(found_devices)
        
        # Configure bike sensor
        self._configure_bike_sensor(found_devices)

        # Save configuration
        self.save_config()

    def _configure_heart_rate_monitor(self, found_devices):
        """Configure heart rate monitor selection."""
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

    def _configure_bike_sensor(self, found_devices):
        """Configure bike sensor selection."""
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