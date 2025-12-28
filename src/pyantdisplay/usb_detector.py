#!/usr/bin/env python3
"""
PyANTDisplay - USB Detector

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

ANT+ USB Stick Detection
Detects if ANT+ USB sticks are connected to the system.
"""

from typing import Dict, List

import colorama
import usb.core
import usb.util
from colorama import Fore, Style

colorama.init()


class ANTUSBDetector:
    """Detector for ANT+ USB sticks."""

    # Common ANT+ USB stick vendor/product IDs
    ANT_DEVICES = [
        # Dynastream/Garmin ANT+ sticks
        {"vendor_id": 0x0FCF, "product_id": 0x1003, "name": "Dynastream ANT USB Stick"},
        {"vendor_id": 0x0FCF, "product_id": 0x1004, "name": "Dynastream ANT USB Stick 2"},
        {"vendor_id": 0x0FCF, "product_id": 0x1006, "name": "Dynastream ANT USB-m Stick"},
        {"vendor_id": 0x0FCF, "product_id": 0x1008, "name": "Dynastream ANT USB-m Stick"},
        {"vendor_id": 0x0FCF, "product_id": 0x1009, "name": "Dynastream ANT USB Stick"},
        # Suunto ANT+ sticks (some models)
        {"vendor_id": 0x1493, "product_id": 0x0003, "name": "Suunto ANT+ USB Stick"},
        # Tacx ANT+ dongles
        {"vendor_id": 0x3561, "product_id": 0x0012, "name": "Tacx ANT+ USB Stick"},
        # Other common ANT+ devices
        {"vendor_id": 0x0FCF, "product_id": 0x1005, "name": "ANT USB Stick"},
    ]

    def __init__(self):
        self.detected_devices = []

    def detect_ant_sticks(self) -> List[Dict]:
        """
        Detect connected ANT+ USB sticks.

        Returns:
            List of dictionaries containing device information
        """
        self.detected_devices = []

        try:
            # Find all USB devices
            devices = usb.core.find(find_all=True)

            for device in devices:
                # Check if this device matches known ANT+ devices
                for ant_device in self.ANT_DEVICES:
                    if device.idVendor == ant_device["vendor_id"] and device.idProduct == ant_device["product_id"]:

                        device_info = {
                            "vendor_id": device.idVendor,
                            "product_id": device.idProduct,
                            "name": ant_device["name"],
                            "bus": device.bus,
                            "address": device.address,
                            "device_object": device,
                        }

                        # Try to get additional device information
                        try:
                            if device.manufacturer:
                                device_info["manufacturer"] = device.manufacturer
                            if device.product:
                                device_info["product"] = device.product
                            if device.serial_number:
                                device_info["serial"] = device.serial_number
                        except (usb.core.USBError, UnicodeDecodeError, ValueError):
                            # Some devices may not allow reading these fields
                            pass

                        self.detected_devices.append(device_info)
                        break

        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Error during USB device detection: {e}{Style.RESET_ALL}")

        return self.detected_devices

    def get_detected_devices(self) -> List[Dict]:
        """Get the list of detected ANT+ devices."""
        return self.detected_devices

    def is_ant_stick_connected(self) -> bool:
        """Check if at least one ANT+ USB stick is connected."""
        return len(self.detected_devices) > 0

    def print_detected_devices(self):
        """Print information about detected ANT+ USB sticks."""
        if not self.detected_devices:
            print(f"{Fore.YELLOW}No ANT+ USB sticks detected.{Style.RESET_ALL}")
            return

        print(f"{Fore.GREEN}Detected ANT+ USB Sticks:{Style.RESET_ALL}")
        for i, device in enumerate(self.detected_devices, 1):
            print(f"  {i}. {device['name']}")
            print(f"     Vendor ID: 0x{device['vendor_id']:04x}")
            print(f"     Product ID: 0x{device['product_id']:04x}")
            print(f"     Bus: {device['bus']}, Address: {device['address']}")

            if "manufacturer" in device:
                print(f"     Manufacturer: {device['manufacturer']}")
            if "product" in device:
                print(f"     Product: {device['product']}")
            if "serial" in device:
                print(f"     Serial: {device['serial']}")
            print()

    def check_usb_permissions(self) -> bool:
        """
        Check if we have permission to access USB devices.

        Returns:
            True if we can access USB devices, False otherwise
        """
        try:
            # Try to enumerate USB devices
            list(usb.core.find(find_all=True))  # Test USB access
            return True
        except usb.core.NoBackendError:
            print(f"{Fore.RED}Error: No USB backend available. Please install libusb.{Style.RESET_ALL}")
            return False
        except usb.core.USBError as e:
            if "Access denied" in str(e) or "Permission denied" in str(e):
                print(f"{Fore.RED}Error: Permission denied accessing USB devices.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Try running with sudo or setting up udev rules.{Style.RESET_ALL}")
                return False
            else:
                print(f"{Fore.YELLOW}Warning: USB error: {e}{Style.RESET_ALL}")
                return True  # May still work for some operations
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Unexpected error checking USB permissions: {e}{Style.RESET_ALL}")
            return True  # Assume it might work

    def print_setup_instructions(self):
        """Print setup instructions for ANT+ USB stick."""
        print(f"\n{Fore.CYAN}ANT+ USB Stick Setup Instructions:{Style.RESET_ALL}")
        print("1. Connect your ANT+ USB stick to a USB port")
        print("2. Make sure you have the necessary permissions:")
        print()
        print(f"{Fore.YELLOW}For Ubuntu/Debian:{Style.RESET_ALL}")
        print("   sudo apt install libusb-1.0-0-dev")
        print("   # Create udev rule for ANT+ stick:")
        print("   sudo nano /etc/udev/rules.d/99-ant-stick.rules")
        print("   # Add this line (adjust vendor/product ID as needed):")
        print('   SUBSYSTEM=="usb", ATTRS{idVendor}=="0fcf", ATTRS{idProduct}=="1008", MODE="0666"')
        print("   # Reload udev rules:")
        print("   sudo udevadm control --reload-rules && sudo udevadm trigger")
        print()
        print(f"{Fore.YELLOW}Alternative:{Style.RESET_ALL}")
        print("   Add your user to the dialout group:")
        print("   sudo usermod -a -G dialout $USER")
        print("   Then log out and back in.")


def main():
    """Test the USB detector."""
    print(f"{Fore.CYAN}ANT+ USB Stick Detector{Style.RESET_ALL}")

    detector = ANTUSBDetector()

    # Check USB permissions first
    if not detector.check_usb_permissions():
        detector.print_setup_instructions()
        return

    # Detect ANT+ devices
    print("Scanning for ANT+ USB sticks...")
    devices = detector.detect_ant_sticks()

    if devices:
        detector.print_detected_devices()
        print(f"{Fore.GREEN}✓ ANT+ USB stick(s) detected and ready to use!{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}No ANT+ USB sticks found.{Style.RESET_ALL}")
        detector.print_setup_instructions()


if __name__ == "__main__":
    main()
