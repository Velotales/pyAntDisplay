#!/usr/bin/env python3
"""
Demo script to showcase the improved data display UI.

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
"""

import os
import random
import time

import colorama
from colorama import Back, Fore, Style

colorama.init()


def demo_display():
    """Demo the improved data display UI with simulated data."""
    print(f"\n{Fore.CYAN}=== ANT+ Data Display UI Demo ==={Style.RESET_ALL}")
    print("This demo shows the improved UI with simulated data")
    print("Press Ctrl+C to stop...\n")
    
    # Simulate some initial values
    heart_rate = 75
    speed = 0.0
    cadence = 0
    distance = 0.0
    hr_connected = True
    bike_connected = True
    
    try:
        for cycle in range(100):  # Run for about 100 cycles
            # Clear screen
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

            # Create data sections with visual boxes
            def print_device_box(title, icon, connected, data_func):
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

            # Heart Rate Monitor display
            def hr_display_func(box_width):
                if hr_connected and heart_rate > 0:
                    # Color code heart rate zones
                    if heart_rate < 100:
                        hr_color = Fore.CYAN
                        zone = "Rest"
                    elif heart_rate < 140:
                        hr_color = Fore.GREEN
                        zone = "Aerobic"
                    elif heart_rate < 170:
                        hr_color = Fore.YELLOW
                        zone = "Threshold"
                    else:
                        hr_color = Fore.RED
                        zone = "Anaerobic"
                    
                    hr_line = f"│ {hr_color}💓 {heart_rate:3d} BPM{Style.RESET_ALL} ({zone})"
                    padding = " " * max(0, box_width - len(f"│ 💓 {heart_rate:3d} BPM ({zone})") - 1) + "│"
                    print(hr_line + padding)
                    
                    rr_count = random.randint(5, 15)
                    rr_line = f"│ 📈 R-R Intervals: {rr_count} samples"
                    rr_padding = " " * max(0, box_width - len(rr_line) - 1) + "│"
                    print(rr_line + rr_padding)
                else:
                    print(f"│ {Fore.YELLOW}⏳ Connected, waiting for heart rate...{Style.RESET_ALL}" + " " * max(0, box_width - 40) + "│")

            # Bike Sensor display  
            def bike_display_func(box_width):
                if bike_connected:
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

            # Display device boxes
            print_device_box("Heart Rate Monitor", "💓", hr_connected, hr_display_func)
            print_device_box("Bike Sensor", "🚴", bike_connected, bike_display_func)

            # Footer with controls - always visible
            control_line = f"{Back.RED}{Fore.WHITE} Press Ctrl+C or 'q' + Enter to quit {Style.RESET_ALL}"
            control_padding = max(0, (cols - 35) // 2)
            print(" " * control_padding + control_line)
            
            print(f"\n{Style.DIM}Refreshing every 1s... (Demo mode){Style.RESET_ALL}")

            # Simulate changing data
            if cycle % 10 == 0:  # Change connection status occasionally
                hr_connected = random.choice([True, True, True, False])  # Mostly connected
                bike_connected = random.choice([True, True, True, False])
            
            if hr_connected:
                # Simulate realistic heart rate changes
                heart_rate += random.randint(-3, 5)
                heart_rate = max(60, min(190, heart_rate))  # Keep in reasonable range
                
            if bike_connected:
                # Simulate cycling data
                if cycle > 5:  # Start moving after a few seconds
                    speed += random.uniform(-2.0, 3.0)
                    speed = max(0, min(45, speed))  # Keep reasonable
                    
                    if speed > 5:  # Only have cadence when moving
                        cadence += random.randint(-5, 8)
                        cadence = max(0, min(120, cadence))
                    else:
                        cadence = 0
                    
                    distance += speed / 3600  # Convert km/h to km per second (roughly)

            time.sleep(1)

    except KeyboardInterrupt:
        print(f"\n{Fore.GREEN}✅ Demo stopped{Style.RESET_ALL}")
        
if __name__ == "__main__":
    demo_display()