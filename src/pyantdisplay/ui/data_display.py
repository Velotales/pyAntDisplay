#!/usr/bin/env python3
"""
PyANTDisplay - Data Display Service

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

Handles real-time data display with terminal UI management.
"""

import os
import select
import sys
import time

from colorama import Back, Fore, Style


class DataDisplayService:
    """Handles real-time data display with terminal UI management."""
    
    def __init__(self, device_manager, config: dict):
        self.device_manager = device_manager
        self.config = config
        self.running = False
        self.quit_requested = False

    def _check_for_quit(self):
        """Check for 'q' key press without blocking."""
        if os.name == 'posix':  # Unix/Linux/macOS
            # Use non-blocking read
            try:
                if select.select([sys.stdin], [], [], 0.01) == ([sys.stdin], [], []):
                    char = sys.stdin.read(1).lower()
                    if char == 'q':
                        return True
            except Exception:
                # If there's any issue with input, just continue
                pass
        else:  # Windows
            try:
                import msvcrt
                if msvcrt.kbhit():
                    char = msvcrt.getch().decode('utf-8').lower()
                    if char == 'q':
                        return True
            except ImportError:
                pass
        return False

    def display_data(self):
        """Display real-time data from connected devices."""
        print(f"\n{Fore.CYAN}=== ANT+ Data Display ==={Style.RESET_ALL}")
        print("Initializing display...")
        
        self.running = True
        self.quit_requested = False
        old_settings = None

        # Only set raw mode if we have devices to display
        connected_devices = [d for d in self.device_manager.devices if d.connected]
        if not connected_devices:
            print(f"{Fore.YELLOW}No ANT+ devices connected. Connect devices first using scan/configure options.{Style.RESET_ALL}")
            return

        # Simpler approach: try to set raw mode but don't fail if it doesn't work
        try:
            if os.name == 'posix':
                import tty, termios
                old_settings = termios.tcgetattr(sys.stdin)
                # Set cbreak mode instead of raw mode - less intrusive
                tty.setcbreak(sys.stdin.fileno())
        except Exception as e:
            print(f"{Fore.YELLOW}Note: Using fallback input mode (raw terminal mode unavailable){Style.RESET_ALL}")
            time.sleep(1)

        try:
            while self.running and not self.quit_requested:
                # Check for quit key first (before clearing screen)
                if self._check_for_quit():
                    print(f"\n{Fore.GREEN}✅ Quit key detected!{Style.RESET_ALL}")
                    self.quit_requested = True
                    break

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
                self._display_header(cols)
                
                # Display device data
                self._display_heart_rate_monitor(cols)
                self._display_bike_sensor(cols)

                # Footer with controls - always visible
                self._display_footer(cols)

                time.sleep(self.config["app"]["data_display_interval"])

        except KeyboardInterrupt:
            print(f"\n{Fore.GREEN}✅ Data display stopped{Style.RESET_ALL}")
        finally:
            # Restore terminal settings
            if old_settings and os.name == 'posix':
                try:
                    import termios
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                except:
                    pass
            
            if self.quit_requested:
                print(f"\n{Fore.GREEN}✅ Data display stopped{Style.RESET_ALL}")

    def _display_header(self, cols):
        """Display the header with timestamp."""
        header = f"🚴 ANT+ Device Data Display 📊"
        header_padding = max(0, (cols - len(header)) // 2)
        border_line = "═" * cols
        
        print(f"{Back.BLUE}{Fore.WHITE}{border_line}{Style.RESET_ALL}")
        print(f"{Back.BLUE}{Fore.WHITE}{' ' * header_padding}{header}{' ' * (cols - len(header) - header_padding)}{Style.RESET_ALL}")
        print(f"{Back.BLUE}{Fore.WHITE}{border_line}{Style.RESET_ALL}")
        
        timestamp = time.strftime('%H:%M:%S • %Y-%m-%d')
        print(f"{Fore.CYAN}🕐 {timestamp}{Style.RESET_ALL}")
        print()

    def _display_footer(self, cols):
        """Display the footer with controls."""
        control_line = f"{Back.RED}{Fore.WHITE} Press 'q' key to quit (no Enter needed) {Style.RESET_ALL}"
        control_padding = max(0, (cols - 40) // 2)
        print(" " * control_padding + control_line)
        
        print(f"\n{Style.DIM}Refreshing every {self.config['app']['data_display_interval']}s...{Style.RESET_ALL}")

    def _display_heart_rate_monitor(self, cols):
        """Display heart rate monitor data in a box."""
        self._print_device_box("Heart Rate Monitor", "💓", 
                              self.device_manager.hr_monitor and self.device_manager.hr_monitor.connected, 
                              self._hr_display_func, cols)
    
    def _display_bike_sensor(self, cols):
        """Display bike sensor data in a box."""
        self._print_device_box("Bike Sensor", "🚴", 
                              self.device_manager.bike_sensor and self.device_manager.bike_sensor.connected, 
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
        hr_data = self.device_manager.hr_data
        hr_monitor = self.device_manager.hr_monitor
        
        if hr_data and hr_monitor.is_data_fresh():
            hr = hr_data["heart_rate"]
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
                
                if hr_data.get("rr_intervals"):
                    rr_count = len(hr_data["rr_intervals"])
                    rr_line = f"│ 📈 R-R Intervals: {rr_count} samples"
                    rr_padding = " " * max(0, box_width - len(rr_line) - 1) + "│"
                    print(rr_line + rr_padding)
            else:
                print(f"│ {Fore.YELLOW}⏳ Connected, waiting for heart rate...{Style.RESET_ALL}" + " " * max(0, box_width - 40) + "│")
        else:
            print(f"│ {Fore.YELLOW}⏳ Waiting for data...{Style.RESET_ALL}" + " " * max(0, box_width - 25) + "│")

    def _bike_display_func(self, box_width):
        """Display bike sensor data inside the box."""
        bike_data = self.device_manager.bike_data
        bike_sensor = self.device_manager.bike_sensor
        
        if bike_data and bike_sensor.is_data_fresh():
            speed = bike_data["speed"]
            cadence = bike_data["cadence"]
            distance = bike_data["distance"]
            
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