#!/usr/bin/env python3
"""
PyANTDisplay - Configuration Manager

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

Handles configuration loading, saving, and device configuration.
"""

import json
import sys

import yaml
from colorama import Fore, Style

from ..services.device_config import DeviceConfigurationService


class ConfigManager:
    """Manages application configuration and device setup."""
    
    def __init__(self, config_file: str = "config/config.yaml"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(self.config_file, "r") as f:
                config = yaml.safe_load(f)
            print(f"{Fore.GREEN}Loaded configuration from {self.config_file}{Style.RESET_ALL}")
            return config
        except FileNotFoundError:
            print(f"{Fore.RED}Configuration file {self.config_file} not found{Style.RESET_ALL}")
            sys.exit(1)
        except Exception as e:
            print(f"{Fore.RED}Error loading configuration: {e}{Style.RESET_ALL}")
            sys.exit(1)

    def save_config(self):
        """Save current configuration to YAML file."""
        try:
            with open(self.config_file, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            print(f"{Fore.GREEN}Configuration saved to {self.config_file}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error saving configuration: {e}{Style.RESET_ALL}")

    def configure_devices_interactive(self):
        """Interactive device configuration."""
        device_config_service = DeviceConfigurationService(self.config)
        if device_config_service.configure_devices_interactive():
            # Save configuration after successful configuration
            self.save_config()