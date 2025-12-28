#!/usr/bin/env python3
"""
PyANTDisplay - Application Launcher

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

Handles application mode dispatching and initialization.
"""

from typing import Optional

from .services.app_modes import AppModeService


class ApplicationLauncher:
    """Handles application mode dispatching and initialization."""

    def __init__(self):
        self.mode_service = AppModeService()

    def run_menu(
        self, app_config: Optional[str] = None, local_config: Optional[str] = None
    ):
        """Run the interactive menu mode."""
        self.mode_service.run_menu(app_config, local_config)

    def run_scan(
        self, app_config: str, local_config: Optional[str] = None, debug: bool = False
    ):
        """Run device scanning mode."""
        self.mode_service.run_scan(app_config, local_config, debug)

    def run_list(self, app_config: str, local_config: Optional[str] = None):
        """List discovered devices."""
        self.mode_service.run_list(app_config, local_config)

    def run_monitor(self, sensor_config: str, save_path: str, debug: bool = False):
        """Run live monitoring mode with curses dashboard."""
        self.mode_service.run_monitor(sensor_config, save_path, debug)

    def run_mqtt(
        self,
        sensor_config: str,
        save_path: str,
        app_config: str,
        local_config: Optional[str] = None,
        debug: bool = False,
    ):
        """Run MQTT publishing mode."""
        self.mode_service.run_mqtt(
            sensor_config, save_path, app_config, local_config, debug
        )
