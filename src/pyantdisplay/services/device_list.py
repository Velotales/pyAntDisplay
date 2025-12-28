#!/usr/bin/env python3
"""
PyANTDisplay - Device List Service

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

Handles device listing and display operations.
"""

import json
import time

from colorama import Fore, Style


class DeviceListService:
    """Handles device listing and display operations."""
    
    def __init__(self, config: dict):
        self.config = config

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

        self._display_devices_table(devices)

    def _display_devices_table(self, devices: dict):
        """Display devices in a formatted table."""
        print(f"\n{Fore.CYAN}=== Found ANT+ Devices ==={Style.RESET_ALL}")
        print(f"{'ID':<8} {'Type':<6} {'Name':<25} {'Last Seen':<20}")
        print("-" * 70)

        for key, device in devices.items():
            last_seen = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(device["last_seen"]))
            print(f"{device['device_id']:<8} {device['device_type']:<6} " 
                  f"{device['device_name']:<25} {last_seen}")

    def get_device_count(self) -> int:
        """Get the count of found devices."""
        devices_file = self.config["app"]["found_devices_file"]
        
        try:
            with open(devices_file, "r") as f:
                devices = json.load(f)
            return len(devices)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0