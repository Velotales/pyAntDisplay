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

import os
import time

from colorama import Back, Fore, Style

from .bike_sensor import BikeSensor
from .heart_rate_monitor import HeartRateMonitor


class DeviceManager:
    """Manages ANT+ device connections and data display."""
    
    def __init__(self, config: dict):
        self.config = config
        self.running = False

        # Device instances
        self.hr_monitor = None
        self.bike_sensor = None

        # Latest data
        self.hr_data = {}
        self.bike_data = {}

    def connect_devices(self):
        """Connect to configured devices."""
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
        print("Initializing display...")

        self.running = True

        try:
            while self.running:
                # Clear screen (works on most terminals)
                os.system("clear" if os.name == "posix" else "cls")

                # Get terminal size for better layout
                try:
                    import shutil
                    cols, rows = shutil.get_terminal_size()
                    cols = min(cols, 80)  # Cap width for readability
                except:
                    cols = 80

                # Display header with border
                header = f"🚴 ANT+ Device Data Display 📊"
                header_padding = max(0, (cols - len(header)) // 2)
                border_line = "═" * cols
                
                print(f"{Back.BLUE}{Fore.WHITE}{border_line}{Style.RESET_ALL}")
                print(f"{Back.BLUE}{Fore.WHITE}{' ' * header_padding}{header}{' ' * (cols - len(header) - header_padding)}{Style.RESET_ALL}")
                print(f"{Back.BLUE}{Fore.WHITE}{border_line}{Style.RESET_ALL}")
                
                timestamp = time.strftime('%H:%M:%S • %Y-%m-%d')
                print(f"{Fore.CYAN}🕐 {timestamp}{Style.RESET_ALL}")
                print()

                # Display device data
                self._display_heart_rate_monitor(cols)
                self._display_bike_sensor(cols)

                # Footer with controls - always visible
                control_line = f"{Back.RED}{Fore.WHITE} Press Ctrl+C or 'q' + Enter to quit {Style.RESET_ALL}"
                control_padding = max(0, (cols - 35) // 2)
                print(" " * control_padding + control_line)
                
                print(f"\n{Style.DIM}Refreshing every {self.config['app']['data_display_interval']}s...{Style.RESET_ALL}")

                time.sleep(self.config["app"]["data_display_interval"])

        except KeyboardInterrupt:
            print(f"\n{Fore.GREEN}✅ Data display stopped{Style.RESET_ALL}")
        finally:
            self.stop()

    def _display_heart_rate_monitor(self, cols):
        """Display heart rate monitor data in a box."""
        self._print_device_box("Heart Rate Monitor", "💓", 
                              self.hr_monitor and self.hr_monitor.connected, 
                              self._hr_display_func, cols)
    
    def _display_bike_sensor(self, cols):
        """Display bike sensor data in a box."""
        self._print_device_box("Bike Sensor", "🚴", 
                              self.bike_sensor and self.bike_sensor.connected, 
                              self._bike_display_func, cols)

    def _print_device_box(self, title, icon, connected, data_func, cols):
        """Print a device data box with border."""
        box_width = cols - 4
        title_line = f"┌─ {icon} {title} "
        title_line += "─" * max(0, box_width - len(title_line) - 1) + "┐"
        
        print(f"{Fore.CYAN}{title_line}{Style.RESET_ALL}")
        
        if connected:
            data_func(box_width)
        else:
            print(f"│ {Fore.RED}❌ Not connected{Style.RESET_ALL}" + " " * max(0, box_width - 18) + "│")
        
        bottom_line = "└" + "─" * (box_width - 2) + "┘"
        print(f"{Fore.CYAN}{bottom_line}{Style.RESET_ALL}")
        print()

    def _hr_display_func(self, box_width):
        """Display heart rate data inside the box."""
        if self.hr_data and self.hr_monitor.is_data_fresh():
            hr = self.hr_data["heart_rate"]
            if hr > 0:
                # Color code heart rate zones
                if hr < 100:
                    hr_color = Fore.CYAN
                    zone = "Rest"
                elif hr < 140:
                    hr_color = Fore.GREEN
                    zone = "Aerobic"
                elif hr < 170:
                    hr_color = Fore.YELLOW
                    zone = "Threshold"
                else:
                    hr_color = Fore.RED
                    zone = "Anaerobic"
                
                hr_line = f"│ {hr_color}💓 {hr:3d} BPM{Style.RESET_ALL} ({zone})"
                padding = " " * max(0, box_width - len(f"│ 💓 {hr:3d} BPM ({zone})") - 1) + "│"
                print(hr_line + padding)
                
                if self.hr_data.get("rr_intervals"):
                    rr_count = len(self.hr_data["rr_intervals"])
                    rr_line = f"│ 📈 R-R Intervals: {rr_count} samples"
                    rr_padding = " " * max(0, box_width - len(rr_line) - 1) + "│"
                    print(rr_line + rr_padding)
            else:
                print(f"│ {Fore.YELLOW}⏳ Connected, waiting for heart rate...{Style.RESET_ALL}" + " " * max(0, box_width - 40) + "│")
        else:
            print(f"│ {Fore.YELLOW}⏳ Waiting for data...{Style.RESET_ALL}" + " " * max(0, box_width - 25) + "│")

    def _bike_display_func(self, box_width):
        """Display bike sensor data inside the box."""
        if self.bike_data and self.bike_sensor.is_data_fresh():
            speed = self.bike_data["speed"]
            cadence = self.bike_data["cadence"]
            distance = self.bike_data["distance"]
            
            # Speed
            speed_color = Fore.GREEN if speed > 0 else Fore.YELLOW
            speed_line = f"│ {speed_color}🚴 Speed: {speed:5.1f} km/h{Style.RESET_ALL}"
            speed_padding = " " * max(0, box_width - len(f"│ 🚴 Speed: {speed:5.1f} km/h") - 1) + "│"
            print(speed_line + speed_padding)
            
            # Cadence
            cadence_color = Fore.GREEN if cadence > 0 else Fore.YELLOW  
            cadence_line = f"│ {cadence_color}🔄 Cadence: {cadence:3d} RPM{Style.RESET_ALL}"
            cadence_padding = " " * max(0, box_width - len(f"│ 🔄 Cadence: {cadence:3d} RPM") - 1) + "│"
            print(cadence_line + cadence_padding)
            
            # Distance
            distance_line = f"│ 📏 Distance: {distance:6.2f} km"
            distance_padding = " " * max(0, box_width - len(distance_line) - 1) + "│"
            print(distance_line + distance_padding)
        else:
            print(f"│ {Fore.YELLOW}⏳ Waiting for data...{Style.RESET_ALL}" + " " * max(0, box_width - 25) + "│")

    def stop(self):
        """Stop the device manager and disconnect devices."""
        self.running = False

        if self.hr_monitor:
            self.hr_monitor.disconnect()

        if self.bike_sensor:
            self.bike_sensor.disconnect()