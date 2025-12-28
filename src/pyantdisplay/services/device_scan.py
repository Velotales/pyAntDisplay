#!/usr/bin/env python3
"""
PyANTDisplay - Device Scan Service

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

Handles ANT+ device scanning operations.
"""

from colorama import Fore, Style

from .device_scanner import DeviceScanner


class DeviceScanService:
    """Handles ANT+ device scanning operations."""
    
    def __init__(self, config: dict):
        self.config = config

    def scan_for_devices(self) -> dict:
        """Scan for ANT+ devices and save to file."""
        print(f"\n{Fore.CYAN}=== ANT+ Device Scanner ==={Style.RESET_ALL}")

        network_key = self.config["ant_network"]["key"]
        scan_timeout = self.config["app"]["scan_timeout"]
        backend_pref = self.config.get("app", {}).get("backend", None)

        # Keep scanner output concise unless explicitly debugging
        scanner = DeviceScanner(network_key, scan_timeout, debug=False, backend_preference=backend_pref)

        print("Make sure your ANT+ devices are active and transmitting...")
        print("Starting scan...")

        # Load previously found devices
        devices_file = self.config["app"]["found_devices_file"]
        found_devices = scanner.load_found_devices(devices_file)

        # Scan for new devices
        new_devices = scanner.scan_for_devices()

        # Merge with existing devices
        found_devices.update(new_devices)

        # Save updated device list
        scanner.save_found_devices(devices_file)

        return found_devices