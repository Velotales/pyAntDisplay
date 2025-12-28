#!/usr/bin/env python3
"""
PyANTDisplay - Device Manager

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

Manages device connections and data display.
"""

from colorama import Fore, Style

from ..devices.bike_sensor import BikeSensor
from ..devices.heart_rate_monitor import HeartRateMonitor


class DeviceManager:
    """Manages ANT+ device connections and data display."""

    def __init__(self, config: dict):
        self.config = config
        self.running = False

        # Device instances
        self.hr_monitor = None
        self.bike_sensor = None
        self.devices: list = []  # List of connected devices

        # Latest data
        self.hr_data: dict = {}
        self.bike_data: dict = {}

    def connect_devices(self):
        """Connect to configured devices."""
        network_key = self.config["ant_network"]["key"]
        self.devices = []  # Reset devices list

        # Connect heart rate monitor
        if (
            self.config["devices"]["heart_rate"]["enabled"]
            and self.config["devices"]["heart_rate"]["device_id"]
        ):
            hr_device_id = self.config["devices"]["heart_rate"]["device_id"]
            self.hr_monitor = HeartRateMonitor(hr_device_id, network_key)
            self.hr_monitor.on_heart_rate_data = self._on_hr_data

            if self.hr_monitor.connect():
                self.devices.append(self.hr_monitor)
            else:
                print(
                    f"{Fore.RED}Failed to connect to heart rate monitor{Style.RESET_ALL}"
                )

        # Connect bike sensor
        if (
            self.config["devices"]["bike_data"]["enabled"]
            and self.config["devices"]["bike_data"]["device_id"]
        ):
            bike_device_id = self.config["devices"]["bike_data"]["device_id"]
            self.bike_sensor = BikeSensor(bike_device_id, network_key)
            self.bike_sensor.on_bike_data = self._on_bike_data

            if self.bike_sensor.connect():
                self.devices.append(self.bike_sensor)
            else:
                print(f"{Fore.RED}Failed to connect to bike sensor{Style.RESET_ALL}")

    def _on_hr_data(self, data):
        """Callback for heart rate data."""
        self.hr_data = data

    def _on_bike_data(self, data):
        """Callback for bike sensor data."""
        self.bike_data = data

    def get_connected_devices(self):
        """Get list of connected devices."""
        return [d for d in self.devices if d.connected]

    def has_connected_devices(self):
        """Check if any devices are connected."""
        return len(self.get_connected_devices()) > 0

    def stop(self):
        """Stop the device manager and disconnect devices."""
        self.running = False

        if self.hr_monitor:
            self.hr_monitor.disconnect()

        if self.bike_sensor:
            self.bike_sensor.disconnect()
