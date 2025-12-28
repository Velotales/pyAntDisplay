#!/usr/bin/env python3
"""
PyANTDisplay - Bike Sensor

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

ANT+ Bike Sensor Reader
Connects to and reads data from ANT+ bike speed and cadence sensors.
"""

import threading
import time

import colorama
from colorama import Fore, Style
from openant.easy.channel import Channel
from openant.easy.node import Node

colorama.init()


class BikeSensor:
    def __init__(
        self, device_id: int, network_key: list, wheel_circumference: float = 2.1
    ):
        self.device_id = device_id
        self.network_key = network_key
        self.wheel_circumference = wheel_circumference  # meters
        self.node = None
        self.channel = None
        self.loop_thread = None
        self.connected = False
        self.running = False

        # Speed and cadence data
        self.speed = 0.0  # km/h
        self.cadence = 0  # rpm
        self.distance = 0.0  # km
        self.last_update = 0

        # Previous values for calculating speed/cadence
        self._last_speed_event_time = 0
        self._last_speed_revolution_count = 0
        self._last_cadence_event_time = 0
        self._last_cadence_revolution_count = 0

        # Callbacks
        self.on_bike_data = None

    def connect(self) -> bool:
        """Connect to the bike sensor."""
        try:
            print(
                f"{Fore.CYAN}Connecting to Bike Sensor (ID: {self.device_id})...{Style.RESET_ALL}"
            )

            self.node = Node()
            # Run event loop in background; Node.start() is blocking
            self.loop_thread = threading.Thread(
                target=self.node.start, name="openant.easy.main", daemon=True
            )
            self.loop_thread.start()

            # Set network key on network 0
            try:
                self.node.set_network_key(0, self.network_key)
            except Exception:
                self.node.new_network(key=self.network_key)

            # Set up channel for bike speed and cadence sensor
            self.channel = self.node.new_channel(Channel.Type.BIDIRECTIONAL_RECEIVE)
            self.channel.on_broadcast_data = self._on_bike_data
            self.channel.on_burst_data = self._on_bike_data

            self.channel.set_period(8086)  # Standard bike sensor period
            self.channel.set_search_timeout(30)
            self.channel.set_rf_freq(57)  # ANT+ frequency
            self.channel.set_id(
                self.device_id, 121, 0
            )  # Speed and cadence device type is 121
            # Prefer extended messages when available
            try:
                self.channel.enable_extended_messages(True)
            except Exception:
                pass

            self.channel.open()
            self.connected = True
            self.running = True

            print(f"{Fore.GREEN}Connected to Bike Sensor{Style.RESET_ALL}")
            return True

        except Exception as e:
            print(f"{Fore.RED}Failed to connect to Bike Sensor: {e}{Style.RESET_ALL}")
            self.disconnect()
            return False

    def disconnect(self):
        """Disconnect from the bike sensor."""
        self.running = False
        self.connected = False

        if self.channel:
            try:
                self.channel.close()
            except Exception as e:
                print(f"{Fore.RED}Error closing channel: {e}{Style.RESET_ALL}")

        if self.node:
            try:
                self.node.stop()
            except Exception as e:
                print(f"{Fore.RED}Error stopping node: {e}{Style.RESET_ALL}")
                pass

        print(f"{Fore.YELLOW}Disconnected from Bike Sensor{Style.RESET_ALL}")

    def _on_bike_data(self, data):
        """Process incoming bike sensor data."""
        if len(data) < 8:
            return

        try:
            # ANT+ Bike Speed and Cadence Sensor data format
            # Bytes 0-1: Cadence event time (1/1024 second resolution)
            # Bytes 2-3: Cadence revolution count
            # Bytes 4-5: Speed event time (1/1024 second resolution)
            # Bytes 6-7: Speed revolution count

            # Extract cadence data
            cadence_event_time = (data[1] << 8) | data[0]
            cadence_revolution_count = (data[3] << 8) | data[2]

            # Extract speed data
            speed_event_time = (data[5] << 8) | data[4]
            speed_revolution_count = (data[7] << 8) | data[6]

            current_time = time.time()

            # Calculate cadence (RPM)
            if self._last_cadence_event_time != 0:
                cadence_time_diff = (
                    cadence_event_time - self._last_cadence_event_time
                ) & 0xFFFF
                cadence_rev_diff = (
                    cadence_revolution_count - self._last_cadence_revolution_count
                ) & 0xFFFF

                if cadence_time_diff > 0 and cadence_rev_diff > 0:
                    # Convert to RPM (revolutions per minute)
                    cadence_freq = cadence_rev_diff / (cadence_time_diff / 1024.0)  # Hz
                    self.cadence = int(cadence_freq * 60)  # RPM

            # Calculate speed (km/h)
            if self._last_speed_event_time != 0:
                speed_time_diff = (
                    speed_event_time - self._last_speed_event_time
                ) & 0xFFFF
                speed_rev_diff = (
                    speed_revolution_count - self._last_speed_revolution_count
                ) & 0xFFFF

                if speed_time_diff > 0 and speed_rev_diff > 0:
                    # Calculate speed
                    distance_traveled = (
                        speed_rev_diff * self.wheel_circumference
                    )  # meters
                    time_elapsed = speed_time_diff / 1024.0  # seconds
                    speed_mps = distance_traveled / time_elapsed  # m/s
                    self.speed = speed_mps * 3.6  # km/h

                    # Update total distance
                    self.distance += distance_traveled / 1000.0  # km

            # Update previous values
            self._last_cadence_event_time = cadence_event_time
            self._last_cadence_revolution_count = cadence_revolution_count
            self._last_speed_event_time = speed_event_time
            self._last_speed_revolution_count = speed_revolution_count

            self.last_update = current_time

            # Call callback if set
            if self.on_bike_data:
                self.on_bike_data(
                    {
                        "speed": self.speed,
                        "cadence": self.cadence,
                        "distance": self.distance,
                        "timestamp": self.last_update,
                    }
                )

        except Exception as e:
            print(f"{Fore.RED}Error processing bike sensor data: {e}{Style.RESET_ALL}")

    def get_current_data(self) -> dict:
        """Get the current bike sensor data."""
        return {
            "speed": self.speed,
            "cadence": self.cadence,
            "distance": self.distance,
            "connected": self.connected,
            "last_update": self.last_update,
            "data_age": time.time() - self.last_update if self.last_update > 0 else 0,
        }

    def is_data_fresh(self, max_age: float = 5.0) -> bool:
        """Check if the bike sensor data is fresh (updated recently)."""
        if self.last_update == 0:
            return False
        return (time.time() - self.last_update) < max_age

    def reset_distance(self):
        """Reset the trip distance counter."""
        self.distance = 0.0
        print(f"{Fore.GREEN}Trip distance reset{Style.RESET_ALL}")


def main():
    """Test the bike sensor."""
    # You'll need to set the actual device ID after scanning
    device_id = 12345  # Replace with actual device ID from scanner
    network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
    wheel_circumference = 2.1  # meters (700c road bike wheel)

    bike_sensor = BikeSensor(device_id, network_key, wheel_circumference)

    def on_bike_data(data):
        print(
            f"Speed: {data['speed']:.1f} km/h, Cadence: {data['cadence']} RPM, Distance: {data['distance']:.2f} km"
        )

    bike_sensor.on_bike_data = on_bike_data

    if bike_sensor.connect():
        try:
            print("Monitoring bike sensor data. Press Ctrl+C to stop...")
            while True:
                time.sleep(1)
                bike_sensor.get_current_data()  # Update internal state
                if not bike_sensor.is_data_fresh():
                    print(
                        f"{Fore.YELLOW}No recent bike sensor data...{Style.RESET_ALL}"
                    )

        except KeyboardInterrupt:
            print("\nStopping bike sensor monitor...")

        finally:
            bike_sensor.disconnect()


if __name__ == "__main__":
    main()
