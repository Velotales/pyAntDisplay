#!/usr/bin/env python3
"""
PyANTDisplay - ANT+ Device Data Display

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

"""
PyANTDisplay - ANT+ Device Data Display

A Python application for reading data from ANT+ devices using an ANT+ USB stick.
Supports heart rate monitors and bike sensors (speed/cadence) with device discovery
and configuration capabilities.
"""

__version__ = "1.0.0"
__author__ = "Velotales"
__email__ = "velotales@users.noreply.github.com"

from .services.device_scanner import DeviceScanner
from .devices.bike_sensor import BikeSensor
from .devices.heart_rate_monitor import HeartRateMonitor
from .utils.usb_detector import ANTUSBDetector

__all__ = [
    "DeviceScanner",
    "HeartRateMonitor",
    "BikeSensor",
    "ANTUSBDetector",
]
