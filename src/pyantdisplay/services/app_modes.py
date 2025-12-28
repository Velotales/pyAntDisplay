#!/usr/bin/env python3
"""
PyANTDisplay - Application Mode Service

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

Handles different application modes and their orchestration.
"""

import json
import time
from typing import Optional

from colorama import Fore, Style

from .device_scanner import DeviceScanner
from .config_manager import ConfigManager
from ..managers.device_manager import DeviceManager
from ..ui.menu_manager import MenuManager
from ..ui.live_monitor import ANT_PLUS_NETWORK_KEY, LiveMonitor
from .mqtt_monitor import MqttMonitor
from ..utils.config_loader import ConfigLoader
from ..utils.usb_detector import ANTUSBDetector


class AppModeService:
    """Handles different application modes and their orchestration."""

    def __init__(self):
        self.config_loader = ConfigLoader()

    def run_menu(
        self, app_config: Optional[str] = None, local_config: Optional[str] = None
    ):
        """Run the interactive menu mode."""
        try:
            # Initialize components
            config_file = local_config or app_config or "config/config.yaml"
            config_manager = ConfigManager(config_file)
            device_manager = DeviceManager(config_manager.config)
            usb_detector = ANTUSBDetector()
            menu_manager = MenuManager(config_manager, device_manager, usb_detector)

            # Check for USB stick on startup
            menu_manager.check_usb_on_startup()

            # Show interactive menu
            menu_manager.show_menu()

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Application interrupted{Style.RESET_ALL}")
        finally:
            # Cleanup
            if "device_manager" in locals():
                device_manager.stop()

    def run_scan(
        self, app_config: str, local_config: Optional[str] = None, debug: bool = False
    ):
        """Run device scanning mode."""
        cfg = self.config_loader.load_app_config(app_config, local_config)
        key = cfg.get("ant_network", {}).get("key", ANT_PLUS_NETWORK_KEY)
        timeout = cfg.get("app", {}).get("scan_timeout", 30)
        backend_pref = cfg.get("app", {}).get("backend", None)
        save_path = cfg.get("app", {}).get("found_devices_file", "found_devices.json")

        print(f"{Fore.CYAN}ANT+ Device Scanner{Style.RESET_ALL}")
        scanner = DeviceScanner(
            key, scan_timeout=timeout, debug=debug, backend_preference=backend_pref
        )
        devices = scanner.scan_for_devices()
        scanner.save_found_devices(save_path)
        print(
            f"{Fore.GREEN}Saved {len(devices)} devices to {save_path}{Style.RESET_ALL}"
        )

    def run_list(self, app_config: str, local_config: Optional[str] = None):
        """List discovered devices."""
        cfg = self.config_loader.load_app_config(app_config, local_config)
        save_path = cfg.get("app", {}).get("found_devices_file", "found_devices.json")

        try:
            with open(save_path, "r") as f:
                devices = json.load(f)
        except FileNotFoundError:
            print(f"{Fore.YELLOW}No device file found: {save_path}{Style.RESET_ALL}")
            return
        except Exception as e:
            print(f"{Fore.RED}Error reading {save_path}: {e}{Style.RESET_ALL}")
            return

        if not devices:
            print(f"{Fore.YELLOW}No devices in {save_path}{Style.RESET_ALL}")
            return

        self._display_device_list(devices)

    def run_monitor(self, sensor_config: str, save_path: str, debug: bool = False):
        """Run live monitoring mode with curses dashboard."""
        mon = LiveMonitor(sensor_config, save_path, debug=debug)
        mon.run()

    def run_mqtt(
        self,
        sensor_config: str,
        save_path: str,
        app_config: str,
        local_config: Optional[str] = None,
        debug: bool = False,
    ):
        """Run MQTT publishing mode."""
        mon = MqttMonitor(
            sensor_config_path=sensor_config,
            save_path=save_path,
            app_config_path=app_config,
            local_app_config_path=local_config,
            debug=debug,
        )
        mon.run()

    def _display_device_list(self, devices: dict):
        """Display devices in a formatted list."""
        print(f"\n{Fore.CYAN}Found ANT+ Devices ({len(devices)}){Style.RESET_ALL}")
        print(f"{'ID':<8} {'Type':<6} {'Key':<15} {'Last Seen':<20}")
        print("-" * 60)
        for k, v in devices.items():
            last = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(v.get("last_seen", 0))
            )
            print(
                f"{v.get('device_id', '-'):<8} {v.get('device_type', '-'):<6} {k:<15} {last:<20}"
            )
