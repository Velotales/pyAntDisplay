#!/usr/bin/env python3
"""
PyANTDisplay - Device Scanner

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

ANT+ Device Scanner
Scans for available ANT+ devices and saves them to a configuration file.
"""

import json
import logging
import threading
import time
from typing import Dict, List, Optional

import colorama
from colorama import Fore, Style

from .ant_backend import AntBackend, ChannelType
from ..utils.common import deep_merge_save, load_manufacturers, parse_common_pages
from ..utils.usb_detector import ANTUSBDetector

colorama.init()


class DeviceScanner:
    def __init__(
        self,
        network_key: List[int],
        scan_timeout: int = 30,
        debug: bool = True,
        backend_preference: Optional[str] = None,
    ):
        self.network_key = network_key
        self.scan_timeout = scan_timeout
        self.found_devices = {}
        self.scanning = False
        self.node = None
        self.debug = debug
        self.backend = AntBackend(preferred=backend_preference, debug=self.debug)
        self.manufacturer_map: Dict[int, str] = load_manufacturers()
        self.last_save_times: Dict[str, float] = {}
        # Quiet openant logging unless debug enabled
        for name in [
            "openant",
            "openant.base",
            "openant.base.ant",
            "openant.base.driver",
            "openant.easy",
            "openant.easy.node",
            "openant.easy.channel",
            "openant.easy.filter",
        ]:
            logging.getLogger(name).setLevel(logging.DEBUG if self.debug else logging.WARNING)

        if self.debug:
            print(f"{Fore.BLUE}[DEBUG] DeviceScanner initialized with timeout: {scan_timeout}s{Style.RESET_ALL}")
            print(f"{Fore.BLUE}[DEBUG] Network key: {[hex(x) for x in network_key]}{Style.RESET_ALL}")
            print(f"{Fore.BLUE}[DEBUG] Using ANT backend: {self.backend.name}{Style.RESET_ALL}")

    def scan_for_devices(self) -> Dict:
        """Scan for ANT+ devices and return a dictionary of found devices."""
        print(f"{Fore.CYAN}Starting ANT+ device scan for {self.scan_timeout} seconds...{Style.RESET_ALL}")

        # Pre-flight checks
        if self.debug:
            print(f"{Fore.BLUE}[DEBUG] Performing pre-flight checks...{Style.RESET_ALL}")

            # Check USB permissions and devices again
            from ..utils.usb_detector import ANTUSBDetector

            usb_detector = ANTUSBDetector()

            print(f"{Fore.BLUE}[DEBUG] Checking USB permissions...{Style.RESET_ALL}")
            if not usb_detector.check_usb_permissions():
                print(f"{Fore.RED}[DEBUG] USB permissions check failed{Style.RESET_ALL}")
                raise Exception("USB permissions not properly configured")
            else:
                print(f"{Fore.BLUE}[DEBUG] USB permissions OK{Style.RESET_ALL}")

            print(f"{Fore.BLUE}[DEBUG] Scanning for ANT+ USB devices...{Style.RESET_ALL}")
            usb_devices = usb_detector.detect_ant_sticks()
            if not usb_devices:
                print(f"{Fore.RED}[DEBUG] No ANT+ USB devices found{Style.RESET_ALL}")
                raise Exception("No ANT+ USB devices detected")
            else:
                print(f"{Fore.BLUE}[DEBUG] Found {len(usb_devices)} ANT+ USB device(s): {usb_devices}{Style.RESET_ALL}")

        try:
            if self.debug:
                print(f"{Fore.BLUE}[DEBUG] Creating ANT+ node...{Style.RESET_ALL}")

            self.node = self.backend.create_node()

            if self.debug:
                print(f"{Fore.BLUE}[DEBUG] ANT+ node created: {self.node}{Style.RESET_ALL}")
                print(f"{Fore.BLUE}[DEBUG] Starting ANT+ node event loop in background...{Style.RESET_ALL}")

            # Start node event loop in background (non-blocking)
            start_thread = threading.Thread(target=self.node.start, name="openant.easy.main", daemon=True)
            start_thread.start()

            if self.debug:
                print(
                    f"{Fore.BLUE}[DEBUG] ANT+ node started (background thread alive: {start_thread.is_alive()}){Style.RESET_ALL}"
                )

            # Set up network: set ANT+ network key on network 0
            if self.debug:
                print(f"{Fore.BLUE}[DEBUG] Setting ANT+ network key...{Style.RESET_ALL}")

            # Support both wrapper and direct call
            if hasattr(self.node, "set_network_key"):
                self.node.set_network_key(0, self.network_key)
            else:
                # Fallback to wrapper's new_network which sets the key
                self.node.new_network(key=self.network_key)

            if self.debug:
                print(f"{Fore.BLUE}[DEBUG] ANT+ network key set{Style.RESET_ALL}")

            # Scan for different device types
            device_types = {
                120: "Heart Rate Monitor",
                121: "Speed and Cadence Sensor",
                122: "Cadence Sensor",
                123: "Speed Sensor",
                11: "Power Meter",
                16: "Fitness Equipment",
                17: "Environment Sensor",
            }

            channels = []

            for device_type, name in device_types.items():
                try:
                    if self.debug:
                        print(
                            f"{Fore.BLUE}[DEBUG] Setting up channel for {name} (Type: {device_type})...{Style.RESET_ALL}"
                        )

                    channel = self.node.new_channel(ChannelType.BIDIRECTIONAL_RECEIVE)

                    if self.debug:
                        print(f"{Fore.BLUE}[DEBUG] Channel created: {channel}{Style.RESET_ALL}")

                    # Set up callbacks with debugging
                    def make_callback(dt, dn, ch_ref):
                        requested_state = {"done": False, "attempts": 0}

                        def callback(data):
                            if self.debug:
                                print(
                                    f"{Fore.BLUE}[DEBUG] Data received on {dn} channel: {[hex(x) for x in data]}{Style.RESET_ALL}"
                                )
                            chan_id = None
                            # Try to read channel ID until we succeed (limited attempts to avoid spam)
                            if not requested_state["done"] and requested_state["attempts"] < 5:
                                chan_id = getattr(ch_ref, "request_channel_id", lambda: None)()
                                if chan_id:
                                    requested_state["done"] = True
                                else:
                                    requested_state["attempts"] += 1
                            self._on_device_found(data, dt, dn, chan_id)

                        return callback

                    callback = make_callback(device_type, name, channel)
                    channel.on_broadcast_data = callback
                    channel.on_burst_data = callback

                    if self.debug:
                        print(f"{Fore.BLUE}[DEBUG] Setting channel parameters...{Style.RESET_ALL}")

                    channel.set_period(8070)  # Standard ANT+ period
                    channel.set_search_timeout(self.scan_timeout)
                    channel.set_rf_freq(57)  # ANT+ frequency
                    channel.set_id(0, device_type, 0)  # Listen for any device ID of this type
                    # Prefer extended messages when available
                    if hasattr(channel, "enable_extended_messages"):
                        channel.enable_extended_messages(True)
                    # Prefer extended messages when available (device id metadata)
                    if hasattr(channel, "enable_extended_messages"):
                        channel.enable_extended_messages(True)

                    if self.debug:
                        print(f"{Fore.BLUE}[DEBUG] Opening channel for {name}...{Style.RESET_ALL}")

                    channel.open()
                    channels.append(channel)
                    print(f"{Fore.GREEN}Scanning for {name} (Type: {device_type}){Style.RESET_ALL}")

                    if self.debug:
                        print(f"{Fore.BLUE}[DEBUG] Channel opened successfully for {name}{Style.RESET_ALL}")

                except Exception as e:
                    print(f"{Fore.RED}Failed to set up channel for {name}: {e}{Style.RESET_ALL}")
                    if self.debug:
                        import traceback

                        print(f"{Fore.RED}[DEBUG] Channel setup error traceback:{Style.RESET_ALL}")
                        traceback.print_exc()

            if self.debug:
                print(f"{Fore.BLUE}[DEBUG] Set up {len(channels)} channels successfully{Style.RESET_ALL}")

            # Scan for the specified timeout period
            self.scanning = True
            start_time = time.time()

            if self.debug:
                print(f"{Fore.BLUE}[DEBUG] Starting scan loop...{Style.RESET_ALL}")

            scan_iterations = 0
            while self.scanning and (time.time() - start_time) < self.scan_timeout:
                time.sleep(0.1)
                scan_iterations += 1

                # Debug progress every 50 iterations (5 seconds)
                if self.debug and scan_iterations % 50 == 0:
                    elapsed = time.time() - start_time
                    remaining = self.scan_timeout - elapsed
                    print(
                        f"{Fore.BLUE}[DEBUG] Scan progress: {elapsed:.1f}s elapsed, {remaining:.1f}s remaining, {len(self.found_devices)} devices found{Style.RESET_ALL}"
                    )

            if self.debug:
                print(f"{Fore.BLUE}[DEBUG] Scan loop completed after {scan_iterations} iterations{Style.RESET_ALL}")

            print(f"{Fore.CYAN}Scan completed. Found {len(self.found_devices)} devices.{Style.RESET_ALL}")

            # Close channels and stop node
            if self.debug:
                print(f"{Fore.BLUE}[DEBUG] Closing {len(channels)} channels...{Style.RESET_ALL}")

            for i, channel in enumerate(channels):
                try:
                    if self.debug:
                        print(f"{Fore.BLUE}[DEBUG] Closing channel {i+1}/{len(channels)}...{Style.RESET_ALL}")
                    channel.close()
                except Exception as e:
                    if self.debug:
                        print(f"{Fore.RED}[DEBUG] Error closing channel {i+1}: {e}{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}Error during device scan: {e}{Style.RESET_ALL}")
            if self.debug:
                import traceback

                print(f"{Fore.RED}[DEBUG] Full error traceback:{Style.RESET_ALL}")
                traceback.print_exc()

        finally:
            if self.node:
                try:
                    if self.debug:
                        print(f"{Fore.BLUE}[DEBUG] Stopping ANT+ node...{Style.RESET_ALL}")
                    self.node.stop()
                    if self.debug:
                        print(f"{Fore.BLUE}[DEBUG] ANT+ node stopped successfully{Style.RESET_ALL}")
                except Exception as e:
                    if self.debug:
                        print(f"{Fore.RED}[DEBUG] Error stopping node: {e}{Style.RESET_ALL}")

        return self.found_devices

    def _on_device_found(self, data: List[int], device_type: int, device_name: str, chan_id=None):
        """Callback for when device data is received."""
        if self.debug:
            print(
                f"{Fore.BLUE}[DEBUG] Processing device data: {[hex(x) for x in data]} from {device_name}{Style.RESET_ALL}"
            )

        if len(data) < 2:
            if self.debug:
                print(f"{Fore.YELLOW}[DEBUG] Insufficient data length: {len(data)}, skipping{Style.RESET_ALL}")
            return

        try:
            # Only persist when we have a valid channel ID; avoid guessing from payload
            if not chan_id:
                if self.debug:
                    print(
                        f"{Fore.YELLOW}[DEBUG] Channel ID not available yet; skipping persistence for {device_name}{Style.RESET_ALL}"
                    )
                return
            device_id, dev_type_resp, transmission_type = chan_id
            # Ensure types align
            if dev_type_resp != device_type:
                device_type = dev_type_resp

            if self.debug:
                print(
                    f"{Fore.BLUE}[DEBUG] Extracted device ID: {device_id} from bytes [{hex(data[0])}, {hex(data[1])}]{Style.RESET_ALL}"
                )

            device_key = f"{device_type}_{device_id}"

            if device_key not in self.found_devices:
                extra = {}
                # Parse common device info pages 80/81 if present
                extra = parse_common_pages(bytes(data))

                self.found_devices[device_key] = {
                    "device_id": device_id,
                    "device_type": device_type,
                    "transmission_type": transmission_type,
                    "device_name": device_name,
                    "description": device_name,
                    "last_seen": time.time(),
                    "signal_strength": "Good",  # Could be enhanced with RSSI
                }
                # Merge extra fields
                self.found_devices[device_key].update(extra)

                print(f"{Fore.GREEN}Found: {device_name} (ID: {device_id}, Type: {device_type}){Style.RESET_ALL}")

                if self.debug:
                    print(f"{Fore.BLUE}[DEBUG] Added new device to found_devices: {device_key}{Style.RESET_ALL}")
                # Persist after each new device found using shared deep-merge
                try:
                    deep_merge_save(
                        "found_devices.json",
                        device_id,
                        device_type,
                        transmission_type,
                        base_extra=extra or None,
                        manufacturers=self.manufacturer_map,
                        rate_limit_secs=30,
                        last_save_times=self.last_save_times,
                    )
                except Exception:
                    pass
            else:
                # Update last seen time
                self.found_devices[device_key]["last_seen"] = time.time()
                # Merge any extra info from common pages
                try:
                    extra = parse_common_pages(bytes(data))
                    if extra:
                        self.found_devices[device_key].update(extra)
                        deep_merge_save(
                            "found_devices.json",
                            device_id,
                            device_type,
                            transmission_type,
                            base_extra=extra,
                            manufacturers=self.manufacturer_map,
                            rate_limit_secs=30,
                            last_save_times=self.last_save_times,
                        )
                except Exception:
                    pass
                if self.debug:
                    print(f"{Fore.BLUE}[DEBUG] Updated last_seen for existing device: {device_key}{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}Error processing device data: {e}{Style.RESET_ALL}")
            if self.debug:
                import traceback

                print(f"{Fore.RED}[DEBUG] Device processing error traceback:{Style.RESET_ALL}")
                traceback.print_exc()

    def save_found_devices(self, filename: str):
        """Save found devices to a JSON file."""
        try:
            # Load existing devices (if any) and merge updates
            try:
                with open(filename, "r") as f:
                    existing = json.load(f)
            except FileNotFoundError:
                existing = {}

            merged = existing.copy()
            merged.update(self.found_devices or {})

            with open(filename, "w") as f:
                json.dump(merged, f, indent=2)
            print(f"{Fore.GREEN}Saved {len(merged)} devices to {filename}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error saving devices: {e}{Style.RESET_ALL}")

    def load_found_devices(self, filename: str) -> Dict:
        """Load previously found devices from a JSON file."""
        try:
            with open(filename, "r") as f:
                devices = json.load(f)
            print(f"{Fore.GREEN}Loaded {len(devices)} devices from {filename}{Style.RESET_ALL}")
            return devices
        except FileNotFoundError:
            print(f"{Fore.YELLOW}No existing device file found: {filename}{Style.RESET_ALL}")
            return {}
        except Exception as e:
            print(f"{Fore.RED}Error loading devices: {e}{Style.RESET_ALL}")
            return {}

    def stop_scan(self):
        """Stop the current scan."""
        self.scanning = False


def main():
    """Test the device scanner."""
    # ANT+ network key
    network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

    print(f"{Fore.YELLOW}ANT+ Device Scanner (Debug Mode){Style.RESET_ALL}")

    # Check for ANT+ USB stick first
    usb_detector = ANTUSBDetector()
    print("Checking for ANT+ USB stick...")

    if not usb_detector.check_usb_permissions():
        usb_detector.print_setup_instructions()
        return

    devices = usb_detector.detect_ant_sticks()
    if not devices:
        print(f"{Fore.YELLOW}No ANT+ USB sticks found.{Style.RESET_ALL}")
        usb_detector.print_setup_instructions()
        return

    print(f"{Fore.GREEN}✓ ANT+ USB stick detected!{Style.RESET_ALL}")

    # Enable debugging for standalone testing
    scanner = DeviceScanner(network_key, scan_timeout=30, debug=True)

    print("Make sure your ANT+ devices are active and transmitting...")

    # Scan for devices
    devices = scanner.scan_for_devices()

    # Save found devices
    scanner.save_found_devices("found_devices.json")

    # Display results
    if devices:
        print(f"\n{Fore.CYAN}Found Devices:{Style.RESET_ALL}")
        for key, device in devices.items():
            print(f"  {device['device_name']} - ID: {device['device_id']}, Type: {device['device_type']}")
    else:
        print(f"\n{Fore.YELLOW}No devices found. Make sure devices are active and transmitting.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
