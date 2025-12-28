#!/usr/bin/env python3
"""
PyANTDisplay - Heart Rate Monitor

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

ANT+ Heart Rate Monitor Reader
Connects to and reads data from ANT+ heart rate monitors.
"""

import threading
import time

import colorama
from colorama import Fore, Style
from openant.easy.channel import Channel
from openant.easy.node import Node

colorama.init()


class HeartRateMonitor:
    def __init__(self, device_id: int, network_key: list):
        self.device_id = device_id
        self.network_key = network_key
        self.node = None
        self.channel = None
        self.loop_thread = None
        self.connected = False
        self.running = False

        # Heart rate data
        self.heart_rate = 0
        self.rr_intervals = []
        self.battery_status = None
        self.last_update = 0

        # Callbacks
        self.on_heart_rate_data = None

    def connect(self) -> bool:
        """Connect to the heart rate monitor."""
        try:
            print(
                f"{Fore.CYAN}Connecting to Heart Rate Monitor (ID: {self.device_id})...{Style.RESET_ALL}"
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
                # Fallback to easy API new_network if needed
                self.node.new_network(key=self.network_key)

            # Set up channel for heart rate monitor
            self.channel = self.node.new_channel(Channel.Type.BIDIRECTIONAL_RECEIVE)
            self.channel.on_broadcast_data = self._on_heart_rate_data
            self.channel.on_burst_data = self._on_heart_rate_data

            self.channel.set_period(8070)  # Standard HR period (4.06 Hz)
            self.channel.set_search_timeout(30)
            self.channel.set_rf_freq(57)  # ANT+ frequency
            self.channel.set_id(self.device_id, 120, 0)  # HR device type is 120
            # Prefer extended messages when available
            try:
                self.channel.enable_extended_messages(True)
            except Exception:
                pass

            self.channel.open()
            self.connected = True
            self.running = True

            print(f"{Fore.GREEN}Connected to Heart Rate Monitor{Style.RESET_ALL}")
            return True

        except Exception as e:
            print(
                f"{Fore.RED}Failed to connect to Heart Rate Monitor: {e}{Style.RESET_ALL}"
            )
            self.disconnect()
            return False

    def disconnect(self):
        """Disconnect from the heart rate monitor."""
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

        print(f"{Fore.YELLOW}Disconnected from Heart Rate Monitor{Style.RESET_ALL}")

    def _on_heart_rate_data(self, data):
        """Process incoming heart rate data."""
        if len(data) < 8:
            return

        try:
            # ANT+ Heart Rate Monitor data format
            # Byte 0: Sync byte
            # Byte 1: Heart rate beat count
            # Byte 2: Computed heart rate
            # Byte 3: Heart rate beat count (MSB)
            # Bytes 4-5: R-R interval data (optional)
            # Bytes 6-7: Additional data

            # Extract heart rate (beats per minute)
            computed_hr = data[7]  # Computed heart rate is in byte 7
            beat_count = data[6]  # Beat count

            if computed_hr > 0:
                self.heart_rate = computed_hr
                self.last_update = time.time()

                # Extract R-R interval if available (for HRV analysis)
                if len(data) >= 6:
                    rr_interval = (data[5] << 8) | data[4]
                    if rr_interval > 0:
                        self.rr_intervals.append(rr_interval)
                        # Keep only last 10 intervals
                        if len(self.rr_intervals) > 10:
                            self.rr_intervals.pop(0)

                # Call callback if set
                if self.on_heart_rate_data:
                    self.on_heart_rate_data(
                        {
                            "heart_rate": self.heart_rate,
                            "beat_count": beat_count,
                            "rr_intervals": self.rr_intervals.copy(),
                            "timestamp": self.last_update,
                        }
                    )

        except Exception as e:
            print(f"{Fore.RED}Error processing heart rate data: {e}{Style.RESET_ALL}")

    def get_current_data(self) -> dict:
        """Get the current heart rate data."""
        return {
            "heart_rate": self.heart_rate,
            "rr_intervals": self.rr_intervals.copy(),
            "connected": self.connected,
            "last_update": self.last_update,
            "data_age": time.time() - self.last_update if self.last_update > 0 else 0,
        }

    def is_data_fresh(self, max_age: float = 5.0) -> bool:
        """Check if the heart rate data is fresh (updated recently)."""
        if self.last_update == 0:
            return False
        return (time.time() - self.last_update) < max_age


def main():
    """Test the heart rate monitor."""
    # You'll need to set the actual device ID after scanning
    device_id = 12345  # Replace with actual device ID from scanner
    network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

    hr_monitor = HeartRateMonitor(device_id, network_key)

    def on_hr_data(data):
        print(f"Heart Rate: {data['heart_rate']} BPM, Beat Count: {data['beat_count']}")
        if data["rr_intervals"]:
            print(f"  R-R Intervals: {data['rr_intervals']}")

    hr_monitor.on_heart_rate_data = on_hr_data

    if hr_monitor.connect():
        try:
            print("Monitoring heart rate data. Press Ctrl+C to stop...")
            while True:
                time.sleep(1)
                hr_monitor.get_current_data()  # Update internal state
                if not hr_monitor.is_data_fresh():
                    print(f"{Fore.YELLOW}No recent heart rate data...{Style.RESET_ALL}")

        except KeyboardInterrupt:
            print("\nStopping heart rate monitor...")

        finally:
            hr_monitor.disconnect()


if __name__ == "__main__":
    main()
