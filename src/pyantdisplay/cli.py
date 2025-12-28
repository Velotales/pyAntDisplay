#!/usr/bin/env python3
"""
PyANTDisplay - CLI Handler

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

Handles command line interface parsing and routing.
"""

import argparse

from .launcher import ApplicationLauncher


class CLIHandler:
    """Handles command line interface parsing and routing."""
    
    def __init__(self):
        self.launcher = ApplicationLauncher()

    def create_parser(self) -> argparse.ArgumentParser:
        """Create and configure argument parser."""
        parser = argparse.ArgumentParser(description="PyANTDisplay entry point")
        parser.add_argument(
            "--mode", 
            choices=["menu", "monitor", "scan", "list", "mqtt"], 
            default="menu", 
            help="Program mode"
        )
        parser.add_argument(
            "--config", 
            type=str, 
            default="config/sensor_map.yaml", 
            help="Sensor map config for monitor/mqtt mode"
        )
        parser.add_argument(
            "--save", 
            type=str, 
            default="found_devices.json", 
            help="Device persistence file for monitor/mqtt mode"
        )
        parser.add_argument(
            "--app-config", 
            type=str, 
            default="config/config.yaml", 
            help="App config for scan/list/menu modes"
        )
        parser.add_argument(
            "--local-config", 
            type=str, 
            default=None, 
            help="Optional local app config that overrides base config"
        )
        parser.add_argument(
            "--debug", 
            action="store_true", 
            help="Enable verbose logging where supported"
        )
        return parser

    def handle_args(self, args):
        """Route arguments to appropriate application mode."""
        if args.mode == "menu":
            self.launcher.run_menu(args.app_config, args.local_config)
        elif args.mode == "monitor":
            self.launcher.run_monitor(args.config, args.save, debug=args.debug)
        elif args.mode == "scan":
            self.launcher.run_scan(args.app_config, args.local_config, debug=args.debug)
        elif args.mode == "list":
            self.launcher.run_list(args.app_config, args.local_config)
        elif args.mode == "mqtt":
            self.launcher.run_mqtt(args.config, args.save, args.app_config, args.local_config, debug=args.debug)

    def run(self):
        """Parse arguments and run the application."""
        parser = self.create_parser()
        args = parser.parse_args()
        self.handle_args(args)